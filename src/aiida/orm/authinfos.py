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

import typing as t

from aiida.common import exceptions
from aiida.manage import get_manager
from aiida.orm import entities, users
from aiida.orm.computers import Computer
from aiida.orm.decorators import column
from aiida.orm.models.adapters import EntityPkAdapter
from aiida.orm.users import User
from aiida.plugins import TransportFactory

if t.TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.authinfos import BackendAuthInfo
    from aiida.transports import Transport

__all__ = ('AuthInfo',)


class AuthInfoCollection(entities.EntityCollection['AuthInfo']):
    """The collection of `AuthInfo` entries."""

    collection_type: t.ClassVar[str] = 'authinfos'

    def delete(self, pk: int) -> None:
        """Delete an entry from the collection.

        :param pk: the pk of the entry to delete
        """
        self._backend.authinfos.delete(pk)

    @staticmethod
    def _entity_base_cls() -> type[AuthInfo]:
        return AuthInfo


class AuthInfo(entities.Entity['BackendAuthInfo', AuthInfoCollection]):
    """ORM class that models the authorization information that allows a `User` to connect to a `Computer`."""

    _CLS_COLLECTION = AuthInfoCollection
    PROPERTY_WORKDIR = 'workdir'

    def __init__(
        self,
        computer: Computer,
        user: User,
        enabled: bool = True,
        auth_params: dict[str, t.Any] | None = None,
        metadata: dict[str, t.Any] | None = None,
        backend: StorageBackend | None = None,
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

    @column
    def enabled(self) -> bool:
        """Whether this instance is enabled."""
        return self._backend_entity.enabled

    @enabled.setter
    def enabled(self, enabled: bool) -> None:
        """The enabled state of this instance."""
        self._backend_entity.enabled = enabled

    @column(
        model_adapter=EntityPkAdapter(Computer),
    )
    def computer(self) -> Computer:
        """The computer associated with this instance."""
        from aiida.orm import computers

        return entities.from_backend_entity(computers.Computer, self._backend_entity.computer)

    @column(
        model_adapter=EntityPkAdapter(User),
    )
    def user(self) -> User:
        """The user associated with this instance."""
        return entities.from_backend_entity(users.User, self._backend_entity.user)

    @column
    def auth_params(self) -> dict[str, t.Any]:
        """The dictionary of authentication parameters."""
        return self._backend_entity.get_auth_params()

    @column
    def metadata(self) -> dict[str, t.Any]:
        """The dictionary of metadata."""
        return self._backend_entity.get_metadata()

    def get_auth_params(self) -> dict[str, t.Any]:
        """Return the dictionary of authentication parameters

        :return: a dictionary with authentication parameters
        """
        return self._backend_entity.get_auth_params()

    def set_auth_params(self, auth_params: dict[str, t.Any]) -> None:
        """Set the dictionary of authentication parameters

        :param auth_params: a dictionary with authentication parameters
        """
        self._backend_entity.set_auth_params(auth_params)

    def get_metadata(self) -> dict[str, t.Any]:
        """Return the dictionary of metadata

        :return: a dictionary with metadata
        """
        return self._backend_entity.get_metadata()

    def set_metadata(self, metadata: dict[str, t.Any]) -> None:
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

    def get_transport(self) -> Transport:
        """Return a fully configured transport that can be used to connect to the computer set for this instance."""
        computer = self.computer
        transport_type = computer.transport_type

        try:
            transport_class = TransportFactory(transport_type)
        except exceptions.EntryPointError as exception:
            msg = f'transport type `{transport_type}` could not be loaded: {exception}'
            raise exceptions.ConfigurationError(msg)

        return transport_class(machine=computer.hostname, **self.get_auth_params())
