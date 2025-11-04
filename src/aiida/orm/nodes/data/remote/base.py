###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin that models a folder on a remote computer."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from aiida.common.pydantic import MetadataField
from aiida.orm import AuthInfo
from aiida.transports import Transport

from ..data import Data

_logger = logging.getLogger(__name__)

__all__ = ('RemoteData',)


class RemoteData(Data):
    """Store a link to a file or folder on a remote machine.

    Remember to pass a computer!
    """

    KEY_EXTRA_CLEANED = 'cleaned'

    class Model(Data.Model):
        remote_path: Optional[str] = MetadataField(
            None,
            title='Remote path',
            description='Filepath on the remote computer.',
            orm_to_model=lambda node: node.get_remote_path(),
        )

    def __init__(self, remote_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        if remote_path is not None:
            self.set_remote_path(remote_path)

    def get_remote_path(self) -> str:
        return self.base.attributes.get('remote_path')

    def set_remote_path(self, val: str):
        self.base.attributes.set('remote_path', val)

    @property
    def is_cleaned(self):
        """Return whether the remote folder has been cleaned."""
        return self.base.extras.get(self.KEY_EXTRA_CLEANED, False)

    @property
    def is_empty(self):
        """Check if remote folder is empty"""
        if self.is_cleaned:
            return True

        authinfo = self.get_authinfo()
        transport = authinfo.get_transport()

        with transport:
            if not transport.isdir(self.get_remote_path()):
                return True

            return not transport.listdir(self.get_remote_path())

    def getfile(self, relpath, destpath):
        """Connects to the remote folder and retrieves the content of a file.

        :param relpath:  The relative path of the file on the remote to retrieve.
        :param destpath: The absolute path of where to store the file on the local machine.
        """
        authinfo = self.get_authinfo()

        with authinfo.get_transport() as transport:
            try:
                full_path = os.path.join(self.get_remote_path(), relpath)
                transport.getfile(full_path, destpath)
            except OSError as exception:
                if exception.errno == 2:  # file does not exist
                    raise OSError(
                        'The required remote file {} on {} does not exist or has been deleted.'.format(
                            full_path, self.computer.label
                        )
                    ) from exception
                raise

    def listdir(self, relpath='.'):
        """Connects to the remote folder and lists the directory content.

        :param relpath: If 'relpath' is specified, lists the content of the given subfolder.
        :return: a flat list of file/directory names (as strings).
        """
        authinfo = self.get_authinfo()

        with authinfo.get_transport() as transport:
            full_path = os.path.join(self.get_remote_path(), relpath)
            if not transport.isdir(full_path):
                raise OSError(
                    f'The required remote path {full_path} on {self.computer.label} does not exist, is not a '
                    'directory or has been deleted.'
                )

            try:
                return transport.listdir(full_path)
            except OSError as exception:
                if exception.errno in (2, 20):
                    # directory not existing or not a directory
                    exc = OSError(
                        f'The required remote folder {full_path} on {self.computer.label} does not exist, is not a '
                        'directory or has been deleted.'
                    )
                    exc.errno = exception.errno
                    raise exc from exception
                else:
                    raise

    def listdir_withattributes(self, path='.'):
        """Connects to the remote folder and lists the directory content.

        :param relpath: If 'relpath' is specified, lists the content of the given subfolder.
        :return: a list of dictionaries, where the documentation
            is in :py:class:Transport.listdir_withattributes.
        """
        authinfo = self.get_authinfo()

        with authinfo.get_transport() as transport:
            full_path = os.path.join(self.get_remote_path(), path)
            if not transport.isdir(full_path):
                raise OSError(
                    f'The required remote folder {full_path} on {self.computer.label} does not exist, is not a '
                    'directory or has been deleted.'
                )

            try:
                return transport.listdir_withattributes(full_path)
            except OSError as exception:
                if exception.errno in (2, 20):
                    # directory not existing or not a directory
                    exc = OSError(
                        f'The required remote folder {full_path} on {self.computer.label} does not exist, is not a '
                        'directory or has been deleted.'
                    )
                    exc.errno = exception.errno
                    raise exc from exception
                else:
                    raise

    def _clean(self, transport=None):
        """Remove all content of the remote folder on the remote computer.

        When the cleaning operation is successful, the extra with the key ``RemoteData.KEY_EXTRA_CLEANED`` is set.

        :param transport: Provide an optional transport that is already open. If not provided, a transport will be
            automatically opened, based on the current default user and the computer of this data node. Passing in the
            transport can be used for efficiency if a great number of nodes need to be cleaned for the same computer.
            Note that the user should take care that the correct transport is passed.
        :raises ValueError: If the hostname of the provided transport does not match that of the node's computer.
        """
        from aiida.orm.utils.remote import clean_remote

        remote_dir = self.get_remote_path()

        if transport is None:
            with self.get_authinfo().get_transport() as _transport:
                clean_remote(_transport, remote_dir)
        else:
            if transport.hostname != self.computer.hostname:
                raise ValueError(
                    f'Transport hostname `{transport.hostname}` does not equal `{self.computer.hostname}` of {self}.'
                )
            clean_remote(transport, remote_dir)

        self.base.extras.set(self.KEY_EXTRA_CLEANED, True)

    def _validate(self):
        from aiida.common.exceptions import ValidationError

        super()._validate()

        try:
            self.get_remote_path()
        except AttributeError as exception:
            raise ValidationError("attribute 'remote_path' not set.") from exception

        computer = self.computer
        if computer is None:
            raise ValidationError('Remote computer not set.')

    def get_authinfo(self):
        return AuthInfo.get_collection(self.backend).get(dbcomputer=self.computer, aiidauser=self.user)

    def get_size_on_disk(
        self,
        relpath: Path | None = None,
        method: str = 'du',
        return_bytes: bool = False,
    ) -> int | str:
        """Connects to the remote Computer of the `RemoteData` object and returns the total size of a file or a
        directory at the given `relpath` in a human-readable format.

        :param relpath: File or directory path for which the total size should be returned, relative to
            ``self.get_remote_path()``.
        :param method: Method to be used to evaluate the directory/file size (either ``du`` or ``stat``).
        :param return_bytes: Return the total byte size is int, or in human-readable format.

        :raises FileNotFoundError: If file or directory does not exist anymore on the remote ``Computer``.
        :raises NotImplementedError: If a method other than ``du`` or ``stat`` is selected.

        :return: Total size of given file or directory.
        """

        from aiida.common.utils import format_directory_size

        total_size: int = -1

        if relpath is None:
            relpath = Path('.')

        authinfo = self.get_authinfo()
        full_path = Path(self.get_remote_path()) / relpath
        computer_label = self.computer.label if self.computer is not None else ''

        with authinfo.get_transport() as transport:
            if not transport.path_exists(str(full_path)):
                exc_message = f'The required remote path {full_path} on Computer <{computer_label}> does not exist.'
                raise FileNotFoundError(exc_message)

            if method not in ('du', 'stat'):
                exc_message = f'Specified method `{method}` is not an valid input. Please choose either `du` or `stat`.'
                raise ValueError(exc_message)

            if method == 'du':
                try:
                    total_size: int = self._get_size_on_disk_du(full_path, transport)
                    _logger.report('Obtained size on the remote using `du`.')
                    if return_bytes:
                        return total_size, method
                    else:
                        return format_directory_size(size_in_bytes=total_size), method

                except (RuntimeError, NotImplementedError):
                    # NotImplementedError captures the fact that, e.g., FirecREST does not allow for `exec_command_wait`
                    stat_warn = (
                        'Problem executing `du` command. Will return total file size based on `stat` as fallback. '
                    )

                    _logger.warning(stat_warn)

            if method == 'stat' or total_size < 0:
                try:
                    total_size: int = self._get_size_on_disk_stat(full_path, transport)
                    _logger.report('Obtained size on the remote using `stat`.')
                    _logger.warning(
                        'Take the result with a grain of salt, as `stat` returns the apparent size of files, '
                        'not their actual disk usage.'
                    )
                    if return_bytes:
                        return total_size, 'stat'
                    else:
                        return format_directory_size(size_in_bytes=total_size), 'stat'

                # This should typically not even be reached, as the OSError occours if the path is not a directory or
                # does not exist. Though, we check for its existence already in the beginning of this method.
                except OSError:
                    _logger.critical('Could not evaluate directory size using either `du` or `stat`.')
                    raise

    def _get_size_on_disk_du(self, full_path: Path, transport: Transport) -> int:
        """Returns the total size of a file/directory at the given ``full_path`` on the remote Computer in bytes using
        the ``du`` command.

        :param full_path: Full path of file or directory for which the size should be evaluated.
        :param transport: Open transport instance.

        :raises NotImplementedError: When ``exec_command_wait`` is not implemented, e.g., for the FirecREST plugin.
        :raises RuntimeError: When ``du`` command cannot be successfully executed.

        :return: Total size of the file/directory in bytes (including all its contents).
        """

        try:
            # Initially, we were using the `--bytes` option here. However, this is equivalent to `--apparent-size` and
            # `--block-size=1`, with the `--apparent-size` option being rather fragile (e.g., its implementation changed
            # between the different versions of `du` of Ubuntu 22.04 and 24.04, causing the tests to fail). Thus, we
            # retain only `--block-size=1` to obtain the total size in **bytes** as an integer value. Note that
            # `--block-size` here refers to the size of "blocks" for displaying the output of `du`, by default 1024
            # bytes (1 KiB), **not** the "disk block size".

            # On the other hand, for the parametrized tests of this functionality in `test_remote.py`, a **disk block
            # size** of 4096 bytes (4 KiB) is assumed, meaning that a file with, e.g., only 1 or 10 bytes of actual
            # content (its `apparent-size`) still occupies 4096 bytes (4 KiB) on disk. In principle, the disk block size
            # can differ between different disk formattings, OS, etc., however, as 4096 bytes (4 KiB) is the default for
            # Linux's ext4, as well as macOS, we assume for now that it is a reasonable assumption and default value.

            # Lastly, the `-s` (`--summarize`) option yields only a single total file size value.
            retval, stdout, stderr = transport.exec_command_wait(f'du -s --block-size=1 {full_path}')
        except NotImplementedError as exc:
            raise NotImplementedError('`exec_command_wait` not implemented for the current transport plugin.') from exc

        if stderr or retval != 0:
            raise RuntimeError(f'Error executing `du` command: {stderr}')
        else:
            total_size: int = int(stdout.split('\t')[0])
            return total_size

    def _get_size_on_disk_stat(self, full_path: Path, transport: Transport) -> int:
        """Returns the total size of a file/directory at the given ``full_path`` on the remote Computer in bytes using
        the ``stat`` command.

        Connects to the remote folder and returns the total size of all files in the directory in bytes using ``stat``.
        Note that `stat` returns the apparent file size, not actual disk usage.  Thus, even if a file is only 1 byte, on
        disk, it still occupies one full disk block size. As such, getting accurate measures of the total expected size
        on disk when retrieving a ``RemoteData`` is not straightforward with ``stat``, as one would need to consider the
        occupied block sizes for each file, as well as repository metadata. Therefore, this function only serves as a
        fallback in the absence of the ``du`` command, and the returned estimate is expected to be smaller than the size
        on disk that is actually occupied. Further note that the `Transport.get_attribute` method that is
        eventually being called on each file, calls `lstat`, which is equivalent to ``os.stat(follow_symlinks=False)``.

        :param full_path: Full path of file or directory of which the size should be evaluated.
        :param transport: Open transport instance.

        :raises OSError: When object at ``full_path`` doesn't exist.

        :return: Total size of the file/directory in bytes (including all its contents).
        """

        def _get_size_on_disk_stat_recursive(full_path: Path, transport: Transport):
            """Helper function for recursive directory traversal."""

            total_size = 0
            contents = self.listdir_withattributes(full_path)

            for item in contents:
                item_path = full_path / item['name']
                # Add size of current item (file or directory metadata)
                total_size += item['attributes']['st_size']

                # If it's a directory, recursively get size of contents
                if item['isdir']:
                    total_size += _get_size_on_disk_stat_recursive(item_path, transport)

            return total_size

        if transport.isfile(path=str(full_path)):
            return transport.get_attribute(str(full_path))['st_size']

        try:
            return _get_size_on_disk_stat_recursive(full_path, transport)

        except OSError:
            # Not a directory or not existing anymore. Exception is captured outside in `get_size_on_disk`.
            raise
