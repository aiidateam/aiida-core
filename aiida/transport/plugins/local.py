# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
###
### GP: a note on the local transport:
### I believe that we must not use os.chdir to keep track of the folder
### in which we are, since this may have very nasty side effects in other
### parts of code, and make things not thread-safe.
### we should instead keep track internally of the 'current working directory'
### in the exact same way as paramiko does already.

import os, shutil, subprocess
import aiida.transport
from aiida.transport import FileAttribute
import StringIO
import glob
from aiida.common import aiidalogger



class LocalTransport(aiida.transport.Transport):
    """
    Support copy and command execution on the same host on which AiiDA is running via direct file copy and execution commands.
    """
    # There are no valid parameters for the local transport
    _valid_auth_params = []

    def __init__(self, **kwargs):
        super(LocalTransport, self).__init__()

        # _internal_dir will emulate the concept of working directory
        # The real current working directory is not to be changed
        # self._internal_dir = None
        self._is_open = False
        self._internal_dir = None
        # Just to avoid errors
        self._machine = kwargs.pop('machine', None)
        if self._machine and self._machine != 'localhost':
            # TODO: check if we want a different logic
            self.logger.debug('machine was passed, but it is not localhost')
        if kwargs:
            raise ValueError("Input parameters to LocalTransport"
                             " are not recognized")

    def open(self):
        """
        Opens a local transport channel

        :raise InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation

        if self._is_open:
            raise InvalidOperation("Cannot open the transport twice")

        self._internal_dir = os.path.expanduser("~")
        self._is_open = True
        return self

    def close(self):
        """
        Closes the local transport channel

        :raise InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation

        if not self._is_open:
            raise InvalidOperation("Cannot close the transport: "
                                   "it is already closed")
        self._is_open = False

    def __str__(self):
        """
        Return a description as a string.
        """

        return "local [{}]".format("OPEN" if self._is_open else "CLOSED")

    @property
    def curdir(self):
        """
        Returns the _internal_dir, if the channel is open.
        If possible, use getcwd() instead!
        """
        if self._is_open:
            return os.path.realpath(self._internal_dir)
        else:
            raise aiida.transport.TransportInternalError(
                "Error, local method called for LocalTransport "
                "without opening the channel first")

    def chdir(self, path):
        """
        Changes directory to path, emulated internally.
        :param path: path to cd into
        :raise OSError: if the directory does not have read attributes.
        """
        new_path = os.path.join(self.curdir, path)
        if os.access(new_path, os.R_OK):
            self._internal_dir = os.path.normpath(new_path)
        else:
            raise IOError('Not having read permissions')

    def normalize(self, path):
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

    def _os_path_split_asunder(self, path):
        """
        Used by makedirs. Takes path (a str)
        and returns a list deconcatenating the path
        """
        # TODO : test it on windows (sigh!)
        parts = []
        while True:
            newpath, tail = os.path.split(path)
            if newpath == path:
                assert not tail
                if path: parts.append(path)
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
        else:
            return os.path.isdir(os.path.join(self.curdir, path))

    def chmod(self, path, mode):
        """
        Changes permission bits of object at path
        :param path: path to modify
        :param mode: permission bits

        :raise IOError: if path does not exist.
        """
        if not path:
            raise IOError("Directory not given in input")
        real_path = os.path.join(self.curdir, path)
        if not os.path.exists(real_path):
            raise IOError("Directory not given in input")
        else:
            os.chmod(real_path, mode)

    def put(self, source, destination, dereference=True, overwrite=True,
            ignore_nonexisting=False):
        """
        Copies a file or a folder from source to destination.
        Automatically redirects to putfile or puttree.

        :param source: absolute path to local file
        :param destination: path to remote file
        :param dereference: if True follows symbolic links.
                                 Default = True
        :param overwrite: if True overwrites destination.
                                 Default = False

        :raise IOError: if destination is not valid
        :raise ValueError: if source is not valid
        """
        if not destination:
            raise IOError("Input destination to put function "
                          "must be a non empty string")
        if not source:
            raise ValueError("Input source to put function "
                             "must be a non empty string")

        if not os.path.isabs(source):
            raise ValueError("Source must be an absolute path")

        if self.has_magic(source):
            if self.has_magic(destination):
                raise ValueError("Pathname patterns are not allowed in the "
                                 "destination")

            to_copy_list = glob.glob(source)  # using local glob here

            rename_remote = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if self.isfile(destination):
                    raise OSError("Remote destination is not a directory")
                # I can't scp more than one file in a non existing directory
                elif not self.path_exists(destination):  # questo dovrebbe valere solo per file
                    raise OSError("Remote directory does not exist")
                else:  # the remote path is a directory
                    rename_remote = True

            for s in to_copy_list:
                if os.path.isfile(s):
                    if rename_remote:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        r = os.path.join(destination, os.path.split(s)[1])
                        self.putfile(s, r, overwrite)

                    elif self.isdir(destination):  # one file to copy in '.'
                        r = os.path.join(destination, os.path.split(s)[1])
                        self.putfile(s, r, overwrite)
                    else:  # one file to copy on one file
                        self.putfile(s, destination, overwrite)
                else:
                    self.puttree(s, destination, dereference, overwrite)

        else:
            if os.path.isdir(source):
                self.puttree(source, destination, dereference, overwrite)
            elif os.path.isfile(source):
                if self.isdir(destination):
                    r = os.path.join(destination, os.path.split(source)[1])
                    self.putfile(source, r, overwrite)
                else:
                    self.putfile(source, destination, overwrite)
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise OSError("The local path {} does not exist"
                                  .format(source))

    def putfile(self, source, destination, overwrite=True):
        """
        Copies a file from source to destination.
        Automatically redirects to putfile or puttree.

        :param source: absolute path to local file
        :param destination: path to remote file
        :param overwrite: if True overwrites destination
                                 Default = False

        :raise IOError: if destination is not valid
        :raise ValueError: if source is not valid
        :raise OSError: if source does not exist
        """
        if not destination:
            raise IOError("Input destination to putfile "
                          "must be a non empty string")
        if not source:
            raise ValueError("Input source to putfile "
                             "must be a non empty string")

        if not os.path.isabs(source):
            raise ValueError("Source must be an absolute path")

        if not os.path.exists(source):
            raise OSError("Source does not exists")

        the_destination = os.path.join(self.curdir, destination)
        if os.path.exists(the_destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copyfile(source, the_destination)

    def puttree(self, source, destination, dereference=True, overwrite=True):
        """
        Copies a folder recursively from source to destination.
        Automatically redirects to putfile or puttree.

        :param source: absolute path to local file
        :param destination: path to remote file
        :param dereference: follow symbolic links.
                                 Default = True
        :param overwrite: if True overwrites destination.
                               Default = False

        :raise IOError: if destination is not valid
        :raise ValueError: if source is not valid
        :raise OSError: if source does not exist
        """
        if not destination:
            raise IOError("Input destination to putfile "
                          "must be a non empty string")
        if not source:
            raise ValueError("Input source to putfile "
                             "must be a non empty string")

        if not os.path.isabs(source):
            raise ValueError("Source must be an absolute path")

        if not os.path.exists(source):
            raise OSError("Source does not exists")

        if self.path_exists(destination) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if self.isfile(destination):
            raise OSError("Cannot copy a directory into a file")

        if self.isdir(destination):
            destination = os.path.join(destination, os.path.split(source)[1])

        the_destination = os.path.join(self.curdir, destination)

        shutil.copytree(source, the_destination, symlinks=not(dereference))

    def rmtree(self, path):
        """
        Remove tree as rm -r would do
        
        :param path: a string to path
        """
        the_path = os.path.join(self.curdir, path)
        try:
            shutil.rmtree(the_path)
        except OSError as e:
            if e.errno == 20:
                os.remove(the_path)
            else:
                raise e

    def get(self, source, destination, dereference=True, overwrite=True,
            ignore_nonexisting=False):
        """
        Copies a folder or a file recursively from 'remote' source to
        'local' destination.
        Automatically redirects to getfile or gettree.

        :param source: path to local file
        :param destination: absolute path to remote file
        :param dereference: follow symbolic links
                                 default = True
        :param overwrite: if True overwrites destination
                               default = False

        :raise IOError: if 'remote' source is not valid
        :raise ValueError: if 'local' destination is not valid
        """
        if not destination:
            raise ValueError("Input destination to get function "
                             "must be a non empty string")
        if not source:
            raise IOError("Input source to get function "
                          "must be a non empty string")

        if not os.path.isabs(destination):
            raise ValueError("Destination must be an absolute path")

        if self.has_magic(source):
            if self.has_magic(destination):
                raise ValueError("Pathname patterns are not allowed in the "
                                 "destination")
            to_copy_list = self.glob(source)

            rename_local = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if os.path.isfile(destination):
                    raise IOError("Remote destination is not a directory")
                # I can't scp more than one file in a non existing directory
                elif not os.path.exists(destination):  # this should hold only for files
                    raise OSError("Remote directory does not exist")
                else:  # the remote path is a directory
                    rename_local = True

            for s in to_copy_list:
                if self.isfile(s):
                    if rename_local:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        r = os.path.join(destination, os.path.split(s)[1])
                        self.getfile(s, r, overwrite)
                    else:  # one file to copy on one file
                        self.getfile(s, destination, overwrite)
                else:
                    self.gettree(s, destination, dereference, overwrite)

        else:
            if self.isdir(source):
                self.gettree(source, destination, dereference, overwrite)
            elif self.isfile(source):
                if os.path.isdir(destination):
                    r = os.path.join(destination, os.path.split(source)[1])
                    self.getfile(source, r, overwrite)
                else:
                    self.getfile(source, destination, overwrite)
            else:
                if ignore_nonexisting:
                    pass
                else:
                    raise IOError("The local path {} does not exist"
                                  .format(destination))

    def getfile(self, source, destination, overwrite=True):
        """
        Copies a file recursively from 'remote' source to
        'local' destination.

        :param source: path to local file
        :param destination: absolute path to remote file
        :param overwrite: if True overwrites destination.
                               Default = False

        :raise IOError if 'remote' source is not valid or not found
        :raise ValueError: if 'local' destination is not valid
        :raise OSError: if unintentionally overwriting
        """
        if not destination:
            raise ValueError("Input destination to get function "
                             "must be a non empty string")
        if not source:
            raise IOError("Input source to get function "
                          "must be a non empty string")
        the_source = os.path.join(self.curdir, source)
        if not os.path.exists(the_source):
            raise IOError("Source not found")
        if not os.path.isabs(destination):
            raise ValueError("Destination must be an absolute path")
        if os.path.exists(destination) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        shutil.copyfile(the_source, destination)

    def gettree(self, source, destination, dereference=True, overwrite=True):
        """
        Copies a folder recursively from 'remote' source to
        'local' destination.

        :param source: path to local file
        :param destination: absolute path to remote file
        :param dereference: follow symbolic links. Default = True
        :param overwrite: if True overwrites destination. Default = False

        :raise IOError: if 'remote' source is not valid
        :raise ValueError: if 'local' destination is not valid
        :raise OSError: if unintentionally overwriting
        """
        if not source:
            raise IOError("Remotepath must be a non empty string")
        if not destination:
            raise ValueError("Localpaths must be a non empty string")

        if not os.path.isabs(destination):
            raise ValueError("Localpaths must be an absolute path")

        if not self.isdir(source):
            raise IOError("Input remotepath is not a folder: {}".format(source))

        if os.path.exists(destination) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if os.path.isfile(destination):
            raise OSError("Cannot copy a directory into a file")

        if os.path.isdir(destination):
            destination = os.path.join(destination, os.path.split(source)[1])

        the_source = os.path.join(self.curdir, source)
        shutil.copytree(the_source, destination, symlinks=not(dereference))

    def copy(self, source, destination, dereference=False):
        """
        Copies a file or a folder from 'remote' source to 'remote' destination.
        Automatically redirects to copyfile or copytree.

        :param source: path to local file
        :param destination: path to remote file
        :param dereference: follow symbolic links. Default = False

        :raise ValueError: if 'remote' source or destination is not valid
        :raise OSError: if source does not exist
        """
        if not source:
            raise ValueError("Input source to copy "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copy "
                             "must be a non empty object")
        if not self.has_magic(source):
            if not os.path.exists(os.path.join(self.curdir, source)):
                raise OSError("Source not found")
        if self.normalize(source) == self.normalize(destination):
            raise ValueError("Cannot copy from itself to itself")

            # # by default, overwrite old files
        #        if not destination.startswith('.'):
        #            if self.isfile(destination) or self.isdir(destination):
        #                self.rmtree(destination)

        the_destination = os.path.join(self.curdir, destination)

        if self.has_magic(source):
            if self.has_magic(destination):
                raise ValueError("Pathname patterns are not allowed in the "
                                 "destination")

            to_copy_list = self.glob(source)

            if len(to_copy_list) > 1:
                if not self.path_exists(destination) or self.isfile(destination):
                    raise OSError("Can't copy more than one file in the same "
                                  "destination file")

            for s in to_copy_list:
                # If s is an absolute path, then the_s = s
                the_s = os.path.join(self.curdir, s)
                if self.isfile(s):
                    # With shutil, use the full path (the_s)
                    shutil.copy(the_s, the_destination)
                else:
                    # With self.copytree, the (possible) relative path is OK
                    self.copytree(s, destination, dereference)

        else:
            # If s is an absolute path, then the_source = source
            the_source = os.path.join(self.curdir, source)
            if self.isfile(source):
                # With shutil, use the full path (the_source)
                shutil.copy(the_source, the_destination)
            else:
                # With self.copytree, the (possible) relative path is OK
                self.copytree(source, destination, dereference)

    def copyfile(self, source, destination):
        """
        Copies a file from 'remote' source to
        'remote' destination.

        :param source: path to local file
        :param destination: path to remote file
        :raise ValueError: if 'remote' source or destination is not valid
        :raise OSError: if source does not exist

        """
        if not source:
            raise ValueError("Input source to copyfile "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copyfile "
                             "must be a non empty object")
        the_source = os.path.join(self.curdir, source)
        the_destination = os.path.join(self.curdir, destination)
        if not os.path.exists(the_source):
            raise OSError("Source not found")

        shutil.copyfile(the_source, the_destination)

    def copytree(self, source, destination, dereference=False):
        """
        Copies a folder from 'remote' source to
        'remote' destination.

        :param source: path to local file
        :param destination: path to remote file
        :param dereference: follow symbolic links. Default = False
        
        :raise ValueError: if 'remote' source or destination is not valid
        :raise OSError: if source does not exist
        """
        if not source:
            raise ValueError("Input source to copytree "
                             "must be a non empty object")
        if not destination:
            raise ValueError("Input destination to copytree "
                             "must be a non empty object")
        the_source = os.path.join(self.curdir, source)
        the_destination = os.path.join(self.curdir, destination)
        if not os.path.exists(the_source):
            raise OSError("Source not found")

        # Using the Ubuntu default behavior (different from Mac)
        if self.isdir(destination):
            the_destination = os.path.join(the_destination,
                                           os.path.split(source)[1])

        shutil.copytree(the_source, the_destination, symlinks=not(dereference))

    def get_attribute(self, path):
        """
        Returns an object FileAttribute,
        as specified in aiida.transport.
        :param path: the path of the given file.
        """
        os_attr = os.lstat(os.path.join(self.curdir, path))
        aiida_attr = FileAttribute()
        # map the paramiko class into the aiida one
        # note that paramiko object contains more informations than the aiida
        for key in aiida_attr._valid_fields:
            aiida_attr[key] = getattr(os_attr, key)
        return aiida_attr

    def _local_listdir(self, path, pattern=None):
        # acts on the local folder, for the rest, same as listdir
        if not pattern:
            return os.listdir(path)
        else:
            import re

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
        :param filter: if set, returns the list of files matching pattern.
                     Unix only. (Use to emulate ls * for example)
        """
        the_path = os.path.join(self.curdir, path).strip()
        if not pattern:
            return os.listdir(the_path)
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
        else:
            return os.path.isfile(os.path.join(self.curdir, path))

    def _exec_command_internal(self, command):
        """
        Executes the specified command, first changing directory to the
        current working directory as returned by self.getcwd().
        Does not wait for the calculation to finish.

        For a higher-level exec_command that automatically waits for the
        job to finish, use exec_command_wait.
        Otherwise, to end the process, use the proc.wait() method.

        :param command: the command to execute
        
        :return: a tuple with (stdin, stdout, stderr, proc),
            where stdin, stdout and stderr behave as file-like objects,
            proc is the process object as returned by the
            subprocess.Popen() class.
        """
        proc = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                cwd=self.getcwd())
        return proc.stdin, proc.stdout, proc.stderr, proc

    def exec_command_wait(self, command, stdin=None):
        """
        Executes the specified command and waits for it to finish.
        
        :param command: the command to execute

        :return: a tuple with (return_value, stdout, stderr) where stdout and 
                 stderr are strings.
        """
        local_stdin, local_stdout, local_stderr, local_proc = self._exec_command_internal(
            command)

        if stdin is not None:
            if isinstance(stdin, basestring):
                filelike_stdin = StringIO.StringIO(stdin)
            else:
                filelike_stdin = stdin

            try:
                for l in filelike_stdin.readlines():
                    local_proc.stdin.write(l)
            except AttributeError:
                raise ValueError("stdin can only be either a string of a "
                                 "file-like object!")
        else:
            filelike_stdin = None

        local_stdin.flush()
        # TODO : instead of stringIO use cstringIO
        # TODO : use input option of communicate()
        output_text, stderr_text = local_proc.communicate()

        retval = local_proc.returncode

        return retval, output_text, stderr_text

    def gotocomputer_command(self, remotedir):
        """
        Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened
        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """
        # return """bash -c "if [ -d {escaped_remotedir} ] ; then cd {escaped_remotedir} ; bash --rcfile <(echo 'if [ -e ~/.bashrc ] ; then source ~/.bashrc ; fi ; export PS1="'"\[\033[01;31m\][AiiDA] \033[00m\]$PS1"'"') ; else echo  '  ** The directory' ; echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
        #        escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir)
        return """bash -c "if [ -d {escaped_remotedir} ] ; then cd {escaped_remotedir} ; bash ; else echo  '  ** The directory' ; echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
            escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir)

    def rename(self, src, dst):
        """
        Rename a file or folder from oldpath to newpath.
        
        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if src/dst is not found
        :raises ValueError: if src/dst is not a valid string
        """
        if not src:
            raise ValueError("Source {} is not a valid string".format(src))
        if not dst:
            raise ValueError("Destination {} is not a valid string".format(dst))
        if not os.path.exists(src):
            raise IOError("Source {} does not exist".format(src))
        if not os.path.exists(dst):
            raise IOError("Destination {} does not exist".format(dst))

        shutil.move(src, dst)

    def symlink(self, remotesource, remotedestination):
        """
        Create a symbolic link between the remote source and the remote 
        destination
        
        :param remotesource: remote source. Can contain a pattern.
        :param remotedestination: remote destination
        """
        remotesource = os.path.normpath(remotesource)
        remotedestination = os.path.normpath(remotedestination)

        if self.has_magic(remotesource):
            if self.has_magic(remotedestination):
                # if there are patterns in dest, I don't know which name to assign
                raise ValueError("Remotedestination cannot have patterns")

            # find all files matching pattern
            for this_file in self.glob(remotesource):
                # create the name of the link: take the last part of the path
                this_remote_dest = os.path.split(this_file)[-1]

                os.symlink(os.path.join(this_file),
                           os.path.join(self.curdir, remotedestination, this_remote_dest))
        else:
            try:
                os.symlink(remotesource,
                           os.path.join(self.curdir, remotedestination))
            except OSError:
                raise OSError("!!: {}, {}, {}".format(remotesource, self.curdir, remotedestination))

    def path_exists(self, path):
        """
        Check if path exists
        """
        return os.path.exists(os.path.join(self.curdir, path))
