# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SqlAlchemy implementation of `aiida.orm.implementation.backends.Backend`."""
from contextlib import contextmanager

from aiida.backends.sqlalchemy import get_scoped_session, reset_session
from aiida.backends.sqlalchemy.manager import SqlaBackendManager
from aiida.backends.sqlalchemy.models import base

from . import authinfos, comments, computers, convert, groups, logs, nodes, querybuilder, users
from ..sql.backends import SqlBackend

__all__ = ('SqlaBackend',)


class SqlaBackend(SqlBackend[base.Base]):
    """SqlAlchemy implementation of `aiida.orm.implementation.backends.Backend`."""

    def __init__(self):
        """Construct the backend instance by initializing all the collections."""
        super().__init__()
        self._authinfos = authinfos.SqlaAuthInfoCollection(self)
        self._comments = comments.SqlaCommentCollection(self)
        self._computers = computers.SqlaComputerCollection(self)
        self._groups = groups.SqlaGroupCollection(self)
        self._logs = logs.SqlaLogCollection(self)
        self._nodes = nodes.SqlaNodeCollection(self)
        self._backend_manager = SqlaBackendManager()
        self._users = users.SqlaUserCollection(self)

    @classmethod
    def load_environment(cls, profile, validate_schema=True, **kwargs):
        get_scoped_session(profile, **kwargs)
        if validate_schema:
            SqlaBackendManager().validate_schema(profile)

    def reset_environment(self):  # pylint: disable=no-self-use
        reset_session()

    def migrate(self):
        self._backend_manager.migrate()

    @property
    def authinfos(self):
        return self._authinfos

    @property
    def comments(self):
        return self._comments

    @property
    def computers(self):
        return self._computers

    @property
    def groups(self):
        return self._groups

    @property
    def logs(self):
        return self._logs

    @property
    def nodes(self):
        return self._nodes

    def query(self):
        return querybuilder.SqlaQueryBuilder(self)

    @property
    def users(self):
        return self._users

    @contextmanager
    def transaction(self):
        """Open a transaction to be used as a context manager.

        If there is an exception within the context then the changes will be rolled back and the state will be as before
        entering. Transactions can be nested.
        """
        session = self.get_session()
        if session.in_transaction():
            with session.begin_nested():
                yield session
        else:
            with session.begin():
                with session.begin_nested():
                    yield session

    @staticmethod
    def get_session():
        """Return a database session that can be used by the `QueryBuilder` to perform its query.

        :return: an instance of :class:`sqlalchemy.orm.session.Session`
        """
        return get_scoped_session()

    # Below are abstract methods inherited from `aiida.orm.implementation.sql.backends.SqlBackend`

    def get_backend_entity(self, model):
        """Return a `BackendEntity` instance from a `DbModel` instance."""
        return convert.get_backend_entity(model, self)

    @contextmanager
    def cursor(self):
        """Return a psycopg cursor to be used in a context manager.

        :return: a psycopg cursor
        :rtype: :class:`psycopg2.extensions.cursor`
        """
        from aiida.backends import sqlalchemy as sa
        try:
            connection = sa.ENGINE.raw_connection()
            yield connection.cursor()
        finally:
            self.get_connection().close()

    def execute_raw(self, query):
        """Execute a raw SQL statement and return the result.

        :param query: a string containing a raw SQL statement
        :return: the result of the query
        """
        from sqlalchemy import text
        from sqlalchemy.exc import ResourceClosedError  # pylint: disable=import-error,no-name-in-module

        with self.transaction() as session:
            queryset = session.execute(text(query))

            try:
                results = queryset.fetchall()
            except ResourceClosedError:
                return None

        return results

    @staticmethod
    def get_connection():
        """Get the SQLA database connection

        :return: the SQLA database connection
        """
        from aiida.backends import sqlalchemy as sa
        return sa.ENGINE.raw_connection()
