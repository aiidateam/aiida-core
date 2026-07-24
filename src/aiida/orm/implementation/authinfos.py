###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the backend implementation of the `AuthInfo` ORM class."""

import abc
import sys
from typing import TYPE_CHECKING, Any

from .entities import BackendCollection, BackendEntity

if TYPE_CHECKING:
    import keyringrs  # type: ignore[import-untyped]

    from .computers import BackendComputer
    from .users import BackendUser

__all__ = ('BackendAuthInfo', 'BackendAuthInfoCollection')


class BackendAuthInfo(BackendEntity):
    """Backend implementation for the `AuthInfo` ORM class.

    An authinfo is a set of credentials that can be used to authenticate to a remote computer.
    """

    METADATA_WORKDIR = 'workdir'

    @property
    @abc.abstractmethod
    def enabled(self) -> bool:
        """Return whether this instance is enabled.

        :return: boolean, True if enabled, False otherwise
        """

    @enabled.setter
    @abc.abstractmethod
    def enabled(self, value: bool) -> None:
        """Set the enabled state

        :param enabled: boolean, True to enable the instance, False to disable it
        """

    @property
    @abc.abstractmethod
    def computer(self) -> 'BackendComputer':
        """Return the computer associated with this instance."""

    @property
    @abc.abstractmethod
    def user(self) -> 'BackendUser':
        """Return the user associated with this instance."""

    @abc.abstractmethod
    def get_auth_params(self) -> dict[str, Any]:
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """

    @abc.abstractmethod
    def set_auth_params(self, auth_params: dict[str, Any]) -> None:
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """

    @abc.abstractmethod
    def get_metadata(self) -> dict[str, Any]:
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """

    @abc.abstractmethod
    def set_metadata(self, metadata: dict[str, Any]) -> None:
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        """

    class SecureStorage:
        """Manager for passwords stored in the system secure storage."""

        _SERVICE_NAME = 'aiida.core.authinfo'

        def __init__(self, uuid: str) -> None:
            self._uuid = uuid

        def _entry(self) -> 'keyringrs.Entry':
            """Return the keyring entry for this UUID, importing ``keyringrs`` lazily."""
            # Imported lazily to avoid loading the native extension on `import aiida.orm`
            import keyringrs

            return keyringrs.Entry(self._SERVICE_NAME, self._uuid)

        def get_password(self) -> str | None:
            """Return the stored password if available."""
            try:
                return self._entry().get_password()
            except KeyError:
                return None

        def set_password(self, password: str) -> None:
            """Store a password in the system secure storage."""
            self._entry().set_password(password)

        def delete_password(self) -> None:
            """Delete the stored password if available."""
            try:
                self._entry().delete_credential()
            except KeyError:
                pass

        def get_cmd_stdout_password(self) -> str:
            """Return a command that prints the stored password to stdout."""
            python_command = (
                'from keyringrs import Entry;'
                f'entry = Entry("{self._SERVICE_NAME}", "{self._uuid}");'
                'print(entry.get_password(), end="")'
            )
            return f'"{sys.executable}" -c \'{python_command}\''

    @property
    def secure_storage(self) -> SecureStorage:
        """Return the secure storage manager for the associated computer."""
        return self.SecureStorage(self.computer.uuid)


class BackendAuthInfoCollection(BackendCollection[BackendAuthInfo]):
    """The collection of backend `AuthInfo` entries."""

    ENTITY_CLASS = BackendAuthInfo

    @abc.abstractmethod
    def delete(self, pk: int) -> None:
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
