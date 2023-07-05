# -*- coding: utf-8 -*-
import errno
import io
from pathlib import Path
import socket
import stat
import time

import fabric

from aiida import common

from .. import transport


class SshLightTransport(transport.Transport):
    _MAX_EXEC_COMMAND_LOG_SIZE = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hostname = kwargs.pop('machine')
        self.connection = fabric.Connection(self.hostname)
        self._sftp = None

    def chdir(self, path):
        """Change directory of the SFTP session. Emulated internally by paramiko."""
        self.sftp.chdir(path)

    def chmod(self, path, mode):
        """Change permissions to path"""
        raise NotImplementedError

    def chown(self, path, uid, gid):
        """Change owner permissions of a file."""
        raise NotImplementedError

    def close(self):
        """Close the SSH connection."""
        if self.connection.is_connected:
            self._sftp.close()
            self.connection.close()

    def copyfile(self, remotesource, remotedestination, dereference=False):
        raise NotImplementedError

    def copytree(self, remotesource, remotedestination, dereference=False):
        raise NotImplementedError

    def copy(self, remotesource, remotedestination, dereference=False, recursive=True):
        raise NotImplementedError

    def _exec_command_internal(self, command, **kwargs):
        channel = self.connection.client.get_transport().open_session()
        if 'combine_stderr' in kwargs:
            channel.set_combine_stderr(kwargs.pop('combine_stderr'))

        if self.getcwd() is not None:
            escaped_folder = common.escaping.escape_for_bash(self.getcwd())
            command_to_execute = f'cd {escaped_folder} && ( {command} )'
        else:
            command_to_execute = command

        self.logger.debug(f'Command to be executed: {command_to_execute[:self._MAX_EXEC_COMMAND_LOG_SIZE]}')
        # Note: The default shell will eat one level of escaping, while
        # 'bash -l -c ...' will eat another. Thus, we need to escape again.
        bash_commmand = self._bash_command_str + '-c '

        channel.exec_command(bash_commmand + common.escaping.escape_for_bash(command_to_execute))

        bufsize = kwargs.pop('bufsize', -1)
        stdin = channel.makefile('wb', bufsize)
        stdout = channel.makefile('rb', bufsize)
        stderr = channel.makefile_stderr('rb', bufsize)

        return stdin, stdout, stderr, channel

    def exec_command_wait_bytes(self, command, stdin=None, **kwargs):
        ssh_stdin, stdout, stderr, channel = self._exec_command_internal(command, **kwargs)
        if stdin is not None:
            if isinstance(stdin, str):
                filelike_stdin = io.StringIO(stdin)
            elif isinstance(stdin, bytes):
                filelike_stdin = io.BytesIO(stdin)
            elif isinstance(stdin, (io.BufferedIOBase, io.TextIOBase)):
                # It seems both StringIO and BytesIO work correctly when doing ssh_stdin.write(line)?
                # (The ChannelFile is opened with mode 'b', but until now it always has been a StringIO)
                filelike_stdin = stdin
            else:
                raise ValueError('You can only pass strings, bytes, BytesIO or StringIO objects')

            for line in filelike_stdin:
                ssh_stdin.write(line)

        # I flush and close them anyway; important to call shutdown_write
        # to avoid hangouts
        ssh_stdin.flush()
        ssh_stdin.channel.shutdown_write()

        # Now I get the output
        stdout_bytes = []
        stderr_bytes = []
        # 100kB buffer (note that this should be smaller than the window size of paramiko)
        # Also, apparently if the data is coming slowly, the read() command will not unlock even for
        # times much larger than the timeout. Therefore we don't want to have very large buffers otherwise
        # you risk that a lot of output is sent to both stdout and stderr, and stderr goes beyond the
        # window size and blocks.
        # Note that this is different than the bufsize of paramiko.
        internal_bufsize = 100 * 1024

        # Set a small timeout on the channels, so that if we get data from both
        # stderr and stdout, and the connection is slow, we interleave the receive and don't hang
        # NOTE: Timeouts and sleep time below, as well as the internal_bufsize above, have been benchmarked
        # to try to optimize the overall throughput. I could get ~100MB/s on a localhost via ssh (and 3x slower
        # if compression is enabled).
        # It's important to mention that, for speed benchmarks, it's important to disable compression
        # in the SSH transport settings, as it will cap the max speed.
        stdout.channel.settimeout(0.01)
        stderr.channel.settimeout(0.01)  # Maybe redundant, as this could be the same channel.

        while True:
            chunk_exists = False

            if stdout.channel.recv_ready():  # True means that the next .read call will at least receive 1 byte
                chunk_exists = True
                try:
                    piece = stdout.read(internal_bufsize)
                    stdout_bytes.append(piece)
                except socket.timeout:
                    # There was a timeout: I continue as there should still be data
                    pass

            if stderr.channel.recv_stderr_ready():  # True means that the next .read call will at least receive 1 byte
                chunk_exists = True
                try:
                    piece = stderr.read(internal_bufsize)
                    stderr_bytes.append(piece)
                except socket.timeout:
                    # There was a timeout: I continue as there should still be data
                    pass

            # If chunk_exists, there is data (either already read and put in the std*_bytes lists, or
            # still in the buffer because of a timeout). I need to loop.
            # Otherwise, there is no data in the buffers, and I enter this block.
            if not chunk_exists:
                # Both channels have no data in the buffer
                if channel.exit_status_ready():
                    # The remote execution is over

                    # I think that in some corner cases there might still be some data,
                    # in case the data arrived between the previous calls and this check.
                    # So we do a final read. Since the execution is over, I think all data is in the buffers,
                    # so we can just read the whole buffer without loops
                    stdout_bytes.append(stdout.read())
                    stderr_bytes.append(stderr.read())
                    # And we go out of the `while True` loop
                    break
                # The exit status is not ready:
                # I just put a small sleep to avoid infinite fast loops when data
                # is not available on a slow connection, and loop
                time.sleep(0.01)

        # I get the return code (blocking)
        # However, if I am here, the exit status is ready so this should be returning very quickly
        retval = channel.recv_exit_status()

        return (retval, b''.join(stdout_bytes), b''.join(stderr_bytes))

    def get(self, remotepath, localpath, *args, **kwargs):
        raise NotImplementedError

    def get_attribute(self, path):
        """Returns the object Fileattribute, specified in aiida.transports."""
        raise NotImplementedError

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
        raise NotImplementedError

    def isdir(self, path):
        """Check if the given path is a directory."""
        return stat.S_ISDIR(self.stat(path).st_mode)

    def isfile(self, path):
        """Check if the given path is a file."""
        if not path:
            return False
        try:
            return stat.S_ISREG(self.stat(path).st_mode)
        except IOError as exc:
            if getattr(exc, 'errno', None) == 2:
                # errno=2 means path does not exist: I return False
                return False
            raise

    def listdir(self, path='.', pattern=None):
        raise NotImplementedError

    def makedirs(self, path, ignore_existing=False):
        raise NotImplementedError

    def mkdir(self, path, ignore_existing=False):
        raise NotImplementedError

    def normalize(self, path='.'):
        """Returns the normalized path (removing double slashes, etc...)."""
        return self.sftp.normalize(path)

    def open(self):
        if not self.connection.is_connected:
            self.connection.open()
            self._sftp = self.connection.client.open_sftp()

    def path_exists(self, path):
        """Check if path exists."""
        try:
            self.stat(path)
        except IOError as exc:
            if exc.errno == errno.ENOENT:
                return False
            raise
        else:
            return True

    def put(self, localpath, remotepath, *args, **kwargs):
        raise NotImplementedError

    def putfile(self, localpath, remotepath, *args, **kwargs):
        """Put a file from local to remote.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist, or unintentionally overwriting
        """

        if not Path(localpath).is_absolute():
            raise ValueError('The localpath must be an absolute path')

        if self.isfile(remotepath) and not kwargs.pop('overwrite', False):
            raise OSError('Destination already exists: not overwriting it')

        return self.sftp.put(localpath, remotepath, callback=kwargs.pop('callback', None))

    def puttree(self, localpath, remotepath, *args, **kwargs):
        raise NotImplementedError

    def remove(self, path):
        """Remove a single file at 'path'."""
        return self.sftp.remove(path)

    def rename(self, oldpath, newpath):
        """Rename a file or folder from 'oldpath' to 'newpath'."""
        raise NotImplementedError

    def rmtree(self, path):
        raise NotImplementedError

    def rmdir(self, path):
        """Remove the folder named 'path' if empty."""
        raise NotImplementedError

    @property
    def sftp(self):
        if not self.connection.is_connected:
            raise transport.TransportInternalError(
                'Error, sftp method called for SshTransport without opening the channel first'
            )
        return self._sftp

    def stat(self, path):
        """Retrieve information about a file on the remote system."""
        return self.sftp.stat(path)

    def symlink(self, remotesource, remotedestination):
        raise NotImplementedError
