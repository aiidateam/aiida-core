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
from contextlib import contextmanager, nullcontext
import functools
from typing import Iterator, List, Sequence

from sqlalchemy.orm import Session

from aiida.backends.sqlalchemy.manager import SqlaBackendManager
from aiida.backends.sqlalchemy.models import base
from aiida.common.exceptions import IntegrityError
from aiida.orm.entities import EntityTypes

from . import authinfos, comments, computers, convert, groups, logs, nodes, querybuilder, users
from ..sql.backends import SqlBackend

__all__ = ('SqlaBackend',)


class SqlaBackend(SqlBackend[base.Base]):
    """SqlAlchemy implementation of `aiida.orm.implementation.backends.Backend`."""

    def __init__(self, profile, validate_db: bool = True):  # pylint: disable=missing-function-docstring
        super().__init__(profile, validate_db)
        self._authinfos = authinfos.SqlaAuthInfoCollection(self)
        self._comments = comments.SqlaCommentCollection(self)
        self._computers = computers.SqlaComputerCollection(self)
        self._groups = groups.SqlaGroupCollection(self)
        self._logs = logs.SqlaLogCollection(self)
        self._nodes = nodes.SqlaNodeCollection(self)
        self._backend_manager = SqlaBackendManager(self)
        self._users = users.SqlaUserCollection(self)

        if validate_db:
            self.get_session()  # ensure that the database is accessible
            self._backend_manager.validate_schema(profile)

    @property
    def backend_manager(self):
        return self._backend_manager

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
    def transaction(self) -> Iterator[Session]:
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

    @property
    def in_transaction(self) -> bool:
        return self.get_session().in_nested_transaction()

    @staticmethod
    @functools.lru_cache(maxsize=18)
    def _get_mapper_from_entity(entity_type: EntityTypes, with_pk: bool):
        """Return the Sqlalchemy mapper and fields corresponding to the given entity.

        :param with_pk: if True, the fields returned will include the primary key
        """
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

    def bulk_insert(self, entity_type: EntityTypes, rows: List[dict], allow_defaults: bool = False) -> List[int]:
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
        session = self.get_session()
        with (nullcontext() if self.in_transaction else self.transaction()):  # type: ignore[attr-defined]
            session.bulk_insert_mappings(mapper, rows, render_nulls=True, return_defaults=True)
        return [row['id'] for row in rows]

    def bulk_update(self, entity_type: EntityTypes, rows: List[dict]) -> None:  # pylint: disable=no-self-use
        mapper, keys = self._get_mapper_from_entity(entity_type, True)
        if not rows:
            return None
        for row in rows:
            if 'id' not in row:
                raise IntegrityError(f"'id' field not given for {entity_type}: {set(row)}")
            if not keys.issuperset(row):
                raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        session = self.get_session()
        with (nullcontext() if self.in_transaction else self.transaction()):  # type: ignore[attr-defined]
            session.bulk_update_mappings(mapper, rows)

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]) -> None:  # pylint: disable=no-self-use
        # pylint: disable=no-value-for-parameter
        from aiida.backends.sqlalchemy.models.group import DbGroupNode
        from aiida.backends.sqlalchemy.models.node import DbLink, DbNode

        if not self.in_transaction:
            raise AssertionError('Cannot delete nodes and links outside a transaction')

        session = self.get_session()
        # Delete the membership of these nodes to groups.
        session.query(DbGroupNode).filter(DbGroupNode.dbnode_id.in_(list(pks_to_delete))
                                          ).delete(synchronize_session='fetch')
        # Delete the links coming out of the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.input_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Delete the links pointing to the nodes marked for deletion.
        session.query(DbLink).filter(DbLink.output_id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')
        # Delete the actual nodes
        session.query(DbNode).filter(DbNode.id.in_(list(pks_to_delete))).delete(synchronize_session='fetch')

    # Below are abstract methods inherited from `aiida.orm.implementation.sql.backends.SqlBackend`

    def get_backend_entity(self, model):
        return convert.get_backend_entity(model, self)

    @contextmanager
    def cursor(self):
        try:
            connection = self.get_session().bind.raw_connection()
            yield connection.cursor()
        finally:
            self._get_connection().close()

    def execute_raw(self, query):
        from sqlalchemy import text
        from sqlalchemy.exc import ResourceClosedError  # pylint: disable=import-error,no-name-in-module

        with self.transaction() as session:
            queryset = session.execute(text(query))

            try:
                results = queryset.fetchall()
            except ResourceClosedError:
                return None

        return results

    def _get_connection(self):
        """Get the SQLA database connection

        :return: the raw SQLA database connection
        """
        return self.get_session().bind.raw_connection()
