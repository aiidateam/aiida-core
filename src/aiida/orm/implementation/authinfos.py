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
from typing import TYPE_CHECKING, Any, Dict, Protocol, Union

import keyringrs

from .entities import BackendCollection, BackendEntity

if TYPE_CHECKING:
    from .computers import BackendComputer
    from .users import BackendUser

__all__ = ('BackendAuthInfo', 'BackendAuthInfoCollection')


class HasUuid(Protocol):
    def uuid(self) -> str: ...


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
    def get_auth_params(self) -> Dict[str, Any]:
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """

    @abc.abstractmethod
    def set_auth_params(self, auth_params: Dict[str, Any]) -> None:
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """

    @abc.abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """

    @abc.abstractmethod
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        """

    class SecureStorage:
        # the service name used to store in the secure storage
        _SERVICE_NAME = 'aiida.core.authinfo'

        def __init__(self, unique_obj: HasUuid):
            self._unique_obj = unique_obj

        def get_password(self) -> Union[str, None]:
            """Retrieves the password associated with this unique_obj from system's secure storage

            :raises RuntimeError: If the keychain is not accessible.
            """
            try:
                return keyringrs.Entry(self._SERVICE_NAME, f'{self._unique_obj.uuid}').get_password()
            except KeyError:
                return None

        def set_password(self, password: str) -> None:
            """Sets the entry with the uuid of the unique_obj to system's secure storage with the `password`.

            :raises RuntimeError: If the keychain is not accessible.
            """
            keyringrs.Entry(self._SERVICE_NAME, f'{self._unique_obj.uuid}').set_password(password)

        def delete_password(self) -> None:
            """Deletes the password associated with this unique_obj from system's secure storage if available.

            :raises RuntimeError: If the keychain is not accessible.
            """

            try:
                keyringrs.Entry(self._SERVICE_NAME, f'{self._unique_obj.uuid}').delete_credential()
            except KeyError:
                return None

        def get_cmd_stdout_password(self) -> str:
            """Returns the command line command to retrieve the password to stdout.

            This is needed for the gotounique_obj commands."""

            python_command = (
                'from keyringrs import Entry;'
                f'entry = Entry("{self._SERVICE_NAME}", "{self._unique_obj.uuid}");'
                'print(entry.get_password(), end="")'
            )
            return f"{sys.executable} -c '{python_command}'"

    @property
    def secure_storage(self) -> SecureStorage:
        """Returns the manager of the password associated to this computer stored in system's secure storage."""
        return self.SecureStorage(self.computer)


class BackendAuthInfoCollection(BackendCollection[BackendAuthInfo]):
    """The collection of backend `AuthInfo` entries."""

    ENTITY_CLASS = BackendAuthInfo

    @abc.abstractmethod
    def delete(self, pk: int) -> None:
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
