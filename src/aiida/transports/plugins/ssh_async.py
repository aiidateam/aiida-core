###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for transport over SSH asynchronously."""

## TODO: put & get methods could be simplified with the asyncssh.sftp.mget() & put() method or sftp.glob()
## https://github.com/aiidateam/aiida-core/issues/6719
import asyncio
import glob
import os
from pathlib import Path, PurePath
from typing import Optional, Union

import asyncssh
import click
from asyncssh import SFTPFileAlreadyExists

from aiida.common.escaping import escape_for_bash
from aiida.common.exceptions import InvalidOperation
from aiida.transports.transport import (
    AsyncTransport,
    Transport,
    TransportInternalError,
    TransportPath,
    validate_positive_number,
)

__all__ = ('AsyncSshTransport',)


def validate_script(ctx, param, value: str):
    if value == 'None':
        return value
    if not os.path.isabs(value):
        raise click.BadParameter(f'{value} is not an absolute path')
    if not os.path.isfile(value):
        raise click.BadParameter(f'The script file: {value} does not exist')
    if not os.access(value, os.X_OK):
        raise click.BadParameter(f'The script {value} is not executable')
    return value


def validate_machine(ctx, param, value: str):
    async def attempt_connection():
        try:
            await asyncssh.connect(value)
        except Exception:
            return False
        return True

    if not asyncio.run(attempt_connection()):
        raise click.BadParameter("Couldn't connect! " 'Please make sure `ssh {value}` would work without password')
    else:
        click.echo(f'`ssh {value}` successful!')

    return value


class AsyncSshTransport(AsyncTransport):
    """Transport plugin via SSH, asynchronously."""

    _DEFAULT_max_io_allowed = 8

    # note, I intentionally wanted to keep connection parameters as simple as possible.
    _valid_auth_options = [
        (
            # the underscore is added to avoid conflict with the machine property
            # which is passed to __init__ as parameter `machine=computer.hostname`
            'machine_or_host',
            {
                'type': str,
                'prompt': 'Machine(or host) name as in `ssh <your-host-name>` command.'
                ' (It should be a password-less setup)',
                'help': 'Password-less host-setup to connect, as in command `ssh <your-host-name>`. '
                "You'll need to have a `Host <your-host-name>` entry defined in your `~/.ssh/config` file.",
                'non_interactive_default': True,
                'callback': validate_machine,
            },
        ),
        (
            'max_io_allowed',
            {
                'type': int,
                'default': _DEFAULT_max_io_allowed,
                'prompt': 'Maximum number of concurrent I/O operations.',
                'help': 'Depends on various factors, such as your network bandwidth, the server load, etc.'
                ' (An experimental number)',
                'non_interactive_default': True,
                'callback': validate_positive_number,
            },
        ),
        (
            'script_before',
            {
                'type': str,
                'default': 'None',
                'prompt': 'Local script to run *before* opening connection (path)',
                'help': ' (optional) Specify a script to run *before* opening SSH connection. '
                'The script should be executable',
                'non_interactive_default': True,
                'callback': validate_script,
            },
        ),
    ]

    @classmethod
    def _get_machine_suggestion_string(cls, computer):
        """Return a suggestion for the parameter machine."""
        # Originally set as 'Hostname' during `verdi computer setup`
        # and is passed as `machine=computer.hostname` in the codebase
        # unfortunately, name of hostname and machine are used interchangeably in the aiida-core codebase
        # TODO: an issue is open: https://github.com/aiidateam/aiida-core/issues/6726
        return computer.hostname

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # the machine is passed as `machine=computer.hostname` in the codebase
        # 'machine' is immutable.
        # 'machine_or_host' is mutable, so it can be changed via command:
        # 'verdi computer configure core.ssh_async <LABEL>'.
        # by default, 'machine_or_host' is set to 'machine' in the __init__ method, if not provided.
        # NOTE: to guarantee a connection,
        # a computer with core.ssh_async transport plugin should be configured before any instantiation.
        self.machine = kwargs.pop('machine_or_host', kwargs.pop('machine'))
        self._max_io_allowed = kwargs.pop('max_io_allowed', self._DEFAULT_max_io_allowed)
        self.script_before = kwargs.pop('script_before', 'None')

        self._concurrent_io = 0

    @property
    def max_io_allowed(self):
        return self._max_io_allowed

    async def _lock(self, sleep_time=0.5):
        while self._concurrent_io >= self.max_io_allowed:
            await asyncio.sleep(sleep_time)
        self._concurrent_io += 1

    async def _unlock(self):
        self._concurrent_io -= 1

    async def open_async(self):
        """Open the transport.
        This plugin supports running scripts before and during the connection.
        The scripts are run locally, not on the remote machine.

        :raises InvalidOperation: if the transport is already open
        """
        if self._is_open:
            raise InvalidOperation('Cannot open the transport twice')

        if self.script_before != 'None':
            os.system(f'{self.script_before}')

        self._conn = await asyncssh.connect(self.machine)
        self._sftp = await self._conn.start_sftp_client()

        self._is_open = True

        return self

    async def close_async(self):
        """Close the transport.

        :raises InvalidOperation: if the transport is already closed
        """
        if not self._is_open:
            raise InvalidOperation('Cannot close the transport: it is already closed')

        self._conn.close()
        await self._conn.wait_closed()
        self._is_open = False

    def __str__(self):
        return f"{'OPEN' if self._is_open else 'CLOSED'} [AsyncSshTransport]"

    async def get_async(
        self,
        remotepath: TransportPath,
        localpath: TransportPath,
        dereference=True,
        overwrite=True,
        ignore_nonexisting=False,
        preserve=False,
        *args,
        **kwargs,
    ):
        """Get a file or folder from remote to local.
        Redirects to getfile or gettree.

        :param remotepath: an absolute remote path
        :param localpath: an absolute local path
        :param dereference: follow symbolic links.
            Default = True
        :param overwrite: if True overwrites files and folders.
            Default = False
        :param ignore_nonexisting: if True, does not raise an error if the remotepath does not exist
            Default = False
        :param preserve: preserve file attributes
            Default = False

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type overwrite: bool
        :type ignore_nonexisting: bool
        :type preserve: bool

        :raise ValueError: if local path is invalid
        :raise OSError: if the remotepath is not found
        """
        remotepath = str(remotepath)
        localpath = str(localpath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if self.has_magic(remotepath):
            if self.has_magic(localpath):
                raise ValueError('Pathname patterns are not allowed in the destination')
            # use the self glob to analyze the path remotely
            to_copy_list = await self.glob_async(remotepath)

            rename_local = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if os.path.isfile(localpath):
                    raise OSError('Remote destination is not a directory')
                # I can't scp more than one file in a non existing directory
                elif not os.path.exists(localpath):  # this should hold only for files
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_local = True

            for file in to_copy_list:
                if await self.isfile_async(file):
                    if rename_local:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        remote = os.path.join(localpath, os.path.split(file)[1])
                        await self.getfile_async(file, remote, dereference, overwrite, preserve)
                    else:  # one file to copy on one file
                        await self.getfile_async(file, localpath, dereference, overwrite, preserve)
                else:
                    await self.gettree_async(file, localpath, dereference, overwrite, preserve)

        elif await self.isdir_async(remotepath):
            await self.gettree_async(remotepath, localpath, dereference, overwrite, preserve)
        elif await self.isfile_async(remotepath):
            if os.path.isdir(localpath):
                remote = os.path.join(localpath, os.path.split(remotepath)[1])
                await self.getfile_async(remotepath, remote, dereference, overwrite, preserve)
            else:
                await self.getfile_async(remotepath, localpath, dereference, overwrite, preserve)
        elif ignore_nonexisting:
            pass
        else:
            raise OSError(f'The remote path {remotepath} does not exist')

    async def getfile_async(
        self,
        remotepath: TransportPath,
        localpath: TransportPath,
        dereference=True,
        overwrite=True,
        preserve=False,
        *args,
        **kwargs,
    ):
        """Get a file from remote to local.

        :param remotepath: an absolute remote path
        :param localpath: an absolute local path
        :param overwrite: if True overwrites files and folders.
            Default = False
        :param dereference: follow symbolic links.
            Default = True
        :param preserve: preserve file attributes
            Default = False

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type overwrite: bool
        :type preserve: bool

        :raise ValueError: if local path is invalid
        :raise OSError: if unintentionally overwriting
        """
        remotepath = str(remotepath)
        localpath = str(localpath)

        if not os.path.isabs(localpath):
            raise ValueError('localpath must be an absolute path')

        if os.path.isfile(localpath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        try:
            await self._lock()
            await self._sftp.get(
                remotepaths=remotepath,
                localpath=localpath,
                preserve=preserve,
                recurse=False,
                follow_symlinks=dereference,
            )
            await self._unlock()
        except (OSError, asyncssh.Error) as exc:
            raise OSError(f'Error while uploading file {localpath}: {exc}')

    async def gettree_async(
        self,
        remotepath: TransportPath,
        localpath: TransportPath,
        dereference=True,
        overwrite=True,
        preserve=False,
        *args,
        **kwargs,
    ):
        """Get a folder recursively from remote to local.

        :param remotepath: an absolute remote path
        :param localpath: an absolute local path
        :param dereference: follow symbolic links.
            Default = True
        :param  overwrite: if True overwrites files and folders.
            Default = True
        :param preserve: preserve file attributes
            Default = False

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type overwrite: bool
        :type preserve: bool

        :raise ValueError: if local path is invalid
        :raise OSError: if the remotepath is not found
        :raise OSError: if unintentionally overwriting
        """
        remotepath = str(remotepath)
        localpath = str(localpath)

        if not remotepath:
            raise OSError('Remotepath must be a non empty string')
        if not localpath:
            raise ValueError('Localpaths must be a non empty string')

        if not os.path.isabs(localpath):
            raise ValueError('Localpaths must be an absolute path')

        if not await self.isdir_async(remotepath):
            raise OSError(f'Input remotepath is not a folder: {localpath}')

        if os.path.exists(localpath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if os.path.isfile(localpath):
            raise OSError('Cannot copy a directory into a file')

        if not os.path.isdir(localpath):  # in this case copy things in the remotepath directly
            os.makedirs(localpath, exist_ok=True)  # and make a directory at its place
        else:  # localpath exists already: copy the folder inside of it!
            localpath = os.path.join(localpath, os.path.split(remotepath)[1])
            os.makedirs(localpath, exist_ok=overwrite)  # create a nested folder

        content_list = await self.listdir_async(remotepath)
        for content_ in content_list:
            try:
                await self._lock()
                await self._sftp.get(
                    remotepaths=PurePath(remotepath) / content_,
                    localpath=localpath,
                    preserve=preserve,
                    recurse=True,
                    follow_symlinks=dereference,
                )
                await self._unlock()
            except (OSError, asyncssh.Error) as exc:
                raise OSError(f'Error while uploading file {localpath}: {exc}')

    async def put_async(
        self,
        localpath: TransportPath,
        remotepath: TransportPath,
        dereference=True,
        overwrite=True,
        ignore_nonexisting=False,
        preserve=False,
        *args,
        **kwargs,
    ):
        """Put a file or a folder from local to remote.
        Redirects to putfile or puttree.

        :param remotepath: an absolute remote path
        :param localpath: an absolute local path
        :param dereference: follow symbolic links
            Default = True
        :param  overwrite: if True overwrites files and folders
            Default = False
        :param ignore_nonexisting: if True, does not raise an error if the localpath does not exist
            Default = False
        :param preserve: preserve file attributes
            Default = False

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type overwrite: bool
        :type ignore_nonexisting: bool
        :type preserve: bool

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist
        """
        localpath = str(localpath)
        remotepath = str(remotepath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if self.has_magic(localpath):
            if self.has_magic(remotepath):
                raise ValueError('Pathname patterns are not allowed in the destination')

            # use the imported glob to analyze the path locally
            to_copy_list = glob.glob(localpath)

            rename_remote = False
            if len(to_copy_list) > 1:
                # I can't scp more than one file on a single file
                if await self.isfile_async(remotepath):
                    raise OSError('Remote destination is not a directory')
                # I can't scp more than one file in a non existing directory
                elif not await self.path_exists_async(remotepath):
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_remote = True

            for file in to_copy_list:
                if os.path.isfile(file):
                    if rename_remote:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        remotefile = os.path.join(remotepath, os.path.split(file)[1])
                        await self.putfile_async(file, remotefile, dereference, overwrite, preserve)

                    elif await self.isdir_async(remotepath):  # one file to copy in '.'
                        remotefile = os.path.join(remotepath, os.path.split(file)[1])
                        await self.putfile_async(file, remotefile, dereference, overwrite, preserve)
                    else:  # one file to copy on one file
                        await self.putfile_async(file, remotepath, dereference, overwrite, preserve)
                else:
                    await self.puttree_async(file, remotepath, dereference, overwrite, preserve)

        elif os.path.isdir(localpath):
            await self.puttree_async(localpath, remotepath, dereference, overwrite, preserve)
        elif os.path.isfile(localpath):
            if await self.isdir_async(remotepath):
                remote = os.path.join(remotepath, os.path.split(localpath)[1])
                await self.putfile_async(localpath, remote, dereference, overwrite, preserve)
            else:
                await self.putfile_async(localpath, remotepath, dereference, overwrite, preserve)
        elif not ignore_nonexisting:
            raise OSError(f'The local path {localpath} does not exist')

    async def putfile_async(
        self,
        localpath: TransportPath,
        remotepath: TransportPath,
        dereference=True,
        overwrite=True,
        preserve=False,
        *args,
        **kwargs,
    ):
        """Put a file from local to remote.

        :param remotepath: an absolute remote path
        :param localpath: an absolute local path
        :param overwrite: if True overwrites files and folders
            Default = True
        :param preserve: preserve file attributes
            Default = False

        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type overwrite: bool
        :type preserve: bool

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist,
                    or unintentionally overwriting
        """
        localpath = str(localpath)
        remotepath = str(remotepath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if await self.isfile_async(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        try:
            await self._lock()
            await self._sftp.put(
                localpaths=localpath,
                remotepath=remotepath,
                preserve=preserve,
                recurse=False,
                follow_symlinks=dereference,
            )
            await self._unlock()
        except (OSError, asyncssh.Error) as exc:
            raise OSError(f'Error while uploading file {localpath}: {exc}')

    async def puttree_async(
        self,
        localpath: TransportPath,
        remotepath: TransportPath,
        dereference=True,
        overwrite=True,
        preserve=False,
        *args,
        **kwargs,
    ):
        """Put a folder recursively from local to remote.

        :param localpath: an absolute local path
        :param remotepath: an absolute remote path
        :param dereference: follow symbolic links
            Default = True
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True
        :param preserve: preserve file attributes
            Default = False

        :type localpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotepath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type overwrite: bool
        :type preserve: bool

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist, or trying to overwrite
        :raise OSError: if remotepath is invalid
        """
        localpath = str(localpath)
        remotepath = str(remotepath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if not os.path.exists(localpath):
            raise OSError('The localpath does not exists')

        if not os.path.isdir(localpath):
            raise ValueError(f'Input localpath is not a folder: {localpath}')

        if not remotepath:
            raise OSError('remotepath must be a non empty string')

        if await self.path_exists_async(remotepath) and not overwrite:
            raise OSError("Can't overwrite existing files")
        if await self.isfile_async(remotepath):
            raise OSError('Cannot copy a directory into a file')

        if not await self.isdir_async(remotepath):  # in this case copy things in the remotepath directly
            await self.makedirs_async(remotepath)  # and make a directory at its place
        else:  # remotepath exists already: copy the folder inside of it!
            remotepath = os.path.join(remotepath, os.path.split(localpath)[1])
            await self.makedirs_async(remotepath, ignore_existing=overwrite)  # create a nested folder

        # This is written in this way, only because AiiDA expects to put file inside an existing folder
        # Or to put and rename the parent folder at the same time
        content_list = os.listdir(localpath)
        for content_ in content_list:
            try:
                await self._lock()
                await self._sftp.put(
                    localpaths=PurePath(localpath) / content_,
                    remotepath=remotepath,
                    preserve=preserve,
                    recurse=True,
                    follow_symlinks=dereference,
                )
                await self._unlock()
            except (OSError, asyncssh.Error) as exc:
                raise OSError(f'Error while uploading file {PurePath(localpath)/content_}: {exc}')

    async def copy_async(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        dereference: bool = False,
        recursive: bool = True,
        preserve: bool = False,
    ):
        """Copy a file or a folder from remote to remote.

        :param remotesource: abs path to the remote source directory / file
        :param remotedestination: abs path to the remote destination directory / file
        :param dereference: follow symbolic links
        :param recursive: copy recursively
        :param preserve: preserve file attributes
            Default = False

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type recursive: bool
        :type preserve: bool

        :raises: OSError, src does not exist or if the copy execution failed.
        """

        remotesource = str(remotesource)
        remotedestination = str(remotedestination)
        if self.has_magic(remotedestination):
            raise ValueError('Pathname patterns are not allowed in the destination')

        if not remotedestination:
            raise ValueError('remotedestination must be a non empty string')
        if not remotesource:
            raise ValueError('remotesource must be a non empty string')

        # SFTP.copy() supports remote copy only in very recent version OpenSSH 9.0 and later.
        # For the older versions, it downloads the file and uploads it again!
        # For performance reasons, we should check if the remote copy is supported, if so use
        # self._sftp.mcopy() & self._sftp.copy() otherwise send a `cp` command to the remote machine.
        # See here: https://github.com/ronf/asyncssh/issues/724
        if self._sftp.supports_remote_copy:
            try:
                if self.has_magic(remotesource):
                    await self._sftp.mcopy(
                        remotesource,
                        remotedestination,
                        preserve=preserve,
                        recurse=recursive,
                        follow_symlinks=dereference,
                        remote_only=True,
                    )
                else:
                    if not await self.path_exists_async(remotesource):
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

                retval, stdout, stderr = await self.exec_command_wait_async(command)

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

            if self.has_magic(remotesource):
                to_copy_list = await self.glob_async(remotesource)

                if len(to_copy_list) > 1:
                    if not await self.path_exists_async(remotedestination) or await self.isfile_async(
                        remotedestination
                    ):
                        raise OSError("Can't copy more than one file in the same destination file")

                for file in to_copy_list:
                    await _exec_cp(cp_exe, cp_flags, file, remotedestination)

            else:
                await _exec_cp(cp_exe, cp_flags, remotesource, remotedestination)

    async def copyfile_async(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        dereference: bool = False,
        preserve: bool = False,
    ):
        """Copy a file from remote to remote.

        :param remotesource: path to the remote source file
        :param remotedestination: path to the remote destination file
        :param dereference: follow symbolic links
        :param preserve: preserve file attributes
            Default = False

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type preserve: bool

        :raises: OSError, src does not exist or if the copy execution failed.
        """
        return await self.copy_async(remotesource, remotedestination, dereference, recursive=False, preserve=preserve)

    async def copytree_async(
        self,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        dereference: bool = False,
        preserve: bool = False,
    ):
        """Copy a folder from remote to remote.

        :param remotesource: path to the remote source directory
        :param remotedestination: path to the remote destination directory
        :param dereference: follow symbolic links
        :param preserve: preserve file attributes
            Default = False

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type dereference: bool
        :type preserve: bool

        :raises: OSError, src does not exist or if the copy execution failed.
        """
        return await self.copy_async(remotesource, remotedestination, dereference, recursive=True, preserve=preserve)

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
        if not await self.isdir_async(root_dir):
            raise OSError(f'The relative root {root_dir} does not exist, or is not a directory.')

        if await self.isdir_async(remotedestination):
            raise OSError(f'The remote destination {remotedestination} is a directory, should include a filename.')

        if not overwrite and await self.path_exists_async(remotedestination):
            raise OSError(f'The remote destination {remotedestination} already exists.')

        if format not in ['tar', 'tar.gz', 'tar.bz2', 'tar.xz']:
            raise ValueError(f'Unsupported compression format: {format}')

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
            if self.has_magic(source):
                try:
                    copy_list += await self.glob_async(source)
                except asyncssh.sftp.SFTPNoSuchFile:
                    raise OSError(
                        f'Either the remote path {source} does not exist, or a matching file/folder not found.'
                    )
            else:
                if not await self.path_exists_async(source):
                    raise OSError(f'The remote path {source} does not exist')

                copy_list.append(source)

        copy_items = ' '.join([str(Path(item).relative_to(root_dir)) for item in copy_list])
        # note: order of the flags is important
        tar_command = (
            f"tar -c{compression_flag!s}{'h' if dereference else ''}f {remotedestination!s} -C {root_dir!s} "
            + copy_items
        )

        retval, stdout, stderr = await self.exec_command_wait_async(tar_command)

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

    async def extract_async(
        self, remotesource: TransportPath, remotedestination: TransportPath, overwrite: bool = True
    ):
        """Extract a remote archive.

        Does not accept glob patterns, as it doesn't make much sense and we don't have a usecase for it.

        :param remotesource: path to the remote archive to extract
        :param remotedestination: path to the remote destination directory
        :param overwrite: if True, overwrite the file at remotedestination if it already exists
            (we don't have a usecase for False, sofar. The parameter is kept for clarity.)

        :raises OSError: if the remotesource does not exist.
        :raises OSError: if the extraction fails.
        """
        if not overwrite:
            raise NotImplementedError('The overwrite=False is not implemented yet')

        if not await self.path_exists_async(remotesource):
            raise OSError(f'The remote path {remotesource} does not exist')

        await self.makedirs_async(remotedestination, ignore_existing=True)

        tar_command = f'tar -xf {remotesource!s} -C {remotedestination!s} '

        retval, stdout, stderr = await self.exec_command_wait_async(tar_command)

        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the tar command: {stderr}')
        else:
            self.logger.error(
                "Problem executing tar. Exit code: {}, stdout: '{}', " "stderr: '{}', command: '{}'".format(
                    retval, stdout, stderr, tar_command
                )
            )
            raise OSError(f'Error while extracting the tar archive. Exit code: {retval}')

    async def exec_command_wait_async(
        self,
        command: str,
        stdin: Optional[str] = None,
        encoding: str = 'utf-8',
        workdir: Optional[TransportPath] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        """Execute a command on the remote machine and wait for it to finish.

        :param command: the command to execute
        :param stdin: the input to pass to the command
            Default = None
        :param encoding: (IGNORED) this is here just to keep the same signature as the one in `Transport` class
            Default = 'utf-8'
        :param workdir: the working directory where to execute the command
            Default = None
        :param timeout: the timeout in seconds
            Default = None

        :type command: str
        :type stdin: str
        :type encoding: str
        :type workdir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type timeout: float

        :return: a tuple with the return code, the stdout and the stderr of the command
        :rtype: tuple(int, str, str)
        """

        if workdir:
            workdir = str(workdir)
            command = f'cd {workdir} && ( {command} )'

        bash_commmand = self._bash_command_str + '-c '

        result = await self._conn.run(
            bash_commmand + escape_for_bash(command), input=stdin, check=False, timeout=timeout
        )
        # Since the command is str, both stdout and stderr are strings
        return (result.returncode, ''.join(str(result.stdout)), ''.join(str(result.stderr)))

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
        path = str(path)
        from aiida.transports.util import FileAttribute

        asyncssh_attr = await self._sftp.lstat(path)
        aiida_attr = FileAttribute()
        # map the asyncssh class into the aiida one
        for key in aiida_attr._valid_fields:
            if key == 'st_size':
                aiida_attr[key] = asyncssh_attr.size
            elif key == 'st_uid':
                aiida_attr[key] = asyncssh_attr.uid
            elif key == 'st_gid':
                aiida_attr[key] = asyncssh_attr.gid
            elif key == 'st_mode':
                aiida_attr[key] = asyncssh_attr.permissions
            elif key == 'st_atime':
                aiida_attr[key] = asyncssh_attr.atime
            elif key == 'st_mtime':
                aiida_attr[key] = asyncssh_attr.mtime
            else:
                raise NotImplementedError(f'Mapping the {key} attribute is not implemented')
        return aiida_attr

    async def isdir_async(self, path: TransportPath):
        """Return True if the given path is a directory, False otherwise.
        Return False also if the path does not exist.

        :param path: the absolute path to check

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: True if the path is a directory, False otherwise
        """
        # Return False on empty string
        if not path:
            return False

        path = str(path)

        return await self._sftp.isdir(path)

    async def isfile_async(self, path: TransportPath):
        """Return True if the given path is a file, False otherwise.
        Return False also if the path does not exist.

        :param path: the absolute path to check

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: True if the path is a file, False otherwise
        """
        # Return False on empty string
        if not path:
            return False

        path = str(path)

        return await self._sftp.isfile(path)

    async def listdir_async(self, path: TransportPath, pattern=None):
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: an absolute path
        :param pattern: if used, listdir returns a list of files matching
                        filters in Unix style. Unix only.

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a list of strings
        """
        path = str(path)
        if not pattern:
            list_ = list(await self._sftp.listdir(path))
        else:
            patterned_path = pattern if pattern.startswith('/') else Path(path).joinpath(pattern)
            # I put the type ignore here because the asyncssh.sftp.glob()
            # method alwyas returns a sequence of str, if input is str
            list_ = list(await self._sftp.glob(patterned_path))  # type: ignore[arg-type]

        for item in ['..', '.']:
            if item in list_:
                list_.remove(item)

        return list_

    async def listdir_withattributes_async(self, path: TransportPath, pattern: Optional[str] = None):
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: absolute path to list
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
        listdir = await self.listdir_async(path, pattern)
        for file_name in listdir:
            filepath = os.path.join(path, file_name)
            attributes = await self.get_attribute_async(filepath)
            retlist.append({'name': file_name, 'attributes': attributes, 'isdir': await self.isdir_async(filepath)})

        return retlist

    async def makedirs_async(self, path, ignore_existing=False):
        """Super-mkdir; create a leaf directory and all intermediate ones.
        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param path: absolute path to directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                if the leaf directory does already exist

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises: OSError, if directory at path already exists
        """
        path = str(path)

        try:
            await self._sftp.makedirs(path, exist_ok=ignore_existing)
        except SFTPFileAlreadyExists as exc:
            raise OSError(f'Error while creating directory {path}: {exc}, directory already exists')
        except asyncssh.sftp.SFTPFailure as exc:
            if (self._sftp.version < 6) and not ignore_existing:
                raise OSError(f'Error while creating directory {path}: {exc}, probably it already exists')
            else:
                raise TransportInternalError(f'Error while creating directory {path}: {exc}')

    async def mkdir_async(self, path: TransportPath, ignore_existing=False):
        """Create a directory.

        :param path: absolute path to directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                if the leaf directory does already exist

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises: OSError, if directory at path already exists
        """
        path = str(path)

        try:
            await self._sftp.mkdir(path)
        except SFTPFileAlreadyExists as exc:
            # note: mkdir() in asyncssh does not support the exist_ok parameter
            if ignore_existing:
                return
            raise OSError(f'Error while creating directory {path}: {exc}, directory already exists')
        except asyncssh.sftp.SFTPFailure as exc:
            if self._sftp.version < 6:
                if ignore_existing:
                    return
                else:
                    raise OSError(f'Error while creating directory {path}: {exc}, probably it already exists')
            else:
                raise TransportInternalError(f'Error while creating directory {path}: {exc}')

    async def normalize_async(self, path: TransportPath):
        raise NotImplementedError('Not implemented, waiting for a use case.')

    async def remove_async(self, path: TransportPath):
        """Remove the file at the given path. This only works on files;
        for removing folders (directories), use rmdir.

        :param path: path to file to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raise OSError: if the path is a directory
        """
        path = str(path)
        # TODO: check if asyncssh does return SFTPFileIsADirectory in this case
        # if that's the case, we can get rid of the isfile check
        # https://github.com/aiidateam/aiida-core/issues/6719
        if await self.isdir_async(path):
            raise OSError(f'The path {path} is a directory')
        else:
            await self._sftp.remove(path)

    async def rename_async(self, oldpath: TransportPath, newpath: TransportPath):
        """
        Rename a file or folder from oldpath to newpath.

        :param oldpath: existing name of the file or folder
        :param newpath: new name for the file or folder

        :type oldpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type newpath:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises OSError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """
        oldpath = str(oldpath)
        newpath = str(newpath)
        if not oldpath or not newpath:
            raise ValueError('oldpath and newpath must be non-empty strings')

        if await self._sftp.exists(newpath):
            raise OSError(f'Cannot rename {oldpath} to {newpath}: destination exists')

        await self._sftp.rename(oldpath, newpath)

    async def rmdir_async(self, path: TransportPath):
        """Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param str path: absolute path to the folder to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """
        path = str(path)
        try:
            await self._sftp.rmdir(path)
        except asyncssh.sftp.SFTPFailure:
            raise OSError(f'Error while removing directory {path}: probably directory is not empty')

    async def rmtree_async(self, path: TransportPath):
        """Remove the folder named path, and all its contents.

        :param str path: absolute path to the folder to remove

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises OSError: if the operation fails
        """
        path = str(path)
        try:
            await self._sftp.rmtree(path, ignore_errors=False)
        except asyncssh.Error as exc:
            raise OSError(f'Error while removing directory tree {path}: {exc}')

    async def path_exists_async(self, path: TransportPath):
        """Returns True if path exists, False otherwise.

        :param path: path to check

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """
        path = str(path)
        return await self._sftp.exists(path)

    async def whoami_async(self):
        """Get the remote username

        :return: username (str),

        :raises OSError: if the command fails
        """
        command = 'whoami'
        # Assuming here that the username is either ASCII or UTF-8 encoded
        # This should be true essentially always
        retval, username, stderr = await self.exec_command_wait_async(command)
        if retval == 0:
            if stderr.strip():
                self.logger.warning(f'There was nonempty stderr in the whoami command: {stderr}')
            return username.strip()

        self.logger.error(f"Problem executing whoami. Exit code: {retval}, stdout: '{username}', stderr: '{stderr}'")
        raise OSError(f'Error while executing whoami. Exit code: {retval}')

    async def symlink_async(self, remotesource: TransportPath, remotedestination: TransportPath):
        """Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: absolute path to remote source
        :param remotedestination: absolute path to remote destination

        :type remotesource:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type remotedestination:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :raises ValueError: if remotedestination has patterns
        """
        remotesource = str(remotesource)
        remotedestination = str(remotedestination)

        if self.has_magic(remotesource):
            if self.has_magic(remotedestination):
                raise ValueError('`remotedestination` cannot have patterns')

            # find all files matching pattern
            for this_source in await self._sftp.glob(remotesource):
                # create the name of the link: take the last part of the path
                this_dest = os.path.join(remotedestination, os.path.split(this_source)[-1])  # type: ignore [arg-type]
                # in the line above I am sure that this_source is a string,
                # since asyncssh.sftp.glob() returns only str if argument remotesource is a str
                await self._sftp.symlink(this_source, this_dest)
        else:
            await self._sftp.symlink(remotesource, remotedestination)

    async def glob_async(self, pathname: TransportPath):
        """Return a list of paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        :param pathname: the pathname pattern to match.
            It should only be absolute path.

        :type pathname:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`

        :return: a list of paths matching the pattern.
        """
        pathname = str(pathname)
        return await self._sftp.glob(pathname)

    async def chmod_async(self, path: TransportPath, mode: int, follow_symlinks: bool = True):
        """Change the permissions of a file.

        :param path: path to the file
        :param mode: the new permissions
        :param bool follow_symlinks: if True, follow symbolic links

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type mode: int
        :type follow_symlinks: bool

        :raises OSError: if the path is empty
        """
        path = str(path)
        if not path:
            raise OSError('Input path is an empty argument.')
        try:
            await self._sftp.chmod(path, mode, follow_symlinks=follow_symlinks)
        except asyncssh.sftp.SFTPNoSuchFile as exc:
            raise OSError(f'Error {exc}, directory does not exists')

    async def chown_async(self, path: TransportPath, uid: int, gid: int):
        """Change the owner and group id of a file.

        :param path: path to the file
        :param uid: the new owner id
        :param gid: the new group id

        :type path:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        :type uid: int
        :type gid: int

        :raises OSError: if the path is empty
        """
        path = str(path)
        if not path:
            raise OSError('Input path is an empty argument.')
        try:
            await self._sftp.chown(path, uid, gid, follow_symlinks=True)
        except asyncssh.sftp.SFTPNoSuchFile as exc:
            raise OSError(f'Error {exc}, directory does not exists')

    async def copy_from_remote_to_remote_async(
        self,
        transportdestination: Transport,
        remotesource: TransportPath,
        remotedestination: TransportPath,
        **kwargs,
    ):
        """Copy files or folders from a remote computer to another remote computer, asynchronously.

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
            await self.get_async(remotesource, sandbox.abspath, **kwargs_get)
            # Then we scan the full sandbox directory with get_content_list,
            # because copying directly from sandbox.abspath would not work
            # to copy a single file into another single file, and copying
            # from sandbox.get_abs_path('*') would not work for files
            # beginning with a dot ('.').
            for filename in sandbox.get_content_list():
                await transportdestination.put_async(
                    os.path.join(sandbox.abspath, filename), remotedestination, **kwargs_put
                )

    def gotocomputer_command(self, remotedir: TransportPath):
        """Return a string to be used to connect to the remote computer.

        :param remotedir: the remote directory to connect to

        :type remotedir:  :class:`Path <pathlib.Path>`, :class:`PurePosixPath <pathlib.PurePosixPath>`, or `str`
        """
        connect_string = self._gotocomputer_string(remotedir)
        cmd = f'ssh -t {self.machine} {connect_string}'
        return cmd
