# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for transport over SSH, when SFTP is not available."""
# pylint: disable=too-many-lines
import glob
import io
import os
from stat import S_ISDIR, S_ISREG
from errno import ENOTDIR
import paramiko
import click

from aiida.cmdline.params import options
from aiida.cmdline.params.types.path import AbsolutePathOrEmptyParamType
from aiida.common.escaping import escape_for_bash
from .ssh import SshTransport
from ..transport import Transport, TransportInternalError

__all__ = ('parse_sshconfig', 'convert_to_bool', 'SshTransport')


class SshOnlyTransport(SshTransport):  # pylint: disable=too-many-public-methods
    """
    Support connection, command execution and data transfer to remote computers via SSH only.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialize the SshOnlyTransport class.

        :param machine: the machine to connect to
        :param load_system_host_keys: (optional, default False)
           if False, do not load the system host keys
        :param key_policy: (optional, default = paramiko.RejectPolicy())
           the policy to use for unknown keys

        Other parameters valid for the ssh connect function (see the
        self._valid_connect_params list) are passed to the connect
        function (as port, username, password, ...); taken from the
        accepted paramiko.SSHClient.connect() params.
        """
        super().__init__(*args, **kwargs)
        self._cwd = None

    def open_file_transport(self):
        self._is_open = True


    def close(self):
        """
        Close the SSHClient.

        :todo: correctly manage exceptions

        :raise aiida.common.InvalidOperation: if the channel is already open
        """
        from aiida.common.exceptions import InvalidOperation

        if not self._is_open:
            raise InvalidOperation('Cannot close the transport: it is already closed')
        self._client.close()
        self._is_open = False

    def _adjust_cwd(self, path):
        """
        Return an adjusted path if we're emulating a "current working
        directory" for the server.
        """
        b_slash = b"/"
        path = paramiko.py3compat.b(path)
        if self._cwd is None:
            return path
        if len(path) and path[0:1] == b_slash:
            # absolute path
            return path
        if self._cwd == b_slash:
            return self._cwd + path
        return self._cwd + b_slash + path

    def getcwd(self):
        return self._cwd and paramiko.py3compat.u(self._cwd)

    def chdir(self, path):
        """
        Change directory of the session. Emulated internally by paramiko.

        Differently from paramiko, if you pass None to chdir, nothing
        happens and the cwd is unchanged.
        """
        old_path = self.getcwd()
        if path is not None:
            if not S_ISDIR(self.stat(path).st_mode):
                code = ENOTDIR
                raise IOError("{}: {}".format(os.strerror(code), path))
            self._cwd = paramiko.py3compat.b(self.normalize(path)).strip()

        # Paramiko already checked that path is a folder, otherwise I would
        # have gotten an exception. Now, I want to check that I have read
        # permissions in this folder (nothing is said on write permissions,
        # though).
        # Otherwise, if I do _exec_command_internal, that as a first operation
        # cd's in a folder, I get a wrong retval, that is an unwanted behavior.
        #
        # Note: I don't store the result of the function; if I have no
        # read permissions, this will raise an exception.
        try:
            self.stat('.')
        except IOError as exc:
            if 'Permission denied' in str(exc):
                self.chdir(old_path)
            raise IOError(str(exc))

    def normalize(self, path='.'):
        """
        Returns the normalized path (removing double slashes, etc...)
        """
        path = self._adjust_cwd(path.strip())

        exe = 'realpath'
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to normalize() must be a non empty string.')

        command = "{} {}".format(exe, paramiko.py3compat.u(path))

        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the normalize command: {}'.format(stderr))
            return paramiko.py3compat.b(stdout)
        self.logger.error(
            "Problem executing normalize. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        raise IOError('Error while executing normalize. Exit code: {}'.format(retval))

    def getcwd(self):
        """
        Return the current working directory for this session, as
        emulated by paramiko. If no directory has been set with chdir,
        this method will return None. But in __enter__ this is set explicitly,
        so this should never happen within this class.
        """
        return self._cwd and paramiko.py3compat.u(self._cwd)

    def stat(self, path, option="--dereference"):

        path = self._adjust_cwd(path.strip())
        command = 'stat --format "%s %u %g %f %X %Y" ' + option + " " + paramiko.py3compat.u(path)

        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the stat command: {}'.format(stderr))
            stat = paramiko.SFTPAttributes()
            statlist = stdout.split()
            stat.st_size = int(statlist[0])
            stat.st_uid = int(statlist[1])
            stat.st_guid = int(statlist[2])
            stat.st_mode = int(statlist[3], 16)
            stat.st_atime = int(statlist[4])
            stat.st_mtime = int(statlist[5])
            return stat

        raise IOError(2, 'Error while executing stat. Exit code: {}'.format(retval))


    def mkdir(self, path, ignore_existing=False):
        """
        Create a folder (directory) named path.

        :param path: name of the folder to create
        :param ignore_existing: if True, does not give any error if the directory
                  already exists

        :raise OSError: If the directory already exists.
        """
        if ignore_existing and self.isdir(path):
            return

        path = self._adjust_cwd(path.strip())
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to mkdir() must be a non empty string.')

        command = "mkdir " + paramiko.py3compat.u(path)
        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the mkdir command: {}'.format(stderr))
            return
        self.logger.error(
            "Problem executing mkdir. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        if os.path.isabs(path):
            raise OSError(
                "Error during mkdir of '{}', "
                "maybe you don't have the permissions to do it, "
                'or the directory already exists? ({})'.format(path, retval)
            )
        else:
            raise OSError(
                "Error during mkdir of '{}' from folder '{}', "
                "maybe you don't have the permissions to do it, "
                'or the directory already exists? ({})'.format(path, self.getcwd(), retval)
            )

    def rmtree(self, path):
        """
        Remove a file or a directory at path, recursively
        Flags used: -r: recursive copy; -f: force, makes the command non interactive;

        :param path: remote path to delete

        :raise IOError: if the rm execution failed.
        """
        # Assuming linux rm command!

        rm_exe = 'rm'
        rm_flags = '-r -f'
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to rmtree() must be a non empty string. ' + 'Found instead %s as path' % path)

        command = '{} {} {}'.format(rm_exe, rm_flags, escape_for_bash(path))

        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the rm command: {}'.format(stderr))
            return True
        self.logger.error(
            "Problem executing rm. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        raise IOError('Error while executing rm. Exit code: {}'.format(retval))

    def rmdir(self, path):
        """
        Remove the folder named 'path' if empty.
        """
        path = self._adjust_cwd(path.strip())
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to rmdir() must be a non empty string.')

        command = "rmdir " + paramiko.py3compat.u(path)
        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the rmdir command: {}'.format(stderr))
            return
        self.logger.error(
            "Problem executing rmdir. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )

    def chmod(self, path, mode):
        """
        Change permissions to path

        :param path: path to file
        :param mode: new permission bits (integer)
        """
        if not path:
            raise IOError('Input path is an empty argument.')
        path = self._adjust_cwd(path.strip())
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to chmod() must be a non empty string.')
        if not mode:
            raise ValueError('mode for chmod() must be a non empty string.')
        #[2:] is to remove 0o prefix.
        command = "chmod " + str(oct(mode)[2:]) + " " + paramiko.py3compat.u(path)
        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the chmod command: {}'.format(stderr))
            return
        self.logger.error(
            "Problem executing chmod. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        raise IOError('Error while executing chmod. Exit code: {}'.format(retval))

    def putfile(self, localpath, remotepath, callback=None, dereference=True, overwrite=True):  # pylint: disable=arguments-differ
        """
        Put a file from local to remote.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist,
                    or unintentionally overwriting
        """
        if not dereference:
            raise NotImplementedError

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if self.isfile(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        file_size = os.stat(localpath).st_size
        with open(localpath, "rb") as fl:
            exe = "echo"
            exe_post = "| cat >"
            command = '{} {} {} {}'.format(exe, escape_for_bash(paramiko.py3compat.u(fl.read())), exe_post, paramiko.py3compat.u(remotepath))

            retval, stdout, stderr = self.exec_command_wait(command)
            if retval == 0:
                if stderr.strip():
                    self.logger.warning('There was nonempty stderr in the put command: {}'.format(stderr))
                if callback is not None:
                    size = self.stat(remotepath).st_size
                    callback(size, file_size)
                #output from put in sftp was always ignored.
                return
            self.logger.error(
                "Problem executing put. Exit code: {}, stdout: '{}', "
                "stderr: '{}'".format(retval, stdout, stderr)
            )
        raise IOError('Error while executing put. Exit code: {}'.format(retval))


    def getfile(self, remotepath, localpath, callback=None, dereference=True, overwrite=True):  # pylint: disable=arguments-differ
        """
        Get a file from remote to local.

        :param remotepath: a remote path
        :param  localpath: an (absolute) local path
        :param  overwrite: if True overwrites files and folders.
                Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if unintentionally overwriting
        """
        if not os.path.isabs(localpath):
            raise ValueError('localpath must be an absolute path')

        if os.path.isfile(localpath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        if not dereference:
            raise NotImplementedError

        with open(localpath, "wb") as fl:

            command = 'cat ' + paramiko.py3compat.u(remotepath)

            retval, stdout, stderr = self.exec_command_wait(command)
            if retval == 0:
                if stderr.strip():
                    self.logger.warning('There was nonempty stderr in the put command: {}'.format(stderr))
                file_size = fl.write(paramiko.py3compat.b(stdout.strip()))
                if callback is not None:
                    size = self.stat(remotepath).st_size
                    callback(size, file_size)
                return
            self.logger.error(
                "Problem executing get. Exit code: {}, stdout: '{}', "
                "stderr: '{}'".format(retval, stdout, stderr)
            )
        raise IOError('Error while executing get. Exit code: {}'.format(retval))

    def lstat(self, path):
        return stat(path, option="")

    def listdir(self, path='.', pattern=None):
        """
        Get the list of files at path.

        :param path: default = '.'
        :param pattern: returns the list of files matching pattern.
                             Unix only. (Use to emulate ``ls *`` for example)
        """
        if not pattern:
            path = self._adjust_cwd(path.strip())

            command = "ls -1 " + paramiko.py3compat.u(path)
            retval, stdout, stderr = self.exec_command_wait(command)

            if retval == 0:
                if stderr.strip():
                    self.logger.warning('There was nonempty stderr in the listdir command: {}'.format(stderr))
                return stdout
            self.logger.error(
                "Problem executing listdir. Exit code: {}, stdout: '{}', "
                "stderr: '{}'".format(retval, stdout, stderr)
            )
            raise IOError('Error while executing listdir. Exit code: {}'.format(retval))

        import re
        if path.startswith('/'):
            base_dir = path
        else:
            base_dir = os.path.join(self.getcwd(), path)

        filtered_list = glob.glob(os.path.join(base_dir, pattern))
        if not base_dir.endswith('/'):
            base_dir += '/'
        return [re.sub(base_dir, '', i) for i in filtered_list]

    def remove(self, path):
        """
        Remove a single file at 'path'
        """
        path = self._adjust_cwd(path.strip())
        # if in input I give an invalid object raise ValueError
        if not path:
            raise ValueError('Input to remove() must be a non empty string.')

        command = "rm " + paramiko.py3compat.u(path)
        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the remove command: {}'.format(stderr))
            return
        self.logger.error(
            "Problem executing remove. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        raise IOError('Error while executing remove. Exit code: {}'.format(retval))

    def rename(self, oldpath, newpath):
        """
        Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises IOError: if oldpath/newpath is not found
        :raises ValueError: if sroldpathc/newpath is not a valid string
        """
        if not oldpath:
            raise ValueError('Source {} is not a valid string'.format(oldpath))
        oldpath = self._adjust_cwd(oldpath.strip())
        if not newpath:
            raise ValueError('Destination {} is not a valid string'.format(newpath))
        newpath = self._adjust_cwd(newpath.strip())

        if not self.isfile(oldpath):
            if not self.isdir(oldpath):
                raise IOError('Source {} does not exist'.format(oldpath))
        if not self.isfile(newpath):
            if not self.isdir(newpath):
                raise IOError('Destination {} does not exist'.format(newpath))

        command = "mv " + paramiko.py3compat.u(oldpath) + " " + paramiko.py3compat.u(newpath)
        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the rename command: {}'.format(stderr))
            return
        self.logger.error(
            "Problem executing rename. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        raise IOError('Error while executing rename. Exit code: {}'.format(retval))


    def symlink_internal(self, source, dest):
        if not source:
            raise ValueError('Input source to symlink() must be a non empty string.')
        source = self._adjust_cwd(source.strip())
        dest = self._adjust_cwd(dest.strip())

        command = "ln -s " + paramiko.py3compat.u(source) + " " + paramiko.py3compat.u(dest)
        retval, stdout, stderr = self.exec_command_wait(command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning('There was nonempty stderr in the symlink command: {}'.format(stderr))
            return
        self.logger.error(
            "Problem executing symlink. Exit code: {}, stdout: '{}', "
            "stderr: '{}'".format(retval, stdout, stderr)
        )
        raise IOError('Error while executing symlink. Exit code: {}'.format(retval))
