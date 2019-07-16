# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Django query builder"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import uuid
import six

from aldjemy import core
# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module, import-error
from sqlalchemy_utils.types.choice import Choice
from sqlalchemy import and_, or_, not_, case
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import Integer, Float, Boolean, DateTime

import aiida.backends.djsite.db.models as djmodels
from aiida.common.exceptions import InputValidationError
from aiida.orm.implementation.querybuilder import BackendQueryBuilder


class jsonb_array_length(FunctionElement):  # pylint: disable=invalid-name
    # pylint: disable=too-few-public-methods
    name = 'jsonb_array_len'


@compiles(jsonb_array_length)
def compile(element, compiler, **_kw):  # pylint: disable=function-redefined, redefined-builtin
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_array_length(%s)" % compiler.process(element.clauses)


class array_length(FunctionElement):  # pylint: disable=invalid-name
    # pylint: disable=too-few-public-methods
    name = 'array_len'


@compiles(array_length)
def compile(element, compiler, **_kw):  # pylint: disable=function-redefined
    """
    Get length of array defined in a JSONB column
    """
    return "array_length(%s)" % compiler.process(element.clauses)


class jsonb_typeof(FunctionElement):  # pylint: disable=invalid-name
    # pylint: disable=too-few-public-methods
    name = 'jsonb_typeof'


@compiles(jsonb_typeof)
def compile(element, compiler, **_kw):  # pylint: disable=function-redefined
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_typeof(%s)" % compiler.process(element.clauses)


class DjangoQueryBuilder(BackendQueryBuilder):
    """Django query builder"""

    # pylint: disable=too-many-public-methods,no-member

    def __init__(self, backend):
        BackendQueryBuilder.__init__(self, backend)

    @property
    def Node(self):
        return djmodels.DbNode.sa

    @property
    def Link(self):
        return djmodels.DbLink.sa

    @property
    def Computer(self):
        return djmodels.DbComputer.sa

    @property
    def User(self):
        return djmodels.DbUser.sa

    @property
    def Group(self):
        return djmodels.DbGroup.sa

    @property
    def AuthInfo(self):
        return djmodels.DbAuthInfo.sa

    @property
    def Comment(self):
        return djmodels.DbComment.sa

    @property
    def Log(self):
        return djmodels.DbLog.sa

    @property
    def table_groups_nodes(self):
        return core.Cache.meta.tables['db_dbgroup_dbnodes']

    def get_filter_expr(self, operator, value, attr_key, is_attribute, alias=None, column=None, column_name=None):
        """
        Applies a filter on the alias given.
        Expects the alias of the ORM-class on which to filter, and filter_spec.
        Filter_spec contains the specification on the filter.
        Expects:

        :param operator: The operator to apply, see below for further details
        :param value:
            The value for the right side of the expression,
            the value you want to compare with.

        :param path: The path leading to the value

        :param attr_key: Boolean, whether the value is in a json-column,
            or in an attribute like table.


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
        # pylint: disable=too-many-branches,too-many-arguments
        # pylint: disable=too-many-branches,too-many-arguments

        expr = None
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
                raise InputValidationError("You have to give an integer when comparing to a length")
        elif operator in ('like', 'ilike'):
            if not isinstance(value, six.string_types):
                raise InputValidationError("Value for operator {} has to be a string (you gave {})"
                                           "".format(operator, value))
        elif operator == 'in':
            value_type_set = set(type(i) for i in value)
            if len(value_type_set) > 1:
                raise InputValidationError('{}  contains more than one type'.format(value))
            elif not value_type_set:
                raise InputValidationError('{}  contains is an empty list'.format(value))
        elif operator in ('and', 'or'):
            expressions_for_this_path = []
            for filter_operation_dict in value:
                for newoperator, newvalue in filter_operation_dict.items():
                    expressions_for_this_path.append(
                        self.get_filter_expr(
                            newoperator,
                            newvalue,
                            attr_key=attr_key,
                            is_attribute=is_attribute,
                            alias=alias,
                            column=column,
                            column_name=column_name))
            if operator == 'and':
                expr = and_(*expressions_for_this_path)
            elif operator == 'or':
                expr = or_(*expressions_for_this_path)

        if expr is None:
            if is_attribute:
                expr = self.get_filter_expr_from_attributes(
                    operator, value, attr_key, column=column, column_name=column_name, alias=alias)
            else:
                if column is None:
                    if (alias is None) and (column_name is None):
                        raise Exception("I need to get the column but do not know the alias and the column name")
                    column = self.get_column(column_name, alias)
                expr = self.get_filter_expr_from_column(operator, value, column)
        if negation:
            return not_(expr)
        return expr

    @staticmethod
    def get_session():
        from aiida.manage.configuration import get_config
        from aiida.backends.sqlalchemy import reset_session
        from aiida.backends.sqlalchemy import get_scoped_session

        if get_scoped_session() is None:
            config = get_config()
            profile = config.current_profile
            reset_session(profile)

        return get_scoped_session()

    def modify_expansions(self, alias, expansions):
        """
        For django, there are no additional expansions for now, so
        I am returning an empty list
        """
        return expansions

    def get_filter_expr_from_attributes(self, operator, value, attr_key, column=None, column_name=None, alias=None):
        # Too many everything!
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
            elif isinstance(value, six.string_types):
                type_filter = jsonb_typeof(path_in_json) == 'string'
                casted_entity = path_in_json.astext
            elif value is None:
                type_filter = jsonb_typeof(path_in_json) == 'null'
                casted_entity = path_in_json.astext.cast(JSONB)  # BOOLEANS?
            else:
                raise TypeError('Unknown type {}'.format(type(value)))
            return type_filter, casted_entity

        if column is None:
            column = self.get_column(column_name, alias)

        database_entity = column[tuple(attr_key)]
        if operator == '==':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity == value)], else_=False)
        elif operator == '>':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity > value)], else_=False)
        elif operator == '<':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity < value)], else_=False)
        elif operator in ('>=', '=>'):
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity >= value)], else_=False)
        elif operator in ('<=', '=<'):
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity <= value)], else_=False)
        elif operator == 'of_type':
            # http://www.postgresql.org/docs/9.5/static/functions-json.html
            #  Possible types are object, array, string, number, boolean, and null.
            valid_types = ('object', 'array', 'string', 'number', 'boolean', 'null')
            if value not in valid_types:
                raise InputValidationError("value {} for of_type is not among valid types\n"
                                           "{}".format(value, valid_types))
            expr = jsonb_typeof(database_entity) == value
        elif operator == 'like':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity.like(value))], else_=False)
        elif operator == 'ilike':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = case([(type_filter, casted_entity.ilike(value))], else_=False)
        elif operator == 'in':
            type_filter, casted_entity = cast_according_to_type(database_entity, value[0])
            expr = case([(type_filter, casted_entity.in_(value))], else_=False)
        elif operator == 'contains':
            expr = database_entity.cast(JSONB).contains(value)
        elif operator == 'has_key':
            expr = database_entity.cast(JSONB).has_key(value)  # noqa
        elif operator == 'of_length':
            expr = case(
                [(jsonb_typeof(database_entity) == 'array', jsonb_array_length(database_entity.cast(JSONB)) == value)],
                else_=False)

        elif operator == 'longer':
            expr = case(
                [(jsonb_typeof(database_entity) == 'array', jsonb_array_length(database_entity.cast(JSONB)) > value)],
                else_=False)
        elif operator == 'shorter':
            expr = case(
                [(jsonb_typeof(database_entity) == 'array', jsonb_array_length(database_entity.cast(JSONB)) < value)],
                else_=False)
        else:
            raise InputValidationError("Unknown operator {} for filters in JSON field".format(operator))
        return expr

    def get_projectable_attribute(self, alias, column_name, attrpath, cast=None, **kwargs):  # pylint: disable=redefined-outer-name
        """
        :returns: An attribute store in a JSON field of the give column
        """
        entity = self.get_column(column_name, alias)[attrpath]
        if cast is None:
            entity = entity
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
            raise InputValidationError("Unkown casting key {}".format(cast))
        return entity

    def get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes). Choice (sqlalchemy_utils)
        will return their value

        :param key: The key
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        if isinstance(res, Choice):
            result = res.value
        elif isinstance(res, uuid.UUID):
            result = six.text_type(res)
        else:
            try:
                result = self._backend.get_backend_entity(res)
            except TypeError:
                result = res

        return result

    def yield_per(self, query, batch_size):
        """
        :param count: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        from django.db import transaction
        with transaction.atomic():
            return query.yield_per(batch_size)

    def count(self, query):

        from django.db import transaction
        with transaction.atomic():
            return query.count()

    def first(self, query):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """
        from django.db import transaction
        with transaction.atomic():
            return query.first()

    def iterall(self, query, batch_size, tag_to_index_dict):
        from django.db import transaction
        if not tag_to_index_dict:
            raise ValueError("Got an empty dictionary: {}".format(tag_to_index_dict))

        with transaction.atomic():
            results = query.yield_per(batch_size)

            if len(tag_to_index_dict) == 1:
                # Sqlalchemy, for some strange reason, does not return a list of lists
                # if you have provided an ormclass

                if list(tag_to_index_dict.values()) == ['*']:
                    for rowitem in results:
                        yield [self.get_aiida_res(tag_to_index_dict[0], rowitem)]
                else:
                    for rowitem, in results:
                        yield [self.get_aiida_res(tag_to_index_dict[0], rowitem)]
            elif len(tag_to_index_dict) > 1:
                for resultrow in results:
                    yield [
                        self.get_aiida_res(tag_to_index_dict[colindex], rowitem)
                        for colindex, rowitem in enumerate(resultrow)
                    ]

    def iterdict(self, query, batch_size, tag_to_projected_properties_dict, tag_to_alias_map):
        from django.db import transaction

        def get_table_name(aliased_class):
            """ Returns the table name given an Aliased class based on Aldjemy"""
            return aliased_class._aliased_insp._target.table.name  # pylint: disable=protected-access

        nr_items = sum(len(v) for v in tag_to_projected_properties_dict.values())

        if not nr_items:
            raise ValueError("Got an empty dictionary")

        # Wrapping everything in an atomic transaction:
        with transaction.atomic():
            results = query.yield_per(batch_size)
            # Two cases: If one column was asked, the database returns a matrix of rows * columns:
            if nr_items > 1:
                for this_result in results:
                    yield {
                        tag: {
                            self.get_corresponding_property(
                                get_table_name(tag_to_alias_map[tag]), attrkey, self.inner_to_outer_schema):
                            self.get_aiida_res(attrkey, this_result[index_in_sql_result])
                            for attrkey, index_in_sql_result in projected_entities_dict.items()
                        } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                    }
            elif nr_items == 1:
                # I this case, sql returns a  list, where each listitem is the result
                # for one row. Here I am converting it to a list of lists (of length 1)
                if [v for entityd in tag_to_projected_properties_dict.values() for v in entityd.keys()] == ['*']:
                    for this_result in results:
                        yield {
                            tag: {
                                self.get_corresponding_property(
                                    get_table_name(tag_to_alias_map[tag]), attrkey, self.inner_to_outer_schema):
                                self.get_aiida_res(attrkey, this_result)
                                for attrkey, position in projected_entities_dict.items()
                            } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                        }
                else:
                    for this_result, in results:
                        yield {
                            tag: {
                                self.get_corresponding_property(
                                    get_table_name(tag_to_alias_map[tag]), attrkey, self.inner_to_outer_schema):
                                self.get_aiida_res(attrkey, this_result)
                                for attrkey, position in projected_entities_dict.items()
                            } for tag, projected_entities_dict in tag_to_projected_properties_dict.items()
                        }

    def get_column_names(self, alias):
        """
        Given the backend specific alias, return the column names that correspond to the aliased table.
        """
        # pylint: disable=protected-access
        return [
            str(c).replace(alias._aliased_insp.class_.table.name + '.', '')
            for c in alias._aliased_insp.class_.table._columns._all_columns
        ]
