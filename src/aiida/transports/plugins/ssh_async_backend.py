###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""""""
from stat import S_ISDIR, S_ISREG
import asyncio


from aiida.cmdline.params import options
from aiida.cmdline.params.types.path import AbsolutePathOrEmptyParamType
from aiida.common.escaping import escape_for_bash
from aiida.common.warnings import warn_deprecation

from aiida.transports.transport import (
    TransportInternalError,
    TransportPath,
    has_magic,
)
import asyncssh
from asyncssh import SFTPFileAlreadyExists
import logging

__all__ = ('OpenSSHwrapper', 'AsyncSSHwrapper')


class AsyncSSHwrapper:
    """A backend class that uses asyncssh to execute commands and transfer files.
    This calss is not part of the public api and should not be used directly.
    """

    def __init__(self, machine: str, logger: logging.LoggerAdapter, bash_command : str):
        self.bash_command = bash_command + '-c '
        self.machine = machine
        self.logger = logger

    async def open(self):
        self._conn = await asyncssh.connect(self.machine)
        self._sftp = await self._conn.start_sftp_client()

    async def close(self):
        self._conn.close()
        await self._conn.wait_closed()

    async def get(self, remotepath: str, localpath: str, dereference: bool,  preserve: bool, recursive: bool):
        return await self._sftp.get(
            remotepaths=remotepath,
            localpath=localpath,
            preserve=preserve,
            recurse=recursive,
            follow_symlinks=dereference,
        )

    async def put(self, localpath: str, remotepath: str, dereference: bool,  preserve: bool, recursive: bool):
        return await self._sftp.put(
            localpaths=localpath,
            remotepath=remotepath,
            preserve=preserve,
            recurse=recursive,
            follow_symlinks=dereference,
        )

    async def run(self, command: str, stdin: str = None, timeout: int = None):
        return await self._conn.run(
            self.bash_command + escape_for_bash(command),
            input=stdin,
            check=False,
            timeout=timeout,
        )

    async def lstat(self, path: str):
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
        except SFTPFileAlreadyExists as exc:
            # SFTPFileAlreadyExists is only supported in asyncssh version 6.0.0 and later
            if not exist_ok:
                raise FileExistsError(f"Directory already exists: {path}")
        except asyncssh.sftp.SFTPFailure as exc:
            if self._sftp.version < 6:
                if not exist_ok:
                    raise FileExistsError(f"Directory already exists: {path}")
            else:
                raise TransportInternalError(f'Error while creating directory {path}: {exc}')

    async def makedirs(self, path: str, exist_ok: bool = False):
        await self.mkdir(path, exist_ok=exist_ok, parents=True)

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

    async def glob(self, path: str):
        return await self._sftp.glob(path)

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

        # SFTP.copy() supports remote copy only in very recent version OpenSSH 9.0 and later.
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
                        raise OSError(f'The remote path {remotesource} does not exist')
                    await self._sftp.copy(
                        remotesource,
                        remotedestination,
                        preserve=preserve,
                        recurse=recursive,
                        follow_symlinks=dereference,
                        remote_only=True,
                    )
            except asyncssh.sftp.SFTPFailure as exc:
                raise OSError(f'Error while copying {remotesource} to {remotedestination}: {exc}')
        else:
            self.logger.warning('The remote copy is not supported, using the `cp` command to copy the file/folder')
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
                    if not await self.path_exists(remotedestination) or await self.isfile(
                        remotedestination
                    ):
                        raise OSError("Can't copy more than one file in the same destination file")

                for file in to_copy_list:
                    await _exec_cp(cp_exe, cp_flags, file, remotedestination)

            else:
                await _exec_cp(cp_exe, cp_flags, remotesource, remotedestination)

class OpenSSHwrapper:
    """A backend class that executes OpenSSH commands directly in a shell.
    This calss is not part of the public api and should not be used directly.
    """


    def __init__(self, machine: str, logger: logging.LoggerAdapter, bash_command : str):
        self.bash_command = bash_command + '-c '
        self.machine = machine
        self.logger = logger


    async def openssh_execute(self, commands, timeout=None):
        """
        Execute a command using the OpenSSH command line client.
        :param commands: The list of commands to execute
        :param timeout: The timeout in seconds
        :return: The return code, stdout, and stderr
        """
        process = await asyncio.create_subprocess_exec(
            *commands,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        if timeout is None:
            stdout, stderr = await process.communicate()
        else:
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return -1, "", "Timeout exceeded"

        return process.returncode, stdout.decode(), stderr.decode()


    def ssh_command_generator(self, raw_command: str):
        """
        Generate the command to execute
        :param raw_command: The command to execute
        """
        return ['ssh', self.machine, self.bash_command +f"\'{raw_command}\'"]

    async def mkdir(self, path: str, exist_ok: bool = False, parents: bool = False):
        if (parents == True and exist_ok == False):
            if await self.path_exists(path):
                raise FileExistsError(f"Directory already exists: {path}")
            
        commands = self.ssh_command_generator(f'mkdir {'-p' if parents else ''} {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            if 'File exists' in stderr:
                if not exist_ok:
                    raise FileExistsError(f"Directory already exists: {path}")
            else:
                raise OSError(f"Failed to create directory: {path}")

    async def makedirs(self, path: str, exist_ok: bool = False):
        await self.mkdir(path, exist_ok=exist_ok, parents=True)



    async def chown(self, path: str, uid: int, gid: int):
        commands = self.ssh_command_generator(f"chown {uid}:{gid} {path}")

        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to change ownership: {path}")

    async def chmod(self, path: str, mode: int, follow_symlinks: bool = True):
        commands = self.command_generator(f"chmod {'-h' if not follow_symlinks else ''} {mode} {path}")
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to change permissions: {path}")

    async def glob(self, path: str):
        return await self.listdir(path)

    async def symlink(self, source: str, destination: str):
        """Create a single link from source to destination.
        No magic is allowed in source or destination.
        """

        commands = self.ssh_command_generator(f"ln -s {source} {destination}")
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to create symlink: {source} -> {destination}")

    async def path_exists(self, path: str):
        commands = self.ssh_command_generator(f'test -e {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if stderr:
            # this should not happen, but just in case for debugging
            raise OSError(stderr)
        return returncode == 0

    async def rmtree(self, path: str):
        commands = self.ssh_command_generator(f'rm -rf {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to remove path: {path}")

    async def rmdir(self, path: str):
        commands = self.ssh_command_generator(f'rmdir {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to remove directory")

    async def rename(self, oldpath: str, newpath: str):
        commands = self.ssh_command_generator(f'mv {oldpath} {newpath}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to rename path: {oldpath} -> {newpath}")

    async def remove(self, path: str):
        commands = self.ssh_command_generator(f'rm {path}')
        returncode, stdout, stderr = await self.openssh_execute(commands)

        if returncode != 0:
            raise OSError(f"Failed to remove path: {path}")


    async def listdir(self, path: str):
        commands = self.ssh_command_generator(f'ls {path}')
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

    async def run(self, command: str, stdin: str = None, timeout: int = None):
        # I ignore un-used stdin, for now
        # command = f"ssh {self.machine} " + self.bash_command + escape_for_bash(command)
        commands = self.ssh_command_generator(command)
        returncode, stdout, stderr = await self.openssh_execute(commands, timeout)

        return returncode, stdout, stderr

    async def get(self, remotepath: str, localpath: str, dereference: bool,  preserve: bool, recursive: bool):
        options = []
        if preserve:
            options.append("-p")
        if dereference:
            # options.append("-L")
            # syminks has to resolved manually
            pass
        if recursive:
            options.append("-r")

        returncode, stdout, stderr = await self.openssh_execute(['scp', *options, f"{self.machine}:{remotepath}", localpath])
        if returncode != 0:
            raise OSError

    async def put(self, localpath: str, remotepath: str, dereference: bool,  preserve: bool, recursive: bool):
        options = []
        if preserve:
            options.append("-p")
        if dereference:
            # options.append("-L")
            # syminks has to resolved manually
            pass
        if recursive:
            options.append("-r")

        returncode, stdout, stderr = await self.openssh_execute(['scp', *options, localpath, f"{self.machine}:{remotepath}"])
        if returncode != 0:
            raise OSError

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
            options.append("-p")
        if dereference:
            # options.append("-L")
            # syminks has to resolved manually
            pass
        if recursive:
            options.append("-r")

        stdout, stderr, returncode = await self.openssh_execute(['scp', *options, f"{self.machine}:{remotesource}", f"{self.machine}:{remotedestination}"])
        if returncode != 0:
            raise OSError(f"Failed to copy from {remotesource} to {remotedestination}")


class Stat:
    def __init__(self, size, uid, gid, permissions, atime, mtime):
        self.st_size = size
        self.st_uid = uid
        self.st_gid = gid
        self.st_mode = permissions
        self.st_atime = atime
        self.st_mtime = mtime
