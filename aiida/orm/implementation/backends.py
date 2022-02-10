# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic backend related objects"""
import abc
from typing import TYPE_CHECKING, Any, ContextManager, List, Optional, Sequence, TypeVar, Union

if TYPE_CHECKING:
    from aiida.manage.configuration.profile import Profile
    from aiida.orm.autogroup import AutogroupManager
    from aiida.orm.entities import EntityTypes
    from aiida.orm.implementation import (
        BackendAuthInfoCollection,
        BackendCommentCollection,
        BackendComputerCollection,
        BackendGroupCollection,
        BackendLogCollection,
        BackendNodeCollection,
        BackendQueryBuilder,
        BackendUserCollection,
    )
    from aiida.repository.backend.abstract import AbstractRepositoryBackend

__all__ = ('Backend',)

TransactionType = TypeVar('TransactionType')


class Backend(abc.ABC):  # pylint: disable=too-many-public-methods
    """Abstraction for a backend to read/write persistent data for a profile's provenance graph.

    AiiDA splits data storage into two sources:

    - Searchable data, which is stored in the database and can be queried using the QueryBuilder
    - Non-searchable (binary) data, which is stored in the repository and can be loaded using the RepositoryBackend

    The two sources are inter-linked by the ``Node.repository_metadata``.
    Once stored, the leaf values of this dictionary must be valid pointers to object keys in the repository.

    The class methods,`version_profile` and `migrate`,
    should be able to be called for existing storage, at any supported schema version (or empty storage).
    But an instance of this class should be created only for the latest schema version.

    """

    @classmethod
    @abc.abstractmethod
    def version_head(cls) -> str:
        """Return the head schema version of this storage backend type."""

    @classmethod
    @abc.abstractmethod
    def version_profile(cls, profile: 'Profile') -> Optional[str]:
        """Return the schema version of the given profile's storage, or None for empty/uninitialised storage.

        :raises: `~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed
        """

    @classmethod
    @abc.abstractmethod
    def migrate(cls, profile: 'Profile') -> None:
        """Migrate the storage of a profile to the latest schema version.

        If the schema version is already the latest version, this method does nothing.
        If the storage is empty/uninitialised, then it will be initialised at head.

        :raises: `~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed
        """

    @abc.abstractmethod
    def __init__(self, profile: 'Profile') -> None:
        """Initialize the backend, for this profile.

        :raises: `~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed
        :raises: `~aiida.common.exceptions.IncompatibleStorageSchema`
            if the profile's storage schema is not at the latest version (and thus should be migrated)
        :raises: :raises: :class:`aiida.common.exceptions.CorruptStorage` if the storage is internally inconsistent
        """
        from aiida.orm.autogroup import AutogroupManager
        self._profile = profile
        self._autogroup = AutogroupManager(self)

    @abc.abstractmethod
    def __str__(self) -> str:
        """Return a string showing connection details for this instance."""

    @property
    def profile(self) -> 'Profile':
        """Return the profile for this backend."""
        return self._profile

    @property
    def autogroup(self) -> 'AutogroupManager':
        """Return the autogroup manager for this backend."""
        return self._autogroup

    def version(self) -> str:
        """Return the schema version of the profile's storage."""
        version = self.version_profile(self.profile)
        assert version is not None
        return version

    @abc.abstractmethod
    def close(self):
        """Close the storage access."""

    @property
    @abc.abstractmethod
    def is_closed(self) -> bool:
        """Return whether the storage is closed."""

    @abc.abstractmethod
    def _clear(self, recreate_user: bool = True) -> None:
        """Clear the storage, removing all data.

        .. warning:: This is a destructive operation, and should only be used for testing purposes.

        :param recreate_user: Re-create the default `User` for the profile, after clearing the storage.
        """
        from aiida.orm.autogroup import AutogroupManager
        self._autogroup = AutogroupManager(self)

    @property
    @abc.abstractmethod
    def authinfos(self) -> 'BackendAuthInfoCollection':
        """Return the collection of authorisation information objects"""

    @property
    @abc.abstractmethod
    def comments(self) -> 'BackendCommentCollection':
        """Return the collection of comments"""

    @property
    @abc.abstractmethod
    def computers(self) -> 'BackendComputerCollection':
        """Return the collection of computers"""

    @property
    @abc.abstractmethod
    def groups(self) -> 'BackendGroupCollection':
        """Return the collection of groups"""

    @property
    @abc.abstractmethod
    def logs(self) -> 'BackendLogCollection':
        """Return the collection of logs"""

    @property
    @abc.abstractmethod
    def nodes(self) -> 'BackendNodeCollection':
        """Return the collection of nodes"""

    @property
    @abc.abstractmethod
    def users(self) -> 'BackendUserCollection':
        """Return the collection of users"""

    @abc.abstractmethod
    def query(self) -> 'BackendQueryBuilder':
        """Return an instance of a query builder implementation for this backend"""

    @abc.abstractmethod
    def transaction(self) -> ContextManager[Any]:
        """
        Get a context manager that can be used as a transaction context for a series of backend operations.
        If there is an exception within the context then the changes will be rolled back and the state will
        be as before entering.  Transactions can be nested.

        :return: a context manager to group database operations
        """

    @property
    @abc.abstractmethod
    def in_transaction(self) -> bool:
        """Return whether a transaction is currently active."""

    @abc.abstractmethod
    def bulk_insert(self, entity_type: 'EntityTypes', rows: List[dict], allow_defaults: bool = False) -> List[int]:
        """Insert a list of entities into the database, directly into a backend transaction.

        :param entity_type: The type of the entity
        :param data: A list of dictionaries, containing all fields of the backend model,
            except the `id` field (a.k.a primary key), which will be generated dynamically
        :param allow_defaults: If ``False``, assert that each row contains all fields (except primary key(s)),
            otherwise, allow default values for missing fields.

        :raises: ``IntegrityError`` if the keys in a row are not a subset of the columns in the table

        :returns: The list of generated primary keys for the entities
        """

    @abc.abstractmethod
    def bulk_update(self, entity_type: 'EntityTypes', rows: List[dict]) -> None:
        """Update a list of entities in the database, directly with a backend transaction.

        :param entity_type: The type of the entity
        :param data: A list of dictionaries, containing fields of the backend model to update,
            and the `id` field (a.k.a primary key)

        :raises: ``IntegrityError`` if the keys in a row are not a subset of the columns in the table
        """

    @abc.abstractmethod
    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]):
        """Delete all nodes corresponding to pks in the input and any links to/from them.

        This method is intended to be used within a transaction context.

        :param pks_to_delete: a sequence of node pks to delete

        :raises: ``AssertionError`` if a transaction is not active
        """

    @abc.abstractmethod
    def get_repository(self) -> 'AbstractRepositoryBackend':
        """Return the object repository configured for this backend."""

    @abc.abstractmethod
    def set_global_variable(
        self, key: str, value: Union[None, str, int, float], description: Optional[str] = None, overwrite=True
    ) -> None:
        """Set a global variable in the storage.

        :param key: the key of the setting
        :param value: the value of the setting
        :param description: the description of the setting (optional)
        :param overwrite: if True, overwrite the setting if it already exists

        :raises: `ValueError` if the key already exists and `overwrite` is False
        """

    @abc.abstractmethod
    def get_global_variable(self, key: str) -> Union[None, str, int, float]:
        """Return a global variable from the storage.

        :param key: the key of the setting

        :raises: `KeyError` if the setting does not exist
        """
