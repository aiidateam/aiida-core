# -*- coding: utf-8 -*-

from datetime import datetime

from querybuilder_base import (
    AbstractQueryBuilder,
    datetime,
    InputValidationError
)

from aiida.backends.querybuild.dummy_model import (
    # Tables:
    DbNode      as DummyNode,
    DbLink      as DummyLink,
    DbCalcState as DummyState,
    DbPath      as DummyPath,
    DbUser      as DummyUser,
    DbComputer  as DummyComputer,
    DbGroup     as DummyGroup,
    DbExtra     as DummyExtra,
    DbAttribute as DummyAttribute,
    table_groups_nodes  as Dummy_table_groups_nodes,
    session,                             # session with DB
)

from aiida.backends.djsite.db.models import DbAttribute, DbExtra, ObjectDoesNotExist


from aiida.backends.querybuild.sa_init import (
    and_, or_, aliased,      # Queryfuncs
    cast, Float, Integer, Boolean, DateTime,
    case, exists, join, select, exists
)

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

class QueryBuilder(AbstractQueryBuilder):

    def __init__(self, *args, **kwargs):
        from aiida.orm.implementation.django.node import Node as AiidaNode
        from aiida.orm.implementation.django.group import Group as AiidaGroup
        from aiida.orm.implementation.django.computer import Computer as AiidaComputer
        from aiida.orm.implementation.django.user import User as AiidaUser

        self.Link               = DummyLink
        self.Path               = DummyPath
        self.Node               = DummyNode
        self.Computer           = DummyComputer
        self.User               = DummyUser
        self.Group              = DummyGroup
        self.table_groups_nodes = Dummy_table_groups_nodes
        self.AiidaNode          = AiidaNode
        self.AiidaGroup         = AiidaGroup
        self.AiidaComputer      = AiidaComputer
        self.AiidaUser          = AiidaUser

        super(QueryBuilder, self).__init__(*args, **kwargs)


    def _get_aiida_res(self, key, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param res: the result returned by the query
        :param key: the key that this entry would be return with

        :returns: an aiida-compatible instance
        """
        if key.startswith('attributes'):
            try:
                returnval = DbAttribute.objects.get(id=res).getvalue()
            except ObjectDoesNotExist:
                returnval = None
        elif key.startswith('extras'):
            try:
                returnval = DbExtra.objects.get(id=res).getvalue()
            except ObjectDoesNotExist:
                returnval = None
        elif isinstance(res, (self.Group, self.Node, self.Computer, self.User)):
            returnval =  res.get_aiida_class()
        else:
            returnval = res
        return returnval


    @staticmethod
    def _get_session():
        return session

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
            mapped_class = db_column.prop.mapper.class_
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
            if issubclass(mapped_class, DummyAttribute):
                expr = alias.attributes.any(mapped_class.key == '.'.join(attr_key+[value]))
            elif issubclass(mapped_class, DummyExtra):
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
            elif isinstance(value_to_consider, datetime.datetime):
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



    def _get_projectable_attribute(
            self, alias, column_name, attrpath,
            cast=None, **kwargs
        ):
        if cast is not None:
            raise NotImplementedError(
                "Casting is not implemented in the Django backend"
            )
        if not attrpath:
            raise NotImplementedError(
                "Cannot project all attributes in the Django backend\n"
                "(You did not provide a key)"
            )

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
