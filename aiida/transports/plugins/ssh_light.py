# -*- coding: utf-8 -*-
"""SSH tranport plugin that requires very little setup."""
import os
from pathlib import Path
import re
import stat

import fabric

from aiida import transports

from .. import transport


class SshLightTransport(transport.Transport):  # pylint: disable=too-many-public-methods
    """Lightweight, easy to setup SSH transport plugin."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hostname = kwargs.pop('machine')
        self.connection = fabric.Connection(self.hostname)
        self.sftp = None

    def _run(self, command, **kwargs):
        self.connection.run(command, hide=True, warn=True, **kwargs)

    def chdir(self, path):
        self.sftp.chdir(path)

    def chmod(self, path, mode):
        """Change permissions to path."""
        return self.sftp.chmod(path, mode)

    def chown(self, path, uid, gid):
        """Change owner permissions of a file."""
        raise self.sftp.chown(path=path, uid=uid, gid=gid)

    def close(self):
        """Close the SSH connection."""
        if self.connection.is_connected:
            self.sftp.close()
            self.connection.close()

    def copyfile(self, remotesource, remotedestination, dereference=False):
        return self.copy(remotesource, remotedestination, dereference)

    def copytree(self, remotesource, remotedestination, dereference=False):
        return self.copy(remotesource, remotedestination, dereference, recursive=True)

    def copy(self, remotesource, remotedestination, dereference=False, recursive=True):
        raise NotImplementedError

    def _exec_command_internal(self, command, **kwargs):

        self.logger.debug(f'Command to be executed: {command}')

        # Do not print command output (hide=True)
        # Do not except on nonzero exit status (warn=True)
        # For more information, see https://docs.pyinvoke.org/en/latest/api/runners.html#invoke.runners.Runner.run
        result = self.connection.run(command, hide=True, warn=True, **kwargs)

        stdin = bytes(result.command, result.encoding)
        stdout = bytes(result.stdout, result.encoding)
        stderr = bytes(result.stderr, result.encoding)

        return stdin, stdout, stderr, result

    def exec_command_wait_bytes(self, command, stdin=None, **kwargs):
        _, stdout, stderr, result = self._exec_command_internal(command, **kwargs)
        return result.return_code, stdout, stderr

    def get(self, remotepath, localpath, *args, **kwargs):
        raise NotImplementedError

    def get_attribute(self, path):
        """Returns the object Fileattribute, specified in aiida.transports."""
        paramiko_attr = self.sftp.lstat(path)
        aiida_attr = transports.util.FileAttribute()
        for key in aiida_attr._valid_fields:  # pylint: disable=protected-access
            aiida_attr[key] = getattr(paramiko_attr, key)
        return aiida_attr

    def getcwd(self):
        """Return the current working directory for this SFTP session, as emulated by paramiko."""
        return self.sftp.getcwd()

    def getfile(self, remotepath, localpath, *args, **kwargs):
        """
        Get a file from remote to local.

        :param remotepath: a remote path
        :param  localpath: an (absolute) local path
        :param  overwrite: if True overwrites files and folders.
                Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if unintentionally overwriting
        """
        if not Path(localpath).is_absolute():
            raise ValueError('localpath must be an absolute path')

        if Path(localpath).is_file() and not kwargs.get('overwrite', True):
            raise OSError('Destination already exists: not overwriting it')

        # Workaround for bug #724 in paramiko -- remove localpath on IOError
        try:
            return self.sftp.get(remotepath, localpath, kwargs.get('callback', None))
        except IOError:
            try:
                Path(localpath).unlink(missing_ok=True)
            except OSError:
                pass
            raise

    def gettree(self, remotepath, localpath, *args, **kwargs):
        raise NotImplementedError

    def gotocomputer_command(self, remotedir):
        return f'ssh -t {self.hostname} {self._gotocomputer_string(remotedir)}'

    def isdir(self, path):
        """Check if the given path is a directory."""
        try:
            return stat.S_ISDIR(self.stat(path).st_mode)
        except (TypeError, FileNotFoundError):  # Wrong path, or path doesn't exist
            return False

    def isfile(self, path):
        """Check if the given path is a file."""
        try:
            return stat.S_ISREG(self.stat(path).st_mode)
        except IOError as exc:
            if getattr(exc, 'errno', None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            raise

    def listdir(self, path='.', pattern=None):
        if not pattern:
            return self.sftp.listdir(path)
        if path.startswith('/'):
            base_dir = path
        else:
            base_dir = os.path.join(self.getcwd(), path)

        filtered_list = self.glob(os.path.join(base_dir, pattern))
        if not base_dir.endswith('/'):
            base_dir += '/'
        return [re.sub(base_dir, '', i) for i in filtered_list]

    def makedirs(self, path, ignore_existing=False):
        return self._run(f'mkdir -p {path}')

    def mkdir(self, path, ignore_existing=False):
        """Attempts to create folder located at path, returns False in case of a failure."""
        if ignore_existing and self.isdir(path):
            return True
        try:
            self.sftp.mkdir(path)
        except Exception:  # pylint: disable=broad-exception-caught
            return False
        return True

    def normalize(self, path='.'):
        """Returns the normalized path (removing double slashes, etc...)."""
        return self.sftp.normalize(path)

    def open(self):
        if not self.connection.is_connected:
            self.sftp = self.connection.sftp()  # It opens the self.connection as well
            self.sftp.chdir('.')  # Needed to make sure sftp.getcwd() returns a valid path

    def path_exists(self, path):
        """Check if path exists."""
        return bool(self.stat(path))

    def put(self, localpath, remotepath, *args, **kwargs):
        if not Path(localpath).is_absolute():
            raise ValueError('The localpath must be an absolute path')

    def putfile(self, localpath, remotepath, *args, **kwargs):
        """Put a file from local to remote. Wrapper around fabrics "put" method.

        For more information, see: https://docs.fabfile.org/en/stable/api/transfer.html#fabric.transfer.Transfer.put
        """
        return self.connection.put(localpath, remotepath)

    def puttree(self, localpath, remotepath, *args, **kwargs):
        raise NotImplementedError

    def remove(self, path):
        """Remove a single file at 'path'."""
        return self.sftp.remove(path)

    def rename(self, oldpath, newpath):
        """Rename a file or folder from 'oldpath' to 'newpath'."""
        return self.sftp.rename(oldpath, newpath)

    def rmtree(self, path):
        return self._run(f'rm -rf {path}')

    def rmdir(self, path):
        """Remove the folder named 'path' if empty."""
        return self.sftp.rmdir(path)

    def stat(self, path):
        """Retrieve information about a file on the remote system."""
        try:
            return self.sftp.stat(path)
        except (TypeError, FileNotFoundError):  # Wrong path, or path doesn't exist
            return None

    def symlink(self, remotesource, remotedestination):
        """Creates a symbolic link between the remote source and the remote destination."""
        self.sftp.symlink(remotesource, remotedestination)
