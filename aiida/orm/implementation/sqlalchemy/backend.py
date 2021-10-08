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
# pylint: disable=missing-function-docstring
from contextlib import contextmanager
import functools
from typing import Any, List

from aiida.backends.sqlalchemy.manager import SqlaBackendManager
from aiida.backends.sqlalchemy.models import base
from aiida.common.exceptions import IntegrityError
from aiida.orm.entities import EntityTypes

from . import authinfos, comments, computers, convert, groups, logs, nodes, querybuilder, users
from ..sql.backends import SqlBackend

__all__ = ('SqlaBackend',)


class SqlaBackend(SqlBackend[base.Base]):
    """SqlAlchemy implementation of `aiida.orm.implementation.backends.Backend`."""

    def __init__(self):
        """Construct the backend instance by initializing all the collections."""
        self._authinfos = authinfos.SqlaAuthInfoCollection(self)
        self._comments = comments.SqlaCommentCollection(self)
        self._computers = computers.SqlaComputerCollection(self)
        self._groups = groups.SqlaGroupCollection(self)
        self._logs = logs.SqlaLogCollection(self)
        self._nodes = nodes.SqlaNodeCollection(self)
        self._schema_manager = SqlaBackendManager()
        self._users = users.SqlaUserCollection(self)

    def migrate(self):
        self._schema_manager.migrate()

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
            session.commit()
        else:
            with session.begin():
                with session.begin_nested():
                    yield session

    @staticmethod
    @functools.lru_cache(maxsize=18)
    def _get_mapper_from_entity(entity_type: EntityTypes, with_pk: bool):
        """Return the Sqlalchemy mapper and non-primary keys corresponding to the given entity."""
        from sqlalchemy import inspect

        from aiida.backends.sqlalchemy.models.authinfo import DbAuthInfo
        from aiida.backends.sqlalchemy.models.comment import DbComment
        from aiida.backends.sqlalchemy.models.computer import DbComputer
        from aiida.backends.sqlalchemy.models.group import DbGroup, DbGroupNode
        from aiida.backends.sqlalchemy.models.log import DbLog
        from aiida.backends.sqlalchemy.models.node import DbLink, DbNode
        from aiida.backends.sqlalchemy.models.user import DbUser
        model = {
            EntityTypes.AUTHINFO: DbAuthInfo,
            EntityTypes.COMMENT: DbComment,
            EntityTypes.COMPUTER: DbComputer,
            EntityTypes.GROUP: DbGroup,
            EntityTypes.LOG: DbLog,
            EntityTypes.NODE: DbNode,
            EntityTypes.USER: DbUser,
            EntityTypes.LINK: DbLink,
            EntityTypes.GROUP_NODE: DbGroupNode,
        }[entity_type]
        mapper = inspect(model).mapper
        keys = {key for key, col in mapper.c.items() if with_pk or col not in mapper.primary_key}
        return mapper, keys

    def bulk_insert(self,
                    entity_type: EntityTypes,
                    rows: List[dict],
                    transaction: Any,
                    allow_defaults: bool = False) -> List[int]:
        mapper, keys = self._get_mapper_from_entity(entity_type, False)
        if not rows:
            return []
        if entity_type in (EntityTypes.COMPUTER, EntityTypes.LOG):
            for row in rows:
                row['_metadata'] = row.pop('metadata')
        if allow_defaults:
            for row in rows:
                if not keys.issuperset(row):
                    raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        else:
            for row in rows:
                if set(row) != keys:
                    raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} != {keys}')
        # note for postgresql+psycopg2 we could also use `save_all` + `flush` with minimal performance degradation, see
        # https://docs.sqlalchemy.org/en/14/changelog/migration_14.html#orm-batch-inserts-with-psycopg2-now-batch-statements-with-returning-in-most-cases
        # by contrast, in sqlite, bulk_insert is faster: https://docs.sqlalchemy.org/en/14/faq/performance.html
        transaction.bulk_insert_mappings(mapper, rows, render_nulls=True, return_defaults=True)
        return [row['id'] for row in rows]

    def bulk_update(self, entity_type: EntityTypes, rows: List[dict], transaction: Any) -> None:
        mapper, keys = self._get_mapper_from_entity(entity_type, True)
        if not rows:
            return None
        for row in rows:
            if 'id' not in row:
                raise IntegrityError(f"'id' field not given for {entity_type}: {set(row)}")
            if not keys.issuperset(row):
                raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        transaction.bulk_update_mappings(mapper, rows)

    @staticmethod
    def get_session():
        """Return a database session that can be used by the `QueryBuilder` to perform its query.

        :return: an instance of :class:`sqlalchemy.orm.session.Session`
        """
        from aiida.backends.sqlalchemy import get_scoped_session
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
