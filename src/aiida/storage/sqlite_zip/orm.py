###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N802
"""This module contains the AiiDA backend ORM classes for the SQLite backend.

It re-uses the classes already defined in ``psql_dos`` backend (for PostGresQL),
but redefines the SQLAlchemy models to the SQLite compatible ones.
"""

import json
from functools import singledispatch
from typing import Any, List, Optional, Tuple, Union

from sqlalchemy import JSON, case, func, select
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql import ColumnElement, null

from aiida.common.lang import type_check
from aiida.storage.psql_dos.orm import authinfos, comments, computers, entities, groups, logs, nodes, users, utils
from aiida.storage.psql_dos.orm.querybuilder.main import (
    BinaryExpression,
    Cast,
    ColumnClause,
    InstrumentedAttribute,
    Label,
    QueryableAttribute,
    SqlaQueryBuilder,
    String,
    get_column,
)
from aiida.storage.utils import _create_smarter_in_clause

from . import models
from .utils import ReadOnlyError


class SqliteEntityOverride:
    """Overrides type-checking of psql_dos ``Entity``."""

    MODEL_CLASS: Any
    _model: utils.ModelWrapper

    @classmethod
    def _class_check(cls):
        """Assert that the class is correctly configured"""
        assert issubclass(
            cls.MODEL_CLASS, models.SqliteBase
        ), 'Must set the MODEL_CLASS in the derived class to a SQLA model'

    @classmethod
    def from_dbmodel(cls, dbmodel, backend):
        """Create an AiiDA Entity from the corresponding SQLA ORM model and storage backend

        :param dbmodel: the SQLAlchemy model to create the entity from
        :param backend: the corresponding storage backend
        :return: the AiiDA entity
        """
        cls._class_check()
        type_check(dbmodel, cls.MODEL_CLASS)
        entity = cls.__new__(cls)
        super(entities.SqlaModelEntity, entity).__init__(backend)  # type: ignore
        entity._model = utils.ModelWrapper(dbmodel, backend)
        return entity

    def store(self, *args, **kwargs):
        backend = self._model._backend
        if backend.read_only:
            raise ReadOnlyError(f'Cannot store entity in read-only backend: {backend}')
        return super().store(*args, **kwargs)  # type: ignore


class SqliteUser(SqliteEntityOverride, users.SqlaUser):
    MODEL_CLASS = models.DbUser


class SqliteUserCollection(users.SqlaUserCollection):
    ENTITY_CLASS = SqliteUser


class SqliteComputer(SqliteEntityOverride, computers.SqlaComputer):
    MODEL_CLASS = models.DbComputer


class SqliteComputerCollection(computers.SqlaComputerCollection):
    ENTITY_CLASS = SqliteComputer


class SqliteAuthInfo(SqliteEntityOverride, authinfos.SqlaAuthInfo):
    MODEL_CLASS = models.DbAuthInfo
    USER_CLASS = SqliteUser
    COMPUTER_CLASS = SqliteComputer


class SqliteAuthInfoCollection(authinfos.SqlaAuthInfoCollection):
    ENTITY_CLASS = SqliteAuthInfo


class SqliteComment(SqliteEntityOverride, comments.SqlaComment):
    MODEL_CLASS = models.DbComment
    USER_CLASS = SqliteUser


class SqliteCommentCollection(comments.SqlaCommentCollection):
    ENTITY_CLASS = SqliteComment


class SqliteGroup(SqliteEntityOverride, groups.SqlaGroup):
    MODEL_CLASS = models.DbGroup
    USER_CLASS = SqliteUser


class SqliteGroupCollection(groups.SqlaGroupCollection):
    ENTITY_CLASS = SqliteGroup


class SqliteLog(SqliteEntityOverride, logs.SqlaLog):
    MODEL_CLASS = models.DbLog


class SqliteLogCollection(logs.SqlaLogCollection):
    ENTITY_CLASS = SqliteLog


class SqliteNode(SqliteEntityOverride, nodes.SqlaNode):
    """SQLA Node backend entity"""

    MODEL_CLASS = models.DbNode
    USER_CLASS = SqliteUser
    COMPUTER_CLASS = SqliteComputer
    LINK_CLASS = models.DbLink


class SqliteNodeCollection(nodes.SqlaNodeCollection):
    ENTITY_CLASS = SqliteNode


class SqliteQueryBuilder(SqlaQueryBuilder):
    """QueryBuilder to use with SQLAlchemy-backend, adapted for SQLite."""

    @property
    def Node(self):
        return models.DbNode

    @property
    def Link(self):
        return models.DbLink

    @property
    def Computer(self):
        return models.DbComputer

    @property
    def User(self):
        return models.DbUser

    @property
    def Group(self):
        return models.DbGroup

    @property
    def AuthInfo(self):
        return models.DbAuthInfo

    @property
    def Comment(self):
        return models.DbComment

    @property
    def Log(self):
        return models.DbLog

    @property
    def table_groups_nodes(self):
        return models.DbGroupNodes.__table__  # type: ignore[attr-defined]

    @staticmethod
    def _get_projectable_entity(
        alias: AliasedClass,
        column_name: str,
        attrpath: List[str],
        cast: Optional[str] = None,
    ) -> Union[ColumnElement, InstrumentedAttribute]:
        if not (attrpath or column_name in ('attributes', 'extras')):
            return get_column(column_name, alias)

        entity = get_column(column_name, alias)[attrpath]
        if cast is None:
            pass
        elif cast == 'f':
            entity = entity.as_float()
        elif cast == 'i':
            entity = entity.as_integer()
        elif cast == 'b':
            entity = entity.as_boolean()
        elif cast == 't':
            entity = entity.as_string()
        elif cast == 'j':
            entity = entity.as_json()
        elif cast == 'd':
            raise NotImplementedError('Date casting (d) for JSON key, not implemented for sqlite backend')
        else:
            raise ValueError(f'Unknown casting key {cast}')
        return entity

    def get_filter_expr_from_jsonb(
        self, operator: str, value, attr_key: List[str], column=None, column_name=None, alias=None
    ):
        """Return a filter expression.

        See: https://www.sqlite.org/json1.html
        """
        if column is None:
            column = get_column(column_name, alias)

        query_str = f'{alias or ""}.{column_name or ""}.{attr_key} {operator} {value}'

        def _cast_json_type(comparator: JSON.Comparator, value: Any) -> Tuple[ColumnElement, JSON.Comparator]:
            """Cast the JSON comparator to the target type."""
            if isinstance(value, bool):
                # SQLite booleans in JSON evaluate to 0/1, see:
                # https://dba.stackexchange.com/questions/287377/how-can-i-set-a-json-value-to-a-boolean-in-sqlite
                return func.json_type(comparator) == 'integer', comparator.as_boolean()
            if isinstance(value, int):
                return func.json_type(comparator).in_(['integer', 'real']), comparator.as_integer()
            if isinstance(value, float):
                return func.json_type(comparator).in_(['integer', 'real']), comparator.as_float()
            if isinstance(value, str):
                return func.json_type(comparator) == 'text', comparator.as_string()
            if isinstance(value, list):
                return func.json_type(comparator) == 'array', comparator.as_json()
            if isinstance(value, dict):
                return func.json_type(comparator) == 'object', comparator.as_json()
            raise TypeError(f'Unsupported type {type(value)} for SQLite query: {query_str}')

        database_entity: JSON.Comparator = column[tuple(attr_key)]

        if operator == '==':
            # to-do: non-existent keys also equate to json_type null, so should check it exists also
            # if value is None:
            #     return func.json_type(database_entity) == 'null'
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            if isinstance(value, (list, dict)):
                return case((type_filter, casted_entity == func.json(json.dumps(value))), else_=False)
            # to-do not working for dict
            return case((type_filter, casted_entity == value), else_=False)
        if operator == '>':
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            return case((type_filter, casted_entity > value), else_=False)
        if operator == '<':
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            return case((type_filter, casted_entity < value), else_=False)
        if operator in ('>=', '=>'):
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            return case((type_filter, casted_entity >= value), else_=False)
        if operator in ('<=', '=<'):
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            return case((type_filter, casted_entity <= value), else_=False)

        if operator == 'of_type':
            # convert from postgres types http://www.postgresql.org/docs/9.5/static/functions-json.html
            # for consistency with other backends
            valid_types = ('object', 'array', 'string', 'number', 'boolean', 'null')
            type_map = {'object': 'object', 'array': 'array', 'string': 'text', 'null': 'null'}
            if value in type_map:
                return func.json_type(database_entity) == type_map[value]
            if value == 'boolean':
                type_filter = func.json_type(database_entity) == 'integer'
                value_filter = database_entity.as_boolean().in_([True, False])
                return case((type_filter, value_filter <= value), else_=False)
            if value == 'number':
                return func.json_type(database_entity).in_(['integer', 'real'])
            raise ValueError(f'value {value!r} for `of_type` is not among valid types: {valid_types}')

        if operator == 'like':
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            return case((type_filter, casted_entity.like(value, escape='\\')), else_=False)
        if operator == 'ilike':
            type_filter, casted_entity = _cast_json_type(database_entity, value)
            return case((type_filter, casted_entity.ilike(value, escape='\\')), else_=False)

        if operator == 'contains':
            # If the operator is 'contains', we must mirror the behavior of the PostgreSQL
            # backend, which returns NULL if `attr_key` doesn't exist. To achieve this,
            # an additional CASE statement is added to directly return NULL in such cases.
            #
            # Instead of using `database_entity`, which would be interpreted as a 'null'
            # string in SQL, this approach ensures a proper NULL value is returned when
            # `attr_key` doesn't exist.
            #
            # Original implementation:
            #   return func.json_contains(database_entity, json.dumps(value))

            return case(
                (func.json_extract(column, '$.' + '.'.join(attr_key)).is_(null()), null()),
                else_=func.json_contains(database_entity, json.dumps(value)),
            )

        if operator == 'has_key':
            return (
                select(database_entity)
                .where(func.json_each(database_entity).table_valued('key', joins_implicitly=True).c.key == value)
                .exists()
            )

        if operator == 'in':
            type_filter, casted_entity = _cast_json_type(database_entity, value[0])
            return case(
                (
                    type_filter,
                    _create_smarter_in_clause(session=self.get_session(), column=casted_entity, values=value),
                ),
                else_=False,
            )

        if operator == 'of_length':
            return case(
                (
                    func.json_type(database_entity) == 'array',
                    func.json_array_length(database_entity.as_json()) == value,
                ),
                else_=False,
            )
        if operator == 'longer':
            return case(
                (
                    func.json_type(database_entity) == 'array',
                    func.json_array_length(database_entity.as_json()) > value,
                ),
                else_=False,
            )
        if operator == 'shorter':
            return case(
                (
                    func.json_type(database_entity) == 'array',
                    func.json_array_length(database_entity.as_json()) < value,
                ),
                else_=False,
            )

        raise ValueError(f'SQLite does not support JSON query: {query_str}')

    def get_filter_expr_from_column(self, operator: str, value: Any, column) -> BinaryExpression:
        # Label is used because it is what is returned for the
        # 'state' column by the hybrid_column construct
        if not isinstance(column, (Cast, InstrumentedAttribute, QueryableAttribute, Label, ColumnClause)):
            raise TypeError(f'column ({type(column)}) {column} is not a valid column')
        database_entity = column
        if operator == '==':
            expr = database_entity == value
        elif operator == '>':
            expr = database_entity > value
        elif operator == '<':
            expr = database_entity < value
        elif operator == '>=':
            expr = database_entity >= value
        elif operator == '<=':
            expr = database_entity <= value
        elif operator == 'like':
            # the like operator expects a string, so we cast to avoid problems
            # with fields like UUID, which don't support the like operator
            expr = database_entity.cast(String).like(value, escape='\\')
        elif operator == 'ilike':
            expr = database_entity.ilike(value, escape='\\')
        elif operator == 'in':
            expr = _create_smarter_in_clause(session=self.get_session(), column=column, values=value)
        else:
            raise ValueError(f'Unknown operator {operator} for filters on columns')
        return expr


@singledispatch
def get_backend_entity(dbmodel, backend):
    raise TypeError(f"No corresponding AiiDA backend class exists for the model class '{dbmodel.__class__.__name__}'")


@get_backend_entity.register(models.DbUser)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteUser.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbGroup)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteGroup.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbComputer)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteComputer.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbNode)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteNode.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbAuthInfo)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteAuthInfo.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbComment)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteComment.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbLog)  # type: ignore[call-overload]
def _(dbmodel, backend):
    return SqliteLog.from_dbmodel(dbmodel, backend)


@get_backend_entity.register(models.DbLink)  # type: ignore[call-overload]
def _(dbmodel, backend):
    from aiida.orm.utils.links import LinkQuadruple

    return LinkQuadruple(dbmodel.input_id, dbmodel.output_id, dbmodel.type, dbmodel.label)
