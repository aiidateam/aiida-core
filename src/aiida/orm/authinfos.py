###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the `AuthInfo` ORM class."""

import enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

from aiida.common import exceptions
from aiida.manage import get_manager
from aiida.orm.implementation.authinfos import BackendAuthInfo
from aiida.plugins import TransportFactory

from . import entities, users
from .fields import add_field

if TYPE_CHECKING:
    from aiida.orm import Computer, User
    from aiida.orm.implementation import StorageBackend
    from aiida.transports import Transport

__all__ = ('AuthInfo',)


class AuthInfoCollection(entities.Collection['AuthInfo']):
    """The collection of `AuthInfo` entries."""

    @staticmethod
    def _entity_base_cls() -> Type['AuthInfo']:
        return AuthInfo

    def delete(self, pk: int) -> None:
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
        self._backend.authinfos.delete(pk)


class AuthInfo(entities.Entity['BackendAuthInfo', AuthInfoCollection]):
    """ORM class that models the authorization information that allows a `User` to connect to a `Computer`."""

    _CLS_COLLECTION = AuthInfoCollection

    __qb_fields__ = [
        add_field(
            'enabled',
            dtype=bool,
            is_attribute=False,
            doc='Whether the instance is enabled',
        ),
        add_field(
            'auth_params',
            dtype=Dict[str, Any],
            is_attribute=False,
            doc='Dictionary of authentication parameters',
        ),
        add_field(
            'metadata',
            dtype=Dict[str, Any],
            is_attribute=False,
            doc='Dictionary of metadata',
        ),
        add_field(
            'computer_pk',
            dtype=int,
            is_attribute=False,
            doc='The PK of the computer',
        ),
        add_field(
            'user_pk',
            dtype=int,
            is_attribute=False,
            doc='The PK of the user',
        ),
    ]

    PROPERTY_WORKDIR = 'workdir'
    SecureStorage = BackendAuthInfo.SecureStorage

    def __init__(self, computer: 'Computer', user: 'User', backend: Optional['StorageBackend'] = None) -> None:
        """Create an `AuthInfo` instance for the given computer and user.

        :param computer: a `Computer` instance
        :param user: a `User` instance
        :param backend: the backend to use for the instance, or use the default backend if None
        """
        backend = backend or get_manager().get_profile_storage()
        model = backend.authinfos.create(computer=computer.backend_entity, user=user.backend_entity)
        super().__init__(model)

    def __str__(self) -> str:
        if self.enabled:
            return f'AuthInfo for {self.user.email} on {self.computer.label}'

        return f'AuthInfo for {self.user.email} on {self.computer.label} [DISABLED]'

    @property
    def enabled(self) -> bool:
        """Return whether this instance is enabled.

        :return: True if enabled, False otherwise
        """
        return self._backend_entity.enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """Set the enabled state

        :param enabled: boolean, True to enable the instance, False to disable it
        """
        self._backend_entity.enabled = enabled

    @property
    def computer(self) -> 'Computer':
        """Return the computer associated with this instance."""
        from . import computers

        return entities.from_backend_entity(computers.Computer, self._backend_entity.computer)

    @property
    def user(self) -> 'User':
        """Return the user associated with this instance."""
        return entities.from_backend_entity(users.User, self._backend_entity.user)

    def get_auth_params(self) -> Dict[str, Any]:
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """
        auth_params = self._backend_entity.get_auth_params()
        if auth_params.get('password', None) == str(Password.OBFUSCATED):
            auth_params['password'] = Password.OBFUSCATED
        return auth_params

    def set_auth_params(self, auth_params: Dict[str, Any]) -> None:
        """Set the dictionary of authentication parameters.

        If password present in `auth_params`, it stores it in secure storage and obfuscates it.

        :param auth_params: a dictionary with authentication parameters
        """
        import copy

        auth_params = copy.deepcopy(auth_params)
        # the default value for the password in CLI is the empty string
        # which is covered by evaluating to False in the conditional statement
        if password := auth_params.pop('password', None):
            self.secure_storage.set_password(password)
            # we cannot store enum in database so we use name
            auth_params['password'] = str(Password.OBFUSCATED)
        self._backend_entity.set_auth_params(auth_params)

    def get_metadata(self) -> Dict[str, Any]:
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """
        return self._backend_entity.get_metadata()

    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the dictionary of metadata

        :param metadata: a dictionary with metadata
        """
        self._backend_entity.set_metadata(metadata)

    def get_workdir(self) -> str:
        """Return the working directory.

        If no explicit work directory is set for this instance, the working directory of the computer will be returned.

        :return: the working directory
        """
        try:
            return self.get_metadata()[self.PROPERTY_WORKDIR]
        except KeyError:
            return self.computer.get_workdir()

    def get_transport(self) -> 'Transport':
        """Return a fully configured transport that can be used to connect to the computer set for this instance."""
        computer = self.computer
        transport_type = computer.transport_type

        try:
            transport_class = TransportFactory(transport_type)
        except exceptions.EntryPointError as exception:
            raise exceptions.ConfigurationError(f'transport type `{transport_type}` could not be loaded: {exception}')

        return transport_class(machine=computer.hostname, secure_storage=self.secure_storage, **self.get_auth_params())

    @property
    def secure_storage(self) -> 'AuthInfo.SecureStorage':
        """Returns the manager of the password associated to this computer stored in system's secure storage."""
        return self.SecureStorage(self.computer)


class Password(enum.Enum):
    OBFUSCATED = 'OBFUSCATED'
