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
from typing import TYPE_CHECKING
import weakref

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session

    from aiida.manage.configuration import Profile
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

__all__ = ('Backend',)

_backends = weakref.WeakValueDictionary()
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
    def migrate(self):
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

    @abc.abstractmethod
    def query(self) -> 'BackendQueryBuilder':
        """Return an instance of a query builder implementation for this backend"""

    @property
    @abc.abstractmethod
    def users(self) -> 'BackendUserCollection':
        """Return the collection of users"""

    @abc.abstractmethod
    def transaction(self):
        """
        Get a context manager that can be used as a transaction context for a series of backend operations.
        If there is an exception within the context then the changes will be rolled back and the state will
        be as before entering.  Transactions can be nested.

        :return: a context manager to group database operations
        """

    @abc.abstractmethod
    def get_session(self) -> 'Session':
        """Return a database session that can be used by the `QueryBuilder` to perform its query.

        :return: an instance of :class:`sqlalchemy.orm.session.Session`
        """
