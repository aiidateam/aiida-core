# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Local transport
"""

###
### GP: a note on the local transport:
### I believe that we must not use os.chdir to keep track of the folder
### in which we are, since this may have very nasty side effects in other
### parts of code, and make things not thread-safe.
### we should instead keep track internally of the 'current working directory'
### in the exact same way as paramiko does already.

import errno
import io
import os
import shutil
import subprocess
import glob

from aiida.transports import cli as transport_cli
from aiida.transports.transport import Transport, TransportInternalError


# refactor or raise the limit: issue #1784
# pylint: disable=too-many-public-methods
class LocalTransport(Transport):
    """
    Support copy and command execution on the same host on which AiiDA is running via direct file copy and
    execution commands.

    Note that the environment variables are copied from the submitting process, so you might need to clean it
    with a ``prepend_text``. For example, the AiiDA daemon sets a ``PYTHONPATH``, so you might want to add
    ``unset PYTHONPATH`` if you plan on running calculations that use Python.
    """

    # There are no valid parameters for the local transport
    _valid_auth_options = []

    # There is no real limit on how fast you can safely connect to a localhost, unlike often the case with SSH transport
    # where the remote computer will rate limit the number of connections.
    _DEFAULT_SAFE_OPEN_INTERVAL = 0.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The `_internal_dir` will emulate the concept of working directory, as the real current working directory is
        # not to be changed to prevent bug-prone situations
        self._internal_dir = None

        # Just to avoid errors
        self._machine = kwargs.pop('machine', None)
        if self._machine and self._machine != 'localhost':
            self.logger.debug('machine was passed, but it is not localhost')

    def open(self):
        """
        Opens a local transport channel

        :raise aiida.common.InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation

        if self._is_open:
            raise InvalidOperation('Cannot open the transport twice')

        self._internal_dir = os.path.expanduser('~')
        self._is_open = True
        return self

    def close(self):
        """
        Closes the local transport channel

        :raise aiida.common.InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation

        if not self._is_open:
            raise InvalidOperation('Cannot close the transport: it is already closed')
        self._is_open = False

    def __str__(self):
        """
        Return a description as a string.
        """
        return 'local [{}]'.format('OPEN' if self._is_open else 'CLOSED')

    @property
    def curdir(self):
        """
        Returns the _internal_dir, if the channel is open.
        If possible, use getcwd() instead!
        """
        if self._is_open:
            return os.path.realpath(self._internal_dir)

        raise TransportInternalError('Error, local method called for LocalTransport without opening the channel first')

    def chdir(self, path):
        """
        Changes directory to path, emulated internally.
        :param path: path to cd into
        :raise OSError: if the directory does not have read attributes.
        """
        new_path = os.path.join(self.curdir, path)
        if not os.path.isdir(new_path):
            raise IOError("'{}' is not a valid directory".format(new_path))
        elif not os.access(new_path, os.R_OK):
            raise IOError("Do not have read permission to '{}'".format(new_path))

        self._internal_dir = os.path.normpath(new_path)

    def chown(self, path, uid, gid):
        os.chown(path, uid, gid)

    def normalize(self, path='.'):
        """
        Normalizes path, eliminating double slashes, etc..
        :param path: path to normalize
        """
        return os.path.realpath(os.path.join(self.curdir, path))

    def getcwd(self):
        """
        Returns the current working directory, emulated by the transport
        """
        return self.curdir

    @staticmethod
    def _os_path_split_asunder(path):
        """Used by makedirs, Takes path (a str) and returns a list deconcatenating the path."""
        parts = []
        while True:
            newpath, tail = os.path.split(path)
            if newpath == path:
                assert not tail
                if path:
                    parts.append(path)
                break
            parts.append(tail)
            path = newpath
        parts.reverse()
        return parts

    def makedirs(self, path, ignore_existing=False):
        """
        Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param path: directory to create
        :param ignore_existing: if set to true, it doesn't give any error
                     if the leaf directory does already exist

        :raise OSError: If the directory already exists and is not ignore_existing
        """
        # check to avoid creation of empty dirs
        path = os.path.normpath(path)

        the_path = os.path.join(self.curdir, path)
        to_create = self._os_path_split_asunder(the_path)
        this_dir = ''
        for count, element in enumerate(to_create):
            this_dir = os.path.join(this_dir, element)
            if count + 1 == len(to_create) and self.isdir(this_dir) and ignore_existing:
                return
            if count + 1 == len(to_create) and self.isdir(this_dir) and not ignore_existing:
                os.mkdir(this_dir)
            if not os.path.exists(this_dir):
                os.mkdir(this_dir)

    def mkdir(self, path, ignore_existing=False):
        """
        Create a folder (directory) named path.

        :param path: name of the folder to create
        :param ignore_existing: if True, does not give any error if the
                directory already exists

        :raise OSError: If the directory already exists.
        """
        if ignore_existing and self.isdir(path):
            return

        os.mkdir(os.path.join(self.curdir, path))

    def rmdir(self, path):
        """
        Removes a folder at location path.
        :param path: path to remove
        """
        os.rmdir(os.path.join(self.curdir, path))

    def isdir(self, path):
        """
        Checks if 'path' is a directory.
        :return: a boolean
        """
        if not path:
            return False

        return os.path.isdir(os.path.join(self.curdir, path))

    def chmod(self, path, mode):
        """
        Changes permission bits of object at path
        :param path: path to modify
        :param mode: permission bits

        :raise IOError: if path does not exist.
        """
        if not path:
            raise IOError('Directory not given in input')
        real_path = os.path.join(self.curdir, path)
        if not os.path.exists(real_path):
            raise IOError('Directory not given in input')
        else:
            os.chmod(real_path, mode)

    # please refactor: issue #1782
    # pylint: disable=too-many-branches
    def put(self, localpath, remotepath, *args, **kwargs):
        """
        Copies a file or a folder from localpath to remotepath.
        Automatically redirects to putfile or puttree.

        :param localpath: absolute path to local file
        :param remotepath: path to remote file
        :param dereference: if True follows symbolic links.
                                 Default = True
        :param overwrite: if True overwrites remotepath.
                                 Default = False

        :raise IOError: if remotepath is not valid
        :raise ValueError: if localpath is not valid
        """
        dereference = kwargs.get('dereference', args[0] if args else True)
        overwrite = kwargs.get('overwrite', args[1] if len(args) > 1 else True)
        ignore_nonexisting = kwargs.get('ignore_noexisting', args[2] if len(args) > 2 else False)
        if not remotepath:
            raise IOError('Input remotepath to put function must be a non empty string')
        if not localpath:
            raise ValueError('Input localpath to put function must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Source must be an absolute path')

        if self.has_magic(localpath):
            if self.has_magic(remotepath):
                raise ValueError('Pathname patterns are not allowed in the remotepath')

            to_copy_list = glob.glob(localpath)  # using local glob here

            rename_remote = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if self.isfile(remotepath):
                    raise OSError('Remote remotepath is not a directory')
                # I can't scp more than one file in a non existing directory
                elif not self.path_exists(remotepath):  # questo dovrebbe valere solo per file
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_remote = True

            for source_path in to_copy_list:
                if os.path.isfile(source_path):
                    if rename_remote:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        subpath = os.path.join(remotepath, os.path.split(source_path)[1])
                        self.putfile(source_path, subpath, overwrite)

                    elif self.isdir(remotepath):  # one file to copy in '.'
                        subpath = os.path.join(remotepath, os.path.split(source_path)[1])
                        self.putfile(source_path, subpath, overwrite)
                    else:  # one file to copy on one file
                        self.putfile(source_path, remotepath, overwrite)
                else:
                    self.puttree(source_path, remotepath, dereference, overwrite)

        else:
            if os.path.isdir(localpath):
                self.puttree(localpath, remotepath, dereference, overwrite)
            elif os.path.isfile(localpath):
                if self.isdir(remotepath):
                    full_destination = os.path.join(remotepath, os.path.split(localpath)[1])
                else:
                    full_destination = remotepath

                self.putfile(localpath, full_destination, overwrite)
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise OSError('The local path {} does not exist'.format(localpath))

    def putfile(self, localpath, remotepath, *args, **kwargs):
        """
        Copies a file from localpath to remotepath.
        Automatically redirects to putfile or puttree.

        :param localpath: absolute path to local file
        :param remotepath: path to remote file
        :param overwrite: if True overwrites remotepath
                                 Default = False

        :raise IOError: if remotepath is not valid
        :raise ValueError: if localpath is not valid
        :raise OSError: if localpath does not exist
        """
        overwrite = kwargs.get('overwrite', args[0] if args else True)
        if not remotepath:
            raise IOError('Input remotepath to putfile must be a non empty string')
        if not localpath:
            raise ValueError('Input localpath to putfile must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Source must be an absolute path')

        if not os.path.exists(localpath):
            raise OSError('Source does not exists')

        the_destination = os.path.join(self.curdir, remotepath)
        if os.path.exists(the_destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copyfile(localpath, the_destination)

    def puttree(self, localpath, remotepath, *args, **kwargs):
        """
        Copies a folder recursively from localpath to remotepath.
        Automatically redirects to putfile or puttree.

        :param localpath: absolute path to local file
        :param remotepath: path to remote file
        :param dereference: follow symbolic links.
                                 Default = True
        :param overwrite: if True overwrites remotepath.
                               Default = False

        :raise IOError: if remotepath is not valid
        :raise ValueError: if localpath is not valid
        :raise OSError: if localpath does not exist
        """
        dereference = kwargs.get('dereference', args[0] if args else True)
        overwrite = kwargs.get('overwrite', args[1] if len(args) > 1 else True)
        if not remotepath:
            raise IOError('Input remotepath to putfile must be a non empty string')
        if not localpath:
            raise ValueError('Input localpath to putfile must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Source must be an absolute path')

        if not os.path.exists(localpath):
            raise OSError('Source does not exists')

        if self.path_exists(remotepath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if self.isfile(remotepath):
            raise OSError('Cannot copy a directory into a file')

        if self.isdir(remotepath):
            remotepath = os.path.join(remotepath, os.path.split(localpath)[1])

        the_destination = os.path.join(self.curdir, remotepath)

        shutil.copytree(localpath, the_destination, symlinks=not dereference)

    def rmtree(self, path):
        """
        Remove tree as rm -r would do

        :param path: a string to path
        """
        the_path = os.path.join(self.curdir, path)
        try:
            shutil.rmtree(the_path)
        except OSError as exception:
            if exception.errno == errno.ENOENT:
                pass
            elif exception.errno == errno.ENOTDIR:
                os.remove(the_path)
            else:
                raise IOError(exception)

    # please refactor: issue #1781
    # pylint: disable=too-many-branches
    def get(self, remotepath, localpath, *args, **kwargs):
        """
        Copies a folder or a file recursively from 'remote' remotepath to
        'local' localpath.
        Automatically redirects to getfile or gettree.

        :param remotepath: path to local file
        :param localpath: absolute path to remote file
        :param dereference: follow symbolic links
                                 default = True
        :param overwrite: if True overwrites localpath
                               default = False

        :raise IOError: if 'remote' remotepath is not valid
        :raise ValueError: if 'local' localpath is not valid
        """
        dereference = kwargs.get('dereference', args[0] if args else True)
        overwrite = kwargs.get('overwrite', args[1] if len(args) > 1 else True)
        ignore_nonexisting = kwargs.get('ignore_nonexisting', args[2] if len(args) > 2 else False)
        if not localpath:
            raise ValueError('Input localpath to get function must be a non empty string')
        if not remotepath:
            raise IOError('Input remotepath to get function must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Destination must be an absolute path')

        if self.has_magic(remotepath):
            if self.has_magic(localpath):
                raise ValueError('Pathname patterns are not allowed in the localpath')
            to_copy_list = self.glob(remotepath)

            rename_local = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if os.path.isfile(localpath):
                    raise IOError('Remote localpath is not a directory')
                # I can't scp more than one file in a non existing directory
                elif not os.path.exists(localpath):  # this should hold only for files
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_local = True

            for source in to_copy_list:
                if self.isfile(source):
                    if rename_local:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        subpath = os.path.join(localpath, os.path.split(source)[1])
                        self.getfile(source, subpath, overwrite)
                    else:  # one file to copy on one file
                        self.getfile(source, localpath, overwrite)
                else:
                    self.gettree(source, localpath, dereference, overwrite)

        else:
            if self.isdir(remotepath):
                self.gettree(remotepath, localpath, dereference, overwrite)
            elif self.isfile(remotepath):
                if os.path.isdir(localpath):
                    subpath = os.path.join(localpath, os.path.split(remotepath)[1])
                    self.getfile(remotepath, subpath, overwrite)
                else:
                    self.getfile(remotepath, localpath, overwrite)
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise IOError('The remote path {} does not exist'.format(remotepath))

    def getfile(self, remotepath, localpath, *args, **kwargs):
        """
        Copies a file recursively from 'remote' remotepath to
        'local' localpath.

        :param remotepath: path to local file
        :param localpath: absolute path to remote file
        :param overwrite: if True overwrites localpath.
                               Default = False

        :raise IOError if 'remote' remotepath is not valid or not found
        :raise ValueError: if 'local' localpath is not valid
        :raise OSError: if unintentionally overwriting
        """
        overwrite = kwargs.get('overwrite', args[0] if args else True)
        if not localpath:
            raise ValueError('Input localpath to get function must be a non empty string')
        if not remotepath:
            raise IOError('Input remotepath to get function must be a non empty string')
        the_source = os.path.join(self.curdir, remotepath)
        if not os.path.exists(the_source):
            raise IOError('Source not found')
        if not os.path.isabs(localpath):
            raise ValueError('Destination must be an absolute path')
        if os.path.exists(localpath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copyfile(the_source, localpath)

    def gettree(self, remotepath, localpath, *args, **kwargs):
        """
        Copies a folder recursively from 'remote' remotepath to
        'local' localpath.

        :param remotepath: path to local file
        :param localpath: absolute path to remote file
        :param dereference: follow symbolic links. Default = True
        :param overwrite: if True overwrites localpath. Default = False

        :raise IOError: if 'remote' remotepath is not valid
        :raise ValueError: if 'local' localpath is not valid
        :raise OSError: if unintentionally overwriting
        """
        dereference = kwargs.get('dereference', args[0] if args else True)
        overwrite = kwargs.get('overwrite', args[1] if len(args) > 1 else True)
        if not remotepath:
            raise IOError('Remotepath must be a non empty string')
        if not localpath:
            raise ValueError('Localpaths must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Localpaths must be an absolute path')

        if not self.isdir(remotepath):
            raise IOError('Input remotepath is not a folder: {}'.format(remotepath))

        if os.path.exists(localpath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if os.path.isfile(localpath):
            raise OSError('Cannot copy a directory into a file')

        if os.path.isdir(localpath):
            localpath = os.path.join(localpath, os.path.split(remotepath)[1])

        the_source = os.path.join(self.curdir, remotepath)
        shutil.copytree(the_source, localpath, symlinks=not dereference)

    # please refactor: issue #1780 on github
    # pylint: disable=too-many-branches
    def copy(self, remotesource, remotedestination, dereference=False, recursive=True):
        """
        Copies a file or a folder from 'remote' remotesource to 'remote' remotedestination.
        Automatically redirects to copyfile or copytree.

        :param remotesource: path to local file
        :param remotedestination: path to remote file
        :param dereference: follow symbolic links. Default = False
        :param recursive: if True copy directories recursively, otherwise only copy the specified file(s)
        :type recursive: bool

        :raise ValueError: if 'remote' remotesource or remotedestinationis not valid
        :raise OSError: if remotesource does not exist
        """
        if not remotesource:
            raise ValueError('Input remotesource to copy must be a non empty object')
        if not remotedestination:
            raise ValueError('Input remotedestination to copy must be a non empty object')
        if not self.has_magic(remotesource):
            if not os.path.exists(os.path.join(self.curdir, remotesource)):
                raise OSError('Source not found')
        if self.normalize(remotesource) == self.normalize(remotedestination):
            raise ValueError('Cannot copy from itself to itself')

            # # by default, overwrite old files
        #        if not remotedestination .startswith('.'):
        #            if self.isfile(remotedestination) or self.isdir(remotedestination):
        #                self.rmtree(remotedestination)

        the_destination = os.path.join(self.curdir, remotedestination)

        if self.has_magic(remotesource):
            if self.has_magic(remotedestination):
                raise ValueError('Pathname patterns are not allowed in the remotedestination')

            to_copy_list = self.glob(remotesource)

            if len(to_copy_list) > 1:
                if not self.path_exists(remotedestination) or self.isfile(remotedestination):
                    raise OSError("Can't copy more than one file in the same remotedestination file")

            for source in to_copy_list:
                # If s is an absolute path, then the_s = s
                the_s = os.path.join(self.curdir, source)
                if self.isfile(source):
                    # With shutil, use the full path (the_s)
                    shutil.copy(the_s, the_destination)
                else:
                    # With self.copytree, the (possible) relative path is OK
                    self.copytree(source, remotedestination, dereference)

        else:
            # If s is an absolute path, then the_source = remotesource
            the_source = os.path.join(self.curdir, remotesource)
            if self.isfile(remotesource):
                # With shutil, use the full path (the_source)
                shutil.copy(the_source, the_destination)
            else:
                # With self.copytree, the (possible) relative path is OK
                self.copytree(remotesource, remotedestination, dereference)

    def copyfile(self, remotesource, remotedestination, dereference=False):
        """
        Copies a file from 'remote' remotesource to
        'remote' remotedestination.

        :param remotesource: path to local file
        :param remotedestination: path to remote file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves
        :type dereference: bool
        :raise ValueError: if 'remote' remotesource or remotedestination is not valid
        :raise OSError: if remotesource does not exist
        """
        if not remotesource:
            raise ValueError('Input remotesource to copyfile must be a non empty object')
        if not remotedestination:
            raise ValueError('Input remotedestination to copyfile must be a non empty object')
        the_source = os.path.join(self.curdir, remotesource)
        the_destination = os.path.join(self.curdir, remotedestination)
        if not os.path.exists(the_source):
            raise OSError('Source not found')

        if not dereference and os.path.islink(remotesource):
            linkto = os.readlink(the_source)
            os.symlink(linkto, the_destination)
        else:
            shutil.copyfile(the_source, the_destination)

    def copytree(self, remotesource, remotedestination, dereference=False):
        """
        Copies a folder from 'remote' remotesource to
        'remote' remotedestination.

        :param remotesource: path to local file
        :param remotedestination: path to remote file
        :param dereference: follow symbolic links. Default = False

        :raise ValueError: if 'remote' remotesource or remotedestination is not valid
        :raise OSError: if remotesource does not exist
        """
        if not remotesource:
            raise ValueError('Input remotesource to copytree must be a non empty object')
        if not remotedestination:
            raise ValueError('Input remotedestination to copytree must be a non empty object')
        the_source = os.path.join(self.curdir, remotesource)
        the_destination = os.path.join(self.curdir, remotedestination)
        if not os.path.exists(the_source):
            raise OSError('Source not found')

        # Using the Ubuntu default behavior (different from Mac)
        if self.isdir(remotedestination):
            the_destination = os.path.join(the_destination, os.path.split(remotesource)[1])

        shutil.copytree(the_source, the_destination, symlinks=not dereference)

    def get_attribute(self, path):
        """
        Returns an object FileAttribute,
        as specified in aiida.transports.
        :param path: the path of the given file.
        """
        from aiida.transports.util import FileAttribute

        os_attr = os.lstat(os.path.join(self.curdir, path))
        aiida_attr = FileAttribute()
        # map the paramiko class into the aiida one
        # note that paramiko object contains more informations than the aiida
        for key in aiida_attr._valid_fields:  # pylint: disable=protected-access
            aiida_attr[key] = getattr(os_attr, key)
        return aiida_attr

    def _local_listdir(self, path, pattern=None):  # pylint: disable=no-self-use
        """Act on the local folder, for the rest, same as listdir."""
        import re

        if not pattern:
            return os.listdir(path)

        if path.startswith('/'):  # always this is the case in the local plugin
            base_dir = path
        else:
            base_dir = os.path.join(os.getcwd(), path)

        filtered_list = glob.glob(os.path.join(base_dir, pattern))
        if not base_dir.endswith(os.sep):
            base_dir += os.sep
        return [re.sub(base_dir, '', i) for i in filtered_list]

    def listdir(self, path='.', pattern=None):
        """
        :return: a list containing the names of the entries in the directory.
        :param path: default ='.'
        :param pattern: if set, returns the list of files matching pattern.
                     Unix only. (Use to emulate ls * for example)
        """
        the_path = os.path.join(self.curdir, path).strip()
        if not pattern:
            try:
                return os.listdir(the_path)
            except OSError as err:
                exc = IOError(str(err))
                exc.errno = err.errno
                raise exc
        else:
            import re

            filtered_list = glob.glob(os.path.join(the_path, pattern))
            if not the_path.endswith('/'):
                the_path += '/'
            return [re.sub(the_path, '', i) for i in filtered_list]

    def remove(self, path):
        """
        Removes a file at position path.
        """
        os.remove(os.path.join(self.curdir, path))

    def isfile(self, path):
        """
        Checks if object at path is a file.
        Returns a boolean.
        """
        if not path:
            return False
        return os.path.isfile(os.path.join(self.curdir, path))

    def _exec_command_internal(self, command, **kwargs):  # pylint: disable=unused-argument
        """
        Executes the specified command in bash login shell.

        Before the command is executed, changes directory to the current
        working directory as returned by self.getcwd().

        For executing commands and waiting for them to finish, use
        exec_command_wait.
        Otherwise, to end the process, use the proc.wait() method.

        The subprocess is set to have a different process group than the
        main process, so that it is shielded from signals sent to the parent.

        :param  command: the command to execute. The command is assumed to be
            already escaped using :py:func:`aiida.common.escaping.escape_for_bash`.

        :return: a tuple with (stdin, stdout, stderr, proc),
            where stdin, stdout and stderr behave as file-like objects,
            proc is the process object as returned by the
            subprocess.Popen() class.
        """
        # pylint: disable=subprocess-popen-preexec-fn
        from aiida.common.escaping import escape_for_bash

        # Note: The outer shell will eat one level of escaping, while
        # 'bash -l -c ...' will eat another. Thus, we need to escape again.
        command = 'bash -l -c ' + escape_for_bash(command)

        proc = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.getcwd(),
            start_new_session=True
        )

        return proc.stdin, proc.stdout, proc.stderr, proc

    def exec_command_wait(self, command, **kwargs):
        """
        Executes the specified command and waits for it to finish.

        :param command: the command to execute

        :return: a tuple with (return_value, stdout, stderr) where stdout and
                 stderr are strings.
        """
        stdin = kwargs.get('stdin')
        local_stdin, _, _, local_proc = self._exec_command_internal(command)

        if stdin is not None:
            if isinstance(stdin, str):
                filelike_stdin = io.StringIO(stdin)
            else:
                filelike_stdin = stdin

            try:
                for line in filelike_stdin.readlines():
                    local_stdin.write(line.encode('utf-8'))  # the Popen.stdin/out/err are byte streams
            except AttributeError:
                raise ValueError('stdin can only be either a string or a file-like object!')
        else:
            filelike_stdin = None

        local_stdin.flush()
        output_text, stderr_text = local_proc.communicate()

        retval = local_proc.returncode

        return retval, output_text.decode('utf-8'), stderr_text.decode('utf-8')

    def gotocomputer_command(self, remotedir):
        """
        Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened
        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """
        script = ' ; '.join([
            'if [ -d {escaped_remotedir} ]', 'then cd {escaped_remotedir}', 'bash', "else echo ' ** The directory'",
            "echo ' ** {remotedir}'", "echo ' ** seems to have been deleted, I logout...'", 'fi'
        ]).format(escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir)
        cmd = 'bash -c "{}"'.format(script)
        return cmd

    def rename(self, oldpath, newpath):
        """
        Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if src/dst is not found
        :raises ValueError: if src/dst is not a valid string
        """
        if not oldpath:
            raise ValueError('Source {} is not a valid string'.format(oldpath))
        if not newpath:
            raise ValueError('Destination {} is not a valid string'.format(newpath))
        if not os.path.exists(oldpath):
            raise IOError('Source {} does not exist'.format(oldpath))
        if not os.path.exists(newpath):
            raise IOError('Destination {} does not exist'.format(newpath))

        shutil.move(oldpath, newpath)

    def symlink(self, remotesource, remotedestination):
        """
        Create a symbolic link between the remote source and the remote
        remotedestination

        :param remotesource: remote source. Can contain a pattern.
        :param remotedestination: remote destination
        """
        remotesource = os.path.normpath(remotesource)
        remotedestination = os.path.normpath(remotedestination)

        if self.has_magic(remotesource):
            if self.has_magic(remotedestination):
                # if there are patterns in dest, I don't know which name to assign
                raise ValueError('Remotedestination cannot have patterns')

            # find all files matching pattern
            for this_file in self.glob(remotesource):
                # create the name of the link: take the last part of the path
                this_remote_dest = os.path.split(this_file)[-1]

                os.symlink(os.path.join(this_file), os.path.join(self.curdir, remotedestination, this_remote_dest))
        else:
            try:
                os.symlink(remotesource, os.path.join(self.curdir, remotedestination))
            except OSError:
                raise OSError('!!: {}, {}, {}'.format(remotesource, self.curdir, remotedestination))

    def path_exists(self, path):
        """
        Check if path exists
        """
        return os.path.exists(os.path.join(self.curdir, path))


CONFIGURE_LOCAL_CMD = transport_cli.create_configure_cmd('local')
