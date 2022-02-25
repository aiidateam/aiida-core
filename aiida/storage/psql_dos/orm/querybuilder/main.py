# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines
"""Sqla query builder implementation"""
from contextlib import contextmanager
from functools import partial
from typing import Any, Dict, Iterable, Iterator, List, Optional, Union
import uuid
import warnings

from sqlalchemy import and_
from sqlalchemy import func as sa_func
from sqlalchemy import not_, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute, QueryableAttribute
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.session import Session
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.compiler import SQLCompiler
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Cast, ColumnClause, ColumnElement, Label
from sqlalchemy.sql.expression import case, text
from sqlalchemy.types import Boolean, DateTime, Float, Integer, String

from aiida.common.exceptions import NotExistent
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation.querybuilder import QUERYBUILD_LOGGER, BackendQueryBuilder, QueryDictType

from .joiner import SqlaJoiner

jsonb_typeof = sa_func.jsonb_typeof
jsonb_array_length = sa_func.jsonb_array_length
array_length = sa_func.array_length


class SqlaQueryBuilder(BackendQueryBuilder):
    """
    QueryBuilder to use with SQLAlchemy-backend and
    schema defined in backends.sqlalchemy.models
    """

    # pylint: disable=redefined-outer-name,too-many-public-methods,invalid-name

    def __init__(self, backend):
        super().__init__(backend)

        self._joiner = SqlaJoiner(self, self.build_filters)

        # CACHING ATTRIBUTES
        # cache of tag mappings to aliased classes, populated during appends (edges populated during build)
        self._tag_to_alias: Dict[str, Optional[AliasedClass]] = {}

        # total number of requested projections, and mapping of tag -> field -> projection_index
        # populated on query build and used by "return" methods (`one`, `iterall`, `iterdict`)
        self._requested_projections: int = 0
        self._tag_to_projected_fields: Dict[str, Dict[str, int]] = {}

        # table -> field -> field
        self.inner_to_outer_schema: Dict[str, Dict[str, str]] = {}
        self.outer_to_inner_schema: Dict[str, Dict[str, str]] = {}
        self.set_field_mappings()

        # data generated from front-end
        self._data: QueryDictType = {
            'path': [],
            'filters': {},
            'project': {},
            'order_by': [],
            'offset': None,
            'limit': None,
            'distinct': False
        }
        self._query: 'Query' = Query([])
        # Hashing the internal query representation avoids rebuilding a query
        self._hash: Optional[str] = None

    def set_field_mappings(self):
        """Set conversions between the field names in the database and used by the `QueryBuilder`"""
        self.outer_to_inner_schema['db_dbauthinfo'] = {'metadata': '_metadata'}
        self.outer_to_inner_schema['db_dbcomputer'] = {'metadata': '_metadata'}
        self.outer_to_inner_schema['db_dblog'] = {'metadata': '_metadata'}

        self.inner_to_outer_schema['db_dbauthinfo'] = {'_metadata': 'metadata'}
        self.inner_to_outer_schema['db_dbcomputer'] = {'_metadata': 'metadata'}
        self.inner_to_outer_schema['db_dblog'] = {'_metadata': 'metadata'}

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
        """
        :returns: a valid session, an instance of :class:`sqlalchemy.orm.session.Session`
        """
        return self._backend.get_session()

    def count(self, data: QueryDictType) -> int:
        with self.use_query(data) as query:
            result = query.count()
        return result

    def first(self, data: QueryDictType) -> Optional[List[Any]]:
        with self.use_query(data) as query:
            result = query.first()

        if result is None:
            return result

        # we discard the first item of the result row,
        # which was what the query was initialised with and not one of the requested projection (see self._build)
        result = result[1:]

        if len(result) != self._requested_projections:
            raise AssertionError(
                f'length of query result ({len(result)}) does not match '
                f'the number of specified projections ({self._requested_projections})'
            )

        return [self.to_backend(r) for r in result]

    def iterall(self, data: QueryDictType, batch_size: Optional[int]) -> Iterable[List[Any]]:
        """Return an iterator over all the results of a list of lists."""
        with self.use_query(data) as query:

            stmt = query.statement.execution_options(yield_per=batch_size)

            for resultrow in self.get_session().execute(stmt):
                # we discard the first item of the result row,
                # which is what the query was initialised with
                # and not one of the requested projection (see self._build)
                resultrow = resultrow[1:]
                yield [self.to_backend(rowitem) for rowitem in resultrow]

    def iterdict(self, data: QueryDictType, batch_size: Optional[int]) -> Iterable[Dict[str, Dict[str, Any]]]:
        """Return an iterator over all the results of a list of dictionaries."""
        with self.use_query(data) as query:

            stmt = query.statement.execution_options(yield_per=batch_size)

            for row in self.get_session().execute(stmt):
                # build the yield result
                yield_result: Dict[str, Dict[str, Any]] = {}
                for tag, projected_entities_dict in self._tag_to_projected_fields.items():
                    yield_result[tag] = {}
                    for attrkey, project_index in projected_entities_dict.items():
                        field_name = self.get_corresponding_property(
                            self.get_table_name(self._get_tag_alias(tag)), attrkey, self.inner_to_outer_schema
                        )
                        yield_result[tag][field_name] = self.to_backend(row[project_index])
                yield yield_result

    @contextmanager
    def use_query(self, data: QueryDictType) -> Iterator[Query]:
        """Yield the built query."""
        query = self._update_query(data)
        try:
            yield query
        except Exception:
            self.get_session().close()
            raise

    def _update_query(self, data: QueryDictType) -> Query:
        """Return the sqlalchemy.orm.Query instance for the current query specification.

        To avoid unnecessary re-builds of the query, the hashed dictionary representation of this instance
        is compared to the last query returned, which is cached by its hash.
        """
        from aiida.common.hashing import make_hash

        query_hash = make_hash(data)

        if self._query and self._hash and self._hash == query_hash:
            # query is up-to-date
            return self._query

        self._data = data
        self._build()
        self._hash = query_hash

        return self._query

    def rebuild_aliases(self) -> None:
        """Rebuild the mapping of `tag` -> `alias`"""
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
        self._tag_to_alias = {}
        for path in self._data['path']:
            # An SAWarning warning is currently emitted:
            # "relationship 'DbNode.input_links' will copy column db_dbnode.id to column db_dblink.output_id,
            # which conflicts with relationship(s): 'DbNode.outputs' (copies db_dbnode.id to db_dblink.output_id)"
            # This should be eventually fixed
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', category=SAWarning)
                self._tag_to_alias[path['tag']] = aliased(cls_map[path['orm_base']])

    def _get_tag_alias(self, tag: str) -> AliasedClass:
        """Get the alias of a tag"""
        alias = self._tag_to_alias[tag]
        if alias is None:
            raise AssertionError('alias is not set')
        return alias

    def _build(self) -> Query:
        """
        build the query and return a sqlalchemy.Query instance
        """
        # pylint: disable=too-many-branches,too-many-locals
        self.rebuild_aliases()
        # Start the build by generating a query from the current session,
        # A query must always be initialised with a starting entity or column (to allow joins),
        # however, we don't actually want to return this, since we set projections explicitly.
        # Therefore, we just add the id field (as we don't want to retrive the entire entity from the database),
        # and then remove it in the "return" methods (`one`, `iterall`, `iterdict`)
        firstalias = self._get_tag_alias(self._data['path'][0]['tag'])
        # we assume here that every table has an 'id' column (currently the case)
        self._query = self.get_session().query(firstalias.id)

        # JOINS ################################

        # Start on second path item, since there is nothing to join if that is the first table
        for index, verticespec in enumerate(self._data['path'][1:], start=1):
            join_to = self._get_tag_alias(verticespec['tag'])
            join_func = self._build_join_func(index, verticespec['joining_keyword'], verticespec['joining_value'])
            edge_tag = verticespec['edge_tag']

            # if verticespec['joining_keyword'] in ('with_ancestors', 'with_descendants'):
            # These require a filter_dict, to help the recursive function find a good starting point.
            filter_dict = self._data['filters'].get(verticespec['joining_value'], {})
            # Also find out whether the path is used in a filter or a project and, if so,
            # instruct the recursive function to build the path on the fly.
            # The default is False, because it's super expensive
            expand_path = ((self._data['filters'][edge_tag].get('path', None) is not None) or
                           any('path' in d.keys() for d in self._data['project'][edge_tag]))

            result = join_func(
                join_to, isouterjoin=verticespec.get('outerjoin'), filter_dict=filter_dict, expand_path=expand_path
            )
            self._query = result.query
            if result.aliased_edge is not None:
                self._tag_to_alias[edge_tag] = result.aliased_edge

        # FILTERS ##############################

        for tag, filter_specs in self._data['filters'].items():
            if not filter_specs:
                continue
            try:
                alias = self._get_tag_alias(tag)
            except KeyError:
                raise ValueError(f'Unknown tag {tag!r} in filters, known: {list(self._tag_to_alias)}')
            filters = self.build_filters(alias, filter_specs)
            if filters is not None:
                self._query = self._query.filter(filters)

        # PROJECTIONS ##########################

        # Reset mapping of tag -> field -> projection_index
        self._tag_to_projected_fields = {}

        projection_count = 1
        QUERYBUILD_LOGGER.debug('projections data: %s', self._data['project'])

        if not any(self._data['project'].values()):
            # If user has not set projection,
            # I will simply project the last item specified!
            # Don't change, path traversal querying relies on this behavior!
            projection_count = self._build_projections(
                self._data['path'][-1]['tag'], projection_count, items_to_project=[{
                    '*': {}
                }]
            )
        else:
            for vertex in self._data['path']:
                projection_count = self._build_projections(vertex['tag'], projection_count)

            # LINK-PROJECTIONS #########################

            for vertex in self._data['path'][1:]:
                edge_tag = vertex.get('edge_tag', None)  # type: ignore

                QUERYBUILD_LOGGER.debug(
                    'Checking projections for edges: This is edge %s from %s, %s of %s', edge_tag, vertex.get('tag'),
                    vertex.get('joining_keyword'), vertex.get('joining_value')
                )
                if edge_tag is not None:
                    projection_count = self._build_projections(edge_tag, projection_count)

        # check the consistency of projections
        projection_index_to_field = {
            index_in_sql_result: attrkey for _, projected_entities_dict in self._tag_to_projected_fields.items()
            for attrkey, index_in_sql_result in projected_entities_dict.items()
        }
        if (projection_count - 1) > len(projection_index_to_field):
            raise ValueError('You are projecting the same key multiple times within the same node')
        if not projection_index_to_field:
            raise ValueError('No projections requested')
        self._requested_projections = projection_count - 1

        # ORDER ################################
        for order_spec in self._data['order_by']:
            for tag, entity_list in order_spec.items():
                alias = self._get_tag_alias(tag)
                for entitydict in entity_list:
                    for entitytag, entityspec in entitydict.items():
                        self._build_order_by(alias, entitytag, entityspec)

        # LIMIT ################################
        if self._data['limit'] is not None:
            self._query = self._query.limit(self._data['limit'])

        # OFFSET ################################
        if self._data['offset'] is not None:
            self._query = self._query.offset(self._data['offset'])

        # DISTINCT #################################
        if self._data['distinct']:
            self._query = self._query.distinct()

        return self._query

    def _build_join_func(self, index: int, joining_keyword: str, joining_value: str):
        """
        :param index: Index of this node within the path specification
        :param joining_keyword: the relation on which to join
        :param joining_value: the tag of the nodes to be joined
        """
        # pylint: disable=unused-argument
        # Set the calling entity - to allow for the correct join relation to be set
        calling_entity = self._data['path'][index]['orm_base']
        try:
            func = self._joiner.get_join_func(calling_entity, joining_keyword)
        except KeyError:
            raise ValueError(f"'{joining_keyword}' is not a valid joining keyword for a '{calling_entity}' type entity")

        if isinstance(joining_value, str):
            try:
                return partial(func, self._query, self._get_tag_alias(joining_value))
            except KeyError:
                raise ValueError(f'joining_value tag {joining_value!r} not in : {list(self._tag_to_alias)}')
        raise ValueError(f"'joining_value' value is not a string: {joining_value}")

    def _build_order_by(self, alias: AliasedClass, field_key: str, entityspec: dict) -> None:
        """Build the order_by parameter of the query."""
        column_name = field_key.split('.')[0]
        attrpath = field_key.split('.')[1:]
        if attrpath and 'cast' not in entityspec.keys():
            # JSONB fields ar delimited by '.' must be cast
            raise ValueError(
                f'To order_by {field_key!r}, the value has to be cast, '
                "but no 'cast' key has been specified."
            )
        entity = self._get_projectable_entity(alias, column_name, attrpath, cast=entityspec.get('cast'))
        order = entityspec.get('order', 'asc')
        if order == 'desc':
            entity = entity.desc()
        elif order != 'asc':
            raise ValueError(f"Unknown 'order' key: {order!r}, must be one of: 'asc', 'desc'")
        self._query = self._query.order_by(entity)

    def _build_projections(
        self, tag: str, projection_count: int, items_to_project: Optional[List[Dict[str, dict]]] = None
    ) -> int:
        """Build the projections for a given tag."""
        if items_to_project is None:
            project_dict = self._data['project'].get(tag, [])
        else:
            project_dict = items_to_project

        # Return here if there is nothing to project, reduces number of key in return dictionary
        QUERYBUILD_LOGGER.debug('projection for %s: %s', tag, project_dict)
        if not project_dict:
            return projection_count

        alias = self._get_tag_alias(tag)

        self._tag_to_projected_fields[tag] = {}

        for projectable_spec in project_dict:
            for projectable_entity_name, extraspec in projectable_spec.items():
                property_names = []
                if projectable_entity_name == '**':
                    # Need to expand
                    property_names.extend(self.modify_expansions(alias, self.get_column_names(alias)))
                else:
                    property_names.extend(self.modify_expansions(alias, [projectable_entity_name]))

                for property_name in property_names:
                    self._add_to_projections(alias, property_name, **extraspec)
                    self._tag_to_projected_fields[tag][property_name] = projection_count
                    projection_count += 1

        return projection_count

    def _add_to_projections(
        self,
        alias: AliasedClass,
        projectable_entity_name: str,
        cast: Optional[str] = None,
        func: Optional[str] = None,
        **_kw: Any
    ) -> None:
        """
        :param alias: An alias for an ormclass
        :param projectable_entity_name:
            User specification of what to project.
            Appends to query's entities what the user wants to project
            (have returned by the query)

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
            self._query = self._query.add_entity(alias)
        else:
            entity_to_project = self._get_projectable_entity(alias, column_name, attr_key, cast=cast)
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
            self._query = self._query.add_columns(entity_to_project)

    def _get_projectable_entity(
        self,
        alias: AliasedClass,
        column_name: str,
        attrpath: List[str],
        cast: Optional[str] = None
    ) -> Union[ColumnElement, InstrumentedAttribute]:
        """Return projectable entity for a given alias and column name."""
        if attrpath or column_name in ('attributes', 'extras'):
            entity = self.get_projectable_attribute(alias, column_name, attrpath, cast=cast)
        else:
            entity = self.get_column(column_name, alias)
        return entity

    def get_projectable_attribute(
        self, alias: AliasedClass, column_name: str, attrpath: List[str], cast: Optional[str] = None
    ) -> ColumnElement:
        """Return an attribute store in a JSON field of the give column"""
        # pylint: disable=unused-argument
        entity: ColumnElement = self.get_column(column_name, alias)[attrpath]
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

    @staticmethod
    def get_column(colname: str, alias: AliasedClass) -> InstrumentedAttribute:
        """
        Return the column for a given projection.
        """
        try:
            return getattr(alias, colname)
        except AttributeError as exc:
            raise ValueError(
                '{} is not a column of {}\n'
                'Valid columns are:\n'
                '{}'.format(colname, alias, '\n'.join(alias._sa_class_manager.mapper.c.keys()))  # pylint: disable=protected-access
            ) from exc

    def build_filters(self, alias: AliasedClass, filter_spec: Dict[str, Any]) -> Optional[BooleanClauseList]:  # pylint: disable=too-many-branches
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
                is_jsonb = (bool(attr_key) or column_name in ('attributes', 'extras'))
                column: Optional[InstrumentedAttribute]
                try:
                    column = self.get_column(column_name, alias)
                except (ValueError, TypeError):
                    if is_jsonb:
                        column = None
                    else:
                        raise
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==': filter_operation_dict}
                for operator, value in filter_operation_dict.items():
                    expressions.append(
                        self.get_filter_expr(
                            operator,
                            value,
                            attr_key,
                            is_jsonb=is_jsonb,
                            column=column,
                            column_name=column_name,
                            alias=alias
                        )
                    )
        return and_(*expressions) if expressions else None

    def modify_expansions(self, alias: AliasedClass, expansions: List[str]) -> List[str]:
        """Modify names of projections if `**` was specified.

        This is important for the schema having attributes in a different table.
        In SQLA, the metadata should be changed to _metadata to be in-line with the database schema
        """
        # pylint: disable=protected-access
        # The following check is added to avoided unnecessary calls to get_inner_property for QB edge queries
        # The update of expansions makes sense only when AliasedClass is provided
        if hasattr(alias, '_sa_class_manager'):
            if '_metadata' in expansions:
                raise NotExistent(f"_metadata doesn't exist for {alias}. Please try metadata.")

            return self.get_corresponding_properties(alias.__tablename__, expansions, self.outer_to_inner_schema)

        return expansions

    @classmethod
    def get_corresponding_properties(
        cls, entity_table: str, given_properties: List[str], mapper: Dict[str, Dict[str, str]]
    ):
        """
        This method returns a list of updated properties for a given list of properties.
        If there is no update for the property, the given property is returned in the list.
        """
        if entity_table in mapper:
            res = []
            for given_property in given_properties:
                res.append(cls.get_corresponding_property(entity_table, given_property, mapper))
            return res

        return given_properties

    @classmethod
    def get_corresponding_property(
        cls, entity_table: str, given_property: str, mapper: Dict[str, Dict[str, str]]
    ) -> str:
        """
        This method returns an updated property for a given a property.
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

    def get_filter_expr(
        self,
        operator: str,
        value: Any,
        attr_key: List[str],
        is_jsonb: bool,
        alias=None,
        column=None,
        column_name=None
    ):
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
        # pylint: disable=too-many-arguments, too-many-branches
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
                            column_name=column_name
                        )
                    )
            if operator == 'and':
                expr = and_(*expressions_for_this_path)
            elif operator == 'or':
                expr = or_(*expressions_for_this_path)

        if expr is None:
            if is_jsonb:
                expr = self.get_filter_expr_from_jsonb(
                    operator, value, attr_key, column=column, column_name=column_name, alias=alias
                )
            else:
                if column is None:
                    if (alias is None) and (column_name is None):
                        raise RuntimeError('I need to get the column but do not know the alias and the column name')
                    column = self.get_column(column_name, alias)
                expr = self.get_filter_expr_from_column(operator, value, column)

        if negation:
            return not_(expr)
        return expr

    def get_filter_expr_from_jsonb(
        self, operator: str, value, attr_key: List[str], column=None, column_name=None, alias=None
    ):
        """Return a filter expression"""

        # pylint: disable=too-many-branches, too-many-arguments, too-many-statements

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
            elif isinstance(value, dict):
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
            column = self.get_column(column_name, alias)

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
            valid_types = ('object', 'array', 'string', 'number', 'boolean', 'null')
            if value not in valid_types:
                raise ValueError(f'value {value} for of_type is not among valid types\n{valid_types}')
            expr = jsonb_typeof(database_entity) == value
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
            expr = database_entity.cast(JSONB).has_key(value)  # noqa
        elif operator == 'of_length':
            expr = case(
                (jsonb_typeof(database_entity) == 'array', jsonb_array_length(database_entity.cast(JSONB)) == value),
                else_=False
            )

        elif operator == 'longer':
            expr = case(
                (jsonb_typeof(database_entity) == 'array', jsonb_array_length(database_entity.cast(JSONB)) > value),
                else_=False
            )
        elif operator == 'shorter':
            expr = case(
                (jsonb_typeof(database_entity) == 'array', jsonb_array_length(database_entity.cast(JSONB)) < value),
                else_=False
            )
        else:
            raise ValueError(f'Unknown operator {operator} for filters in JSON field')
        return expr

    @staticmethod
    def get_filter_expr_from_column(operator: str, value: Any, column) -> BinaryExpression:
        """A method that returns an valid SQLAlchemy expression.

        :param operator: The operator provided by the user ('==',  '>', ...)
        :param value: The value to compare with, e.g. (5.0, 'foo', ['a','b'])
        :param column: an instance of sqlalchemy.orm.attributes.InstrumentedAttribute or

        """
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
            expr = database_entity.cast(String).like(value)
        elif operator == 'ilike':
            expr = database_entity.ilike(value)
        elif operator == 'in':
            expr = database_entity.in_(value)
        else:
            raise ValueError(f'Unknown operator {operator} for filters on columns')
        return expr

    @staticmethod
    def get_table_name(aliased_class: AliasedClass) -> str:
        """ Returns the table name given an Aliased class"""
        return aliased_class.__tablename__

    @staticmethod
    def get_column_names(alias: AliasedClass) -> List[str]:
        """
        Given the backend specific alias, return the column names that correspond to the aliased table.
        """
        return [str(c).replace(f'{alias.__table__.name}.', '') for c in alias.__table__.columns]

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
            return self._backend.get_backend_entity(res)
        except TypeError:
            return res

    @staticmethod
    def _compile_query(query: Query, literal_binds: bool = False) -> SQLCompiler:
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
                except NotImplementedError:
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

    def as_sql(self, data: QueryDictType, inline: bool = False) -> str:
        with self.use_query(data) as query:
            compiled = self._compile_query(query, literal_binds=inline)
        if inline:
            return compiled.string + '\n'
        return f'{compiled.string!r} % {compiled.params!r}\n'

    def analyze_query(self, data: QueryDictType, execute: bool = True, verbose: bool = False) -> str:
        with self.use_query(data) as query:
            if query.session.bind.dialect.name != 'postgresql':  # type: ignore[union-attr]
                raise NotImplementedError('Only PostgreSQL is supported for this method')
            compiled = self._compile_query(query, literal_binds=True)
        options = ', '.join((['ANALYZE'] if execute else []) + (['VERBOSE'] if verbose else []))
        options = f' ({options})' if options else ''
        rows = self.get_session().execute(text(f'EXPLAIN{options} {compiled.string}')).fetchall()
        return '\n'.join(row[0] for row in rows)

    def get_creation_statistics(self, user_pk: Optional[int] = None) -> Dict[str, Any]:
        session = self.get_session()
        retdict: Dict[Any, Any] = {}

        total_query = session.query(self.Node)
        types_query = session.query(self.Node.node_type.label('typestring'), sa_func.count(self.Node.id))  # pylint: disable=no-member
        stat_query = session.query(
            sa_func.date_trunc('day', self.Node.ctime).label('cday'),  # pylint: disable=no-member
            sa_func.count(self.Node.id)  # pylint: disable=no-member
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

        ctime_by_day = {_[0].strftime('%Y-%m-%d'): _[1] for _ in stat}
        retdict['ctime_by_day'] = ctime_by_day

        return retdict
        # Still not containing all dates
