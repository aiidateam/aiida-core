###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module instruct a `_AsynchronousSSHBackend` class that backends `AsyncSshTransport`.
It also provides two implementation classes: `_AsyncSSH` and `_OpenSSH`, which are used to
interact with remote machines over SSH.

The `_AsyncSSH` class uses the `asyncssh` library to execute commands and transfer files,
while the `_OpenSSH` class uses the `ssh` command line client.
"""

import abc
import asyncio
import logging
import posixpath
from typing import Optional

import asyncssh
from asyncssh import SFTPFileAlreadyExists

from aiida.common.escaping import escape_for_bash
from aiida.transports.transport import (
    TransportInternalError,
    has_magic,
)


class _AsynchronousSSHBackend(abc.ABC):
    """
    This is a base class for the backend adaptors of `AsyncSshTransport` class.
    It defines the interface for the methods that need to be implemented by the subclasses.
    Note: Subclasses should not be part of the public API and should not be used directly.
    """

    def __init__(self, machine: str, logger: logging.LoggerAdapter, bash_command: str):
        self.bash_command = bash_command + '-c '
        self.machine = machine
        self.logger = logger

    @abc.abstractmethod
    async def open(self):
        """Open the connection"""

    @abc.abstractmethod
    async def close(self):
        """Close the connection"""

    @abc.abstractmethod
    async def get(self, remotepath: str, localpath: str, dereference: bool, preserve: bool, recursive: bool):
        """Get a file or directory from the remote machine.
        :param remotepath: The path to the file or directory on the remote machine
        :param localpath: The path to the file or directory on the local machine
        :param dereference: Whether to follow symlinks
        :param preserve: Whether to preserve the file attributes
        :param recursive: Whether to copy directories recursively.
        If `remotepath` is a file, set this to `False`, `True` otherwise.

        :raises OSError: If failed for whatever reason
        """

    @abc.abstractmethod
    async def put(self, localpath: str, remotepath: str, dereference: bool, preserve: bool, recursive: bool):
        """Put a file or directory on the remote machine.
        :param localpath: The path to the file or directory on the local machine
        :param remotepath: The path to the file or directory on the remote machine
        :param dereference: Whether to follow symlinks
        :param preserve: Whether to preserve the file attributes
        :param recursive: Whether to copy directories recursively.
        If `localpath` is a file, set this to `False`, `True` otherwise.

        :raises OSError: If failed for whatever reason
        """

    @abc.abstractmethod
    async def run(self, command: str, stdin: Optional[str] = None, timeout: Optional[int] = None):
        """Run a command on the remote machine.
        :param command: The command to run
        :param stdin: The input to send to the command
        :param timeout: The timeout in seconds
        :return: The return code, str(stdout), and str(stderr)
        """

    @abc.abstractmethod
    async def lstat(self, path: str):
        """Get the stat of a file or directory.
        :param path: The path to the file or directory
        :return: An instance of `Stat` class
        """

    @abc.abstractmethod
    async def isdir(self, path: str):
        """Check if a path is a directory."""

    @abc.abstractmethod
    async def isfile(self, path: str):
        """Check if a path is a file."""

    @abc.abstractmethod
    async def listdir(self, path: str):
        """List the contents of a directory.
        :param path: The path to the directory
        :return: A list of file and directory names
        """

    @abc.abstractmethod
    async def mkdir(self, path: str, exist_ok: bool = False, parents: bool = False):
        """Create a directory.
        :param path: The path to the directory
        :param exist_ok: If `True`, do not raise an error if the directory already exists
        :param parents: If `True`, create parent directories if they do not exist
        """

    @abc.abstractmethod
    async def remove(self, path: str):
        """Remove a file.
        :param path: The path to the file.
        :raises OSError: If the path is a directory.
        """

    @abc.abstractmethod
    async def rename(self, oldpath: str, newpath: str):
        """Rename a file or directory.
        :param oldpath: The old path and name
        :param newpath: The new path and name
        """

    @abc.abstractmethod
    async def rmdir(self, path: str):
        """Remove an empty directory.
        :param path: The path to the directory

        :raises OSError: If the directory is not empty.
        """

    @abc.abstractmethod
    async def rmtree(self, path: str):
        """Remove a directory and all its contents.
        :param path: The path to the directory

        :raises OSError: If it fails for whatever reason.
        """

    @abc.abstractmethod
    async def path_exists(self, path: str):
        """Check if a path exists.
        :param path: The path to check
        :return: `True` if the path exists, `False` otherwise
        """

    @abc.abstractmethod
    async def symlink(self, source: str, destination: str):
        """Create a single link from source to destination.
        No magic is allowed in source or destination.
        :param source: The source path
        :param destination: The destination path
        """

    @abc.abstractmethod
    async def glob(self, path: str, ignore_nonexisting: bool = True):
        """Return a list of files and directories matching the glob pattern.
        :param path: A path potentially containing the glob pattern
        :param ignore_nonexisting: If `True` (default),
        return an empty list when path does not exist or no matching files/folders are found.

        :return: A list of matching files and directories

        :raises OSError: If the path does not exist or no matching files/folders are found,
            and only if `ignore_nonexisting` is `False`.
        """

    @abc.abstractmethod
    async def chmod(self, path: str, mode: int, follow_symlinks: bool = True):
        """Change the permissions of a file or directory.
        :param path: The path to the file or directory
        :param mode: Th permissions to set (An integer number base 10 -- not octal!)
        :param follow_symlinks: If `True`, change the permissions of the target of a symlink
        """

    @abc.abstractmethod
    async def chown(self, path: str, uid: int, gid: int):
        """Change the ownership of a file or directory.
        :param path: The path to the file or directory
        :param uid: The user ID to set
        :param gid: The group ID to set
        """

    @abc.abstractmethod
    async def copy(
        self,
        remotesource: str,
        remotedestination: str,
        dereference: bool,
        recursive: bool,
        preserve: bool,
    ):
        """Copy a file or directory from one location to another.
        :param remotesource: The source path on the remote machine
        :param remotedestination: The destination path on the remote machine
        :param dereference: Whether to follow symlinks
        :param recursive: Whether to copy directories recursively.
        If `remotesource` is a file, set this to `False`, `True` otherwise.
        :param preserve: Whether to preserve the file attributes

        :raises OSError: If failed for whatever reason
        """


class _AsyncSSH(_AsynchronousSSHBackend):
    """A backend class that uses asyncssh to execute commands and transfer files.
    This class is not part of the public api and should not be used directly.
    Note: This class is not part of the public API and should not be used directly.
    """

    def __init__(self, machine: str, logger: logging.LoggerAdapter, bash_command: str):
        super().__init__(machine, logger, bash_command)

    async def open(self):
        self._conn = await asyncssh.connect(self.machine)
        self._sftp = await self._conn.start_sftp_client()

    async def close(self):
        self._conn.close()
        await self._conn.wait_closed()

    async def get(self, remotepath: str, localpath: str, dereference: bool, preserve: bool, recursive: bool):
        try:
            return await self._sftp.get(
                remotepaths=remotepath,
                localpath=localpath,
                preserve=preserve,
                recurse=recursive,
                follow_symlinks=dereference,
            )
        except asyncssh.Error as exc:
            raise OSError from exc

    async def put(self, localpath: str, remotepath: str, dereference: bool, preserve: bool, recursive: bool):
        try:
            return await self._sftp.put(
                localpaths=localpath,
                remotepath=remotepath,
                preserve=preserve,
                recurse=recursive,
                follow_symlinks=dereference,
            )
        except asyncssh.Error as exc:
            raise OSError from exc

    async def run(self, command: str, stdin: Optional[str] = None, timeout: Optional[int] = None):
        result = await self._conn.run(
            self.bash_command + escape_for_bash(command),
            input=stdin,
            check=False,
            timeout=timeout,
        )
        # Since the command is str, both stdout and stderr are strings
        return (result.returncode, ''.join(str(result.stdout)), ''.join(str(result.stderr)))

    async def lstat(self, path: str):
        # The return object from asyncssh is compatible with `class::Stat`
        return await self._sftp.lstat(path)

    async def isdir(self, path: str):
        return await self._sftp.isdir(path)

    async def isfile(self, path: str):
        return await self._sftp.isfile(path)

    async def listdir(self, path: str):
        return list(await self._sftp.listdir(path))

    async def mkdir(self, path: str, exist_ok: bool = False, parents: bool = False):
        try:
            if parents:
                await self._sftp.makedirs(path, exist_ok=exist_ok)
            else:
                # note: mkdir() in asyncssh does not support the exist_ok parameter
                # we handle it via a try-except block
                await self._sftp.mkdir(path)
        except SFTPFileAlreadyExists:
            # SFTPFileAlreadyExists is only supported in asyncssh version 6.0.0 and later
            if not exist_ok:
                raise FileExistsError(f'Directory already exists: {path}')
        except asyncssh.sftp.SFTPFailure as exc:
            if self._sftp.version < 6:
                if not exist_ok:
                    raise FileExistsError(f'Directory already exists: {path}')
            else:
                raise TransportInternalError(f'Error while creating directory {path}: {exc}')

    async def remove(self, path: str):
        # TODO: check if asyncssh does return SFTPFileIsADirectory in this case
        # if that's the case, we can get rid of the isfile check
        # https://github.com/aiidateam/aiida-core/issues/6719
        if await self.isdir(path):
            raise OSError(f'The path {path} is a directory')
        else:
            await self._sftp.remove(path)

    async def rename(self, oldpath: str, newpath: str):
        await self._sftp.rename(oldpath, newpath)

    async def rmdir(self, path: str):
        try:
            await self._sftp.rmdir(path)
        except asyncssh.sftp.SFTPFailure:
            raise OSError(f'Error while removing directory {path}: probably directory is not empty')

    async def rmtree(self, path: str):
        try:
            await self._sftp.rmtree(path, ignore_errors=False)
        except asyncssh.Error as exc:
            raise OSError(f'Error while removing directory tree {path}: {exc}')

    async def path_exists(self, path: str):
        return await self._sftp.exists(path)

    async def symlink(self, source: str, destination: str):
        """Create a single link from source to destination.
        No magic is allowed in source or destination.
        """
        await self._sftp.symlink(source, destination)

    async def glob(self, path: str, ignore_nonexisting: bool = True):
        try:
            return await self._sftp.glob(path)
        except asyncssh.sftp.SFTPNoSuchFile:
            if ignore_nonexisting:
                self.logger.debug(f'Glob pattern {path} did not match any files or directories. Ignoring.')
                return []
            raise OSError(f'Either the remote path {path} does not exist, or a matching file/folder not found.')

    async def chmod(self, path: str, mode: int, follow_symlinks: bool = True):
        await self._sftp.chmod(path, mode, follow_symlinks=follow_symlinks)

    async def chown(self, path: str, uid: int, gid: int):
        await self._sftp.chown(path, uid, gid, follow_symlinks=True)

    async def copy(
        self,
        remotesource: str,
        remotedestination: str,
        dereference: bool,
        recursive: bool,
        preserve: bool,
    ):
        # SFTP.copy() supports remote copy only in very recent version _OpenSSH 9.0 and later.
        # For the older versions, it downloads the file and uploads it again!
        # For performance reasons, we should check if the remote copy is supported, if so use
        # self._sftp.mcopy() & self._sftp.copy() otherwise send a `cp` command to the remote machine.
        # See here: https://github.com/ronf/asyncssh/issues/724
        if self._sftp.supports_remote_copy:
            try:
                if has_magic(remotesource):
                    await self._sftp.mcopy(
                        remotesource,
                        remotedestination,
                        preserve=preserve,
                        recurse=recursive,
                        follow_symlinks=dereference,
                        remote_only=True,
                    )
                else:
                    if not await self.path_exists(remotesource):
                        raise FileNotFoundError(f'The remote path {remotesource} does not exist')
                    await self._sftp.copy(
                        remotesource,
                        remotedestination,
                        preserve=preserve,
                        recurse=recursive,
                        follow_symlinks=dereference,
                        remote_only=True,
                    )
            except asyncssh.sftp.SFTPNoSuchFile as exc:
                # note: one could just create directories, but aiida engine expects this behavior
                # see `execmanager.py`::_copy_remote_files for more details
                raise FileNotFoundError(
                    f'The remote path {remotedestination} is not reachable,'
                    f'perhaps the parent folder does not exists: {exc}'
                )
            except asyncssh.sftp.SFTPFailure as exc:
                raise OSError(f'Error while copying {remotesource} to {remotedestination}: {exc}')
        else:
            self.logger.debug(
                'The SSH server does not support SFTP remote copy (SFTP >= v9.0), '
                'falling back on the `cp` command to copy the file/folder.'
            )
            # I copy pasted the whole logic below from SshTransport class:

            async def _exec_cp(cp_exe: str, cp_flags: str, src: str, dst: str):
                """Execute the ``cp`` command on the remote machine."""
                # to simplify writing the above copy function
                command = f'{cp_exe} {cp_flags} {escape_for_bash(src)} {escape_for_bash(dst)}'

                retval, stdout, stderr = await self.run(command)

                if retval == 0:
                    if stderr.strip():
                        self.logger.warning(f'There was nonempty stderr in the cp command: {stderr}')
                else:
                    self.logger.error(
                        "Problem executing cp. Exit code: {}, stdout: '{}', " "stderr: '{}', command: '{}'".format(
                            retval, stdout, stderr, command
                        )
                    )
                    if 'No such file or directory' in str(stderr):
                        raise FileNotFoundError(f'Error while executing cp: {stderr}')

                    raise OSError(
                        'Error while executing cp. Exit code: {}, '
                        "stdout: '{}', stderr: '{}', "
                        "command: '{}'".format(retval, stdout, stderr, command)
                    )

            cp_exe = 'cp'
            cp_flags = '-f'

            if recursive:
                cp_flags += ' -r'

            if preserve:
                cp_flags += ' -p'

            if dereference:
                # use -L; --dereference is not supported on mac
                cp_flags += ' -L'

            if has_magic(remotesource):
                to_copy_list = await self.glob(remotesource)

                if len(to_copy_list) > 1:
                    if not await self.path_exists(remotedestination) or await self.isfile(remotedestination):
                        raise OSError("Can't copy more than one file in the same destination file")

                for file in to_copy_list:
                    await _exec_cp(cp_exe, cp_flags, file, remotedestination)

            else:
                await _exec_cp(cp_exe, cp_flags, remotesource, remotedestination)


class _OpenSSH(_AsynchronousSSHBackend):
    """A backend class that executes _OpenSSH commands directly in a shell.
    This class is not part of the public api and should not be used directly.
    Note: This class is not part of the public API and should not be used directly.
    """

    def __init__(self, machine: str, logger: logging.LoggerAdapter, bash_command: str):
        super().__init__(machine, logger, bash_command)

    async def openssh_execute(self, commands, stdin: Optional[str] = None, timeout: Optional[float] = None):
        """
        Execute a command using the _OpenSSH command line client.
        :param commands: The list of commands to execute
        :param timeout: The timeout in seconds
        :return: The return code, stdout, and stderr
        """
        process = await asyncio.create_subprocess_exec(
            *commands, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        if stdin:
            process.stdin.write(stdin.encode())  # type: ignore[union-attr]
            await process.stdin.drain()  # type: ignore[union-attr]
            process.stdin.close()  # type: ignore[union-attr]

        if timeout is None:
            stdout, stderr = await process.communicate()
        else:
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return -1, '', 'Timeout exceeded'

        return process.returncode, stdout.decode(), stderr.decode()

    def ssh_command_generator(self, raw_command: str):
        """
        Generate the command to execute
        :param raw_command: The command to execute
        """
        # if "'" in raw_command:
        treated_raw_command = f'"{raw_command}"'
        # else:
        #     treated_raw_command = f"\'{raw_command}\'"
        return ['ssh', self.machine, self.bash_command + treated_raw_command]

    async def mkdir(self, path: str, exist_ok: bool = False, parents: bool = False):
        if parents and not exist_ok:
            if await self.path_exists(path):
                raise FileExistsError(f'Directory already exists: {path}')

        commands = self.ssh_command_generator(f"mkdir {'-p' if parents else ''} {path}")
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            if 'File exists' in stderr:
                if not exist_ok:
                    raise FileExistsError(f'Directory already exists: {path}')
            else:
                raise OSError(f'Failed to create directory: {path}')

    async def chown(self, path: str, uid: int, gid: int) -> None:
        commands = self.ssh_command_generator(f'chown {uid}:{gid} {path}')

        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f'Failed to change ownership: {path}')

    async def chmod(self, path: str, mode: int, follow_symlinks: bool = True):
        # chmod works with octal numbers, so we have to convert the mode to octal
        mode = oct(mode)[2:]  # type: ignore[assignment]
        commands = self.ssh_command_generator(f"chmod {'-h' if not follow_symlinks else ''} {mode} {path}")
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f'Failed to change permissions: {path}')

    async def glob(self, path: str, ignore_nonexisting: bool = True):
        commands = self.ssh_command_generator(f'find {path} -maxdepth 0')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            if ignore_nonexisting:
                self.logger.debug(f'Glob pattern {path} did not match any files or directories. Ignoring.')
                return []
            raise OSError(f'Either the path {path} does not exist, or a matching file/folder not found.')

        return list(stdout.strip().split())

    async def symlink(self, source: str, destination: str):
        """Create a single link from source to destination.
        No magic is allowed in source or destination.
        """

        commands = self.ssh_command_generator(f'ln -s {source} {destination}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f'Failed to create symlink: {source} -> {destination}')

    async def path_exists(self, path: str):
        commands = self.ssh_command_generator(f'test -e {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if stderr:
            # this should not happen, but just in case for debugging
            self.logger.debug(f'Unexpected stderr: {stderr}')
            raise OSError(stderr)
        return returncode == 0

    async def rmtree(self, path: str):
        commands = self.ssh_command_generator(f'rm -rf {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f'Failed to remove path: {path}')

    async def rmdir(self, path: str):
        commands = self.ssh_command_generator(f'rmdir {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError('Failed to remove directory')

    async def rename(self, oldpath: str, newpath: str):
        commands = self.ssh_command_generator(f'mv {oldpath} {newpath}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f'Failed to rename path: {oldpath} -> {newpath}')

    async def remove(self, path: str):
        commands = self.ssh_command_generator(f'rm {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f'Failed to remove path: {path}')

    async def listdir(self, path: str):
        commands = self.ssh_command_generator(f'ls {path}')
        # '-d' is used prevents recursive listing of directories.
        # This is useful when 'path' includes glob patterns.
        returncode, stdout, stderr = await self.openssh_execute(commands)
        if returncode != 0:
            raise FileNotFoundError
        return list(stdout.strip().split())

    async def isdir(self, path: str):
        commands = self.ssh_command_generator(f'test -d {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)
        return returncode == 0

    async def isfile(self, path: str):
        commands = self.ssh_command_generator(f'test -f {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)
        return returncode == 0

    async def lstat(self, path: str):
        # order of stat matters
        commands = self.ssh_command_generator(f"stat -c '%s %u %g %a %X %Y' {path}")
        returncode, stdout, stderr = await self.openssh_execute(commands)

        stdout = stdout.strip()
        if not stdout:
            raise FileNotFoundError

        # order matters
        return Stat(*stdout.split())

    async def run(self, command: str, stdin: Optional[str] = None, timeout: Optional[float] = None):
        # Not sure if sending the entire command as a single string is a good idea
        # This is a hack to escape the $ character in the stdin
        command = command.replace('$', r'\$')
        command = command.replace('\\$', r'\$')
        commands = self.ssh_command_generator(command)

        returncode, stdout, stderr = await self.openssh_execute(commands, stdin, timeout)
        return returncode, stdout, stderr

    async def get(self, remotepath: str, localpath: str, dereference: bool, preserve: bool, recursive: bool):
        options = []
        if preserve:
            options.append('-p')
        if dereference:
            # options.append("-L")
            # symlinks has to resolved manually
            pass
        if recursive:
            options.append('-r')

        returncode, stdout, stderr = await self.openssh_execute(
            ['scp', *options, f'{self.machine}:{remotepath}', localpath]
        )
        if returncode != 0:
            raise OSError({stderr})

    async def put(self, localpath: str, remotepath: str, dereference: bool, preserve: bool, recursive: bool):
        options = []
        if preserve:
            options.append('-p')
        if dereference:
            # options.append("-L")
            # symlinks has to resolved manually
            pass
        if recursive:
            options.append('-r')

        returncode, stdout, stderr = await self.openssh_execute(
            ['scp', *options, localpath, f'{self.machine}:{remotepath}']
        )
        if returncode != 0:
            raise OSError({stderr})

    async def open(self):
        pass

    async def close(self):
        pass

    async def copy(
        self,
        remotesource: str,
        remotedestination: str,
        dereference: bool,
        recursive: bool,
        preserve: bool,
    ):
        options = []
        if preserve:
            options.append('-p')
        if dereference:
            # options.append("-L")
            # symlinks has to resolved manually
            pass
        if recursive:
            options.append('-r')

        if has_magic(remotesource):
            to_copy_list = await self.glob(remotesource)

            if len(to_copy_list) > 1:
                if not await self.path_exists(remotedestination) or await self.isfile(remotedestination):
                    raise OSError("Can't copy more than one file in the same destination file")

        elif not await self.path_exists(remotesource):
            raise FileNotFoundError(f'The remote path {remotesource} does not exist')

        parent_directory = posixpath.dirname(remotedestination)
        if not await self.path_exists(parent_directory):
            # note: one could just create directories, but aiida engine expects this behavior
            # see `execmanager.py`::_copy_remote_files for more details
            raise FileNotFoundError(
                f'The remote path {remotedestination} is not reachable,'
                f'perhaps the parent folder does not exist: {parent_directory}'
            )

        returncode, stdout, stderr = await self.openssh_execute(
            ['scp', *options, f'{self.machine}:{remotesource}', f'{self.machine}:{remotedestination}']
        )
        if returncode != 0:
            raise OSError(f'Failed to copy from {remotesource} to {remotedestination} : {stderr}')


class Stat:
    def __init__(self, size, uid, gid, permissions, atime, mtime):
        self.size = int(size)
        self.uid = int(uid)
        self.gid = int(gid)
        # convert the octal permissions to decimal
        self.permissions = int(permissions, 8)
        self.atime = int(atime)
        self.mtime = int(mtime)
