# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Transport interface."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from abc import ABCMeta
import os
import re
import fnmatch
import sys
from collections import OrderedDict

import six
from aiida.common.exceptions import InternalError
from aiida.common.lang import classproperty

DEFAULT_TRANSPORT_INTERVAL = 30.

__all__ = ('Transport',)


@six.add_metaclass(ABCMeta)
class Transport(object):
    """
    Abstract class for a generic transport (ssh, local, ...)
    Contains the set of minimal methods
    """
    # pylint: disable=too-many-public-methods,useless-object-inheritance,bad-option-value

    # To be defined in the subclass
    # See the ssh or local plugin to see the format
    _valid_auth_params = None
    _MAGIC_CHECK = re.compile('[*?[]')
    _valid_auth_options = []
    _common_auth_options = [('safe_interval', {
        'type': int,
        'prompt': 'Connection cooldown time (sec)',
        'help': 'Minimum time between connections in sec',
        'non_interactive_default': True
    })]

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        __init__ method of the Transport base class.
        """
        from aiida.common import AIIDA_LOGGER

        self._logger = AIIDA_LOGGER.getChild('transport').getChild(self.__class__.__name__)
        self._logger_extra = None
        self._is_open = False
        self._enters = 0
        self._safe_open_interval = DEFAULT_TRANSPORT_INTERVAL

    def __enter__(self):
        """
        For transports that require opening a connection, opens
        all required channels (used in 'with' statements).

        This object can be used in nested `with` statements and the connection
        will only be opened once and closed when the final `with` scope
        finishes e.g.::

            t = Transport()
            with t:
                # Connection is now open..
                with t:
                    # ..still open..
                    pass
                # ..still open..
            # ...closed

        """
        # Keep track of how many times enter has been called
        if self._enters == 0:
            if self.is_open:
                # Already open, so just add one to the entered counter
                # this way on the final exit we will not close
                self._enters += 1
            else:
                self.open()
        self._enters += 1
        return self

    def __exit__(self, type_, value, traceback):
        """
        Closes connections, if needed (used in 'with' statements).
        """
        self._enters -= 1
        if self._enters == 0:
            self.close()

    @property
    def is_open(self):
        return self._is_open

    def open(self):
        """
        Opens a local transport channel
        """
        raise NotImplementedError

    def close(self):
        """
        Closes the local transport channel
        """
        raise NotImplementedError

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    # redefine this in each subclass
    def __str__(self):
        return "[Transport class or subclass]"

    def set_logger_extra(self, logger_extra):
        """
        Pass the data that should be passed automatically to self.logger
        as 'extra' keyword. This is typically useful if you pass data
        obtained using get_dblogger_extra in aiida.backends.djsite.utils, to automatically
        log also to the DbLog table.

        :param logger_extra: data that you want to pass as extra to the
          self.logger. To write to DbLog, it should be created by the
          aiida.backends.djsite.utils.get_dblogger_extra function. Pass None if you
          do not want to have extras passed.
        """
        self._logger_extra = logger_extra

    @classmethod
    def get_short_doc(cls):
        """
        Return the first non-empty line of the class docstring, if available
        """
        # Remove empty lines
        docstring = cls.__doc__
        if not docstring:
            return "No documentation available"

        doclines = [i for i in docstring.splitlines() if i.strip()]
        if doclines:
            return doclines[0].strip()
        return "No documentation available"

    @classmethod
    def get_valid_transports(cls):
        """
        :return: a list of existing plugin names
        """
        from aiida.plugins.entry_point import get_entry_point_names

        return get_entry_point_names('aiida.transports')

    @classmethod
    def get_valid_auth_params(cls):
        """
        Return the internal list of valid auth_params
        """
        if cls._valid_auth_options is None:
            raise NotImplementedError
        else:
            return cls.auth_options.keys()  # pylint: disable=no-member

    @classproperty
    def auth_options(cls):  # pylint: disable=no-self-argument
        return OrderedDict(cls._valid_auth_options + cls._common_auth_options)

    @classmethod
    def _get_safe_interval_suggestion_string(cls, computer):  # pylint: disable=unused-argument
        """
        Default time in seconds between consecutive checks.

        Set to a non-zero value to be safe e.g. in the case of transports with a connection limit,
        to avoid overloading the server (and being banned). Should be overriden
        in plugins. This is anyway just a default, as the value can be changed
        by the user in the Computer properties, for instance.
        Currently both the local and the ssh transport override this value, so this is not used,
        but it will be the default for possible new plugins.
        """
        return DEFAULT_TRANSPORT_INTERVAL

    @property
    def logger(self):
        """
        Return the internal logger.
        If you have set extra parameters using set_logger_extra(), a
        suitable LoggerAdapter instance is created, bringing with itself
        also the extras.
        """
        try:
            import logging

            if self._logger_extra is not None:
                return logging.LoggerAdapter(logger=self._logger, extra=self._logger_extra)
            return self._logger
        except AttributeError:
            raise InternalError("No self._logger configured for {}!")

    def get_safe_open_interval(self):
        """
        Get an interval (in seconds) that suggests how long the user should wait
        between consecutive calls to open the transport.  This can be used as
        a way to get the user to not swamp a limited number of connections, etc.
        However it is just advisory.

        If returns 0, it is taken that there are no reasons to limit the
        frequency of open calls.

        In the main class, it returns a default value (>0 for safety), set in
        the _DEFAULT_SAFE_OPEN_INTERVAL attribute of the class. Plugins should override it.

        :return: The safe interval between calling open, in seconds
        :rtype: float
        """
        return self._safe_open_interval

    def chdir(self, path):
        """
        Change directory to 'path'

        :param str path: path to change working directory into.
        :raises: IOError, if the requested path does not exist
        :rtype: str
        """

        raise NotImplementedError

    def chmod(self, path, mode):
        """
        Change permissions of a path.

        :param str path: path to file
        :param int mode: new permissions
        """
        raise NotImplementedError

    def chown(self, path, uid, gid):
        """
        Change the owner (uid) and group (gid) of a file.
        As with python's os.chown function, you must pass both arguments,
        so if you only want to change one, use stat first to retrieve the
        current owner and group.

        :param str path: path to the file to change the owner and group of
        :param int uid: new owner's uid
        :param int gid: new group id
        """
        raise NotImplementedError

    def copy(self, remotesource, remotedestination, dereference=False, recursive=True):
        """
        Copy a file or a directory from remote source to remote destination
        (On the same remote machine)

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves
        :type dereference: bool
        :param recursive: if True copy directories recursively, otherwise only copy the specified file(s)
        :type recursive: bool

        :raises: IOError, if one of src or dst does not exist
        """
        raise NotImplementedError

    def copyfile(self, remotesource, remotedestination, dereference=False):
        """
        Copy a file from remote source to remote destination
        (On the same remote machine)

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves
        :type dereference: bool

        :raises IOError: if one of src or dst does not exist
        """
        raise NotImplementedError

    def copytree(self, remotesource, remotedestination, dereference=False):
        """
        Copy a folder from remote source to remote destination
        (On the same remote machine)

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves
        :type dereference: bool

        :raise IOError: if one of src or dst does not exist
        """
        raise NotImplementedError

    def copy_from_remote_to_remote(self, transportdestination, remotesource, remotedestination, **kwargs):
        """
        Copy files or folders from a remote computer to another remote computer.

        :param transportdestination: transport to be used for the destination computer
        :param str remotesource: path to the remote source directory / file
        :param str remotedestination: path to the remote destination directory / file
        :param kwargs: keyword parameters passed to the call to transportdestination.put,
            except for 'dereference' that is passed to self.get

        .. note:: the keyword 'dereference' SHOULD be set to False for the
         final put (onto the destination), while it can be set to the
         value given in kwargs for the get from the source. In that
         way, a symbolic link would never be followed in the final
         copy to the remote destination. That way we could avoid getting
         unknown (potentially malicious) files into the destination computer.
         HOWEVER, since dereference=False is currently NOT
         supported by all plugins, we still force it to True for the final put.

        .. note:: the supported keys in kwargs are callback, dereference,
           overwrite and ignore_nonexisting.
        """
        from aiida.common.folders import SandboxFolder

        kwargs_get = {
            'callback': None,
            'dereference': kwargs.pop('dereference', True),
            'overwrite': True,
            'ignore_nonexisting': False,
        }
        kwargs_put = {
            'callback': kwargs.pop('callback', None),
            'dereference': True,
            'overwrite': kwargs.pop('overwrite', True),
            'ignore_nonexisting': kwargs.pop('ignore_nonexisting', False),
        }

        if kwargs:
            self.logger.error("Unknown parameters passed to copy_from_remote_to_remote")

        with SandboxFolder() as sandbox:
            self.get(remotesource, sandbox.abspath, **kwargs_get)
            # Then we scan the full sandbox directory with get_content_list,
            # because copying directly from sandbox.abspath would not work
            # to copy a single file into another single file, and copying
            # from sandbox.get_abs_path('*') would not work for files
            # beginning with a dot ('.').
            for filename in sandbox.get_content_list():
                transportdestination.put(os.path.join(sandbox.abspath, filename), remotedestination, **kwargs_put)

    def _exec_command_internal(self, command, **kwargs):
        """
        Execute the command on the shell, similarly to os.system.

        Enforce the execution to be run from the cwd (as given by
        self.getcwd), if this is not None.

        If possible, use the higher-level
        exec_command_wait function.

        :param str command: execute the command given as a string
        :return: stdin, stdout, stderr and the session, when this exists \
                 (can be None).
        """
        raise NotImplementedError

    def exec_command_wait(self, command, **kwargs):
        """
        Execute the command on the shell, waits for it to finish,
        and return the retcode, the stdout and the stderr.

        Enforce the execution to be run from the pwd (as given by
        self.getcwd), if this is not None.

        :param str command: execute the command given as a string
        :return: a list: the retcode (int), stdout (str) and stderr (str).
        """
        raise NotImplementedError

    def get(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a file or folder from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param remotepath: (str) remote_folder_path
        :param localpath: (str) local_folder_path
        """
        raise NotImplementedError

    def getfile(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a file from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """
        raise NotImplementedError

    def gettree(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a folder recursively from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """
        raise NotImplementedError

    def getcwd(self):
        """
        Get working directory

        :return: a string identifying the current working directory
        """
        raise NotImplementedError

    def get_attribute(self, path):
        """
        Return an object FixedFieldsAttributeDict for file in a given path,
        as defined in aiida.common.extendeddicts
        Each attribute object consists in a dictionary with the following keys:

        * st_size: size of files, in bytes

        * st_uid: user id of owner

        * st_gid: group id of owner

        * st_mode: protection bits

        * st_atime: time of most recent access

        * st_mtime: time of most recent modification

        :param str path: path to file
        :return: object FixedFieldsAttributeDict
        """
        raise NotImplementedError

    def get_mode(self, path):
        """
        Return the portion of the file's mode that can be set by chmod().

        :param str path: path to file
        :return: the portion of the file's mode that can be set by chmod()
        """
        import stat

        return stat.S_IMODE(self.get_attribute(path).st_mode)

    def isdir(self, path):
        """
        True if path is an existing directory.

        :param str path: path to directory
        :return: boolean
        """
        raise NotImplementedError

    def isfile(self, path):
        """
        Return True if path is an existing file.

        :param str path: path to file
        :return: boolean
        """
        raise NotImplementedError

    def listdir(self, path='.', pattern=None):
        """
        Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param str path: path to list (default to '.')
        :param str pattern: if used, listdir returns a list of files matching
                            filters in Unix style. Unix only.
        :return: a list of strings
        """
        raise NotImplementedError

    def listdir_withattributes(self, path='.', pattern=None):  # pylint: disable=unused-argument
        """
        Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param str path: path to list (default to '.')
        :param str pattern: if used, listdir returns a list of files matching
                            filters in Unix style. Unix only.
        :return: a list of dictionaries, one per entry.
            The schema of the dictionary is
            the following::

                {
                   'name': String,
                   'attributes': FileAttributeObject,
                   'isdir': Bool
                }

            where 'name' is the file or folder directory, and any other information is metadata
            (if the file is a folder, a directory, ...). 'attributes' behaves as the output of
            transport.get_attribute(); isdir is a boolean indicating if the object is a directory or not.
        """
        retlist = []
        full_path = self.getcwd()
        for file_name in self.listdir():
            filepath = os.path.join(full_path, file_name)
            attributes = self.get_attribute(filepath)
            retlist.append({'name': file_name, 'attributes': attributes, 'isdir': self.isdir(filepath)})
        return retlist

    def makedirs(self, path, ignore_existing=False):
        """
        Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param str path: directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                                     if the leaf directory does already exist

        :raises: OSError, if directory at path already exists
        """
        raise NotImplementedError

    def mkdir(self, path, ignore_existing=False):
        """
        Create a folder (directory) named path.

        :param str path: name of the folder to create
        :param bool ignore_existing: if True, does not give any error if the
                                     directory already exists

        :raises: OSError, if directory at path already exists
        """
        raise NotImplementedError

    def normalize(self, path='.'):
        """
        Return the normalized path (on the server) of a given path.
        This can be used to quickly resolve symbolic links or determine
        what the server is considering to be the "current folder".

        :param str path: path to be normalized

        :raise IOError: if the path can't be resolved on the server
        """
        raise NotImplementedError

    def put(self, localpath, remotepath, *args, **kwargs):
        """
        Put a file or a directory from local src to remote dst.
        src must be an absolute path (dst not necessarily))
        Redirects to putfile and puttree.

        :param str localpath: absolute path to local source
        :param str remotepath: path to remote destination
        """
        raise NotImplementedError

    def putfile(self, localpath, remotepath, *args, **kwargs):
        """
        Put a file from local src to remote dst.
        src must be an absolute path (dst not necessarily))

        :param str localpath: absolute path to local file
        :param str remotepath: path to remote file
        """
        raise NotImplementedError

    def puttree(self, localpath, remotepath, *args, **kwargs):
        """
        Put a folder recursively from local src to remote dst.
        src must be an absolute path (dst not necessarily))

        :param str localpath: absolute path to local folder
        :param str remotepath: path to remote folder
        """
        raise NotImplementedError

    def remove(self, path):
        """
        Remove the file at the given path. This only works on files;
        for removing folders (directories), use rmdir.

        :param str path: path to file to remove

        :raise IOError: if the path is a directory
        """
        raise NotImplementedError

    def rename(self, oldpath, newpath):
        """
        Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """
        raise NotImplementedError

    def rmdir(self, path):
        """
        Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param str path: absolute path to the folder to remove
        """
        raise NotImplementedError

    def rmtree(self, path):
        """
        Remove recursively the content at path

        :param str path: absolute path to remove
        """
        raise NotImplementedError

    def gotocomputer_command(self, remotedir):
        """
        Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened

        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """
        raise NotImplementedError

    def symlink(self, remotesource, remotedestination):
        """
        Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: remote source
        :param remotedestination: remote destination
        """
        raise NotImplementedError

    def whoami(self):
        """
        Get the remote username

        :return: list of username (str),
                 retval (int),
                 stderr (str)
        """

        command = 'whoami'
        retval, username, stderr = self.exec_command_wait(command)
        if retval == 0:
            if stderr.strip():
                self.logger.warning("There was nonempty stderr in the whoami command: {}".format(stderr))
            return username.strip()

        self.logger.error("Problem executing whoami. Exit code: {}, stdout: '{}', "
                          "stderr: '{}'".format(retval, username, stderr))
        raise IOError("Error while executing whoami. Exit code: {}".format(retval))

    def path_exists(self, path):
        """
        Returns True if path exists, False otherwise.
        """
        raise NotImplementedError

    # The following definitions are almost copied and pasted
    # from the python module glob.
    def glob(self, pathname):
        """Return a list of paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.
        """
        return list(self.iglob(pathname))

    def iglob(self, pathname):
        """Return an iterator which yields the paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        """
        if not self.has_magic(pathname):
            # if os.path.lexists(pathname): # ORIGINAL
            # our implementation
            if self.path_exists(pathname):
                yield pathname
            return
        dirname, basename = os.path.split(pathname)
        if not dirname:
            # for name in self.glob1(os.curdir, basename): # ORIGINAL
            for name in self.glob1(self.getcwd(), basename):
                yield name
            return
        if self.has_magic(dirname):
            dirs = self.iglob(dirname)
        else:
            dirs = [dirname]
        if self.has_magic(basename):
            glob_in_dir = self.glob1
        else:
            glob_in_dir = self.glob0
        for dirname in dirs:
            for name in glob_in_dir(dirname, basename):
                yield os.path.join(dirname, name)

    # These 2 helper functions non-recursively glob inside a literal directory.
    # They return a list of basenames. `glob1` accepts a pattern while `glob0`
    # takes a literal basename (so it only has to check for its existence).

    def glob1(self, dirname, pattern):
        """Match subpaths of dirname against pattern."""
        if not dirname:
            # dirname = os.curdir # ORIGINAL
            dirname = self.getcwd()
        if isinstance(pattern, six.text_type) and not isinstance(dirname, six.text_type):
            dirname = dirname.decode(sys.getfilesystemencoding() or sys.getdefaultencoding())
        try:
            # names = os.listdir(dirname)
            # print dirname
            names = self.listdir(dirname)
        except EnvironmentError:  # in PY2 a superclass of OS/IOError, in PY3 an alias for OSError, like IOError
            return []
        if pattern[0] != '.':
            names = [name for name in names if name[0] != '.']
        return fnmatch.filter(names, pattern)

    def glob0(self, dirname, basename):
        """Wrap basename i a list if it is empty or if dirname/basename is an existing path, else return empty list."""
        if basename == '':
            # `os.path.split()` returns an empty basename for paths ending with a
            # directory separator.  'q*x/' should match only directories.
            # if os.path.isdir(dirname):
            if self.isdir(dirname):
                return [basename]
        elif self.path_exists(os.path.join(dirname, basename)):
            # if os.path.lexists(os.path.join(dirname, basename)):
            return [basename]
        return []

    def has_magic(self, string):
        return self._MAGIC_CHECK.search(string) is not None


class TransportInternalError(InternalError):
    """
    Raised if there is a transport error that is raised to an internal error (e.g.
    a transport method called without opening the channel first).
    """
