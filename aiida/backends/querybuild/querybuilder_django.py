# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0"

import datetime
from datetime import datetime
from json import loads as json_loads

import aiida.backends.querybuild.dummy_model as dummy_model
from aiida.backends.djsite.db.models import DbAttribute, DbExtra, ObjectDoesNotExist
from aiida.backends.querybuild.sa_init import (
    and_, or_, aliased,      # Queryfuncs
    cast, Float, case, select, exists
)
from aiida.common.exceptions import InputValidationError
from querybuilder_base import AbstractQueryBuilder

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1"

class QueryBuilder(AbstractQueryBuilder):

    def __init__(self, *args, **kwargs):
        from aiida.orm.implementation.django.node import Node as AiidaNode
        from aiida.orm.implementation.django.group import Group as AiidaGroup
        from aiida.orm.implementation.django.computer import Computer as AiidaComputer
        from aiida.orm.implementation.django.user import User as AiidaUser

        self.Link               = dummy_model.DbLink
        self.Node               = dummy_model.DbNode
        self.Computer           = dummy_model.DbComputer
        self.User               = dummy_model.DbUser
        self.Group              = dummy_model.DbGroup
        self.table_groups_nodes = dummy_model.table_groups_nodes
        self.AiidaNode          = AiidaNode
        self.AiidaGroup         = AiidaGroup
        self.AiidaComputer      = AiidaComputer
        self.AiidaUser          = AiidaUser

        super(QueryBuilder, self).__init__(*args, **kwargs)

    def _prepare_with_dbpath(self):
        from aiida.backends.querybuild.dummy_model import DbPath as DummyPath
        self.Path = DummyPath

    def _get_aiida_res(self, key, res):
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


    @staticmethod
    def _get_session():
        return dummy_model.session

    @classmethod
    def _get_filter_expr_from_attributes(
            cls, operator, value, attr_key,
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
                        cls._get_filter_expr(
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


    def _modify_expansions(self, alias, expansions):
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

    def _get_projectable_attribute(
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
            # in _get_aiida_res, this is transformed to the dictionary of attributes.
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


    def _yield_per(self, batch_size):
        """
        :param count: Number of rows to yield per step

        Yields *count* rows at a time

        :returns: a generator
        """
        return self.get_query().yield_per(batch_size)


    def _all(self):
        from django.db import transaction
        with transaction.atomic():
            return self.get_query().all()

    def _first(self):
        """
        Executes query in the backend asking for one instance.

        :returns: One row of aiida results
        """
        from django.db import transaction
        with transaction.atomic():
            return self.get_query().first()


    def iterall(self, batch_size=100):
        """
        Same as :func:`QueryBuilderBase.all`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per

        With respect to SQLA implementation of the QueryBuilder, this is wrapped into one atomic transaction
        """

        from django.db import transaction
        with transaction.atomic():
            if batch_size is not None:
                results = self._yield_per(batch_size)
            else:
                results = self._all()
            try:
                for resultrow in results:
                    yield [
                        self._get_aiida_res(self._attrkeys_as_in_sql_result[colindex], rowitem)
                        for colindex, rowitem
                        in enumerate(resultrow)
                    ]
            except TypeError:
                # resultrow not an iterable:
                # Checked, result that raises exception is included
                if len(self._attrkeys_as_in_sql_result) > 1:
                    raise Exception(
                        "I have not received an iterable\n"
                        "but the number of projections is > 1"
                    )
                for rowitem in results:
                    yield [self._get_aiida_res(self._attrkeys_as_in_sql_result[0], rowitem)]


    def iterdict(self, batch_size=100):
        """
        Same as :func:`QueryBuilderBase.dict`, but returns a generator.
        Be aware that this is only safe if no commit will take place during this
        transaction. You might also want to read the SQLAlchemy documentation on
        http://docs.sqlalchemy.org/en/latest/orm/query.html#sqlalchemy.orm.query.Query.yield_per


        :param int batch_size:
            The size of the batches to ask the backend to batch results in subcollections.
            You can optimize the speed of the query by tuning this parameter.

        :returns: a generator of dictionaries

        In the implementation using Django in the backend, the query is context in an atomic transaction
        """

        from django.db import transaction
        with transaction.atomic():

            if batch_size is not None:
                results = self._yield_per(batch_size=batch_size)
            else:
                results = self._all()

            try:
                for this_result in results:
                    yield {
                        tag:{
                            attrkey:self._get_aiida_res(
                                    attrkey, this_result[index_in_sql_result]
                                )
                            for attrkey, index_in_sql_result
                            in projected_entities_dict.items()
                        }
                        for tag, projected_entities_dict
                        in self.tag_to_projected_entity_dict.items()
                    }
            except TypeError:
                # resultrow not an iterable:
                # Checked, result that raises exception is included
                if len(self._attrkeys_as_in_sql_result) > 1:
                    raise Exception(
                        "I have not received an iterable\n"
                        "but the number of projections is > 1"
                    )
                for this_result in results:
                    yield {
                        tag:{
                            attrkey : self._get_aiida_res(attrkey, this_result)
                            for attrkey, position in projected_entities_dict.items()
                        }
                        for tag, projected_entities_dict in self.tag_to_projected_entity_dict.items()
                    }

