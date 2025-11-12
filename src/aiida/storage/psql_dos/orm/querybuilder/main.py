###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N802
"""Sqla query builder implementation"""

from __future__ import annotations

import uuid
import warnings
from collections.abc import Iterable, Iterator
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import and_, not_, or_, select
from sqlalchemy import func as sa_func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Row
from sqlalchemy.exc import CompileError, SAWarning
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.elements import BinaryExpression, Cast, ColumnClause, ColumnElement, Label
from sqlalchemy.sql.expression import case, text
from sqlalchemy.types import Boolean, DateTime, Float, Integer, String

from aiida.common.exceptions import NotExistent
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation.querybuilder import QUERYBUILD_LOGGER, BackendQueryBuilder, QueryDictType

from .joiner import JoinReturn, SqlaJoiner

jsonb_typeof = sa_func.jsonb_typeof
jsonb_array_length = sa_func.jsonb_array_length
array_length = sa_func.array_length

PROJECT_MAP = {
    'db_dbauthinfo': {
        'pk': 'id',
        'computer_pk': 'dbcomputer_id',
        'user_pk': 'aiidauser_id',
    },
    'db_dbnode': {
        'pk': 'id',
        'computer_pk': 'dbcomputer_id',
        'user_pk': 'user_id',
    },
    'db_dbcomputer': {
        'pk': 'id',
    },
    'db_dbgroup': {
        'pk': 'id',
        'user_pk': 'user_id',
    },
    'db_dbcomment': {
        'pk': 'id',
        'user_pk': 'user_id',
        'node_pk': 'dbnode_id',
    },
    'db_dblog': {
        'pk': 'id',
        'node_pk': 'dbnode_id',
    },
}


@dataclass
class BuiltQuery:
    """A class to store the query and the corresponding projections."""

    query: Query
    tag_to_alias: Dict[str, Optional[AliasedClass]]
    tag_to_projected: Dict[str, Dict[str, int]]


class SqlaQueryBuilder(BackendQueryBuilder):
    """QueryBuilder to use with SQLAlchemy-backend and
    schema defined in backends.sqlalchemy.models
    """

    def __init__(self, backend):
        super().__init__(backend)

        self._joiner = SqlaJoiner(self, self.build_filters)

        # Set conversions between the field names in the database and used by the `QueryBuilder`
        # table -> field -> field
        self.inner_to_outer_schema: Dict[str, Dict[str, str]] = {
            'db_dbauthinfo': {'_metadata': 'metadata'},
            'db_dbcomputer': {'_metadata': 'metadata'},
            'db_dblog': {'_metadata': 'metadata'},
        }
        self.outer_to_inner_schema: Dict[str, Dict[str, str]] = {
            'db_dbauthinfo': {'metadata': '_metadata'},
            'db_dbcomputer': {'metadata': '_metadata'},
            'db_dblog': {'metadata': '_metadata'},
        }

        # data generated from front-end
        self._data: QueryDictType = {
            'path': [],
            'filters': {},
            'project': {},
            'project_map': {},
            'order_by': [],
            'offset': None,
            'limit': None,
            'distinct': False,
        }

        # Hashing the internal query representation avoids rebuilding a query
        self._query_cache: Optional[BuiltQuery] = None
        self._query_hash: Optional[str] = None

    @property
    def Node(self):
        import aiida.storage.psql_dos.models.node

        return aiida.storage.psql_dos.models.node.DbNode

    @property
    def Link(self):
        import aiida.storage.psql_dos.models.node

        return aiida.storage.psql_dos.models.node.DbLink

    @property
    def Computer(self):
        import aiida.storage.psql_dos.models.computer

        return aiida.storage.psql_dos.models.computer.DbComputer

    @property
    def User(self):
        import aiida.storage.psql_dos.models.user

        return aiida.storage.psql_dos.models.user.DbUser

    @property
    def Group(self):
        import aiida.storage.psql_dos.models.group

        return aiida.storage.psql_dos.models.group.DbGroup

    @property
    def AuthInfo(self):
        import aiida.storage.psql_dos.models.authinfo

        return aiida.storage.psql_dos.models.authinfo.DbAuthInfo

    @property
    def Comment(self):
        import aiida.storage.psql_dos.models.comment

        return aiida.storage.psql_dos.models.comment.DbComment

    @property
    def Log(self):
        import aiida.storage.psql_dos.models.log

        return aiida.storage.psql_dos.models.log.DbLog

    @property
    def table_groups_nodes(self):
        import aiida.storage.psql_dos.models.group

        return aiida.storage.psql_dos.models.group.table_groups_nodes

    def get_session(self) -> Session:
        """Get the connection to the database"""
        return self._backend.get_session()  # type: ignore[attr-defined]

    def count(self, data: QueryDictType) -> int:
        with self.query_session(data) as build:
            result = build.query.count()
        return result

    def first(self, data: QueryDictType) -> Optional[List[Any]]:
        with self.query_session(data) as build:
            result = build.query.first()

        if result is None:
            return result

        # SQLA will return a Row, if only certain columns are requested,
        # or a database model if that is requested
        if not isinstance(result, Row):
            result = (result,)

        return [self.to_backend(r) for r in result]

    def iterall(self, data: QueryDictType, batch_size: Optional[int]) -> Iterable[List[Any]]:
        """Return an iterator over all the results of a list of lists."""
        with self.query_session(data) as build:
            stmt = build.query.statement.execution_options(yield_per=batch_size)
            session = self.get_session()

            # Open a session transaction unless already inside one. This prevents the `ModelWrapper` from calling commit
            # on the session when a yielded row is mutated. This would reset the cursor invalidating it and causing an
            # exception to be raised in the next batch of rows in the iteration.
            with nullcontext() if session.in_nested_transaction() else self._backend.transaction():
                for resultrow in session.execute(stmt):
                    yield [self.to_backend(rowitem) for rowitem in resultrow]

    def iterdict(self, data: QueryDictType, batch_size: Optional[int]) -> Iterable[Dict[str, Dict[str, Any]]]:
        """Return an iterator over all the results of a list of dictionaries."""
        with self.query_session(data) as build:
            stmt = build.query.statement.execution_options(yield_per=batch_size)
            session = self.get_session()

            # Open a session transaction unless already inside one. This prevents the `ModelWrapper` from calling commit
            # on the session when a yielded row is mutated. This would reset the cursor invalidating it and causing an
            # exception to be raised in the next batch of rows in the iteration.
            with nullcontext() if session.in_nested_transaction() else self._backend.transaction():
                for row in self.get_session().execute(stmt):
                    # build the yield result
                    yield_result: Dict[str, Dict[str, Any]] = {}
                    for (
                        tag,
                        projected_entities_dict,
                    ) in build.tag_to_projected.items():
                        yield_result[tag] = {}
                        for attrkey, project_index in projected_entities_dict.items():
                            alias = build.tag_to_alias.get(tag)
                            if alias is None:
                                raise ValueError(f'No alias found for tag {tag}')
                            field_name = get_corresponding_property(
                                get_table_name(alias),
                                attrkey,
                                self.inner_to_outer_schema,
                            )
                            key = self._data['project_map'].get(tag, {}).get(field_name, field_name)
                            yield_result[tag][key] = self.to_backend(row[project_index])
                    yield yield_result

    def get_query(self, data: QueryDictType) -> BuiltQuery:
        """Return the built query.

        To avoid unnecessary re-builds of the query, the hashed dictionary representation of this instance
        is compared to the last query returned, which is cached by its hash.
        """
        from aiida.common.hashing import make_hash

        query_hash = make_hash(data)

        if not (self._query_cache and self._query_hash and self._query_hash == query_hash):
            self._query_cache = self._build(data)
            self._query_hash = query_hash

        return self._query_cache

    @contextmanager
    def query_session(self, data: QueryDictType) -> Iterator[BuiltQuery]:
        """Yield the built query, ensuring the session is closed on an exception."""
        query = self.get_query(data)
        try:
            yield query
        except Exception:
            self.get_session().close()
            raise

    def _build(self, data: QueryDictType) -> BuiltQuery:
        """Build the query and return."""
        # generate aliases for tags
        tag_to_alias: Dict[str, Optional[AliasedClass]] = {}
        cls_map = {
            EntityTypes.AUTHINFO.value: self.AuthInfo,
            EntityTypes.COMMENT.value: self.Comment,
            EntityTypes.COMPUTER.value: self.Computer,
            EntityTypes.GROUP.value: self.Group,
            EntityTypes.NODE.value: self.Node,
            EntityTypes.LOG.value: self.Log,
            EntityTypes.USER.value: self.User,
            EntityTypes.LINK.value: self.Link,
        }
        for path in data['path']:
            # An SAWarning warning is currently emitted:
            # "relationship 'DbNode.input_links' will copy column db_dbnode.id to column db_dblink.output_id,
            # which conflicts with relationship(s): 'DbNode.outputs' (copies db_dbnode.id to db_dblink.output_id)"
            # This should be eventually fixed
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=SAWarning)
                tag_to_alias[path['tag']] = aliased(cls_map[path['orm_base']])

        # now create joins first, so we can populate edge tag aliases
        joins = generate_joins(data, tag_to_alias, self._joiner)
        for join in joins:
            if join.aliased_edge is not None:
                tag_to_alias[join.edge_tag] = join.aliased_edge

        # generate the projections
        projections, tag_to_projected = generate_projections(
            data, tag_to_alias, self.outer_to_inner_schema, self._get_projectable_entity
        )

        # initialise the query
        query = self.get_session().query()
        # add the projections
        for projection, is_entity in projections:
            if is_entity:
                query = query.add_entity(projection)
            else:
                query = query.add_columns(projection)
        # and the starting table, from which joins will be made
        starting_table = tag_to_alias.get(data['path'][0]['tag'])
        if starting_table is None:
            raise ValueError('starting tag not found')
        query = query.select_from(starting_table)

        # add the joins
        for join in joins:
            query = join.join(query)

        # add the filters
        for tag, filter_specs in data['filters'].items():
            if not filter_specs:
                continue
            alias = tag_to_alias.get(tag)
            if not alias:
                raise ValueError(f'Unknown tag {tag!r} in filters, known: {list(tag_to_alias)}')
            filters = self.build_filters(alias, filter_specs)
            if filters is not None:
                query = query.filter(filters)

        # set the ordering
        for order_spec in data['order_by']:
            for tag, entity_list in order_spec.items():
                alias = tag_to_alias.get(tag)
                if not alias:
                    raise ValueError(f'Unknown tag {tag!r} in order_by, known: {list(tag_to_alias)}')
                for entitydict in entity_list:
                    for entitytag, entityspec in entitydict.items():
                        query = query.order_by(self._create_order_by(alias, entitytag, entityspec))

        # final setup for the query
        if data['limit'] is not None:
            query = query.limit(data['limit'])
        if data['offset'] is not None:
            query = query.offset(data['offset'])
        if data['distinct']:
            query = query.distinct()

        return BuiltQuery(query, tag_to_alias, tag_to_projected)

    def _create_order_by(
        self, alias: AliasedClass, field_key: str, entityspec: dict
    ) -> Union[ColumnElement, InstrumentedAttribute]:
        """Build the order_by parameter of the query."""
        column_name = field_key.split('.')[0]
        attrpath = field_key.split('.')[1:]
        if attrpath and 'cast' not in entityspec.keys():
            # JSONB fields ar delimited by '.' must be cast
            raise ValueError(
                f'To order_by {field_key!r}, the value has to be cast, ' "but no 'cast' key has been specified."
            )
        entity = self._get_projectable_entity(alias, column_name, attrpath, cast=entityspec.get('cast'))
        order = entityspec.get('order', 'asc')
        if order == 'desc':
            entity = entity.desc()
        elif order != 'asc':
            raise ValueError(f"Unknown 'order' key: {order!r}, must be one of: 'asc', 'desc'")
        return entity

    @staticmethod
    def _get_projectable_entity(
        alias: AliasedClass,
        column_name: str,
        attrpath: List[str],
        cast: Optional[str] = None,
    ) -> Union[ColumnElement, InstrumentedAttribute]:
        """Return projectable entity for a given alias and column name."""
        if not (attrpath or column_name in ('attributes', 'extras')):
            return get_column(column_name, alias)

        entity: ColumnElement = get_column(column_name, alias)[attrpath]
        if cast is None:
            pass
        elif cast == 'f':
            entity = entity.astext.cast(Float)
        elif cast == 'i':
            entity = entity.astext.cast(Integer)
        elif cast == 'b':
            entity = entity.astext.cast(Boolean)
        elif cast == 't':
            entity = entity.astext
        elif cast == 'j':
            entity = entity.astext.cast(JSONB)
        elif cast == 'd':
            entity = entity.astext.cast(DateTime)
        else:
            raise ValueError(f'Unknown casting key {cast}')
        return entity

    def build_filters(self, alias: AliasedClass, filter_spec: dict[str, Any]) -> ColumnElement[bool] | None:
        """Recurse through the filter specification and apply filter operations.

        :param alias: The alias of the ORM class the filter will be applied on
        :param filter_spec: the specification of the filter

        :returns: an sqlalchemy expression.
        """
        expressions: List[Any] = []
        for path_spec, filter_operation_dict in filter_spec.items():
            if path_spec in ('and', 'or', '~or', '~and', '!and', '!or'):
                subexpressions = []
                for sub_filter_spec in filter_operation_dict:
                    filters = self.build_filters(alias, sub_filter_spec)
                    if filters is not None:
                        subexpressions.append(filters)
                if subexpressions:
                    if path_spec == 'and':
                        expressions.append(and_(*subexpressions))
                    elif path_spec == 'or':
                        expressions.append(or_(*subexpressions))
                    elif path_spec in ('~and', '!and'):
                        expressions.append(not_(and_(*subexpressions)))
                    elif path_spec in ('~or', '!or'):
                        expressions.append(not_(or_(*subexpressions)))
            else:
                column_name = path_spec.split('.')[0]

                attr_key = path_spec.split('.')[1:]
                is_jsonb = bool(attr_key) or column_name in ('dict', 'attributes', 'extras')
                column: Optional[InstrumentedAttribute]
                try:
                    column = get_column(column_name, alias)
                except (ValueError, TypeError):
                    if is_jsonb:
                        column = None
                    else:
                        raise
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==': filter_operation_dict}  # noqa: PLW2901
                for operator, value in filter_operation_dict.items():
                    expressions.append(
                        self.get_filter_expr(
                            operator,
                            value,
                            attr_key,
                            is_jsonb=is_jsonb,
                            column=column,
                            column_name=column_name,
                            alias=alias,
                        )
                    )
        return and_(*expressions) if expressions else None

    def get_filter_expr(
        self,
        operator: str,
        value: Any,
        attr_key: List[str],
        is_jsonb: bool,
        alias: AliasedClass | None = None,
        column: InstrumentedAttribute | None = None,
        column_name: str | None = None,
    ) -> Any:
        """Applies a filter on the alias given.

        Expects the alias of the ORM-class on which to filter, and filter_spec.
        Filter_spec contains the specification on the filter.
        Expects:

        :param operator: The operator to apply, see below for further details
        :param value:
            The value for the right side of the expression,
            the value you want to compare with.

        :param path: The path leading to the value

        :param is_jsonb: Whether the value is in a json-column, or in an attribute like table.


        Implemented and valid operators:

        *   for any type:
            *   ==  (compare single value, eg: '==':5.0)
            *   in    (compare whether in list, eg: 'in':[5, 6, 34]
        *  for floats and integers:
            *   >
            *   <
            *   <=
            *   >=
        *  for strings:
            *   like  (case - sensitive), for example
                'like':'node.calc.%'  will match node.calc.relax and
                node.calc.RELAX and node.calc. but
                not node.CALC.relax
            *   ilike (case - unsensitive)
                will also match node.CaLc.relax in the above example

            .. note::
                The character % is a reserved special character in SQL,
                and acts as a wildcard. If you specifically
                want to capture a ``%`` in the string, use: ``_%``

        *   for arrays and dictionaries (only for the
            SQLAlchemy implementation):

            *   contains: pass a list with all the items that
                the array should contain, or that should be among
                the keys, eg: 'contains': ['N', 'H'])
            *   has_key: pass an element that the list has to contain
                or that has to be a key, eg: 'has_key':'N')

        *  for arrays only (SQLAlchemy version):
            *   of_length
            *   longer
            *   shorter

        All the above filters invoke a negation of the
        expression if preceded by **~**::

            # first example:
            filter_spec = {
                'name' : {
                    '~in':[
                        'halle',
                        'lujah'
                    ]
                } # Name not 'halle' or 'lujah'
            }

            # second example:
            filter_spec =  {
                'id' : {
                    '~==': 2
                }
            } # id is not 2
        """
        expr: Any = None
        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        elif operator.startswith('!'):
            negation = True
            operator = operator.lstrip('!')
        else:
            negation = False
        if operator in ('longer', 'shorter', 'of_length'):
            if not isinstance(value, int):
                raise TypeError('You have to give an integer when comparing to a length')
        elif operator in ('like', 'ilike'):
            if not isinstance(value, str):
                raise TypeError(f'Value for operator {operator} has to be a string (you gave {value})')

        elif operator == 'in':
            try:
                value_type_set = set(type(i) for i in value)
            except TypeError:
                raise TypeError('Value for operator `in` could not be iterated')
            if not value_type_set:
                raise ValueError('Value for operator `in` is an empty list')
            if len(value_type_set) > 1:
                raise ValueError(f'Value for operator `in` contains more than one type: {value}')
        elif operator in ('and', 'or'):
            expressions_for_this_path = []
            for filter_operation_dict in value:
                for newoperator, newvalue in filter_operation_dict.items():
                    expressions_for_this_path.append(
                        self.get_filter_expr(
                            newoperator,
                            newvalue,
                            attr_key=attr_key,
                            is_jsonb=is_jsonb,
                            alias=alias,
                            column=column,
                            column_name=column_name,
                        )
                    )
            if operator == 'and':
                expr = and_(*expressions_for_this_path)
            elif operator == 'or':
                expr = or_(*expressions_for_this_path)

        if expr is None:
            if is_jsonb:
                expr = self.get_filter_expr_from_jsonb(
                    operator,
                    value,
                    attr_key,
                    column=column,
                    column_name=column_name,
                    alias=alias,
                )
            else:
                if column is None:
                    if alias is None or column_name is None:
                        raise RuntimeError('I need to get the column but do not know the alias and the column name')
                    column = get_column(column_name, alias)
                expr = self.get_filter_expr_from_column(operator, value, column)

        if negation:
            return not_(expr)
        return expr

    def get_filter_expr_from_jsonb(
        self,
        operator: str,
        value: Any,
        attr_key: List[str],
        column: InstrumentedAttribute | None = None,
        column_name: str | None = None,
        alias: AliasedClass | None = None,
    ) -> Any:
        """Return a filter expression"""

        def cast_according_to_type(path_in_json, value):
            """Cast the value according to the type"""
            if isinstance(value, bool):
                type_filter = jsonb_typeof(path_in_json) == 'boolean'
                casted_entity = path_in_json.astext.cast(Boolean)
            elif isinstance(value, (int, float)):
                type_filter = jsonb_typeof(path_in_json) == 'number'
                casted_entity = path_in_json.astext.cast(Float)
            elif isinstance(value, dict) or value is None:
                type_filter = jsonb_typeof(path_in_json) == 'object'
                casted_entity = path_in_json.astext.cast(JSONB)  # BOOLEANS?
            elif isinstance(value, list):
                type_filter = jsonb_typeof(path_in_json) == 'array'
                casted_entity = path_in_json.astext.cast(JSONB)  # BOOLEANS?
            elif isinstance(value, str):
                type_filter = jsonb_typeof(path_in_json) == 'string'
                casted_entity = path_in_json.astext
            elif value is None:
                type_filter = jsonb_typeof(path_in_json) == 'null'
                casted_entity = path_in_json.astext.cast(JSONB)  # BOOLEANS?
            else:
                raise TypeError(f'Unknown type {type(value)}')
            return type_filter, casted_entity

        if column is None:
            if alias is None or column_name is None:
                raise RuntimeError('I need to get the column but do not know the alias and the column name')
            column = get_column(column_name, alias)

        database_entity = column[tuple(attr_key)]
        expr: Any
        if operator == '==':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity == value), else_=False)
        elif operator == '>':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity > value), else_=False)
        elif operator == '<':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity < value), else_=False)
        elif operator in ('>=', '=>'):
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity >= value), else_=False)
        elif operator in ('<=', '=<'):
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity <= value), else_=False)
        elif operator == 'of_type':
            # http://www.postgresql.org/docs/9.5/static/functions-json.html
            #  Possible types are object, array, string, number, boolean, and null.
            value_types = ('object', 'array', 'string', 'number', 'boolean')
            null_types = ('null',)
            valid_types = value_types + null_types
            if value not in valid_types:
                raise ValueError(f'value {value} for of_type is not among valid types\n{valid_types}')
            if value in value_types:
                expr = jsonb_typeof(database_entity) == value
            elif value in null_types:
                # https://www.postgresql.org/docs/current/functions-json.html
                # json_typeof('null'::json) → null
                # json_typeof(NULL::json) IS NULL → t
                tp = jsonb_typeof(database_entity)
                expr = or_(tp == 'null', tp.is_(None))
        elif operator == 'like':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity.like(value)), else_=False)
        elif operator == 'ilike':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case((type_filter, casted_entity.ilike(value)), else_=False)
        elif operator == 'in':
            type_filter, casted_entity = cast_according_to_type(database_entity, value[0])
            expr = case((type_filter, casted_entity.in_(value)), else_=False)
        elif operator == 'contains':
            expr = database_entity.cast(JSONB).contains(value)
        elif operator == 'has_key':
            expr = database_entity.cast(JSONB).has_key(value)
        elif operator == 'of_length':
            expr = case(
                (
                    jsonb_typeof(database_entity) == 'array',
                    jsonb_array_length(database_entity.cast(JSONB)) == value,
                ),
                else_=False,
            )

        elif operator == 'longer':
            expr = case(
                (
                    jsonb_typeof(database_entity) == 'array',
                    jsonb_array_length(database_entity.cast(JSONB)) > value,
                ),
                else_=False,
            )
        elif operator == 'shorter':
            expr = case(
                (
                    jsonb_typeof(database_entity) == 'array',
                    jsonb_array_length(database_entity.cast(JSONB)) < value,
                ),
                else_=False,
            )
        else:
            raise ValueError(f'Unknown operator {operator} for filters in JSON field')
        return expr

    def get_filter_expr_from_column(self, operator: str, value: Any, column) -> BinaryExpression:
        """A method that returns an valid SQLAlchemy expression.

        :param operator: The operator provided by the user ('==',  '>', ...)
        :param value: The value to compare with, e.g. (5.0, 'foo', ['a','b'])
        :param column: an instance of sqlalchemy.orm.attributes.InstrumentedAttribute or

        """
        # Label is used because it is what is returned for the
        # 'state' column by the hybrid_column construct
        if not isinstance(
            column,
            (Cast, InstrumentedAttribute, QueryableAttribute, Label, ColumnClause),
        ):
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
            expr = database_entity.cast(String).like(value)
        elif operator == 'ilike':
            expr = database_entity.ilike(value)
        elif operator == 'in':
            # Instead of plain `in` use `unnest()` (PSQL) or `json_each` (SQLite) to avoid parameter limits
            # For a regular `IN` clause, each value in the clause uses one parameter.
            # Instead using unnest() with an array uses only 1 parameter.
            expr = self._create_smarter_in_clause(column, value)
        else:
            raise ValueError(f'Unknown operator {operator} for filters on columns')
        return expr

    def _create_smarter_in_clause(self, column, values_list):
        """Return an IN condition using database-specific functions to avoid parameter limits.

        This method uses different approaches depending on the database backend and list size:
        - For small lists (<1000 items): Uses regular IN clause (fastest)
        - For medium lists (1000-100k items): Uses unnest() (PostgreSQL) or json_each() (SQLite)
        - For large lists (>100k items): Automatically batches into multiple OR'd conditions

        The batching threshold balances query performance with memory usage and database load.
        Even though modern databases can handle larger IN clauses, batching at 100k provides
        a safety valve for extreme cases while maintaining good performance for typical queries.

        For example, with 250k items:
            WHERE (
                column IN (SELECT unnest(:array_1))  -- First 100k
                OR column IN (SELECT unnest(:array_2))  -- Second 100k
                OR column IN (SELECT unnest(:array_3))  -- Remaining 50k
            )
        """
        import json

        from sqlalchemy import cast as sql_cast
        from sqlalchemy import func, type_coerce

        # Thresholds for optimization strategy
        small_list_threshold = 999
        batch_threshold = 100_000

        list_size = len(values_list)

        # For small lists, regular IN is fastest (no subquery overhead)
        if list_size < small_list_threshold:
            return column.in_(values_list)

        # For very large lists, batch internally to avoid memory/performance issues
        if list_size > batch_threshold:
            batches = []
            for i in range(0, list_size, batch_threshold):
                batch = values_list[i : i + batch_threshold]
                # Recursively call with smaller batch (will use unnest/json_each)
                batches.append(self._create_smarter_in_clause(column, batch))
            return or_(*batches)

        # Medium-sized lists: use database-specific optimized approach
        session = self.get_session()
        dialect_name = session.bind.dialect.name

        if dialect_name == 'postgresql':
            # PostgreSQL: Use unnest() with array
            from sqlalchemy.dialects.postgresql import ARRAY

            coltype = column.type
            unnest_expr = func.unnest(type_coerce(values_list, ARRAY(coltype)))
            subq = select(unnest_expr).scalar_subquery()

        elif dialect_name == 'sqlite':
            # SQLite: Use json_each() with JSON array
            coltype = column.type
            json_array = json.dumps(list(values_list))

            # Create table-valued function: json_each(json_array)
            json_each_table = func.json_each(json_array).table_valued('value')

            # Select and cast the value column
            value_col = json_each_table.c.value
            subq = select(sql_cast(value_col, coltype)).select_from(json_each_table).scalar_subquery()

        else:
            # AiiDA only supports PostgreSQL and SQLite
            raise NotImplementedError(
                f'Unsupported database backend: {dialect_name}. ' 'AiiDA only supports PostgreSQL and SQLite.'
            )

        return column.in_(subq)

    def to_backend(self, res) -> Any:
        """Convert results to return backend specific objects.

        - convert `DbModel` instances to `BackendEntity` instances.
        - convert UUIDs to strings

        :param res: the result returned by the query

        :returns:backend compatible instance
        """
        if isinstance(res, uuid.UUID):
            return str(res)

        try:
            return self._backend.get_backend_entity(res)  # type: ignore[attr-defined]
        except TypeError:
            return res

    def as_sql(self, data: QueryDictType, inline: bool = False) -> str:
        """Return the SQL query as a string."""
        with self.query_session(data) as build:
            compiled = compile_query(build.query, literal_binds=inline)
        if inline:
            return compiled.string + '\n'
        return f'{compiled.string!r} % {compiled.params!r}\n'

    def analyze_query(self, data: QueryDictType, execute: bool = True, verbose: bool = False) -> str:
        """Analyze the query and return the result as a string."""
        with self.query_session(data) as build:
            if build.query.session.bind.dialect.name != 'postgresql':  # type: ignore[union-attr]
                raise NotImplementedError('Only PostgreSQL is supported for this method')
            compiled = compile_query(build.query, literal_binds=True)
        options = ', '.join((['ANALYZE'] if execute else []) + (['VERBOSE'] if verbose else []))
        options = f' ({options})' if options else ''
        rows = self.get_session().execute(text(f'EXPLAIN{options} {compiled.string}')).fetchall()
        return '\n'.join(row[0] for row in rows)

    def get_creation_statistics(self, user_pk: Optional[int] = None) -> Dict[str, Any]:
        session = self.get_session()
        retdict: Dict[Any, Any] = {}

        total_query = session.query(self.Node)
        types_query = session.query(self.Node.node_type.label('typestring'), sa_func.count(self.Node.id))

        dialect = session.bind.dialect.name  # type: ignore[union-attr]
        date_format = '%Y-%m-%d'

        if dialect == 'sqlite':
            cday = sa_func.strftime(date_format, sa_func.datetime(self.Node.ctime, 'localtime'))

            def date_to_str(d):
                return d

        elif dialect == 'postgresql':
            cday = sa_func.date_trunc('day', self.Node.ctime)

            def date_to_str(d):
                return d.strftime(date_format)

        else:
            raise NotImplementedError(f'unsupported dialect: {dialect}')

        stat_query = session.query(
            cday.label('cday'),
            sa_func.count(self.Node.id),
        )

        if user_pk is not None:
            total_query = total_query.filter(self.Node.user_id == user_pk)
            types_query = types_query.filter(self.Node.user_id == user_pk)
            stat_query = stat_query.filter(self.Node.user_id == user_pk)

        # Total number of nodes
        retdict['total'] = total_query.count()

        # Nodes per type
        retdict['types'] = dict(types_query.group_by('typestring').all())

        # Nodes created per day
        stat = stat_query.group_by('cday').order_by('cday').all()

        ctime_by_day = {date_to_str(entry[0]): entry[1] for entry in stat}
        retdict['ctime_by_day'] = ctime_by_day

        return retdict
        # Still not containing all dates


def get_corresponding_property(entity_table: str, given_property: str, mapper: Dict[str, Dict[str, str]]) -> str:
    """This method returns an updated property for a given a property.
    If there is no update for the property, the given property is returned.
    """
    try:
        # Get the mapping for the specific entity_table
        property_mapping = mapper[entity_table]
        try:
            # Get the mapping for the specific property
            return property_mapping[given_property]
        except KeyError:
            # If there is no mapping, the property remains unchanged
            return given_property
    except KeyError:
        # If it doesn't exist, it means that the given_property remains v
        return given_property


def get_corresponding_properties(entity_table: str, given_properties: List[str], mapper: Dict[str, Dict[str, str]]):
    """This method returns a list of updated properties for a given list of properties.
    If there is no update for the property, the given property is returned in the list.
    """
    if entity_table in mapper:
        res = []
        for given_property in given_properties:
            res.append(get_corresponding_property(entity_table, given_property, mapper))
        return res

    return given_properties


def modify_expansions(
    alias: AliasedClass,
    expansions: List[str],
    outer_to_inner_schema=Dict[str, Dict[str, str]],
) -> List[str]:
    """Modify names of projections if `**` was specified.

    This is important for the schema having attributes in a different table.
    In SQLA, the metadata should be changed to _metadata to be in-line with the database schema
    """
    # The following check is added to avoided unnecessary calls to get_inner_property for QB edge queries
    # The update of expansions makes sense only when AliasedClass is provided
    if hasattr(alias, '_sa_class_manager'):
        if '_metadata' in expansions:
            raise NotExistent(f"_metadata doesn't exist for {alias}. Please try metadata.")

        return get_corresponding_properties(alias.__tablename__, expansions, outer_to_inner_schema)

    return expansions


def get_column(colname: str, alias: AliasedClass) -> InstrumentedAttribute:
    """Return the column for a given projection."""
    table_name = get_table_name(alias)
    if projections := PROJECT_MAP.get(table_name):
        colname = projections.get(colname, colname)
    try:
        return getattr(alias, colname)
    except AttributeError as exc:
        raise ValueError(
            '{} is not a column of {}\n' 'Valid columns are:\n' '{}'.format(
                colname, alias, '\n'.join(alias._sa_class_manager.mapper.c.keys())
            )
        ) from exc


def get_column_names(alias: AliasedClass) -> List[str]:
    """Given the backend specific alias, return the column names that correspond to the aliased table."""
    return [str(c).replace(f'{alias.__table__.name}.', '') for c in alias.__table__.columns]


def get_table_name(aliased_class: AliasedClass) -> str:
    """Returns the table name given an Aliased class"""
    return aliased_class.__tablename__


def compile_query(query: Query, literal_binds: bool = False) -> SQLCompiler:
    """Compile the query to the SQL executable.

    :params literal_binds: Inline bound parameters (this is normally handled by the Python DBAPI).
    """
    dialect = query.session.bind.dialect  # type: ignore[union-attr]

    class _Compiler(dialect.statement_compiler):  # type: ignore[name-defined]
        """Override the compiler with additional literal value renderers."""

        def render_literal_value(self, value, type_):
            """Render the value of a bind parameter as a quoted literal.

            See https://www.postgresql.org/docs/current/functions-json.html for serialisation specs
            """
            from datetime import date, datetime, timedelta

            try:
                return super().render_literal_value(value, type_)
            # sqlalchemy<1.4.45 raises NotImplementedError, sqlalchemy>=1.4.45 raises CompileError
            except (NotImplementedError, CompileError):
                if isinstance(value, list):
                    values = ','.join(self.render_literal_value(item, type_) for item in value)
                    return f"'[{values}]'"
                if isinstance(value, int):
                    return str(value)
                if isinstance(value, (str, date, datetime, timedelta)):
                    escaped = str(value).replace('"', '\\"')
                    return f'"{escaped}"'
                raise

    return _Compiler(dialect, query.statement, compile_kwargs=dict(literal_binds=literal_binds))


def generate_joins(
    data: QueryDictType, aliases: Dict[str, Optional[AliasedClass]], joiner: SqlaJoiner
) -> List[JoinReturn]:
    """Generate the joins for the query."""
    joins: List[JoinReturn] = []
    # Start on second path item, since there is nothing to join if that is the first table
    for index, verticespec in enumerate(data['path'][1:], start=1):
        join_to = aliases[verticespec['tag']]
        if join_to is None:
            raise ValueError(f'No alias found for tag {verticespec["tag"]}')

        calling_entity = data['path'][index]['orm_base']
        joining_keyword = verticespec['joining_keyword']
        joining_value = verticespec['joining_value']
        try:
            join_func = joiner.get_join_func(calling_entity, joining_keyword)
        except KeyError:
            raise ValueError(f"'{joining_keyword}' is not a valid joining keyword for a '{calling_entity}' type entity")

        if not isinstance(joining_value, str):
            raise ValueError(f"'joining_value' value is not a string: {joining_value}")

        join_tag = aliases.get(joining_value, None)
        if not join_tag:
            raise ValueError(f'no alias found for joining_value tag {joining_value!r}')

        edge_tag = verticespec['edge_tag']

        # if verticespec['joining_keyword'] in ('with_ancestors', 'with_descendants'):
        # These require a filter_dict, to help the recursive function find a good starting point.
        filter_dict = data['filters'].get(verticespec['joining_value'], {})
        # Also find out whether the path is used in a filter or a project and, if so,
        # instruct the recursive function to build the path on the fly.
        # The default is False, because it's super expensive
        expand_path = (data['filters'][edge_tag].get('path', None) is not None) or any(
            'path' in d.keys() for d in data['project'][edge_tag]
        )
        join = join_func(
            join_tag,
            join_to,
            isouterjoin=verticespec.get('outerjoin'),  # type: ignore[call-arg]
            filter_dict=filter_dict,
            expand_path=expand_path,
        )
        join.edge_tag = edge_tag
        joins.append(join)
    return joins


def generate_projections(
    data: QueryDictType, aliases: Dict[str, Optional[AliasedClass]], outer_to_inner_schema, get_projectable_entity
):
    """Generate the projections for the query."""
    # mapping of tag -> field -> projection_index
    tag_to_projected_fields: Dict[str, Dict[str, int]] = {}
    projections: List[Tuple[Union[AliasedClass, ColumnElement], bool]] = []

    QUERYBUILD_LOGGER.debug('projections data: %s', data['project'])

    if not any(data['project'].values()):
        # If user has not set projection,
        # I will simply project the last item specified!
        # Don't change, path traversal querying relies on this behavior!
        projections += _create_projections(
            data['path'][-1]['tag'],
            aliases,
            len(projections),
            [{'*': {}}],
            get_projectable_entity,
            tag_to_projected_fields,
            outer_to_inner_schema,
        )
    else:
        for vertex in data['path']:
            project_dict = data['project'].get(vertex['tag'], [])
            projections += _create_projections(
                vertex['tag'],
                aliases,
                len(projections),
                project_dict,
                get_projectable_entity,
                tag_to_projected_fields,
                outer_to_inner_schema,
            )

        for vertex in data['path'][1:]:
            edge_tag = vertex.get('edge_tag', None)

            QUERYBUILD_LOGGER.debug(
                'Checking projections for edges: This is edge %s from %s, %s of %s',
                edge_tag,
                vertex.get('tag'),
                vertex.get('joining_keyword'),
                vertex.get('joining_value'),
            )
            if edge_tag is not None:
                project_dict = data['project'].get(edge_tag, [])
                projections += _create_projections(
                    edge_tag,
                    aliases,
                    len(projections),
                    project_dict,
                    get_projectable_entity,
                    tag_to_projected_fields,
                    outer_to_inner_schema,
                )

    # check the consistency of projections
    projection_index_to_field = {
        index_in_sql_result: attrkey
        for _, projected_entities_dict in tag_to_projected_fields.items()
        for attrkey, index_in_sql_result in projected_entities_dict.items()
    }
    if len(projections) > len(projection_index_to_field):
        raise ValueError('You are projecting the same key multiple times within the same node')
    if not projection_index_to_field:
        raise ValueError('No projections requested')
    return projections, tag_to_projected_fields


def _create_projections(
    tag: str,
    aliases: Dict[str, Optional[AliasedClass]],
    projection_count: int,
    project_dict: List[Dict[str, dict]],
    get_projectable_entity,
    tag_to_projected_fields,
    outer_to_inner_schema,
) -> List[Tuple[Union[AliasedClass, ColumnElement], bool]]:
    """Build the projections for a given tag.

    :param tag: the tag of the node for which to build the projections
    :param projection_count: the number of previous projections
    :param items_to_project: the list of projections to build, if None, use the projections specified in the query

    """
    # Return here if there is nothing to project, reduces number of key in return dictionary
    QUERYBUILD_LOGGER.debug('projection for %s: %s', tag, project_dict)
    if not project_dict:
        return []

    alias = aliases.get(tag)
    if alias is None:
        raise ValueError(f'No alias found for tag {tag}')

    tag_to_projected_fields[tag] = {}

    projections = []

    for projectable_spec in project_dict:
        for projectable_entity_name, extraspec in projectable_spec.items():
            property_names = []
            if projectable_entity_name == '**':
                # Need to expand
                property_names.extend(modify_expansions(alias, get_column_names(alias), outer_to_inner_schema))
            else:
                property_names.extend(modify_expansions(alias, [projectable_entity_name], outer_to_inner_schema))

            for property_name in property_names:
                projections.append(_get_projection(alias, property_name, get_projectable_entity, **extraspec))
                tag_to_projected_fields[tag][property_name] = projection_count
                projection_count += 1

    return projections


def _get_projection(
    alias: AliasedClass,
    projectable_entity_name: str,
    get_projectable_entity,
    cast: Optional[str] = None,
    func: Optional[str] = None,
    **_kw: Any,
) -> Tuple[Union[AliasedClass, ColumnElement], bool]:
    """:param alias: An alias for an ormclass
    :param projectable_entity_name:
        User specification of what to project.
        Appends to query's entities what the user wants to project
        (have returned by the query)
    :param cast: Cast the value to a different type
    :param func: Apply a function to the projection

    :return: The projection
    """
    column_name = projectable_entity_name.split('.')[0]
    attr_key = projectable_entity_name.split('.')[1:]

    if column_name == '*':
        if func is not None:
            raise ValueError(
                'Very sorry, but functions on the aliased class\n'
                "(You specified '*')\n"
                'will not work!\n'
                "I suggest you apply functions on a column, e.g. ('id')\n"
            )
        return alias, True

    entity_to_project = get_projectable_entity(alias, column_name, attr_key, cast=cast)
    if func is None:
        pass
    elif func == 'max':
        entity_to_project = sa_func.max(entity_to_project)
    elif func == 'min':
        entity_to_project = sa_func.max(entity_to_project)
    elif func == 'count':
        entity_to_project = sa_func.count(entity_to_project)
    else:
        raise ValueError(f'\nInvalid function specification {func}')

    return entity_to_project, False
