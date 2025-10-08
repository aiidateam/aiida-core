###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the `AuthInfo` ORM class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional, Type, cast

from aiida.common import exceptions
from aiida.common.pydantic import MetadataField
from aiida.manage import get_manager
from aiida.plugins import TransportFactory

from . import entities, users
from .computers import Computer
from .users import User

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.authinfos import BackendAuthInfo
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
    PROPERTY_WORKDIR = 'workdir'

    class Model(entities.Entity.Model):
        computer: int = MetadataField(
            description='The PK of the computer',
            is_attribute=False,
            orm_class=Computer,
            orm_to_model=lambda auth_info, _: cast('AuthInfo', auth_info).computer.pk,
        )
        user: int = MetadataField(
            description='The PK of the user',
            is_attribute=False,
            orm_class=User,
            orm_to_model=lambda auth_info, _: cast('AuthInfo', auth_info).user.pk,
        )
        enabled: bool = MetadataField(
            True,
            description='Whether the instance is enabled',
            is_attribute=False,
        )
        auth_params: Dict[str, Any] = MetadataField(
            default_factory=dict,
            description='Dictionary of authentication parameters',
            is_attribute=False,
        )
        metadata: Dict[str, Any] = MetadataField(
            default_factory=dict,
            description='Dictionary of metadata',
            is_attribute=False,
        )

    def __init__(
        self,
        computer: 'Computer',
        user: 'User',
        enabled: bool = True,
        auth_params: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        backend: Optional['StorageBackend'] = None,
    ) -> None:
        """Create an `AuthInfo` instance for the given computer and user.

        :param computer: a `Computer` instance
        :param user: a `User` instance
        :param backend: the backend to use for the instance, or use the default backend if None
        """
        backend = backend or get_manager().get_profile_storage()
        model = backend.authinfos.create(
            computer=computer.backend_entity,
            user=user.backend_entity,
            enabled=enabled,
            auth_params=auth_params or {},
            metadata=metadata or {},
        )
        super().__init__(model)

    def __str__(self) -> str:
        if self.enabled:
            return f'AuthInfo for {self.user.email} on {self.computer.label}'

        return f'AuthInfo for {self.user.email} on {self.computer.label} [DISABLED]'

    def __eq__(self, other) -> bool:
        if not isinstance(other, AuthInfo):
            return False

        return (
            self.user.pk == other.user.pk
            and self.computer.pk == other.computer.pk
            and self.enabled == other.enabled
            and self.auth_params == other.auth_params
            and self.metadata == other.metadata
        )

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

    @property
    def auth_params(self) -> Dict[str, Any]:
        return self._backend_entity.get_auth_params()

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._backend_entity.get_metadata()

    def get_auth_params(self) -> Dict[str, Any]:
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """
        return self._backend_entity.get_auth_params()

    def set_auth_params(self, auth_params: Dict[str, Any]) -> None:
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """
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

        return transport_class(machine=computer.hostname, **self.get_auth_params())
