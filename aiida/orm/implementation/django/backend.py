# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django implementation of `aiida.orm.implementation.backends.Backend`."""
from contextlib import contextmanager
import functools
from typing import Any, ContextManager, List, Sequence

# pylint: disable=import-error,no-name-in-module
from django.apps import apps
from django.db import models
from django.db import transaction as django_transaction

from aiida.backends.djsite.db import models as dbm
from aiida.backends.djsite.manager import DjangoBackendManager
from aiida.common.exceptions import IntegrityError
from aiida.orm.entities import EntityTypes

from . import authinfos, comments, computers, convert, groups, logs, nodes, querybuilder, users
from ..sql.backends import SqlBackend

__all__ = ('DjangoBackend',)


class DjangoBackend(SqlBackend[models.Model]):
    """Django implementation of `aiida.orm.implementation.backends.Backend`."""

    def __init__(self):
        """Construct the backend instance by initializing all the collections."""
        self._authinfos = authinfos.DjangoAuthInfoCollection(self)
        self._comments = comments.DjangoCommentCollection(self)
        self._computers = computers.DjangoComputerCollection(self)
        self._groups = groups.DjangoGroupCollection(self)
        self._logs = logs.DjangoLogCollection(self)
        self._nodes = nodes.DjangoNodeCollection(self)
        self._backend_manager = DjangoBackendManager()
        self._users = users.DjangoUserCollection(self)

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
        return querybuilder.DjangoQueryBuilder(self)

    @property
    def users(self):
        return self._users

    @staticmethod
    def get_session():
        """Return a database session that can be used by the `QueryBuilder` to perform its query.

        If there is an exception within the context then the changes will be rolled back and the state will
        be as before entering.  Transactions can be nested.

        :return: an instance of :class:`sqlalchemy.orm.session.Session`
        """
        from aiida.backends.djsite import get_scoped_session
        return get_scoped_session()

    @staticmethod
    def transaction() -> ContextManager[Any]:
        """Open a transaction to be used as a context manager."""
        return django_transaction.atomic()

    @property
    def in_transaction(self) -> bool:
        return not django_transaction.get_autocommit()

    @staticmethod
    @functools.lru_cache(maxsize=18)
    def _get_model_from_entity(entity_type: EntityTypes, with_pk: bool):
        """Return the Django model and fields corresponding to the given entity.

        :param with_pk: if True, the fields returned will include the primary key
        """
        from sqlalchemy import inspect

        model = {
            EntityTypes.AUTHINFO: dbm.DbAuthInfo,
            EntityTypes.COMMENT: dbm.DbComment,
            EntityTypes.COMPUTER: dbm.DbComputer,
            EntityTypes.GROUP: dbm.DbGroup,
            EntityTypes.LOG: dbm.DbLog,
            EntityTypes.NODE: dbm.DbNode,
            EntityTypes.USER: dbm.DbUser,
            EntityTypes.LINK: dbm.DbLink,
            EntityTypes.GROUP_NODE:
            {model._meta.db_table: model for model in apps.get_models(include_auto_created=True)}['db_dbgroup_dbnodes']
        }[entity_type]
        mapper = inspect(model.sa).mapper  # here aldjemy provides us the SQLAlchemy model
        keys = {key for key, col in mapper.c.items() if with_pk or col not in mapper.primary_key}
        return model, keys

    def bulk_insert(self, entity_type: EntityTypes, rows: List[dict], allow_defaults: bool = False) -> List[int]:
        model, keys = self._get_model_from_entity(entity_type, False)
        if allow_defaults:
            for row in rows:
                if not keys.issuperset(row):
                    raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
        else:
            for row in rows:
                if set(row) != keys:
                    raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} != {keys}')
        objects = [model(**row) for row in rows]
        # if there is an mtime field, disable the automatic update, so as not to change it
        if entity_type in (EntityTypes.NODE, EntityTypes.COMMENT):
            with dbm.suppress_auto_now([(model, ['mtime'])]):
                model.objects.bulk_create(objects)
        else:
            model.objects.bulk_create(objects)
        return [obj.id for obj in objects]

    def bulk_update(self, entity_type: EntityTypes, rows: List[dict]) -> None:
        model, keys = self._get_model_from_entity(entity_type, True)
        id_entries = {}
        fields = None
        for row in rows:
            if not keys.issuperset(row):
                raise IntegrityError(f'Incorrect fields given for {entity_type}: {set(row)} not subset of {keys}')
            try:
                id_entries[row['id']] = {k: v for k, v in row.items() if k != 'id'}
                fields = fields or list(id_entries[row['id']])
                assert fields == list(id_entries[row['id']])
            except KeyError:
                raise IntegrityError(f"'id' field not given for {entity_type}: {set(row)}")
            except AssertionError:
                # this is handled in sqlalchemy, but would require more complex logic here
                raise NotImplementedError(f'Cannot bulk update {entity_type} with different fields')
        if fields is None:
            return
        objects = []
        for pk, obj in model.objects.in_bulk(list(id_entries), field_name='id').items():
            for name, value in id_entries[pk].items():
                setattr(obj, name, value)
            objects.append(obj)
        model.objects.bulk_update(objects, fields)

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]) -> None:
        if not self.in_transaction:
            raise AssertionError('Cannot delete nodes outside a transaction')
        # Delete all links pointing to or from a given node
        dbm.DbLink.objects.filter(models.Q(input__in=pks_to_delete) | models.Q(output__in=pks_to_delete)).delete()
        # now delete nodes
        dbm.DbNode.objects.filter(pk__in=pks_to_delete).delete()

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
        try:
            yield self._get_connection().cursor()
        finally:
            pass

    def execute_raw(self, query):
        """Execute a raw SQL statement and return the result.

        :param query: a string containing a raw SQL statement
        :return: the result of the query
        """
        with self.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        return results

    @staticmethod
    def _get_connection():
        """
        Get the Django connection

        :return: the django connection
        """
        # pylint: disable=import-error,no-name-in-module
        from django.db import connection

        # For now we just return the global but if we ever support multiple Django backends
        # being loaded this should be specific to this backend
        return connection
