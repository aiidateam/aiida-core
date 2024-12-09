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

from aiida.orm import AuthInfo
from aiida.orm.fields import add_field
from aiida.transports import Transport

from ..data import Data

_logger = logging.getLogger(__name__)

__all__ = ('RemoteData',)


class RemoteData(Data):
    """Store a link to a file or folder on a remote machine.

    Remember to pass a computer!
    """

    KEY_EXTRA_CLEANED = 'cleaned'
    __qb_fields__ = [
        add_field(
            'remote_path',
            dtype=str,
        ),
    ]

    def __init__(self, remote_path=None, **kwargs):
        super().__init__(**kwargs)
        if remote_path is not None:
            self.set_remote_path(remote_path)

    def get_remote_path(self) -> str:
        return self.base.attributes.get('remote_path')

    def set_remote_path(self, val):
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
                    f'The required remote folder {full_path} on {self.computer.label} does not exist, is not a '
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
        :return: a list of dictionaries, where the documentation is in :py:class:Transport.listdir_withattributes.
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

    def get_size_on_disk(self, relpath: Path | None = None) -> str:
        """
        Connects to the remote folder and returns the total size of all files in the directory recursively in a
        human-readable format.

        :param relpath: File or directory path for which the total size should be returned, relative to
        ``self.get_remote_path()``.
        :return: Total size of file or directory in human-readable format.

        :raises: ``FileNotFoundError``, if file or directory does not exist anymore on the remote ``Computer``.
        """

        from aiida.common.utils import format_directory_size

        if relpath is None:
            relpath = Path('.')

        authinfo = self.get_authinfo()
        full_path = Path(self.get_remote_path()) / relpath
        computer_label = self.computer.label if self.computer is not None else ''

        with authinfo.get_transport() as transport:
            if not transport.path_exists(str(full_path)):
                exc_message = (
                    f'The required remote folder {full_path} on Computer <{computer_label}>'
                    'does not exist, is not a directory or has been deleted.'
                )
                raise FileNotFoundError(exc_message)

            try:
                total_size: int = self._get_size_on_disk_du(full_path, transport)

            except (RuntimeError, NotImplementedError):
                lstat_warn = (
                    'Problem executing `du` command. Will return total file size based on `lstat`. '
                    'Take the result with a grain of salt, as `lstat` does not consider the file system block size, '
                    'but instead returns the true size of the files in bytes, which differs from the actual space'
                    'requirements on disk.'
                )
                _logger.warning(lstat_warn)

                try:
                    total_size: int = self._get_size_on_disk_lstat(full_path, transport)

                except OSError:
                    _logger.critical('Could not evaluate directory size using either `du` or `lstat`.')

        return format_directory_size(size_in_bytes=total_size)

    def _get_size_on_disk_du(self, full_path: Path, transport: Transport) -> int:
        """Connects to the remote folder and returns the total size of all files in the directory recursively in bytes
        using the ``du`` command.

        :param full_path: Full path of which the size should be evaluated.
        :param transport: Open transport instance.
        :raises NotImplementedError: When ``exec_command_wait`` is not implemented, e.g., for the FirecREST plugin.
        :raises RuntimeError: When ``du`` command cannot be successfully executed.
        :return: Total size of directory recursively in bytes.
        """

        try:
            retval, stdout, stderr = transport.exec_command_wait(f'du --bytes {full_path}')
            if not stderr and retval == 0:
                total_size: int = int(stdout.split('\t')[0])
                return total_size
            else:
                raise RuntimeError(f'Error executing `du` command: {stderr}')

        except NotImplementedError as exc:
            raise NotImplementedError('`exec_command_wait` not implemented for the current transport plugin.') from exc
            # _logger.critical('`exec_command_wait` not implemented for the current transport plugin.')

    def _get_size_on_disk_lstat(self, full_path: Path, transport: Transport) -> int:
        """
        Connects to the remote folder and returns the total size of all files in the directory recursively in bytes
        using ``lstat``. Note that even if a file is only 1 byte, on disk, it still occupies one full disk block size.
        As such, getting accurate measures of the total expected size on disk when retrieving a ``RemoteData`` is not
        straightforward with ``lstat``, as one would need to consider the occupied block sizes for each file, as well as
        repository metadata. Thus, this function only serves as a fallback in the absence of the ``du`` command.

        :param full_path: Full path of which the size should be evaluated.
        :param transport: Open transport instance.
        :raises OSError: When directory given by ``full_path`` not existing or not a directory.
        :return: Total size of directory recursively in bytes.
        """
        try:
            total_size = 0
            contents = self.listdir_withattributes(full_path)

            for item in contents:
                item_path = full_path / item['name']
                # Add size of current item (file or directory metadata)
                total_size += item['attributes']['st_size']

                # If it's a directory, recursively get size of contents
                if item['isdir']:
                    total_size += self._get_size_on_disk_lstat(item_path, transport)

            return total_size

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
