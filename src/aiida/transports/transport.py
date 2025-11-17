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
import fnmatch
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path, PurePosixPath
from typing import Optional, Union

from pydantic import BaseModel

from aiida.common.exceptions import InternalError
from aiida.common.lang import classproperty
from aiida.common.pydantic import MetadataField
from aiida.common.warnings import warn_deprecation

__all__ = ('AsyncTransport', 'BlockingTransport', 'Transport', 'TransportPath', 'has_magic')

TransportPath = Union[str, Path, PurePosixPath]

_MAGIC_CHECK = re.compile('[*?[]')


def has_magic(string: TransportPath):
    string = str(string)
    """Return True if the given string contains any special shell characters."""
    return _MAGIC_CHECK.search(string) is not None


def validate_positive_number(ctx, param, value):
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
    """Abstract class for a generic transport.
    A plugin inheriting from this class should implement all the abstract methods.
    In case your plugin is strictly asynchronous (blocking), you may want to inherit
    from `AsyncTransport` (BlockingTransport) for easier adoption.

    ..note::

        All the methods that start with ``_get_`` are class methods that
        return a suggestion for the specific field. They are being used in
        a function called ``transport_option_default`` in ``transports/cli.py``,
        during an interactive ``verdi computer configure`` command.
    """

    # This will be used for ``Computer.get_minimum_job_poll_interval``
    DEFAULT_MINIMUM_JOB_POLL_INTERVAL = 10.0

    # This is used as a global default in case subclasses don't redefine this,
    # but this should  be redefined in plugins where appropriate
    _DEFAULT_SAFE_OPEN_INTERVAL = 15.0

    # To be defined in the subclass
    # See the ssh or local plugin to see the format
    # This will be used for connection authentication
    # To be defined in the subclass, the format is a list of tuples
    # where the first element is the name of the parameter and the second
    # is a dictionary with the following
    # keys: 'default', 'prompt', 'help', 'non_interactive_default'
    _valid_auth_params = None
    _valid_auth_options: list = []
    _common_auth_options = [
        (
            'use_login_shell',
            {
                'default': True,
                'switch': True,
                'prompt': 'Use login shell when executing command',
                'help': ' Not using a login shell can help suppress potential'
                ' spurious text output that can prevent AiiDA from parsing the output of commands,'
                ' but may result in some startup files (.profile) not being sourced.',
                'non_interactive_default': True,
            },
        ),
        (
            'safe_interval',
            {
                'type': float,
                'prompt': 'Connection cooldown time (s)',
                'help': 'Minimum time interval in seconds between opening new connections.',
                'callback': validate_positive_number,
                'default': _DEFAULT_SAFE_OPEN_INTERVAL,
                'non_interactive_default': True,
            },
        ),
    ]

    class Model(BaseModel):
        """Model describing required information to create an instance."""

        use_login_shell: bool = MetadataField(
            True,
            title='Use login shell when executing command',
            description='Not using a login shell can help suppress potential spurious text output that can prevent '
            'AiiDA from parsing the output of commands, but may result in some startup files not being sourced.',
        )
        safe_interval: float = MetadataField(
            0.0,
            title='Connection cooldown time (s)',
            description='Minimum time interval in seconds between opening new connections.',
        )

    def __init__(self, *args, **kwargs):
        """__init__ method of the Transport base class.

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

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self!s}>'

    @abc.abstractmethod
    def __str__(self):
        """return [Transport class or subclass]"""

    @abc.abstractmethod
    def open(self):
        """Opens a transport channel

        :raises InvalidOperation: if the transport is already open.
        """

    @abc.abstractmethod
    def close(self):
        """Closes the transport channel.

        :raises InvalidOperation: if the transport is already closed.
        """

    def __enter__(self):
        """For transports that require opening a connection, opens
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
        """Closes connections, if needed (used in 'with' statements)."""
        self._enters -= 1
        if self._enters == 0:
            self.close()

    @property
    def is_open(self):
        return self._is_open

    def set_logger_extra(self, logger_extra):
        """Pass the data that should be passed automatically to self.logger
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
        """Return the first non-empty line of the class docstring, if available"""
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
        """Return the internal list of valid auth_params"""
        if cls._valid_auth_options is None:
            raise NotImplementedError
        else:
            return cls.auth_options.keys()

    @classproperty
    def auth_options(cls) -> OrderedDict:  # noqa: N805
        """Return the authentication options to be used for building the CLI.

        :return: `OrderedDict` of tuples, with first element option name and second dictionary of kwargs
        """
        return OrderedDict(cls._valid_auth_options + cls._common_auth_options)

    @classmethod
    def _get_safe_interval_suggestion_string(cls, computer):
        """Return as a suggestion the default safe interval of this Transport class.

        This is used to provide a default in ``verdi computer configure``.
        """
        return cls._DEFAULT_SAFE_OPEN_INTERVAL

    @classmethod
    def _get_use_login_shell_suggestion_string(cls, computer):
        """Return a suggestion for the specific field."""
        return 'True'

    @property
    def logger(self):
        """Return the internal logger.
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
        """Get an interval (in seconds) that suggests how long the user should wait
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

    def _gotocomputer_string(self, remotedir):
        """Command executed when goto computer."""
        connect_string = (
            """ "if [ -d {escaped_remotedir} ] ;"""
            """ then cd {escaped_remotedir} ; {bash_command} ; else echo '  ** The directory' ; """
            """echo '  ** {remotedir}' ; echo '  ** seems to have been deleted, I logout...' ; fi" """.format(
                bash_command=self._bash_command_str, escaped_remotedir="'{}'".format(remotedir), remotedir=remotedir
            )
        )

        return connect_string

    ## Blocking abstract methods

    @abc.abstractmethod
    def chmod(self, path: TransportPath, mode):
        """Change permissions of a path.

        :param path: path to file
        :param mode: new permissions

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type mode: int
        """

    @abc.abstractmethod
    def chown(self, path: TransportPath, uid: int, gid: int):
        """Change the owner (uid) and group (gid) of a file.
        As with python's os.chown function, you must pass both arguments,
        so if you only want to change one, use stat first to retrieve the
        current owner and group.

        :param path: path to the file to change the owner and group of
        :param uid: new owner's uid
        :param gid: new group id

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type uid: int
        :type gid: int
        """

    @abc.abstractmethod
    def copy(self, remotesource: TransportPath, remotedestination: TransportPath, dereference=False, recursive=True):
        """Copy a file or a directory from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path of the remote source directory / file
        :param remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves
        :param recursive: if True copy directories recursively, otherwise only copy the specified file(s)

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type recursive: bool

        :raises: OSError, if one of src or dst does not exist
        """

    @abc.abstractmethod
    def copyfile(self, remotesource: TransportPath, remotedestination: TransportPath, dereference=False):
        """Copy a file from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path of the remote source directory / file
        :param remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool

        :raises OSError: if one of src or dst does not exist
        """

    @abc.abstractmethod
    def copytree(self, remotesource: TransportPath, remotedestination: TransportPath, dereference=False):
        """Copy a folder from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path of the remote source directory / file
        :param remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool

        :raise OSError: if one of src or dst does not exist
        """

    ## non-abtract methods. Plugin developers can safely ignore developing these methods
    def copy_from_remote_to_remote(
        self,
        transportdestination: 'Transport',
        remotesource: TransportPath,
        remotedestination: TransportPath,
        **kwargs,
    ):
        """Copy files or folders from a remote computer to another remote computer.

        :param transportdestination: transport to be used for the destination computer
        :param remotesource: path to the remote source directory / file
        :param remotedestination: path to the remote destination directory / file
        :param kwargs: keyword parameters passed to the call to transportdestination.put,
            except for 'dereference' that is passed to self.get

        :type transportdestination: :class:`Transport <aiida.transports.transport.Transport>`,
        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

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
            # TODO: mypy error: Argument 2 to "get" of "Transport"
            # has incompatible type "str | PurePath";
            # expected "str | Path | PurePosixPath"
            self.get(remotesource, sandbox.abspath, **kwargs_get)  # type: ignore[arg-type]
            # Then we scan the full sandbox directory with get_content_list,
            # because copying directly from sandbox.abspath would not work
            # to copy a single file into another single file, and copying
            # from sandbox.get_abs_path('*') would not work for files
            # beginning with a dot ('.').
            for filename in sandbox.get_content_list():
                # no matter is transpordestination is Transport or AsyncTransport
                # the following method will work, as both classes support put(), blocking method
                transportdestination.put(os.path.join(sandbox.abspath, filename), remotedestination, **kwargs_put)

    @abc.abstractmethod
    def _exec_command_internal(self, command: str, workdir: Optional[TransportPath] = None, **kwargs):
        """Execute the command on the shell, similarly to os.system.

        Enforce the execution to be run from `workdir`.

        If possible, use the higher-level
        exec_command_wait function.

        :param command: execute the command given as a string
        :param workdir: (optional, default=None) if set, the command will be executed
                in the specified working directory.

        :type command: str
        :type workdir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: stdin, stdout, stderr and the session, when this exists \
                 (can be None).
        """

    @abc.abstractmethod
    def exec_command_wait_bytes(self, command: str, stdin=None, workdir: Optional[TransportPath] = None, **kwargs):
        """Execute the command on the shell, waits for it to finish,
        and return the retcode, the stdout and the stderr as bytes.

        Enforce the execution to be run from workdir, if this is not None.

        The command implementation can have some additional plugin-specific kwargs.

        :param command: execute the command given as a string
        :param stdin: (optional,default=None) can be bytes or a file-like object.
        :param workdir: (optional, default=None) if set, the command will be executed
                in the specified working directory.

        :type command: str
        :type workdir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a tuple: the retcode (int), stdout (bytes) and stderr (bytes).
        """

    def exec_command_wait(
        self, command, stdin=None, encoding='utf-8', workdir: Optional[TransportPath] = None, **kwargs
    ):
        """Executes the specified command and waits for it to finish.

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
        :param workdir: (optional, default=None) if set, the command will be executed
            in the specified working directory.

        :type command: str
        :type encoding: str
        :type workdir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a tuple with (return_value, stdout, stderr) where stdout and stderr are both strings, decoded
            with the specified encoding.
        """
        retval, stdout_bytes, stderr_bytes = self.exec_command_wait_bytes(
            command=command, stdin=stdin, workdir=workdir, **kwargs
        )
        # Return the decoded strings
        if sys.platform == 'win32':
            import chardet

            outenc = chardet.detect(stdout_bytes)['encoding']
            errenc = chardet.detect(stderr_bytes)['encoding']
            if outenc is None:
                outenc = 'utf-8'
            if errenc is None:
                errenc = 'utf-8'
            return (retval, stdout_bytes.decode(outenc), stderr_bytes.decode(errenc))
        else:
            return (retval, stdout_bytes.decode(encoding), stderr_bytes.decode(encoding))

    @abc.abstractmethod
    def get(self, remotepath: TransportPath, localpath: TransportPath, *args, **kwargs):
        """Retrieve a file or folder from remote source to local destination
        both localpath and remotepath must be an absolute path.

        This method should be able to handle remothpath containing glob patterns,
            in that case should only downloading matching patterns.

        :param remotepath: remote_folder_path
        :param localpath: (local_folder_path

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def getfile(self, remotepath: TransportPath, localpath: TransportPath, *args, **kwargs):
        """Retrieve a file from remote source to local destination
        both localpath and remotepath must be an absolute path.

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def gettree(self, remotepath: TransportPath, localpath: TransportPath, *args, **kwargs):
        """Retrieve a folder recursively from remote source to local destination
        both localpath and remotepath must be an absolute path.

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    def getcwd(self):
        """
        DEPRECATED: This method is deprecated and should be removed in the next major version.
            PLEASE DON'T USE IT IN THE INTERFACE!!

        Get working directory
        :return: a string identifying the current working directory
        """

        warn_deprecation(
            '`getcwd()` is deprecated and will be removed in the next major version.',
            version=3,
        )

    @abc.abstractmethod
    def get_attribute(self, path: TransportPath):
        """Return an object FixedFieldsAttributeDict for file in a given path,
        as defined in aiida.common.extendeddicts
        Each attribute object consists in a dictionary with the following keys:

        * st_size: size of files, in bytes

        * st_uid: user id of owner

        * st_gid: group id of owner

        * st_mode: protection bits

        * st_atime: time of most recent access

        * st_mtime: time of most recent modification

        :param path: path to file

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: object FixedFieldsAttributeDict
        """

    def get_mode(self, path: TransportPath):
        """Return the portion of the file's mode that can be set by chmod().

        :param path: path to file

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: the portion of the file's mode that can be set by chmod()
        """
        import stat

        return stat.S_IMODE(self.get_attribute(path).st_mode)

    @abc.abstractmethod
    def isdir(self, path: TransportPath):
        """True if path is an existing directory.
        Return False also if the path does not exist.

        :param path: path to directory

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: boolean
        """

    @abc.abstractmethod
    def isfile(self, path: TransportPath):
        """Return True if path is an existing file.
        Return False also if the path does not exist.

        :param path: path to file

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: boolean
        """

    @abc.abstractmethod
    def listdir(self, path: TransportPath = '.', pattern=None):
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: path to list (default to '.')
            DEPRECATED: using '.' is deprecated and will be removed in the next major version.
        :param pattern: if used, listdir returns a list of files matching
                            filters in Unix style. Unix only.

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a list of strings
        """

    def listdir_withattributes(self, path: TransportPath = '.', pattern: Optional[str] = None):
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: path to list (default to '.')
            if using a relative path, it is relative to the current working directory,
            taken from DEPRECATED `self.getcwd()`.
        :param pattern: if used, listdir returns a list of files matching
                            filters in Unix style. Unix only.
        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type pattern: str
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
        path = str(path)
        retlist = []
        if path.startswith('/'):
            cwd = Path(path).resolve().as_posix()
        else:
            warn_deprecation(
                'Using relative paths in `listdir_withattributes` is no longer supported '
                'and will be removed in the next major version.',
                version=3,
            )
            cwd = self.getcwd()
        for file_name in self.listdir(cwd):
            filepath = os.path.join(cwd, file_name)
            attributes = self.get_attribute(filepath)
            retlist.append({'name': file_name, 'attributes': attributes, 'isdir': self.isdir(filepath)})
        return retlist

    @abc.abstractmethod
    def makedirs(self, path: TransportPath, ignore_existing=False):
        """Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param path: directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                                     if the leaf directory does already exist
        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises: OSError, if directory at path already exists
        """

    @abc.abstractmethod
    def mkdir(self, path: TransportPath, ignore_existing=False):
        """Create a folder (directory) named path.

        :param path: name of the folder to create
        :param bool ignore_existing: if True, does not give any error if the
                                     directory already exists
        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises: OSError, if directory at path already exists
        """

    @abc.abstractmethod
    def normalize(self, path: TransportPath = '.'):
        """Return the normalized path (on the server) of a given path.
        This can be used to quickly resolve symbolic links or determine
        what the server is considering to be the "current folder".

        :param path: path to be normalized

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the path can't be resolved on the server
        """

    @abc.abstractmethod
    def put(self, localpath: TransportPath, remotepath: TransportPath, *args, **kwargs):
        """Put a file or a directory from local src to remote dst.
        both localpath and remotepath must be an absolute path.
        Redirects to putfile and puttree.

        This method should be able to handle localpath containing glob patterns,
            in that case should only uploading matching patterns.

        :param localpath: absolute path to local source
        :param remotepath: path to remote destination

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def putfile(self, localpath: TransportPath, remotepath: TransportPath, *args, **kwargs):
        """Put a file from local src to remote dst.
        both localpath and remotepath must be an absolute path.

        :param localpath: absolute path to local file
        :param remotepath: path to remote file

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def puttree(self, localpath: TransportPath, remotepath: TransportPath, *args, **kwargs):
        """Put a folder recursively from local src to remote dst.
        both localpath and remotepath must be an absolute path.

        :param localpath: absolute path to local folder
        :param remotepath: path to remote folder

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def remove(self, path: TransportPath):
        """Remove the file at the given path. This only works on files;
        for removing folders (directories), use rmdir.

        :param path: path to file to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the path is a directory
        """

    @abc.abstractmethod
    def rename(self, oldpath: TransportPath, newpath: TransportPath):
        """Rename a file or folder from oldpath to newpath.

        :param oldpath: existing name of the file or folder
        :param newpath: new name for the file or folder

        :type oldpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type newpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises OSError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """

    @abc.abstractmethod
    def rmdir(self, path: TransportPath):
        """Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param path: absolute path to the folder to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def rmtree(self, path: TransportPath):
        """Remove recursively the content at path

        :param  path: absolute path to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the rm execution failed.
        """

    @abc.abstractmethod
    def gotocomputer_command(self, remotedir: TransportPath):
        """Return a string to be run using os.system in order to connect
        via the transport to the remote directory.

        NOTE: This method is not async, and need not to be,
            as it's eventually used for interactive shell commands.

        Expected behaviors:

        * A new bash session is opened

        * A reasonable error message is produced if the folder does not exist

        :param remotedir: the full path of the remote directory

        :type remotedir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    def symlink(self, remotesource: TransportPath, remotedestination: TransportPath):
        """Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: remote source
        :param remotedestination: remote destination

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    def whoami(self):
        """Get the remote username

        :return: username (str)

        :raise OSError: if the whoami command fails.
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
        raise OSError(f'Error while executing whoami. Exit code: {retval}')

    @abc.abstractmethod
    def path_exists(self, path: TransportPath):
        """Returns True if path exists, False otherwise.

        :param path: path to check for existence

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`"""

    # The following definitions are almost copied and pasted
    # from the python module glob.
    def glob(self, pathname: TransportPath):
        """Return a list of paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        :param pathname: the pathname pattern to match.
            It should only be an absolute path.
            DEPRECATED: using relative path is deprecated.

        :type pathname:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a list of paths matching the pattern.
        """
        pathname = str(pathname)
        if not pathname.startswith('/'):
            warn_deprecation(
                'Using relative paths across transport in `glob` is deprecated '
                'and will be removed in the next major version.',
                version=3,
            )
        return list(self.iglob(pathname))

    def iglob(self, pathname):
        """Return an iterator which yields the paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        :param pathname: the pathname pattern to match.
        """
        if not has_magic(pathname):
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

        if has_magic(dirname):
            dirs = [d for d in self.iglob(dirname) if self.isdir(d)]
        else:
            dirs = [dirname] if self.isdir(dirname) else []

        if has_magic(basename):
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
        """Match subpaths of dirname against pattern.

        :param dirname: path to the directory
        :param pattern: pattern to match against
        """
        if not dirname:
            dirname = self.getcwd()
        if isinstance(pattern, str) and not isinstance(dirname, str):
            dirname = dirname.decode(sys.getfilesystemencoding() or sys.getdefaultencoding())
        try:
            names = self.listdir(dirname)
        except EnvironmentError:
            return []
        if pattern[0] != '.':
            names = [name for name in names if name[0] != '.']
        return fnmatch.filter(names, pattern)

    def glob0(self, dirname, basename):
        """Wrap basename i a list if it is empty or if dirname/basename is an existing path, else return empty list.

        :param dirname: path to the directory
        :param basename: basename to match against
        """
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

    @abc.abstractmethod
    def compress(
        self,
        format: str,
        remotesources: Union[TransportPath, list[TransportPath]],
        remotedestination: TransportPath,
        root_dir: TransportPath,
        overwrite: bool = True,
        dereference: bool = False,
    ):
        """Compress a remote directory.

        This method supports `remotesources` with glob patterns.

        :param format: format of compression, should support: 'tar', 'tar.gz', 'tar.bz', 'tar.xz'
        :param remotesources: path (list of paths) to the remote directory(ies) (and/)or file(s) to compress
        :param remotedestination: path to the remote destination file (including file name).
        :param root_dir: the path that compressed files will be relative to.
        :param overwrite: if True, overwrite the file at remotedestination if it already exists.
        :param dereference: if True, follow symbolic links.
            Compress where they point to, instead of the links themselves.

        :raises ValueError: if format is not supported
        :raises OSError: if remotesource does not exist, or a matching file/folder cannot be found
        :raises OSError: if remotedestination already exists and overwrite is False. Or if it is a directory.
        :raises OSError: if cannot create remotedestination
        :raises OSError: if root_dir is not a directory
        """

    @abc.abstractmethod
    def extract(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        overwrite: bool = True,
        strip_components: int = 0,
    ):
        """Extract a remote archive.

        Does not accept glob patterns, as it doesn't make much sense and we don't have a usecase for it.

        :param remotesource: path to the remote archive to extract
        :param remotedestination: path to the remote destination directory
        :param overwrite: if True, overwrite the file at remotedestination if it already exists
            (we don't have a usecase for False, sofar. The parameter is kept for clarity.)
        :param strip_components: strip NUMBER leading components from file names on extraction

        :raises OSError: if the remotesource does not exist.
        :raises OSError: if the extraction fails.
        """

    ## aiida-core engine is ultimately moving towards async, so this is a step in that direction.

    @abc.abstractmethod
    async def open_async(self):
        """Open a transport channel.

        :raises InvalidOperation: if the transport is already open.
        """

    @abc.abstractmethod
    async def close_async(self):
        """Close the transport channel.

        :raises InvalidOperation: if the transport is already closed.
        """

    @abc.abstractmethod
    async def chmod_async(self, path: TransportPath, mode: int):
        """Change permissions of a path.

        :param path: path to file or directory
        :param mode: new permissions

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type mode: int
        """

    @abc.abstractmethod
    async def chown_async(self, path: TransportPath, uid: int, gid: int):
        """Change the owner (uid) and group (gid) of a file.

        :param path: path to file
        :param uid: user id of the new owner
        :param gid: group id of the new owner

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type uid: int
        :type gid: int
        """

    @abc.abstractmethod
    async def copy_async(self, remotesource, remotedestination, dereference=False, recursive=True):
        """Copy a file or a directory from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path to the remote source directory / file
        :param remotedestination: path to the remote destination directory / file
        :param dereference: follow symbolic links
        :param recursive: copy recursively

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type recursive: bool

        :raises: OSError, src does not exist or if the copy execution failed.
        """

    @abc.abstractmethod
    async def copyfile_async(self, remotesource: TransportPath, remotedestination: TransportPath, dereference=False):
        """Copy a file from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path to the remote source file
        :param remotedestination: path to the remote destination file
        :param dereference: follow symbolic links

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool

        :raises: OSError, src does not exist or if the copy execution failed."""

    @abc.abstractmethod
    async def copytree_async(self, remotesource: TransportPath, remotedestination: TransportPath, dereference=False):
        """Copy a folder from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path to the remote source folder
        :param remotedestination: path to the remote destination folder
        :param dereference: follow symbolic links

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool

        :raises: OSError, src does not exist or if the copy execution failed."""

    @abc.abstractmethod
    async def copy_from_remote_to_remote_async(
        self,
        transportdestination: 'Transport',
        remotesource: TransportPath,
        remotedestination: TransportPath,
        **kwargs,
    ):
        """Copy files or folders from a remote computer to another remote computer.

        :param transportdestination: destination transport
        :param remotesource: path to the remote source directory / file
        :param remotedestination: path to the remote destination directory / file
        :param kwargs: keyword parameters passed to the call to transportdestination.put,
            except for 'dereference' that is passed to self.get

        :type transportdestination: :class:`Transport <aiida.transports.transport.Transport>`
        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def exec_command_wait_async(
        self,
        command: str,
        stdin: Optional[str] = None,
        encoding: str = 'utf-8',
        workdir: Optional[TransportPath] = None,
        **kwargs,
    ):
        """Executes the specified command and waits for it to finish.

        :param command: the command to execute
        :param stdin: input to the command
        :param encoding: (IGNORED) this is here just to keep the same signature as the one in `Transport` class
        :param workdir: working directory where the command will be executed

        :type command: str
        :type stdin: str
        :type encoding: str
        :type workdir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a tuple with (return_value, stdout, stderr) where stdout and stderr are both strings.
        :rtype: Tuple[int, str, str]
        """

    @abc.abstractmethod
    async def get_async(self, remotepath: TransportPath, localpath: TransportPath, *args, **kwargs):
        """Retrieve a file or folder from remote source to local destination
        both remotepath and localpath must be absolute paths

        This method should be able to handle remotepath containing glob patterns,
            in that case should only downloading matching patterns.

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def getfile_async(self, remotepath: TransportPath, localpath: TransportPath, *args, **kwargs):
        """Retrieve a file from remote source to local destination
        both remotepath and localpath must be absolute paths

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def gettree_async(self, remotepath: TransportPath, localpath: TransportPath, *args, **kwargs):
        """Retrieve a folder recursively from remote source to local destination
        both remotepath and localpath must be absolute paths

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def get_attribute_async(self, path: TransportPath):
        """Return an object FixedFieldsAttributeDict for file in a given path,
        as defined in aiida.common.extendeddicts
        Each attribute object consists in a dictionary with the following keys:

        * st_size: size of files, in bytes

        * st_uid: user id of owner

        * st_gid: group id of owner

        * st_mode: protection bits

        * st_atime: time of most recent access

        * st_mtime: time of most recent modification

        :param path: path to file

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: object FixedFieldsAttributeDict
        """

    async def get_mode_async(self, path: TransportPath):
        """Return the portion of the file's mode that can be set by chmod().

        :param str path: path to file

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: the portion of the file's mode that can be set by chmod()
        """
        import stat

        attr = await self.get_attribute_async(path)
        return stat.S_IMODE(attr.st_mode)

    @abc.abstractmethod
    async def isdir_async(self, path: TransportPath):
        """True if path is an existing directory.
        Return False also if the path does not exist.

        :param path: path to directory

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: boolean
        """

    @abc.abstractmethod
    async def isfile_async(self, path: TransportPath):
        """Return True if path is an existing file.
        Return False also if the path does not exist.

        :param path: path to file

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: boolean
        """

    @abc.abstractmethod
    async def listdir_async(self, path: TransportPath, pattern: Optional[str] = None):
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: an absolute path
        :param pattern: if used, listdir returns a list of files matching
                        filters in Unix style. Unix only.

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a list of strings
        """

    @abc.abstractmethod
    async def listdir_withattributes_async(
        self,
        path: TransportPath,
        pattern: Optional[str] = None,
    ):
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: absolute path to list.
        :param pattern: if used, listdir returns a list of files matching
                        filters in Unix style. Unix only.

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type pattern: str
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

    @abc.abstractmethod
    async def makedirs_async(self, path: TransportPath, ignore_existing=False):
        """Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param path: directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                                     if the leaf directory does already exist
        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises: OSError, if directory at path already exists
        """

    @abc.abstractmethod
    async def mkdir_async(self, path: TransportPath, ignore_existing=False):
        """Create a folder (directory) named path.

        :param path: name of the folder to create
        :param bool ignore_existing: if True, does not give any error if the
                                     directory already exists.
        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises: OSError, if directory at path already exists
        """

    @abc.abstractmethod
    async def normalize_async(self, path: TransportPath):
        """Return the normalized path (on the server) of a given path.
        This can be used to quickly resolve symbolic links or determine
        what the server is considering to be the "current folder".

        :param path: path to be normalized

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the path can't be resolved on the server
        """

    @abc.abstractmethod
    async def put_async(self, localpath: TransportPath, remotepath: TransportPath, *args, **kwargs):
        """Put a file or a directory from local src to remote dst.
        both localpath and remotepath must be absolute paths.
        Redirects to putfile and puttree.

        This method should be able to handle localpath containing glob patterns,
            in that case should only uploading matching patterns.

        :param localpath: absolute path to local source
        :param remotepath: path to remote destination

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def putfile_async(self, localpath: TransportPath, remotepath: TransportPath, *args, **kwargs):
        """Put a file from local src to remote dst.
        both localpath and remotepath must be absolute paths.

        :param localpath: absolute path to local file
        :param remotepath: path to remote file

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def puttree_async(self, localpath: TransportPath, remotepath: TransportPath, *args, **kwargs):
        """Put a folder recursively from local src to remote dst.
        both localpath and remotepath must be absolute paths.

        :param localpath: absolute path to local folder
        :param remotepath: path to remote folder

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def remove_async(self, path: TransportPath):
        """Remove the file at the given path. This only works on files;
        for removing folders (directories), use rmdir.

        :param path: path to file to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the path is a directory
        """

    @abc.abstractmethod
    async def rename_async(self, oldpath: TransportPath, newpath: TransportPath):
        """Rename a file or folder from oldpath to newpath.

        :param oldpath: existing name of the file or folder
        :param newpath: new name for the file or folder

        :type oldpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type newpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises OSError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """

    @abc.abstractmethod
    async def rmdir_async(self, path: TransportPath):
        """Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param path: absolute path to the folder to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def rmtree_async(self, path: TransportPath):
        """Remove recursively the content at path

        :param  path: absolute path to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the rm execution failed.
        """

    @abc.abstractmethod
    async def symlink_async(self, remotesource: TransportPath, remotedestination: TransportPath):
        """Create a symbolic link between the remote source and the remote destination.

        :param remotesource: remote source
        :param remotedestination: remote destination

        :param remotesource: absolute path to remote source
        :param remotedestination: absolute path to remote destination
        """

    @abc.abstractmethod
    async def whoami_async(self):
        """Get the remote username

        :return: username (str)

        :raise OSError: if the whoami command fails.
        """

    @abc.abstractmethod
    async def path_exists_async(self, path: TransportPath):
        """Returns True if path exists, False otherwise.

        :param path: path to check for existence

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """

    @abc.abstractmethod
    async def glob_async(self, pathname: TransportPath):
        """Return a list of paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        :param pathname: the pathname pattern to match.
            It should only be absolute path.

        :type pathname:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a list of paths matching the pattern.
        """

    @abc.abstractmethod
    async def compress_async(
        self,
        format: str,
        remotesources: Union[TransportPath, list[TransportPath]],
        remotedestination: TransportPath,
        root_dir: TransportPath,
        overwrite: bool = True,
        dereference: bool = False,
    ):
        """Compress a remote directory.

        This method supports `remotesources` with glob patterns.

        :param format: format of compression, should support: 'tar', 'tar.gz', 'tar.bz', 'tar.xz'
        :param remotesources: path (list of paths) to the remote directory(ies) (and/)or file(s) to compress
        :param remotedestination: path to the remote destination file (including file name).
        :param root_dir: the path that compressed files will be relative to.
        :param overwrite: if True, overwrite the file at remotedestination if it already exists.
        :param dereference: if True, follow symbolic links.
            Compress where they point to, instead of the links themselves.

        :raises ValueError: if format is not supported
        :raises OSError: if remotesource does not exist, or a matching file/folder cannot be found
        :raises OSError: if remotedestination already exists and overwrite is False. Or if it is a directory.
        :raises OSError: if cannot create remotedestination
        :raises OSError: if root_dir is not a directory
        """

    @abc.abstractmethod
    async def extract_async(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        overwrite: bool = True,
        strip_components: int = 0,
    ):
        """Extract a remote archive.

        Does not accept glob patterns, as it doesn't make much sense and we don't have a usecase for it.

        :param remotesource: path to the remote archive to extract
        :param remotedestination: path to the remote destination directory
        :param overwrite: if True, overwrite the file at remotedestination if it already exists
            (we don't have a usecase for False, sofar. The parameter is kept for clarity.)
        :param strip_components: strip NUMBER leading components from file names on extraction

        :raises OSError: if the remotesource does not exist.
        :raises OSError: if the extraction fails.
        """


class BlockingTransport(Transport):
    """Abstract class for a generic blocking transport.
    A plugin inheriting from this class can safely ignore implementing async abstract methods.

    Here we overwrite the async counterparts of the methods.
    This is done by awaiting the sync methods.
    """

    def compress(
        self,
        format: str,
        remotesources: Union[TransportPath, list[TransportPath]],
        remotedestination: TransportPath,
        root_dir: TransportPath,
        overwrite: bool = True,
        dereference: bool = False,
    ):
        # The following implementation works for all blocking transoprt plugins
        """Compress a remote directory.

        This method supports `remotesources` with glob patterns.

        :param format: format of compression, should support: 'tar', 'tar.gz', 'tar.bz', 'tar.xz'
        :param remotesources: path (list of paths) to the remote directory(ies) (and/)or file(s) to compress
        :param remotedestination: path to the remote destination file (including file name).
        :param root_dir: the path that compressed files will be relative to.
        :param overwrite: if True, overwrite the file at remotedestination if it already exists.
        :param dereference: if True, follow symbolic links.
            Compress where they point to, instead of the links themselves.

        :raises ValueError: if format is not supported
        :raises OSError: if remotesource does not exist, or a matching file/folder cannot be found
        :raises OSError: if remotedestination already exists and overwrite is False. Or if it is a directory.
        :raises OSError: if cannot create remotedestination
        :raises OSError: if root_dir is not a directory
        """
        if not self.isdir(root_dir):
            raise OSError(f'The relative root {root_dir} does not exist, or is not a directory.')

        if self.isdir(remotedestination):
            raise OSError(f'The remote destination {remotedestination} is a directory, should include a filename.')

        if not overwrite and self.path_exists(remotedestination):
            raise OSError(f'The remote destination {remotedestination} already exists.')

        if format not in ['tar', 'tar.gz', 'tar.bz2', 'tar.xz']:
            raise ValueError(f'Unsupported compression format: {type}')

        self.makedirs(Path(remotedestination).parent, ignore_existing=True)

        compression_flag = {
            'tar': '',
            'tar.gz': 'z',
            'tar.bz2': 'j',
            'tar.xz': 'J',
        }[format]

        if not isinstance(remotesources, list):
            remotesources = [remotesources]

        copy_list = []

        for source in remotesources:
            if has_magic(source):
                copy_list = self.glob(source)
                if not copy_list:
                    raise OSError(
                        f'Either the remote path {source} does not exist, or a matching file/folder not found.'
                    )
            else:
                if not self.path_exists(source):
                    raise OSError(f'The remote path {source} does not exist')

                copy_list.append(source)

        copy_items = ' '.join([str(Path(item).relative_to(root_dir)) for item in copy_list])
        # note: order of the flags is important
        tar_command = (
            f'tar -c{compression_flag!s}{"h" if dereference else ""}f {remotedestination!s} -C {root_dir!s} '
            + copy_items
        )

        retval, stdout, stderr = self.exec_command_wait(tar_command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the tar command: {stderr}')
        else:
            self.logger.error(
                "Problem executing tar. Exit code: {}, stdout: '{}', stderr: '{}', command: '{}'".format(
                    retval, stdout, stderr, tar_command
                )
            )
            raise OSError(f'Error while creating the tar archive. Exit code: {retval}')

    def extract(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        overwrite: bool = True,
        strip_components: int = 0,
        *args,
        **kwargs,
    ):
        # The following implementation works for all blocking transoprt plugins
        """Extract a remote archive.

        Does not accept glob patterns, as it doesn't make much sense and we don't have a usecase for it.

        :param remotesource: path to the remote archive to extract
        :param remotedestination: path to the remote destination directory
        :param overwrite: if True, overwrite the file at remotedestination if it already exists
            (we don't have a usecase for False, sofar. The parameter is kept for clarity.)
        :param strip_components: strip NUMBER leading components from file names on extraction

        :raises OSError: if the remotesource does not exist.
        :raises OSError: if the extraction fails.
        """
        if not overwrite:
            raise NotImplementedError('The overwrite=False is not implemented yet')

        if not self.path_exists(remotesource):
            raise OSError(f'The remote path {remotesource} does not exist')

        self.makedirs(remotedestination, ignore_existing=True)

        tar_command = f'tar --strip-components {strip_components} -xf {remotesource!s} -C {remotedestination!s} '

        retval, stdout, stderr = self.exec_command_wait(tar_command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the tar command: {stderr}')
        else:
            self.logger.error(
                "Problem executing tar. Exit code: {}, stdout: '{}', stderr: '{}', command: '{}'".format(
                    retval, stdout, stderr, tar_command
                )
            )
            raise OSError(f'Error while extracting the tar archive. Exit code: {retval}')

    async def open_async(self):
        """Counterpart to open() that is async."""
        return self.open()

    async def close_async(self):
        """Counterpart to close() that is async."""
        return self.close()

    async def chmod_async(self, path, mode):
        """Counterpart to chmod() that is async."""
        return self.chmod(path, mode)

    async def chown_async(self, path, uid, gid):
        """Counterpart to chown() that is async."""
        return self.chown(path, uid, gid)

    async def copy_async(self, remotesource, remotedestination, dereference=False, recursive=True):
        """Counterpart to copy() that is async."""
        return self.copy(remotesource, remotedestination, dereference, recursive)

    async def copyfile_async(self, remotesource, remotedestination, dereference=False):
        """Counterpart to copyfile() that is async."""
        return self.copyfile(remotesource, remotedestination, dereference)

    async def copytree_async(self, remotesource, remotedestination, dereference=False):
        """Counterpart to copytree() that is async."""
        return self.copytree(remotesource, remotedestination, dereference)

    async def copy_from_remote_to_remote_async(self, transportdestination, remotesource, remotedestination, **kwargs):
        """Counterpart to copy_from_remote_to_remote()."""
        return self.copy_from_remote_to_remote(transportdestination, remotesource, remotedestination, **kwargs)

    async def exec_command_internal_async(self, command, workdir=None, **kwargs):
        """Counterpart to _exec_command_internal() that is async."""
        return self._exec_command_internal(command, workdir, **kwargs)

    async def exec_command_wait_bytes_async(self, command, stdin=None, workdir=None, **kwargs):
        """Counterpart to exec_command_wait_bytes() that is async."""
        return self.exec_command_wait_bytes(command, stdin, workdir, **kwargs)

    async def exec_command_wait_async(self, command, stdin=None, encoding='utf-8', workdir=None, **kwargs):
        """Counterpart to exec_command_wait() that is async."""
        return self.exec_command_wait(command, stdin, encoding, workdir, **kwargs)

    async def get_async(self, remotepath, localpath, *args, **kwargs):
        """Counterpart to get() that is async."""
        return self.get(remotepath, localpath, *args, **kwargs)

    async def getfile_async(self, remotepath, localpath, *args, **kwargs):
        """Counterpart to getfile() that is async."""
        return self.getfile(remotepath, localpath, *args, **kwargs)

    async def gettree_async(self, remotepath, localpath, *args, **kwargs):
        """Counterpart to gettree() that is async."""
        return self.gettree(remotepath, localpath, *args, **kwargs)

    async def get_attribute_async(self, path):
        """Counterpart to get_attribute() that is async."""
        return self.get_attribute(path)

    async def get_mode_async(self, path):
        """Counterpart to get_mode() that is async."""
        return self.get_mode(path)

    async def isdir_async(self, path):
        """Counterpart to isdir() that is async."""
        return self.isdir(path)

    async def isfile_async(self, path):
        """Counterpart to isfile() that is async."""
        return self.isfile(path)

    async def listdir_async(self, path, pattern=None):
        """Counterpart to listdir() that is async."""
        return self.listdir(path, pattern)

    async def listdir_withattributes_async(self, path: TransportPath, pattern=None):
        """Counterpart to listdir_withattributes() that is async."""
        return self.listdir_withattributes(path, pattern)

    async def makedirs_async(self, path, ignore_existing=False):
        """Counterpart to makedirs() that is async."""
        return self.makedirs(path, ignore_existing)

    async def mkdir_async(self, path, ignore_existing=False):
        """Counterpart to mkdir() that is async."""
        return self.mkdir(path, ignore_existing)

    async def normalize_async(self, path):
        """Counterpart to normalize() that is async."""
        return self.normalize(path)

    async def put_async(self, localpath, remotepath, *args, **kwargs):
        """Counterpart to put() that is async."""
        return self.put(localpath, remotepath, *args, **kwargs)

    async def putfile_async(self, localpath, remotepath, *args, **kwargs):
        """Counterpart to putfile() that is async."""
        return self.putfile(localpath, remotepath, *args, **kwargs)

    async def puttree_async(self, localpath, remotepath, *args, **kwargs):
        """Counterpart to puttree() that is async."""
        return self.puttree(localpath, remotepath, *args, **kwargs)

    async def remove_async(self, path):
        """Counterpart to remove() that is async."""
        return self.remove(path)

    async def rename_async(self, oldpath, newpath):
        """Counterpart to rename() that is async."""
        return self.rename(oldpath, newpath)

    async def rmdir_async(self, path):
        """Counterpart to rmdir() that is async."""
        return self.rmdir(path)

    async def rmtree_async(self, path):
        """Counterpart to rmtree() that is async."""
        return self.rmtree(path)

    async def symlink_async(self, remotesource, remotedestination):
        """Counterpart to symlink() that is async."""
        return self.symlink(remotesource, remotedestination)

    async def whoami_async(self):
        """Counterpart to whoami() that is async."""
        return self.whoami()

    async def path_exists_async(self, path):
        """Counterpart to path_exists() that is async."""
        return self.path_exists(path)

    async def glob_async(self, pathname):
        """Counterpart to glob() that is async."""
        return self.glob(pathname)

    async def compress_async(
        self, format, remotesources, remotedestination, root_dir, overwrite=True, dereference=False
    ):
        """Counterpart to compress() that is async."""
        return self.compress(format, remotesources, remotedestination, root_dir, overwrite, dereference)

    async def extract_async(self, remotesource, remotedestination, overwrite=True, strip_components=0):
        """Counterpart to extract() that is async."""
        return self.extract(remotesource, remotedestination, overwrite, strip_components)


class AsyncTransport(Transport):
    """An abstract base class for asynchronous transports.
    All asynchronous abstract methods of the parent class should be implemented by subclasses.
    While blocking method can be safely ignored, as this class overwrites them.
    However, be aware you cannot use the blocking methods in an async function,
    because they will block the event loop.
    """

    def run_command_blocking(self, func, *args, **kwargs):
        """The event loop must be the one of manager."""

        from aiida.manage import get_manager

        loop = get_manager().get_runner()
        return loop.run_until_complete(func(*args, **kwargs))

    def open(self):
        return self.run_command_blocking(self.open_async)

    def close(self):
        return self.run_command_blocking(self.close_async)

    def get(self, *args, **kwargs):
        return self.run_command_blocking(self.get_async, *args, **kwargs)

    def getfile(self, *args, **kwargs):
        return self.run_command_blocking(self.getfile_async, *args, **kwargs)

    def gettree(self, *args, **kwargs):
        return self.run_command_blocking(self.gettree_async, *args, **kwargs)

    def get_mode(self, *args, **kwargs):
        return self.run_command_blocking(self.get_mode_async, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.run_command_blocking(self.put_async, *args, **kwargs)

    def putfile(self, *args, **kwargs):
        return self.run_command_blocking(self.putfile_async, *args, **kwargs)

    def puttree(self, *args, **kwargs):
        return self.run_command_blocking(self.puttree_async, *args, **kwargs)

    def chmod(self, *args, **kwargs):
        return self.run_command_blocking(self.chmod_async, *args, **kwargs)

    def chown(self, path, uid, gid):
        return self.run_command_blocking(self.chown_async, path, uid, gid)

    def copy(self, *args, **kwargs):
        return self.run_command_blocking(self.copy_async, *args, **kwargs)

    def copyfile(self, *args, **kwargs):
        return self.run_command_blocking(self.copyfile_async, *args, **kwargs)

    def copytree(self, *args, **kwargs):
        return self.run_command_blocking(self.copytree_async, *args, **kwargs)

    def exec_command_wait(self, *args, **kwargs):
        return self.run_command_blocking(self.exec_command_wait_async, *args, **kwargs)

    def exec_command_wait_bytes(self, *args, **kwargs):
        raise NotImplementedError('Use exec_command_wait instead')

    def _exec_command_internal(self, *args, **kwargs):
        raise NotImplementedError('Use exec_command_wait instead')

    def get_attribute(self, *args, **kwargs):
        return self.run_command_blocking(self.get_attribute_async, *args, **kwargs)

    def isdir(self, *args, **kwargs):
        return self.run_command_blocking(self.isdir_async, *args, **kwargs)

    def isfile(self, *args, **kwargs):
        return self.run_command_blocking(self.isfile_async, *args, **kwargs)

    def listdir(self, *args, **kwargs):
        return self.run_command_blocking(self.listdir_async, *args, **kwargs)

    def listdir_withattributes(self, *args, **kwargs):
        return self.run_command_blocking(self.listdir_withattributes_async, *args, **kwargs)

    def makedirs(self, *args, **kwargs):
        return self.run_command_blocking(self.makedirs_async, *args, **kwargs)

    def mkdir(self, *args, **kwargs):
        return self.run_command_blocking(self.mkdir_async, *args, **kwargs)

    def remove(self, *args, **kwargs):
        return self.run_command_blocking(self.remove_async, *args, **kwargs)

    def rename(self, *args, **kwargs):
        return self.run_command_blocking(self.rename_async, *args, **kwargs)

    def rmdir(self, *args, **kwargs):
        return self.run_command_blocking(self.rmdir_async, *args, **kwargs)

    def rmtree(self, *args, **kwargs):
        return self.run_command_blocking(self.rmtree_async, *args, **kwargs)

    def path_exists(self, *args, **kwargs):
        return self.run_command_blocking(self.path_exists_async, *args, **kwargs)

    def whoami(self, *args, **kwargs):
        return self.run_command_blocking(self.whoami_async, *args, **kwargs)

    def symlink(self, *args, **kwargs):
        return self.run_command_blocking(self.symlink_async, *args, **kwargs)

    def glob(self, *args, **kwargs):
        return self.run_command_blocking(self.glob_async, *args, **kwargs)

    def normalize(self, *args, **kwargs):
        return self.run_command_blocking(self.normalize_async, *args, **kwargs)

    def extract(self, *args, **kwargs):
        return self.run_command_blocking(self.extract_async, *args, **kwargs)

    def compress(self, *args, **kwargs):
        return self.run_command_blocking(self.compress_async, *args, **kwargs)


class TransportInternalError(InternalError):
    """Raised if there is a transport error that is raised to an internal error (e.g.
    a transport method called without opening the channel first).
    """
