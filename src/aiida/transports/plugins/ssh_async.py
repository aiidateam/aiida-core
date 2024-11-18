###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for transport over SSH asynchronously.

Since for many dependencies the blocking methods are required,
this plugin develops both blocking methods, as well.
"""

## TODO:
## and start writing tests!
## put & get methods could be simplified with the asyncssh.sftp.mget() & put() method or sftp.glob()
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

from ..transport import Transport, TransportInternalError, _TransportPath, fix_path

__all__ = ('AsyncSshTransport',)


def _validate_script(ctx, param, value: str):
    if value == 'None':
        return value
    if not os.path.isabs(value):
        raise click.BadParameter(f'{value} is not an absolute path')
    if not os.path.isfile(value):
        raise click.BadParameter(f'The script file: {value} does not exist')
    if not os.access(value, os.X_OK):
        raise click.BadParameter(f'The script {value} is not executable')
    return value


def _validate_machine(ctx, param, value: str):
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


class AsyncSshTransport(Transport):
    """Transport plugin via SSH, asynchronously."""

    # note, I intentionally wanted to keep connection parameters as simple as possible.
    _valid_auth_options = [
        (
            'machine',
            {
                'type': str,
                'prompt': 'machine as in `ssh machine` command',
                'help': 'Password-less host-setup to connect, as in command `ssh machine`. '
                "You'll need to have a `Host machine` "
                'entry defined in your `~/.ssh/config` file. ',
                'non_interactive_default': True,
                'callback': _validate_machine,
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
                'callback': _validate_script,
            },
        ),
        (
            'script_during',
            {
                'type': str,
                'default': 'None',
                'prompt': 'Local script to run *during* opening connection (path)',
                'help': '(optional) Specify a script to run *during* opening SSH connection. '
                'The script should be executable',
                'non_interactive_default': True,
                'callback': _validate_script,
            },
        ),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.machine = kwargs.pop('machine')
        self.script_before = kwargs.pop('script_before', 'None')
        self.script_during = kwargs.pop('script_during', 'None')

    def __str__(self):
        return f"{'OPEN' if self._is_open else 'CLOSED'} [AsyncSshTransport]"

    async def open_async(self):
        if self._is_open:
            raise InvalidOperation('Cannot open the transport twice')

        if self.script_before != 'None':
            os.system(f'{self.script_before}')

        self._conn = await asyncssh.connect(self.machine)

        if self.script_during != 'None':
            os.system(f'{self.script_during}')

        self._sftp = await self._conn.start_sftp_client()

        self._is_open = True

        return self

    async def close_async(self):
        if not self._is_open:
            raise InvalidOperation('Cannot close the transport: it is already closed')

        self._conn.close()
        await self._conn.wait_closed()
        self._is_open = False

    async def get_async(self, remotepath, localpath, dereference=True, overwrite=True, ignore_nonexisting=False):
        """Get a file or folder from remote to local.
        Redirects to getfile or gettree.

        :param remotepath: a remote path
        :param localpath: an (absolute) local path
        :param dereference: follow symbolic links.
            Default = True (default behaviour in paramiko).
            False is not implemented.
        :param overwrite: if True overwrites files and folders.
            Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if the remotepath is not found
        """
        remotepath = fix_path(remotepath)
        localpath = fix_path(localpath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        ## TODO: this whole glob part can be simplified via the asyncssh glob
        ## or by using the asyncssh.sftp.mget() method
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
                        await self.getfile_async(file, remote, dereference, overwrite)
                    else:  # one file to copy on one file
                        await self.getfile_async(file, localpath, dereference, overwrite)
                else:
                    await self.gettree_async(file, localpath, dereference, overwrite)

        elif await self.isdir_async(remotepath):
            await self.gettree_async(remotepath, localpath, dereference, overwrite)
        elif await self.isfile_async(remotepath):
            if os.path.isdir(localpath):
                remote = os.path.join(localpath, os.path.split(remotepath)[1])
                await self.getfile_async(remotepath, remote, dereference, overwrite)
            else:
                await self.getfile_async(remotepath, localpath, dereference, overwrite)
        elif ignore_nonexisting:
            pass
        else:
            raise OSError(f'The remote path {remotepath} does not exist')

    async def getfile_async(self, remotepath, localpath, dereference=True, overwrite=True):
        """Get a file from remote to local.

        :param remotepath: a remote path
        :param  localpath: an (absolute) local path
        :param  overwrite: if True overwrites files and folders.
                Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if unintentionally overwriting
        """
        remotepath = fix_path(remotepath)
        localpath = fix_path(localpath)

        if not os.path.isabs(localpath):
            raise ValueError('localpath must be an absolute path')

        if os.path.isfile(localpath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        try:
            await self._sftp.get(
                remotepaths=remotepath, localpath=localpath, preserve=True, recurse=False, follow_symlinks=dereference
            )
        except (OSError, asyncssh.Error) as exc:
            raise OSError(f'Error while uploading file {localpath}: {exc}')

    async def gettree_async(self, remotepath, localpath, dereference=True, overwrite=True):
        """Get a folder recursively from remote to local.

        :param remotepath: a remote path
        :param localpath: an (absolute) local path
        :param dereference: follow symbolic links.
            Default = True (default behaviour in paramiko).
            False is not implemented.
        :param  overwrite: if True overwrites files and folders.
            Default = False

        :raise ValueError: if local path is invalid
        :raise OSError: if the remotepath is not found
        :raise OSError: if unintentionally overwriting
        """
        remotepath = fix_path(remotepath)
        localpath = fix_path(localpath)

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
                await self._sftp.get(
                    remotepaths=PurePath(remotepath) / content_,
                    localpath=localpath,
                    preserve=True,
                    recurse=True,
                    follow_symlinks=dereference,
                )
            except (OSError, asyncssh.Error) as exc:
                raise OSError(f'Error while uploading file {localpath}: {exc}')

    async def put_async(self, localpath, remotepath, dereference=True, overwrite=True, ignore_nonexisting=False):
        """Put a file or a folder from local to remote.
        Redirects to putfile or puttree.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param dereference: follow symbolic links (boolean).
            Default = True (default behaviour in paramiko). False is not implemented.
        :param  overwrite: if True overwrites files and folders (boolean).
            Default = False.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist
        """
        localpath = fix_path(localpath)
        remotepath = fix_path(remotepath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        # TODO: this whole glob part can be simplified via the asyncssh glob
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
                elif not await self.path_exists_async(remotepath):  # questo dovrebbe valere solo per file
                    raise OSError('Remote directory does not exist')
                else:  # the remote path is a directory
                    rename_remote = True

            for file in to_copy_list:
                if os.path.isfile(file):
                    if rename_remote:  # copying more than one file in one directory
                        # here is the case isfile and more than one file
                        remotefile = os.path.join(remotepath, os.path.split(file)[1])
                        await self.putfile_async(file, remotefile, dereference, overwrite)

                    elif await self.isdir_async(remotepath):  # one file to copy in '.'
                        remotefile = os.path.join(remotepath, os.path.split(file)[1])
                        await self.putfile_async(file, remotefile, dereference, overwrite)
                    else:  # one file to copy on one file
                        await self.putfile_async(file, remotepath, dereference, overwrite)
                else:
                    await self.puttree_async(file, remotepath, dereference, overwrite)

        elif os.path.isdir(localpath):
            await self.puttree_async(localpath, remotepath, dereference, overwrite)
        elif os.path.isfile(localpath):
            if await self.isdir_async(remotepath):
                remote = os.path.join(remotepath, os.path.split(localpath)[1])
                await self.putfile_async(localpath, remote, dereference, overwrite)
            else:
                await self.putfile_async(localpath, remotepath, dereference, overwrite)
        elif not ignore_nonexisting:
            raise OSError(f'The local path {localpath} does not exist')

    async def putfile_async(self, localpath, remotepath, dereference=True, overwrite=True):
        """Put a file from local to remote.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True.

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist,
                    or unintentionally overwriting
        """
        localpath = fix_path(localpath)
        remotepath = fix_path(remotepath)

        if not os.path.isabs(localpath):
            raise ValueError('The localpath must be an absolute path')

        if await self.isfile_async(remotepath) and not overwrite:
            raise OSError('Destination already exists: not overwriting it')

        try:
            await self._sftp.put(
                localpaths=localpath, remotepath=remotepath, preserve=True, recurse=False, follow_symlinks=dereference
            )
        except (OSError, asyncssh.Error) as exc:
            raise OSError(f'Error while uploading file {localpath}: {exc}')

    async def puttree_async(self, localpath, remotepath, dereference=True, overwrite=True):
        """Put a folder recursively from local to remote.

        By default, overwrite.

        :param localpath: an (absolute) local path
        :param remotepath: a remote path
        :param dereference: follow symbolic links (boolean)
            Default = True (default behaviour in paramiko). False is not implemented.
        :param overwrite: if True overwrites files and folders (boolean).
            Default = True

        :raise ValueError: if local path is invalid
        :raise OSError: if the localpath does not exist, or trying to overwrite
        :raise OSError: if remotepath is invalid

        .. note:: setting dereference equal to True could cause infinite loops.
              see os.walk() documentation
        """
        localpath = fix_path(localpath)
        remotepath = fix_path(remotepath)

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
            await self.mkdir_async(remotepath)  # and make a directory at its place
        else:  # remotepath exists already: copy the folder inside of it!
            remotepath = os.path.join(remotepath, os.path.split(localpath)[1])
            await self.makedirs_async(remotepath, ignore_existing=overwrite)  # create a nested folder

        # This is written in this way, only because AiiDA expects to put file inside an existing folder
        # Or to put and rename the parent folder at the same time
        content_list = os.listdir(localpath)
        for content_ in content_list:
            try:
                await self._sftp.put(
                    localpaths=PurePath(localpath) / content_,
                    remotepath=remotepath,
                    preserve=True,
                    recurse=True,
                    follow_symlinks=dereference,
                )
            except (OSError, asyncssh.Error) as exc:
                raise OSError(f'Error while uploading file {PurePath(localpath)/content_}: {exc}')

    async def copy_async(
        self,
        remotesource: _TransportPath,
        remotedestination: _TransportPath,
        dereference: bool = False,
        recursive: bool = True,
        preserve: bool = False,
    ):
        """ """
        remotesource = fix_path(remotesource)
        remotedestination = fix_path(remotedestination)
        if self.has_magic(remotedestination):
            raise ValueError('Pathname patterns are not allowed in the destination')

        if not remotedestination:
            raise ValueError('remotedestination must be a non empty string')
        if not remotesource:
            raise ValueError('remotesource must be a non empty string')
        try:
            if self.has_magic(remotesource):
                await self._sftp.mcopy(
                    remotesource,
                    remotedestination,
                    preserve=preserve,
                    recurse=recursive,
                    follow_symlinks=dereference,
                )
            else:
                await self._sftp.copy(
                    remotesource,
                    remotedestination,
                    preserve=preserve,
                    recurse=recursive,
                    follow_symlinks=dereference,
                )
        except asyncssh.sftp.SFTPFailure as exc:
            raise OSError(f'Error while copying {remotesource} to {remotedestination}: {exc}')

    async def exec_command_wait_async(
        self,
        command: str,
        stdin: Optional[str] = None,
        encoding: str = 'utf-8',
        workdir: Union[_TransportPath, None] = None,
        timeout: Optional[float] = 2,
        **kwargs,
    ):
        """Execute a command on the remote machine and wait for it to finish.

        :param command: the command to execute
        :param stdin: the standard input to pass to the command
        :param encoding: (IGNORED) this is here just to keep the same signature as the one in `Transport` class
        :param workdir: the working directory where to execute the command
        :param timeout: the timeout in seconds

        :type command: str
        :type stdin: str
        :type encoding: str
        :type workdir: str
        :type timeout: float

        :return: a tuple with the return code, the stdout and the stderr of the command
        :rtype: tuple(int, str, str)
        """

        if workdir:
            command = f'cd {workdir} && {command}'

        bash_commmand = self._bash_command_str + '-c '

        result = await self._conn.run(
            bash_commmand + escape_for_bash(command), input=stdin, check=False, timeout=timeout
        )
        # both stdout and stderr are strings
        return (result.returncode, ''.join(result.stdout), ''.join(result.stderr))  # type: ignore [arg-type]

    async def get_attribute_async(self, path):
        """ """
        path = fix_path(path)
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

    async def isdir_async(self, path):
        """Return True if the given path is a directory, False otherwise.
        Return False also if the path does not exist.
        """
        # Return False on empty string
        if not path:
            return False

        path = fix_path(path)

        return await self._sftp.isdir(path)

    async def isfile_async(self, path):
        """Return True if the given path is a file, False otherwise.
        Return False also if the path does not exist.
        """
        # Return False on empty string
        if not path:
            return False

        path = fix_path(path)

        return await self._sftp.isfile(path)

    async def listdir_async(self, path, pattern=None):  # type: ignore[override]
        """

        :param path: the absolute path to list
        """
        path = fix_path(path)
        if not pattern:
            list_ = await self._sftp.listdir(path)
        else:
            patterned_path = pattern if pattern.startswith('/') else Path(path).joinpath(pattern)
            list_ = await self._sftp.glob(patterned_path)

        for item in ['..', '.']:
            if item in list_:
                list_.remove(item)

        return list_

    async def listdir_withattributes_async(self, path: _TransportPath, pattern: Optional[str] = None):  # type: ignore[override]
        """Return a list of the names of the entries in the given path.
        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param str path: absolute path to list
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
        path = fix_path(path)
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

        :param str path: absolute path to directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                if the leaf directory does already exist

        :raises: OSError, if directory at path already exists
        """
        path = fix_path(path)

        try:
            await self._sftp.makedirs(path, exist_ok=ignore_existing)
        except SFTPFileAlreadyExists as exc:
            raise OSError(f'Error while creating directory {path}: {exc}, directory already exists')
        except asyncssh.sftp.SFTPFailure as exc:
            if (self._sftp.version < 6) and not ignore_existing:
                raise OSError(f'Error while creating directory {path}: {exc}, probably it already exists')
            else:
                raise TransportInternalError(f'Error while creating directory {path}: {exc}')

    async def mkdir_async(self, path: _TransportPath, ignore_existing=False):
        """Create a directory.

        :param str path: absolute path to directory to create
        :param bool ignore_existing: if set to true, it doesn't give any error
                if the leaf directory does already exist

        :raises: OSError, if directory at path already exists
        """
        path = fix_path(path)

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

    async def remove_async(self, path):
        """Remove the file at the given path. This only works on files;
        for removing folders (directories), use rmdir.

        :param str path: path to file to remove

        :raise OSError: if the path is a directory
        """
        path = fix_path(path)
        # TODO: check if asyncssh does return SFTPFileIsADirectory in this case
        # if that's the case, we can get rid of the isfile check
        if await self.isdir_async(path):
            raise OSError(f'The path {path} is a directory')
        else:
            await self._sftp.remove(path)

    async def rename_async(self, oldpath, newpath):
        """
        Rename a file or folder from oldpath to newpath.

        :param str oldpath: existing name of the file or folder
        :param str newpath: new name for the file or folder

        :raises OSError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """
        oldpath = fix_path(oldpath)
        newpath = fix_path(newpath)
        if not oldpath or not newpath:
            raise ValueError('oldpath and newpath must be non-empty strings')

        if await self._sftp.exists(newpath):
            raise OSError(f'Cannot rename {oldpath} to {newpath}: destination exists')

        await self._sftp.rename(oldpath, newpath)

    async def rmdir_async(self, path):
        """Remove the folder named path.
        This works only for empty folders. For recursive remove, use rmtree.

        :param str path: absolute path to the folder to remove
        """
        path = fix_path(path)
        try:
            await self._sftp.rmdir(path)
        except asyncssh.sftp.SFTPFailure:
            raise OSError(f'Error while removing directory {path}: probably directory is not empty')

    async def rmtree_async(self, path):
        """Remove the folder named path, and all its contents.

        :param str path: absolute path to the folder to remove
        """
        path = fix_path(path)
        try:
            await self._sftp.rmtree(path, ignore_errors=False)
        except asyncssh.Error as exc:
            raise OSError(f'Error while removing directory tree {path}: {exc}')

    async def path_exists_async(self, path):
        """Returns True if path exists, False otherwise."""
        path = fix_path(path)
        return await self._sftp.exists(path)

    async def whoami_async(self):
        """Get the remote username

        :return: list of username (str),
                 retval (int),
                 stderr (str)
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

    async def symlink_async(self, remotesource, remotedestination):
        """Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: absolute path to remote source
        :param remotedestination: absolute path to remote destination
        """
        remotesource = fix_path(remotesource)
        remotedestination = fix_path(remotedestination)

        if self.has_magic(remotesource):
            if self.has_magic(remotedestination):
                raise ValueError('`remotedestination` cannot have patterns')

            # find all files matching pattern
            for this_source in await self._sftp.glob(remotesource):
                # create the name of the link: take the last part of the path
                this_dest = os.path.join(remotedestination, os.path.split(this_source)[-1])
                await self._sftp.symlink(this_source, this_dest)
        else:
            await self._sftp.symlink(remotesource, remotedestination)

    async def glob_async(self, pathname):
        """Return a list of paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards a la fnmatch.

        :param str pathname: the pathname pattern to match.
            It should only be an absolute path.
        :return: a list of paths matching the pattern.
        """
        return await self._sftp.glob(pathname)

    async def chmod_async(self, path, mode, follow_symlinks=True):
        """Change the permissions of a file.

        :param str path: path to the file
        :param int mode: the new permissions
        """
        path = fix_path(path)
        if not path:
            raise OSError('Input path is an empty argument.')
        try:
            await self._sftp.chmod(path, mode, follow_symlinks=follow_symlinks)
        except asyncssh.sftp.SFTPNoSuchFile as exc:
            raise OSError(f'Error {exc}, directory does not exists')

    ## Blocking methods. We need these for backwards compatibility
    # This is useful, only because some part of engine and
    # many external plugins are synchronous, in those cases blocking calls make more sense.
    # However, be aware you cannot use these methods in an async functions,
    # because they will block the event loop.

    def run_command_blocking(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))

    def open(self):
        return self.run_command_blocking(self.open_async)

    def close(self):
        return self.run_command_blocking(self.close_async)

    def chown(self, *args, **kwargs):
        raise NotImplementedError('Not implemented, for now')

    def get(self, *args, **kwargs):
        return self.run_command_blocking(self.get_async, *args, **kwargs)

    def getfile(self, *args, **kwargs):
        return self.run_command_blocking(self.getfile_async, *args, **kwargs)

    def gettree(self, *args, **kwargs):
        return self.run_command_blocking(self.gettree_async, *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.run_command_blocking(self.put_async, *args, **kwargs)

    def putfile(self, *args, **kwargs):
        return self.run_command_blocking(self.putfile_async, *args, **kwargs)

    def puttree(self, *args, **kwargs):
        return self.run_command_blocking(self.puttree_async, *args, **kwargs)

    def chmod(self, *args, **kwargs):
        return self.run_command_blocking(self.chmod_async, *args, **kwargs)

    def copy(self, *args, **kwargs):
        return self.run_command_blocking(self.copy_async, *args, **kwargs)

    def copyfile(self, *args, **kwargs):
        return self.copy(*args, **kwargs)

    def copytree(self, *args, **kwargs):
        return self.copy(*args, **kwargs)

    def exec_command_wait(self, *args, **kwargs):
        return self.run_command_blocking(self.exec_command_wait_async, *args, **kwargs)

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

    def gotocomputer_command(self, remotedir):
        connect_string = self._gotocomputer_string(remotedir)
        cmd = f'ssh -t {self.machine} {connect_string}'
        return cmd

    ## These methods are not implemented for async transport,
    ## mainly because they are not being used across the codebase.
    ## If you need them, please open an issue on GitHub

    def exec_command_wait_bytes(self, *args, **kwargs):
        raise NotImplementedError('Not implemented, waiting for a use case')

    def _exec_command_internal(self, *args, **kwargs):
        raise NotImplementedError('Not implemented, waiting for a use case')

    def normalize(self, *args, **kwargs):
        raise NotImplementedError('Not implemented, waiting for a use case')

    def chdir(self, *args, **kwargs):
        raise NotImplementedError("It's not safe to chdir() for async transport")

    def getcwd(self, *args, **kwargs):
        raise NotImplementedError("It's not safe to getcwd() for async transport")
