# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from datetime import datetime
import aiida.backends.sqlalchemy

from sqlalchemy import and_, or_, not_
from sqlalchemy.types import Integer, Float, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import cast


from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import Cast, Label
from sqlalchemy_utils.types.choice import Choice

from aiida.common.exceptions import (
        InputValidationError, DbContentError,
        MissingPluginError, ConfigurationError
    )
from aiida.common.exceptions import InputValidationError
from aiida.backends.general.querybuilder_interface import QueryBuilderInterface
from aiida.backends.utils import _get_column
from sqlalchemy.sql.elements import Cast

from sqlalchemy.sql.expression import FunctionElement

from sqlalchemy.ext.compiler import compiles

class jsonb_array_length(FunctionElement):
    name = 'jsonb_array_len'

@compiles(jsonb_array_length)
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_array_length(%s)" % compiler.process(element.clauses)


class array_length(FunctionElement):
    name = 'array_len'

@compiles(array_length)
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "array_length(%s)" % compiler.process(element.clauses)



class jsonb_typeof(FunctionElement):
    name = 'jsonb_typeof'

@compiles(jsonb_typeof  )
def compile(element, compiler, **kw):
    """
    Get length of array defined in a JSONB column
    """
    return "jsonb_typeof(%s)" % compiler.process(element.clauses)


class QueryBuilderImplSQLA(QueryBuilderInterface):
    """
    QueryBuilder to use with SQLAlchemy-backend and
    schema defined in backends.sqlalchemy.models
    """

    def __init__(self, *args, **kwargs):
        #~ from aiida.orm.implementation.sqlalchemy.node import Node as AiidaNode
        #~ from aiida.orm.implementation.sqlalchemy.group import Group as AiidaGroup
        #~ from aiida.orm.implementation.sqlalchemy.computer import Computer as AiidaComputer
        #~ from aiida.orm.implementation.sqlalchemy.user import User as AiidaUser
        #~ self.Link               = DbLink
        #~ self.Node               = DbNode
        #~ self.Computer           = DbComputer
        #~ self.User               = DbUser
        #~ self.Group              = DbGroup
        #~ self.table_groups_nodes = table_groups_nodes
        #~ self.AiidaNode          = AiidaNode
        #~ self.AiidaGroup         = AiidaGroup
        #~ self.AiidaComputer      = AiidaComputer
        #~ self.AiidaUser          = AiidaUser
        super(QueryBuilderImplSQLA, self).__init__(*args, **kwargs)


    @property
    def Node(self):
        import aiida.backends.sqlalchemy.models.node
        return aiida.backends.sqlalchemy.models.node.DbNode
    @property
    def Link(self):
        import aiida.backends.sqlalchemy.models.node
        return aiida.backends.sqlalchemy.models.node.DbLink

    @property
    def Computer(self):
        import aiida.backends.sqlalchemy.models.computer
        return aiida.backends.sqlalchemy.models.computer.DbComputer

    @property
    def User(self):
        import aiida.backends.sqlalchemy.models.user
        return aiida.backends.sqlalchemy.models.user.DbUser

    @property
    def Group(self):
        import aiida.backends.sqlalchemy.models.group
        return aiida.backends.sqlalchemy.models.group.DbGroup

    @property
    def table_groups_nodes(self):
        import aiida.backends.sqlalchemy.models.group
        return aiida.backends.sqlalchemy.models.group.table_groups_nodes

    @property
    def AiidaNode(self):
        import aiida.orm.implementation.sqlalchemy.node
        return aiida.orm.implementation.sqlalchemy.node.Node

    @property
    def AiidaGroup(self):
        import aiida.orm.implementation.sqlalchemy.group
        return aiida.orm.implementation.sqlalchemy.group.Group

    @property
    def AiidaUser(self):
        import aiida.orm.implementation.sqlalchemy.user
        return aiida.orm.implementation.sqlalchemy.user.User

    @property
    def AiidaComputer(self):
        import aiida.orm.implementation.sqlalchemy.computer
        return aiida.orm.implementation.sqlalchemy.computer.Computer


    def prepare_with_dbpath(self):
        from aiida.backends.sqlalchemy.models.node import DbPath
        self.Path = DbPath

    def get_session(self):
        return aiida.backends.sqlalchemy.get_scoped_session()

    def modify_expansions(self, alias, expansions):
        """
        For sqlalchemy, there are no additional expansions for now, so
        I am returning an empty list
        """
        if issubclass(alias._sa_class_manager.class_, self.Computer):
            try:
                expansions.remove('metadata')
                expansions.append('_metadata')
            except KeyError:
                pass

        return expansions


    def get_filter_expr(
            self, operator, value, attr_key, is_attribute,
            alias=None, column=None, column_name=None
        ):
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
                raise InputValidationError(
                    "You have to give an integer when comparing to a length"
                )
        elif operator in ('like', 'ilike'):
            if not isinstance(value, basestring):
                raise InputValidationError(
                    "Value for operator {} has to be a string (you gave {})"
                    "".format(operator, value)
                )

        elif operator == 'in':
            value_type_set = set([type(i) for i in value])
            if len(value_type_set) > 1:
                raise InputValidationError(
                        '{}  contains more than one type'.format(value)
                    )
            elif len(value_type_set) == 0:
                raise InputValidationError(
                        '{}  contains is an empty list'.format(value)
                    )
        elif operator in ('and', 'or'):
            expressions_for_this_path = []
            for filter_operation_dict in value:
                for newoperator, newvalue in filter_operation_dict.items():
                    expressions_for_this_path.append(
                            self.get_filter_expr(
                                    newoperator, newvalue,
                                    attr_key=attr_key, is_attribute=is_attribute,
                                    alias=alias, column=column,
                                    column_name=column_name
                                )
                        )
            if operator == 'and':
                expr = and_(*expressions_for_this_path)
            elif operator == 'or':
                 expr = or_(*expressions_for_this_path)

        if expr is None:
            if is_attribute:
                expr = self.get_filter_expr_from_attributes(
                        operator, value, attr_key,
                        column=column, column_name=column_name, alias=alias
                    )
            else:
                if column is None:
                    if (alias is None) and (column_name is None):
                        raise Exception(
                            "I need to get the column but do not know \n"
                            "the alias and the column name"
                        )
                    column = _get_column(column_name, alias)
                expr = self._get_filter_expr_from_column(operator, value, column)
        if negation:
            return not_(expr)
        return expr


    def _get_filter_expr_from_column(self, operator, value, column):

        # Label is used because it is what is returned for the
        # 'state' column by the hybrid_column construct
        if not isinstance(column, (Cast, InstrumentedAttribute, Label)):
            raise TypeError(
                'column ({}) {} is not a valid column'.format(
                    type(column), column
                )
            )
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
            # This operator can only exist for strings, so I cast to avoid problems
            # as they occured for the UUID, which does not support the like operator
            expr = database_entity.cast(String).like(value)
        elif operator == 'ilike':
            expr = database_entity.cast(String).ilike(value)
        elif operator == 'in':
            expr = database_entity.in_(value)
        else:
            raise InputValidationError(
                'Unknown operator {} for filters on columns'.format(operator)
            )
        return expr



    def get_filter_expr_from_attributes(
            self, operator, value, attr_key,
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
            column = _get_column(column_name, alias)

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
        elif operator in ('<=', '=<'):
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


    def get_projectable_attribute(
            self, alias, column_name, attrpath,
            cast=None, **kwargs
        ):
        """
        :returns: An attribute store in a JSON field of the give column
        """

        entity = _get_column(column_name, alias)[(attrpath)]
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




    def get_aiida_res(self, key, res):
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





    def get_ormclass(self, cls, ormclasstype):
        """
        Return the valid ormclass for the connections
        """
        # Checks whether valid cls and ormclasstype are done before

        # If it is a class:
        if cls:
            # Nodes:
            if issubclass(cls, self.Node):
                # If something pass an ormclass node
                # Users wouldn't do that, by why not...
                ormclasstype = self.AiidaNode._plugin_type_string
                query_type_string = self.AiidaNode._query_type_string
                ormclass = cls
            elif issubclass(cls, self.AiidaNode):
                ormclasstype = cls._plugin_type_string
                query_type_string = cls._query_type_string
                ormclass = self.Node
            # Groups:
            elif issubclass(cls, self.Group):
                ormclasstype = 'group'
                query_type_string = None
                ormclass = cls
            elif issubclass(cls, self.AiidaGroup):
                ormclasstype = 'group'
                query_type_string = None
                ormclass = self.Group
            # Computers:
            elif issubclass(cls, self.Computer):
                ormclasstype = 'computer'
                query_type_string = None
                ormclass = cls
            elif issubclass(cls, self.AiidaComputer):
                ormclasstype = 'computer'
                query_type_string = None
                ormclass = self.Computer

            # Users
            elif issubclass(cls, self.User):
                ormclasstype = 'user'
                query_type_string = None
                ormclass = cls
            elif issubclass(cls, self.AiidaUser):
                ormclasstype = 'user'
                query_type_string = None
                ormclass = self.User
            else:
                raise InputValidationError(
                        "\n\n\n"
                        "I do not know what to do with {}"
                        "\n\n\n".format(cls)
                    )
        # If it is not a class
        else:
            if ormclasstype.lower() == 'group':
                ormclasstype = ormclasstype.lower()
                query_type_string = None
                ormclass = self.Group
            elif ormclasstype.lower() == 'computer':
                ormclasstype = ormclasstype.lower()
                query_type_string = None
                ormclass = self.Computer
            elif ormclasstype.lower() == 'user':
                ormclasstype = ormclasstype.lower()
                query_type_string = None
                ormclass = self.User
            else:
                # At this point, it has to be a node.
                # The only valid string at this point is a string
                # that matches exactly the _plugin_type_string
                # of a node class
                from aiida.common.old_pluginloader import from_type_to_pluginclassname
                from aiida.common.pluginloader import load_plugin
                ormclass = self.Node
                try:
                    pluginclassname = from_type_to_pluginclassname(ormclasstype)

                    # I want to check at this point if that is a valid class,
                    # so I use the load_plugin to load the plugin class
                    # and use the classes _plugin_type_string attribute
                    # In the future, assuming the user knows what he or she is doing
                    # we could remove that check
                    # The query_type_string we can get from
                    # the aiida.common.old_pluginloader function get_query_type_string
                    PluginClass = load_plugin(self.AiidaNode, 'aiida.orm', pluginclassname)
                except (DbContentError, MissingPluginError) as e:
                    raise InputValidationError(
                        "\nYou provide a vertice of the path with\n"
                        "type={}\n"
                        "But that string is not a valid type string\n"
                        "Exception raise during check\n"
                        "{}".format(ormclasstype, e)
                    )


                ormclasstype = PluginClass._plugin_type_string
                query_type_string = PluginClass._query_type_string

        return ormclass, ormclasstype, query_type_string

    def yield_per(self, query, batch_size):
        """
        :param count: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        try:
            return query.yield_per(batch_size)
        except Exception as e:
            # exception was raised. Rollback the session
            self.get_session().rollback()
            raise e



    def count(self, query):

        try:
            return query.count()
        except Exception as e:
            # exception was raised. Rollback the session
            self.get_session().rollback()
            raise e


    def first(self, query):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """
        try:
            return query.first()
        except Exception as e:
            # exception was raised. Rollback the session
            self.get_session().rollback()
            raise e


    def iterall(self, query, batch_size, tag_to_index_dict):
        try:
            results = query.yield_per(batch_size)

            if len(tag_to_index_dict) == 1:
                # Sqlalchemy, for some strange reason, does not return a list of lsits
                # if you have provided an ormclass

                if tag_to_index_dict.values() == ['*']:
                    for rowitem in results:
                        yield [self.get_aiida_res(tag_to_index_dict[0], rowitem)]
                else:
                    for rowitem, in results:
                        yield [self.get_aiida_res(tag_to_index_dict[0], rowitem)]
            elif len(tag_to_index_dict) > 1:
                for resultrow in results:
                    yield [
                        self.get_aiida_res(tag_to_index_dict[colindex], rowitem)
                        for colindex, rowitem
                        in enumerate(resultrow)
                    ]
            else:
                raise Exception("Got an empty dictionary")
        except Exception as e:
            self.get_session().rollback()
            raise e



    def iterdict(self, query, batch_size, tag_to_projected_entity_dict):


        # Wrapping everything in an atomic transaction:
        try:
            results = query.yield_per(batch_size)
            nr_items = sum([len(v) for v in tag_to_projected_entity_dict.values()])
            if nr_items > 1:
                for this_result in results:
                    yield {
                        tag:{
                            attrkey:self.get_aiida_res(
                                    attrkey, this_result[index_in_sql_result]
                                )
                            for attrkey, index_in_sql_result
                            in projected_entities_dict.items()
                        }
                        for tag, projected_entities_dict
                        in tag_to_projected_entity_dict.items()
                    }
            elif nr_items == 1:
                # I this case, sql returns a  list, where each listitem is the result
                # for one row. Here I am converting it to a list of lists (of length 1)
                if [ v for entityd in tag_to_projected_entity_dict.values() for v in entityd.keys()] == ['*']:
                    for this_result in results:
                        yield {
                            tag:{
                                attrkey : self.get_aiida_res(attrkey, this_result)
                                for attrkey, position in projected_entities_dict.items()
                            }
                            for tag, projected_entities_dict in tag_to_projected_entity_dict.items()
                        }
                else:
                    for this_result, in results:
                        yield {
                            tag:{
                                attrkey : self.get_aiida_res(attrkey, this_result)
                                for attrkey, position in projected_entities_dict.items()
                            }
                            for tag, projected_entities_dict in tag_to_projected_entity_dict.items()
                        }
            else:
                raise Exception("Got an empty dictionary")
        except Exception as e:
            self.get_session().rollback()
            raise e

