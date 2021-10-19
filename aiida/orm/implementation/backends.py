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
from typing import TYPE_CHECKING, Any, ContextManager, List, Sequence
import weakref

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session

    from aiida.manage.configuration import Profile
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

    BackendCacheType = weakref.WeakValueDictionary[int, 'Backend']  # pylint: disable=unsubscriptable-object

__all__ = ('Backend',)

_backends: 'BackendCacheType' = weakref.WeakValueDictionary()
"""Weak-referencing dictionary of loaded Backends.
"""


def close_all_backends():
    """Close all loaded backends.

    This function is not for general use but may be useful for test suites
    within the teardown scheme.
    """
    for backend in _backends.values():
        backend.close()


class Backend(abc.ABC):
    """Abstraction for a backend to read/write persistent data for a profile's provenance graph."""

    def __init__(self, profile: 'Profile', validate_db: bool = True) -> None:  # pylint: disable=unused-argument
        """Instatiate the backend.

        :param profile: the profile provides the configuration details for connecting to the persistent storage
        :param validate_db: if True, the backend will perform validation tests on the database consistency
        """
        self._profile = profile
        self._hashkey = 1 if not _backends else max(_backends.keys()) + 1
        _backends[self._hashkey] = self

    @property
    def profile(self) -> 'Profile':
        """Return the profile used to initialize the backend."""
        return self._profile

    @abc.abstractmethod
    def close(self) -> None:
        """Close the backend.

        This method is called when the backend is no longer needed,
        and should be used to close any open connections to the persistent storage
        """

    @abc.abstractmethod
    def reset(self, **kwargs) -> None:
        """Reset the backend.

        This method should reset any open connections to the persistent storage
        """

    @abc.abstractmethod
    def migrate(self) -> None:
        """Migrate the persistent storage to the latest schema generation or version."""

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
    def get_session(self) -> 'Session':
        """Return a database session that can be used by the `QueryBuilder` to perform its query.

        :return: an instance of :class:`sqlalchemy.orm.session.Session`
        """

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
