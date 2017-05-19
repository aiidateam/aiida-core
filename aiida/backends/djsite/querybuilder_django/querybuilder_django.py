# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


import datetime
from datetime import datetime
from json import loads as json_loads

#~ import aiida.backends.djsite.querybuilder_django.dummy_model as dummy_model
import dummy_model
from aiida.backends.djsite.db.models import DbAttribute, DbExtra, ObjectDoesNotExist


from sqlalchemy import and_, or_, not_, exists, select, exists, case
from sqlalchemy.types import Float,  String
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import InstrumentedAttribute

from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.elements import Cast, Label
from aiida.common.exceptions import InputValidationError
from aiida.backends.general.querybuilder_interface import QueryBuilderInterface
from aiida.backends.utils import _get_column
from aiida.common.exceptions import (
        InputValidationError, DbContentError,
        MissingPluginError, ConfigurationError
    )

class QueryBuilderImplDjango(QueryBuilderInterface):

    def __init__(self, *args, **kwargs):
        #~ from aiida.orm.implementation.django.node import Node as AiidaNode
        #~ from aiida.orm.implementation.django.group import Group as AiidaGroup
        #~ from aiida.orm.implementation.django.computer import Computer as AiidaComputer
        #~ from aiida.orm.implementation.django.user import User as AiidaUser

        #~ self.Link               = dummy_model.DbLink
        #~ self.Node               = dummy_model.DbNode
        #~ self.Computer           = dummy_model.DbComputer
        #~ self.User               = dummy_model.DbUser
        #~ self.Group              = dummy_model.DbGroup
        #~ self.table_groups_nodes = dummy_model.table_groups_nodes
        #~ self.AiidaNode          = AiidaNode
        #~ self.AiidaGroup         = AiidaGroup
        #~ self.AiidaComputer      = AiidaComputer
        #~ self.AiidaUser          = AiidaUser

        super(QueryBuilderImplDjango, self).__init__(*args, **kwargs)


    @property
    def Node(self):
        return dummy_model.DbNode

    @property
    def Link(self):
        return dummy_model.DbLink

    @property
    def Computer(self):
        return dummy_model.DbComputer

    @property
    def User(self):
        return dummy_model.DbUser

    @property
    def Group(self):
        return dummy_model.DbGroup

    @property
    def table_groups_nodes(self):
        return dummy_model.table_groups_nodes

    @property
    def AiidaNode(self):
        import aiida.orm.implementation.django.node
        return aiida.orm.implementation.django.node.Node

    @property
    def AiidaGroup(self):
        import aiida.orm.implementation.django.group
        return aiida.orm.implementation.django.group.Group

    @property
    def AiidaUser(self):
        import aiida.orm.implementation.django.user
        return aiida.orm.implementation.django.user.User

    @property
    def AiidaComputer(self):
        import aiida.orm.implementation.django.computer
        return aiida.orm.implementation.django.computer.Computer


    def get_filter_expr_from_column(self, operator, value, column):

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
            expr = database_entity.like(value)
        elif operator == 'ilike':
            expr = database_entity.ilike(value)
        elif operator == 'in':
            expr = database_entity.in_(value)
        else:
            raise InputValidationError(
                'Unknown operator {} for filters on columns'.format(operator)
            )
        return expr


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
                expr = self.get_filter_expr_from_column(operator, value, column)
        if negation:
            return not_(expr)
        return expr




    def prepare_with_dbpath(self):
        #~ from aiida.backends.querybuild.dummy_model import DbPath as DummyPath
        self.Path = dummy_model.DbPath



    def get_session(self):
        return dummy_model.get_aldjemy_session()
        # return dummy_model.session


    def modify_expansions(self, alias, expansions):
        """
        For the Django schema, we have as additioanl expansions 'attributes'
        and 'extras'
        """

        if issubclass(alias._sa_class_manager.class_, self.Node):
            expansions.append("attributes")
            expansions.append("extras")
        elif issubclass(alias._sa_class_manager.class_, self.Computer):
            try:
                expansions.remove('metadata')
                expansions.append('_metadata')
            except KeyError:
                pass

        return expansions

    def get_filter_expr_from_attributes(
            self, operator, value, attr_key,
            column=None, column_name=None,
            alias=None):

        def get_attribute_db_column(mapped_class, dtype, castas=None):
            if dtype == 't':
                mapped_entity = mapped_class.tval
            elif dtype == 'b':
                mapped_entity = mapped_class.bval
                #~ mapped_entity = cast(mapped_class.value_str, Boolean)
            elif dtype == 'f':
                mapped_entity = mapped_class.fval
                #~ mapped_entity = cast(mapped_class.value_str, Float)
            elif dtype == 'i':
                mapped_entity = mapped_class.ival
                #~ mapped_entity = cast(mapped_class.value_str, Integer)
            elif dtype == 'd':
                mapped_entity = mapped_class.dval
            else:
                raise InputValidationError(
                    "I don't know what to do with dtype {}".format(dtype)
                )
            if castas == 't':
                mapped_entity = cast(mapped_entity, String)
            elif castas == 'f':
                mapped_entity = cast(mapped_entity, Float)

            return mapped_entity
        if column:
            mapped_class = column.prop.mapper.class_
        else:
            column = getattr(alias, column_name)
            mapped_class = column.prop.mapper.class_
        # Ok, so we have an attribute key here.
        # Unless cast is specified, will try to infer my self where the value
        # is stored
        # Datetime -> dval
        # bool -> bval
        # string -> tval
        # integer -> ival, fval (cast ival to float)
        # float -> ival, fval (cast ival to float)
        # If the user specified of_type ??
        # That is basically a query for where the value is sitting
        #   (which db_column in the dbattribtues)
        # If the user specified in what to cast, he wants an operation to
        #   be performed to cast the value to a different type
        if  isinstance(value, (list, tuple)):
            value_type_set = set([type(i) for i in value])
            if len(value_type_set) > 1:
                raise InputValidationError( '{}  contains more than one type'.format(value))
            elif len(value_type_set) == 0:
                raise InputValidationError('Given list is empty, cannot determine type')
            else:
                value_to_consider = value[0]
        else:
            value_to_consider = value


        # First cases, I maybe need not do anything but just count the
        # number of entries
        if operator in ('of_length', 'shorter', 'longer'):
            raise NotImplementedError(
                "Filtering by lengths of arrays or lists is not implemented\n"
                "in the Django-Backend"
            )
        elif operator  == 'of_type':
            raise NotImplementedError(
                "Filtering by type is not implemented\n"
                "in the Django-Backend"
            )
        elif operator == 'contains':
            raise NotImplementedError(
                "Contains is not implemented in the Django-backend"
            )


        elif operator=='has_key':
            if issubclass(mapped_class, dummy_model.DbAttribute):
                expr = alias.attributes.any(mapped_class.key == '.'.join(attr_key+[value]))
            elif issubclass(mapped_class, dummy_model.DbExtra):
                expr = alias.extras.any(mapped_class.key == '.'.join(attr_key+[value]))
            else:
                raise Exception("I was given {} as an attribute base class".format(mapped_class))

        else:
            types_n_casts = []
            if isinstance(value_to_consider, basestring):
                types_n_casts.append(('t', None))
            elif isinstance(value_to_consider, bool):
                types_n_casts.append(('b', None))
            elif isinstance(value_to_consider, (int, float)):
                types_n_casts.append(('f', None))
                types_n_casts.append(('i', 'f'))
            elif isinstance(value_to_consider, datetime):
                types_n_casts.append(('d', None))

            expressions = []
            for dtype, castas in types_n_casts:
                try:
                    expressions.append(
                        self.get_filter_expr(
                            operator, value, attr_key=[],
                            column=get_attribute_db_column(mapped_class, dtype, castas=castas),
                            is_attribute=False
                        )
                    )
                except InputValidationError as e:
                    raise e

            actual_attr_key = '.'.join(attr_key)
            expr = column.any(and_(
                    mapped_class.key == actual_attr_key,
                    or_(*expressions)
                )
            )
        return expr

    def get_projectable_attribute(
            self, alias, column_name, attrpath,
            cast=None, **kwargs
        ):
        if cast is not None:
            raise NotImplementedError(
                "Casting is not implemented in the Django backend"
            )
        if not attrpath:
            # If the user with Django backend wants all the attributes or all
            # the extras, I will select as entity the ID of the node.
            # in get_aiida_res, this is transformed to the dictionary of attributes.
            if column_name in ('attributes', 'extras'):
                entity = alias.id
            else:
                raise NotImplementedError(
                        "Whatever you asked for "
                        "({}) is not implemented"
                        "".format(column_name)
                    )
        else:
            aliased_attributes = aliased(getattr(alias, column_name).prop.mapper.class_)

            if not issubclass(alias._aliased_insp.class_,self.Node):
                NotImplementedError(
                    "Other classes than Nodes are not implemented yet"
                )

            attrkey = '.'.join(attrpath)

            exists_stmt = exists(select([1], correlate=True).select_from(
                    aliased_attributes
                ).where(and_(
                    aliased_attributes.key==attrkey,
                    aliased_attributes.dbnode_id==alias.id
                )))

            select_stmt = select(
                    [aliased_attributes.id], correlate=True
                ).select_from(aliased_attributes).where(and_(
                    aliased_attributes.key==attrkey,
                    aliased_attributes.dbnode_id==alias.id
                )).label('miao')

            entity = case([(exists_stmt, select_stmt), ], else_=None)

        return entity

    def get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param res: the result returned by the query
        :param key: the key that this entry would be return with

        :returns: an aiida-compatible instance
        """
        if key.startswith('attributes.'):
            # If you want a specific attributes, that key was stored in res.
            # So I call the getvalue method to expand into a dictionary
            try:
                returnval = DbAttribute.objects.get(id=res).getvalue()
            except ObjectDoesNotExist:
                # If the object does not exist, return None. This is consistent
                # with SQLAlchemy inside the JSON
                returnval = None
        elif key.startswith('extras.'):
            # Same as attributes
            try:
                returnval = DbExtra.objects.get(id=res).getvalue()
            except ObjectDoesNotExist:
                returnval = None
        elif key == 'attributes':
            # If you asked for all attributes, the QB return the ID of the node
            # I use DbAttribute.get_all_values_for_nodepk
            # to get the dictionary
            return DbAttribute.get_all_values_for_nodepk(res)
        elif key == 'extras':
            # same as attributes
            return DbExtra.get_all_values_for_nodepk(res)
        elif key in ('_metadata', 'transport_params'):
            # Metadata and transport_params are stored as json strings in the DB:
            return json_loads(res)
        elif isinstance(res, (self.Group, self.Node, self.Computer, self.User)):
            returnval =  res.get_aiida_class()
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

        with transaction.atomic():
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
                raise Exception("Got an empty dictionary: {}".format(tag_to_index_dict))


    def iterdict(self, query, batch_size, tag_to_projected_entity_dict):
        from django.db import transaction
        # Wrapping everything in an atomic transaction:
        with transaction.atomic():
            results = query.yield_per(batch_size)
            # Two cases: If one column was asked, the database returns a matrix of rows * columns:
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



