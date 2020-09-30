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

__all__ = ('Backend',)


class Backend(abc.ABC):
    """The public interface that defines a backend factory that creates backend specific concrete objects."""

    @abc.abstractmethod
    def migrate(self):
        """Migrate the database to the latest schema generation or version."""

    @abc.abstractproperty
    def authinfos(self):
        """
        Return the collection of authorisation information objects

        :return: the authinfo collection
        :rtype: :class:`aiida.orm.implementation.BackendAuthInfoCollection`
        """

    @abc.abstractproperty
    def comments(self):
        """
        Return the collection of comments

        :return: the comment collection
        :rtype: :class:`aiida.orm.implementation.BackendCommentCollection`
        """

    @abc.abstractproperty
    def computers(self):
        """
        Return the collection of computers

        :return: the computers collection
        :rtype: :class:`aiida.orm.implementation.BackendComputerCollection`
        """

    @abc.abstractproperty
    def groups(self):
        """
        Return the collection of groups

        :return: the groups collection
        :rtype: :class:`aiida.orm.implementation.BackendGroupCollection`
        """

    @abc.abstractproperty
    def logs(self):
        """
        Return the collection of logs

        :return: the log collection
        :rtype: :class:`aiida.orm.implementation.BackendLogCollection`
        """

    @abc.abstractproperty
    def nodes(self):
        """
        Return the collection of nodes

        :return: the nodes collection
        :rtype: :class:`aiida.orm.implementation.BackendNodeCollection`
        """

    @abc.abstractproperty
    def query_manager(self):
        """
        Return the query manager for the objects stored in the backend

        :return: The query manger
        :rtype: :class:`aiida.backends.general.abstractqueries.AbstractQueryManager`
        """

    @abc.abstractmethod
    def query(self):
        """
        Return an instance of a query builder implementation for this backend

        :return: a new query builder instance
        :rtype: :class:`aiida.orm.implementation.BackendQueryBuilder`
        """

    @abc.abstractproperty
    def users(self):
        """
        Return the collection of users

        :return: the users collection
        :rtype: :class:`aiida.orm.implementation.BackendUserCollection`
        """

    @abc.abstractmethod
    def transaction(self):
        """
        Get a context manager that can be used as a transaction context for a series of backend operations.
        If there is an exception within the context then the changes will be rolled back and the state will
        be as before entering.  Transactions can be nested.

        :return: a context manager to group database operations
        """

    @abc.abstractmethod
    def get_session(self):
        """Return a database session that can be used by the `QueryBuilder` to perform its query.

        :return: an instance of :class:`sqlalchemy.orm.session.Session`
        """
