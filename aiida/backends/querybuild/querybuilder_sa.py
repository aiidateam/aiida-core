# -*- coding: utf-8 -*-

from datetime import datetime

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

try:
    import ultrajson
    from functools import partial
    json_loads = partial(ultrajson.loads, precise_float=True)
except ImportError:
    from json import loads as json_loads



from aiida.backends.querybuild.querybuilder_base import AbstractQueryBuilder
from sa_init import (
        and_, or_, not_,
        Integer, Float, Boolean, JSONB, DateTime,
        jsonb_array_length, jsonb_typeof
    )

from sqlalchemy_utils.types.choice import Choice
from aiida.backends.sqlalchemy import session as sa_session
from aiida.backends.sqlalchemy.models.node import DbNode, DbLink, DbPath
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.group import DbGroup, table_groups_nodes
from aiida.backends.sqlalchemy.models.user import DbUser

from aiida.common.exceptions import InputValidationError



class QueryBuilder(AbstractQueryBuilder):
    """
    QueryBuilder to use with SQLAlchemy-backend and
    schema defined in backends.sqlalchemy.models
    """

    def __init__(self, *args, **kwargs):
        from aiida.orm.implementation.sqlalchemy.node import Node as AiidaNode
        from aiida.orm.implementation.sqlalchemy.group import Group as AiidaGroup
        from aiida.orm.implementation.sqlalchemy.computer import Computer as AiidaComputer
        from aiida.orm.implementation.sqlalchemy.user import User as AiidaUser
        self.Link               = DbLink
        self.Path               = DbPath
        self.Node               = DbNode
        self.Computer           = DbComputer
        self.User               = DbUser
        self.Group              = DbGroup
        self.table_groups_nodes = table_groups_nodes
        self.AiidaNode          = AiidaNode
        self.AiidaGroup         = AiidaGroup
        self.AiidaComputer      = AiidaComputer
        self.AiidaUser          = AiidaUser
        super(QueryBuilder, self).__init__(*args, **kwargs)

    def _get_session(self):
        return sa_session

    @classmethod
    def _get_filter_expr_from_attributes(
            cls, operator, value, attr_key,
            column=None, column_name=None,
            alias=None):

        def cast_according_to_type(path_in_json, value):
            if isinstance(value, bool):
                type_filter = jsonb_typeof(path_in_json)=='boolean'
                casted_entity = path_in_json.cast(Boolean)
            elif isinstance(value, (int, float)):
                type_filter = jsonb_typeof(path_in_json)=='number'
                casted_entity = path_in_json.cast(Float)
            elif isinstance(value, dict) or value is None:
                type_filter = jsonb_typeof(path_in_json)=='object'
                casted_entity = path_in_json.cast(JSONB) # BOOLEANS?
            elif isinstance(value, dict):
                type_filter = jsonb_typeof(path_in_json)=='array'
                casted_entity = path_in_json.cast(JSONB) # BOOLEANS?
            elif isinstance(value, (str, unicode)):
                type_filter = jsonb_typeof(path_in_json)=='string'
                casted_entity = path_in_json.astext
            elif value is None:
                type_filter = jsonb_typeof(path_in_json)=='null'
                casted_entity = path_in_json.cast(JSONB) # BOOLEANS?
            elif isinstance(value, datetime):
                # type filter here is filter whether this attributes stores
                # a string and a filter whether this string
                # is compatible with a datetime (using a regex)
                #  - What about historical values (BC, or before 1000AD)??
                #  - Different ways to represent the timezone

                type_filter = jsonb_typeof(path_in_json)=='string'
                regex_filter = path_in_json.astext.op(
                        "SIMILAR TO"
                    )("\d\d\d\d-[0-1]\d-[0-3]\dT[0-2]\d:[0-5]\d:\d\d\.\d+((\+|\-)\d\d:\d\d)?")
                type_filter =  and_(type_filter, regex_filter)
                casted_entity = path_in_json.cast(DateTime)
            else:
                raise Exception('Unknown type {}'.format(type(value)))
            return type_filter, casted_entity

        if column is None:
            column = cls._get_column(column_name, alias)

        database_entity = column[tuple(attr_key)]
        if operator == '==':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity == value)
        elif operator == '>':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity > value)
        elif operator == '<':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity < value)
        elif operator in ('>=', '=>'):
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity >= value)
        elif operator == ('<=', '=<'):
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity <= value)
        elif operator == 'of_type':
            # http://www.postgresql.org/docs/9.5/static/functions-json.html
            #  Possible types are object, array, string, number, boolean, and null.
            valid_types = ('object', 'array', 'string', 'number', 'boolean', 'null')
            if value not in valid_types:
                raise InputValidationError(
                    "value {} for of_type is not among valid types\n"
                    "{}".format(value, valid_types)
                )
            expr = jsonb_typeof(database_entity) == value
        elif operator == 'like':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity.like(value))
        elif operator == 'ilike':
            type_filter, casted_entity = cast_according_to_type(database_entity, value)
            expr = and_(type_filter, casted_entity.ilike(value))
        elif operator == 'in':
            type_filter, casted_entity = cast_according_to_type(database_entity, value[0])
            expr = and_(type_filter, casted_entity.in_(value))
        elif operator == 'contains':
            expr = database_entity.cast(JSONB).contains(value)
        elif operator == 'has_key':
            expr = database_entity.cast(JSONB).has_key(value)
        elif operator == 'of_length':
            expr=  and_(
                jsonb_typeof(database_entity) == 'array',
                jsonb_array_length(database_entity.cast(JSONB)) == value
            )
        elif operator == 'longer':
            expr = and_(
                jsonb_typeof(database_entity) == 'array',
                jsonb_array_length(database_entity.cast(JSONB)) > value
            )
        elif operator == 'shorter':
            expr =  and_(
                jsonb_typeof(database_entity) == 'array',
                jsonb_array_length(database_entity.cast(JSONB)) < value
            )
        else:
            raise InputValidationError(
                "Unknown operator {} for filters in JSON field".format(operator)
            )
        return expr


    def _get_projectable_attribute(
            self, alias, column_name, attrpath,
            cast=None, **kwargs
        ):
        """
        :returns: An attribute store in a JSON field of the give column
        """

        entity = self._get_column(column_name, alias)[(attrpath)]
        if cast is None:
            entity = entity
        elif cast=='f':
            entity = entity.cast(Float)
        elif cast=='i':
            entity = entity.cast(Integer)
        elif cast=='b':
            entity = entity.cast(Boolean)
        elif cast=='t':
            entity = entity.astext
        elif cast=='j':
            entity = entity.cast(JSONB)
        elif cast=='d':
            entity = entity.cast(DateTime)
        else:
            raise InputValidationError(
                "Unkown casting key {}".format(cast)
            )
        return entity




    def _get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes). Choice (sqlalchemy_utils)
        will return their value

        :param key: The key
        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        if isinstance(res, (self.Group, self.Node, self.Computer, self.User)):
            returnval = res.get_aiida_class()
        elif isinstance(res, Choice):
            returnval = res.value
        else:
            returnval = res
        return returnval


