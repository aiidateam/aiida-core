# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import aiida.common
from aiida.common.exceptions import InternalError
from aiida.common.extendeddicts import FixedFieldsAttributeDict

import os, re, fnmatch, sys  # for glob commands


magic_check = re.compile('[*?[]')


def TransportFactory(module):
    """
    Used to return a suitable Transport subclass.

    :param str module: name of the module containing the Transport subclass
    :return: the transport subclass located in module 'module'
    """
    from aiida.common.pluginloader import BaseFactory

    return BaseFactory(module, Transport, "aiida.transport.plugins")


class FileAttribute(FixedFieldsAttributeDict):
    """
    A class, resembling a dictionary, to describe the attributes of a file,
    that is returned by get_attribute().
    Possible keys: st_size, st_uid, st_gid, st_mode, st_atime, st_mtime
    """
    _valid_fields = (
        'st_size',
        'st_uid',
        'st_gid',
        'st_mode',
        'st_atime',
        'st_mtime',
    )


class TransportInternalError(InternalError):
    """
    Raised if there is a transport error that is raised to an internal error (e.g.
    a transport method called without opening the channel first).
    """
    pass


def copy_from_remote_to_remote(transportsource,transportdestination,
                                  remotesource,remotedestination,**kwargs):
    """
    Copy files or folders from a remote computer to another remote computer.

    :param transportsource: transport to be used for the source computer
    :param transportdestination: transport to be used for the destination computer
    :param str remotesource: path to the remote source directory / file
    :param str remotedestination: path to the remote destination directory / file
    :param kwargs: keyword parameters passed to the final put,
        except for 'dereference' that is passed to the initial get

    .. note:: it uses the method transportsource.copy_from_remote_to_remote
    """
    transportsource.copy_from_remote_to_remote(transportdestination,
                                               remotesource,remotedestination,
                                               **kwargs)

class Transport(object):
    """
    Abstract class for a generic transport (ssh, local, ...)
    Contains the set of minimal methods
    """
    # To be defined in the subclass
    # See the ssh or local plugin to see the format
    _valid_auth_params = None

    def __init__(self, *args, **kwargs):
        """
        __init__ method of the Transport base class.
        """
        self._logger = aiida.common.aiidalogger.getChild('transport').getChild(
            self.__class__.__name__)

        self._logger_extra = None

    def __enter__(self):
        """
        For transports that require opening a connection, opens
        all required channels (used in 'with' statements)
        """
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        """
        Closes connections, if needed (used in 'with' statements).
        """
        self.close()

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

    def _set_logger_extra(self, logger_extra):
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
    def get_short_doc(self):
        """
        Return the first non-empty line of the class docstring, if available
        """
        # Remove empty lines
        docstring = self.__doc__
        if not docstring:
            return "No documentation available"

        doclines = [i for i in docstring.splitlines() if i.strip()]
        if doclines:
            return doclines[0].strip()
        else:
            return "No documentation available"

    @classmethod
    def get_valid_transports(cls):
        """
        :return: a list of existing plugin names
        """
        from aiida.common.pluginloader import existing_plugins

        return existing_plugins(Transport, "aiida.transport.plugins")

    @classmethod
    def get_valid_auth_params(cls):
        """
        Return the internal list of valid auth_params
        """
        if cls._valid_auth_params is None:
            raise NotImplementedError
        else:
            return cls._valid_auth_params

    @property
    def logger(self):
        """
        Return the internal logger.
        If you have set extra parameters using _set_logger_extra(), a
        suitable LoggerAdapter instance is created, bringing with itself
        also the extras.
        """
        try:
            import logging
            from aiida.utils.logger import get_dblogger_extra

            if self._logger_extra is not None:
                return logging.LoggerAdapter(logger=self._logger,
                                             extra=self._logger_extra)
            else:
                return self._logger
        except AttributeError:
            raise InternalError("No self._logger configured for {}!")

    def chdir(self, path):
        """
        Change directory to 'path'

        :param str path: path to change working directory into.
        :raises: IOError, if the requested path does not exist
        :rtype: str
        """
        # #TODO: understand if we want this behavior: this is emulated
        # by paramiko, and we should emulate it also for the local
        #        transport, since we do not want a global chdir for the whole
        #        code (the same holds for get_pwd).
        #        However, it could be useful to execute by default the
        #        codes from that specific directory.

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


    def copy(self, remotesource, remotedestination, *args, **kwargs):
        """
        Copy a file or a directory from remote source to remote destination
        (On the same remote machine)

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raises: IOError, if one of src or dst does not exist
        """
        raise NotImplementedError


    def copyfile(self, remotesource, remotedestination, *args, **kwargs):
        """
        Copy a file from remote source to remote destination
        (On the same remote machine)

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raises IOError: if one of src or dst does not exist
        """
        raise NotImplementedError


    def copytree(self, remotesource, remotedestination, *args, **kwargs):
        """
        Copy a folder from remote source to remote destination
        (On the same remote machine)

        :param str remotesource: path of the remote source directory / file
        :param str remotedestination: path of the remote destination directory / file

        :raise IOError: if one of src or dst does not exist
        """
        raise NotImplementedError


    def copy_from_remote_to_remote(self,transportdestination,
                                      remotesource,remotedestination,**kwargs):
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

        kwargs_get = {'callback': None,
                      'dereference': kwargs.pop('dereference',True),
                      'overwrite': True,
                      'ignore_nonexisting': False,
                      }
        # TODO: dereference should be set to False in the following, as soon as
        # dereference=False is supported by all transport plugins
        kwargs_put = {'callback': kwargs.pop('callback',None),
                      'dereference': True,
                      'overwrite': kwargs.pop('overwrite',True),
                      'ignore_nonexisting': kwargs.pop('ignore_nonexisting',False),
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
                transportdestination.put(os.path.join(sandbox.abspath,filename),
                                         remotedestination,**kwargs_put)


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
        # TODO : add tests for this method

        command = 'whoami'
        retval, username, stderr = self.exec_command_wait(command)
        if retval == 0:
            if stderr.strip():
                self.logger.warning("There was nonempty stderr in the whoami "
                                    "command: {}".format(stderr))
            return username.strip()
        else:
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
        if not dirname:
            # dirname = os.curdir # ORIGINAL
            dirname = self.getcwd()
        if isinstance(pattern, unicode) and not isinstance(dirname, unicode):
            dirname = unicode(dirname, sys.getfilesystemencoding() or
                              sys.getdefaultencoding())
        try:
            # names = os.listdir(dirname)
            #print dirname
            names = self.listdir(dirname)
        except os.error:
            return []
        except IOError:
            return []
        if pattern[0] != '.':
            names = filter(lambda x: x[0] != '.', names)
        return fnmatch.filter(names, pattern)

    def glob0(self, dirname, basename):
        if basename == '':
            # `os.path.split()` returns an empty basename for paths ending with a
            # directory separator.  'q*x/' should match only directories.
            # if os.path.isdir(dirname):
            if self.isdir(dirname):
                return [basename]
        else:
            # if os.path.lexists(os.path.join(dirname, basename)):
            if self.path_exists(os.path.join(dirname, basename)):
                return [basename]
        return []

    def has_magic(self, s):
        return magic_check.search(s) is not None
