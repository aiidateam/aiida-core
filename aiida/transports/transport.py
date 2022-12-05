# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Transport interface."""
import abc
from collections import OrderedDict
import fnmatch
import os
import re
import sys

from aiida.common.exceptions import InternalError
from aiida.common.lang import classproperty

__all__ = ('Transport',)


def validate_positive_number(ctx, param, value):  # pylint: disable=unused-argument
    """Validate that the number passed to this parameter is a positive number.

    :param ctx: the `click.Context`
    :param param: the parameter
    :param value: the value passed for the parameter
    :raises `click.BadParameter`: if the value is not a positive number
    """
    if not isinstance(value, (int, float)) or value < 0:
        from click import BadParameter
        raise BadParameter(f'{value} is not a valid positive number')

    return value


class Transport(abc.ABC):
    """Abstract class for a generic transport (ssh, local, ...) contains the set of minimal methods."""
    # pylint: disable=too-many-public-methods

    # This will be used for ``Computer.get_minimum_job_poll_interval``
    DEFAULT_MINIMUM_JOB_POLL_INTERVAL = 10

    # This is used as a global default in case subclasses don't redefine this,
    # but this should  be redefined in plugins where appropriate
    _DEFAULT_SAFE_OPEN_INTERVAL = 30.

    # To be defined in the subclass
    # See the ssh or local plugin to see the format
    _valid_auth_params = None
    _MAGIC_CHECK = re.compile('[*?[]')
    _valid_auth_options: list = []
    _common_auth_options = [
        (
            'use_login_shell', {
                'default':
                True,
                'switch':
                True,
                'prompt':
                'Use login shell when executing command',
                'help':
                ' Not using a login shell can help suppress potential'
                ' spurious text output that can prevent AiiDA from parsing the output of commands,'
                ' but may result in some startup files (.profile) not being sourced.',
                'non_interactive_default':
                True
            }
        ),
        (
            'safe_interval', {
                'type': float,
                'prompt': 'Connection cooldown time (s)',
                'help': 'Minimum time interval in seconds between opening new connections.',
                'callback': validate_positive_number
            }
        ),
    ]

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        __init__ method of the Transport base class.

        :param safe_interval: (optional, default self._DEFAULT_SAFE_OPEN_INTERVAL)
           Minimum time interval in seconds between opening new connections.
        :param use_login_shell: (optional, default True)
           if False, do not use a login shell when executing command
        """
        from aiida.common import AIIDA_LOGGER
        self._safe_open_interval = kwargs.pop('safe_interval', self._DEFAULT_SAFE_OPEN_INTERVAL)
        self._use_login_shell = kwargs.pop('use_login_shell', True)
        if self._use_login_shell:
            self._bash_command_str = 'bash -l '
        else:
            self._bash_command_str = 'bash '

        self._logger = AIIDA_LOGGER.getChild('transport').getChild(self.__class__.__name__)
        self._logger_extra = None
        self._is_open = False
        self._enters = 0

        # for accessing the identity of the underlying machine
        self.hostname = kwargs.get('machine')

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

    @abc.abstractmethod
    def open(self):
        """
        Opens a local transport channel
        """

    @abc.abstractmethod
    def close(self):
        """
        Closes the local transport channel
        """

    def __repr__(self):
        return f'<{self.__class__.__name__}: {str(self)}>'

    # redefine this in each subclass
    def __str__(self):
        return '[Transport class or subclass]'

    def set_logger_extra(self, logger_extra):
        """
        Pass the data that should be passed automatically to self.logger
        as 'extra' keyword. This is typically useful if you pass data
        obtained using get_dblogger_extra in aiida.orm.utils.log, to automatically
        log also to the DbLog table.

        :param logger_extra: data that you want to pass as extra to the
          self.logger. To write to DbLog, it should be created by the
          aiida.orm.utils.log.get_dblogger_extra function. Pass None if you
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
            return 'No documentation available'

        doclines = [i for i in docstring.splitlines() if i.strip()]
        if doclines:
            return doclines[0].strip()
        return 'No documentation available'

    @classmethod
    def get_valid_auth_params(cls):
        """
        Return the internal list of valid auth_params
        """
        if cls._valid_auth_options is None:
            raise NotImplementedError
        else:
            return cls.auth_options.keys()

    @classproperty
    def auth_options(cls) -> OrderedDict:  # pylint: disable=no-self-argument
        """Return the authentication options to be used for building the CLI.

        :return: `OrderedDict` of tuples, with first element option name and second dictionary of kwargs
        """
        return OrderedDict(cls._valid_auth_options + cls._common_auth_options)

    @classmethod
    def _get_safe_interval_suggestion_string(cls, computer):  # pylint: disable=unused-argument
        """
        Return as a suggestion the default safe interval of this Transport class.

        This is used to provide a default in ``verdi computer configure``.
        """
        return cls._DEFAULT_SAFE_OPEN_INTERVAL

    @classmethod
    def _get_use_login_shell_suggestion_string(cls, computer):  # pylint: disable=unused-argument
        """
        Return a suggestion for the specific field.
        """
        return 'True'

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
            raise InternalError('No self._logger configured for {}!')

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

    @abc.abstractmethod
    def chdir(self, path):
        """
        Change directory to 'path'

        :param str path: path to change working directory into.
        :raises: IOError, if the requested path does not exist
        :rtype: str
        """

    @abc.abstractmethod
    def chmod(self, path, mode):
        """
        Change permissions of a path.

        :param str path: path to file
        :param int mode: new permissions
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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
            self.logger.error('Unknown parameters passed to copy_from_remote_to_remote')

        with SandboxFolder() as sandbox:
            self.get(remotesource, sandbox.abspath, **kwargs_get)
            # Then we scan the full sandbox directory with get_content_list,
            # because copying directly from sandbox.abspath would not work
            # to copy a single file into another single file, and copying
            # from sandbox.get_abs_path('*') would not work for files
            # beginning with a dot ('.').
            for filename in sandbox.get_content_list():
                transportdestination.put(os.path.join(sandbox.abspath, filename), remotedestination, **kwargs_put)

    @abc.abstractmethod
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

    @abc.abstractmethod
    def exec_command_wait_bytes(self, command, stdin=None, **kwargs):
        """
        Execute the command on the shell, waits for it to finish,
        and return the retcode, the stdout and the stderr as bytes.

        Enforce the execution to be run from the pwd (as given by self.getcwd), if this is not None.

        The command implementation can have some additional plugin-specific kwargs.

        :param str command: execute the command given as a string
        :param stdin: (optional,default=None) can be a string or a file-like object.
        :return: a tuple: the retcode (int), stdout (bytes) and stderr (bytes).
        """

    def exec_command_wait(self, command, stdin=None, encoding='utf-8', **kwargs):
        """
        Executes the specified command and waits for it to finish.

        :note: this function also decodes the bytes received into a string with the specified encoding,
            which is set to be ``utf-8`` by default (for backward-compatibility with earlier versions) of
            AiiDA.
            Use this method only if you are sure that you are getting a properly encoded string; otherwise,
            use the ``exec_command_wait_bytes`` method that returns the undecoded byte stream.

        :note: additional kwargs are passed to the ``exec_command_wait_bytes`` function, that might use them
            depending on the plugin.

        :param command: the command to execute
        :param stdin: (optional,default=None) can be a string or a file-like object.
        :param encoding: the encoding to use to decode the byte stream received from the remote command execution.

        :return: a tuple with (return_value, stdout, stderr) where stdout and stderr are both strings, decoded
            with the specified encoding.
        """
        retval, stdout_bytes, stderr_bytes = self.exec_command_wait_bytes(command=command, stdin=stdin, **kwargs)
        # Return the decoded strings
        return (retval, stdout_bytes.decode(encoding), stderr_bytes.decode(encoding))

    @abc.abstractmethod
    def get(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a file or folder from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param remotepath: (str) remote_folder_path
        :param localpath: (str) local_folder_path
        """

    @abc.abstractmethod
    def getfile(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a file from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """

    @abc.abstractmethod
    def gettree(self, remotepath, localpath, *args, **kwargs):
        """
        Retrieve a folder recursively from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param str remotepath: remote_folder_path
        :param str localpath: local_folder_path
        """

    @abc.abstractmethod
    def getcwd(self):
        """
        Get working directory

        :return: a string identifying the current working directory
        """

    @abc.abstractmethod
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

    def get_mode(self, path):
        """
        Return the portion of the file's mode that can be set by chmod().

        :param str path: path to file
        :return: the portion of the file's mode that can be set by chmod()
        """
        import stat

        return stat.S_IMODE(self.get_attribute(path).st_mode)

    @abc.abstractmethod
    def isdir(self, path):
        """
        True if path is an existing directory.

        :param str path: path to directory
        :return: boolean
        """

    @abc.abstractmethod
    def isfile(self, path):
        """
        Return True if path is an existing file.

        :param str path: path to file
        :return: boolean
        """

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
    def mkdir(self, path, ignore_existing=False):
        """
        Create a folder (directory) named path.

        :param str path: name of the folder to create
        :param bool ignore_existing: if True, does not give any error if the
                                     directory already exists

        :raises: OSError, if directory at path already exists
        """

    @abc.abstractmethod
    def normalize(self, path='.'):
        """
        Return the normalized path (on the server) of a given path.
        This can be used to quickly resolve symbolic links or determine
        what the server is considering to be the "current folder".

        :param str path: path to be normalized

        :raise IOError: if the path can't be resolved on the server
        """

    @abc.abstractmethod
    def put(self, localpath, remotepath, *args, **kwargs):
        """
        Put a file or a directory from local src to remote dst.
        src must be an absolute path (dst not necessarily))
        Redirects to putfile and puttree.

        :param str localpath: absolute path to local source
        :param str remotepath: path to remote destination
        """

    @abc.abstractmethod
    def putfile(self, localpath, remotepath, *args, **kwargs):
        """
        Put a file from local src to remote dst.
        src must be an absolute path (dst not necessarily))

        :param str localpath: absolute path to local file
        :param str remotepath: path to remote file
        """

    @abc.abstractmethod
    def puttree(self, localpath, remotepath, *args, **kwargs):
        """
        Put a folder recursively from local src to remote dst.
        src must be an absolute path (dst not necessarily))

        :param str localpath: absolute path to local folder
        :param str remotepath: path to remote folder
        """

    @abc.abstractmethod
    def remove(self, path):
        """
        Remove the file at the given path. This only works on files;
        for removing folders (directories), use rmdir.

        :param str path: path to file to remove

        :raise IOError: if the path is a directory
        """

    @abc.abstractmethod
    def rename(self, oldpath, newpath):
        """
        Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """

    @abc.abstractmethod
    def rmdir(self, path):
        """
        Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param str path: absolute path to the folder to remove
        """

    @abc.abstractmethod
    def rmtree(self, path):
        """
        Remove recursively the content at path

        :param str path: absolute path to remove
        """

    @abc.abstractmethod
    def gotocomputer_command(self, remotedir):
        """
        Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        Expected behaviors:

        * A new bash session is opened

        * A reasonable error message is produced if the folder does not exist

        :param str remotedir: the full path of the remote directory
        """

    @abc.abstractmethod
    def symlink(self, remotesource, remotedestination):
        """
        Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: remote source
        :param remotedestination: remote destination
        """

    def whoami(self):
        """
        Get the remote username

        :return: list of username (str),
                 retval (int),
                 stderr (str)
        """

        command = 'whoami'
        # Assuming here that the username is either ASCII or UTF-8 encoded
        # This should be true essentially always
        retval, username, stderr = self.exec_command_wait(command)
        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the whoami command: {stderr}')
            return username.strip()

        self.logger.error(f"Problem executing whoami. Exit code: {retval}, stdout: '{username}', stderr: '{stderr}'")
        raise IOError(f'Error while executing whoami. Exit code: {retval}')

    @abc.abstractmethod
    def path_exists(self, path):
        """
        Returns True if path exists, False otherwise.
        """

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
        if isinstance(pattern, str) and not isinstance(dirname, str):
            dirname = dirname.decode(sys.getfilesystemencoding() or sys.getdefaultencoding())
        try:
            # names = os.listdir(dirname)
            # print dirname
            names = self.listdir(dirname)
        except EnvironmentError:
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

    def _gotocomputer_string(self, remotedir):
        """command executed when goto computer."""
        connect_string = (
            """ "if [ -d {escaped_remotedir} ] ;"""
            """ then cd {escaped_remotedir} ; {bash_command} ; else echo '  ** The directory' ; """
            """echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
                bash_command=self._bash_command_str, escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir
            )
        )

        return connect_string


class TransportInternalError(InternalError):
    """
    Raised if there is a transport error that is raised to an internal error (e.g.
    a transport method called without opening the channel first).
    """
