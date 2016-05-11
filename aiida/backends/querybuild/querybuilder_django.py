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

from aiida.backends.querybuild.sa_init import (
    and_, or_, not_, except_, aliased,      # Queryfuncs
    func as sa_func, cast, Float, Integer, Boolean, DateTime,
    case, exists, join, select, text
)
class QueryBuilder(AbstractQueryBuilder):

    def __init__(self, *args, **kwargs):
        from aiida.orm.implementation.django.node import Node as AiidaNode
        from aiida.orm.implementation.django.group import Group as AiidaGroup
        from aiida.orm.implementation.django.computer import Computer as AiidaComputer

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

        super(QueryBuilder, self).__init__(*args, **kwargs)


    def _get_aiida_res(self, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes)

        :param res: the result returned by the query
        :param key: the key that this entry would be return with

        :returns: an aiida-compatible instance
        """
        if isinstance(res, (self.Group, self.Node, self.Computer, self.User)):
            return res.get_aiida_class()
        else:
            return res

    @staticmethod
    def _get_session():
        return session

    @classmethod
    def _get_expr(cls, operator, value, column, attr_key, types=None):
        """
        :param operator:
            A string representation of a valid operator,
            '==', '<=', '<', '>' ,' >=', 'in', 'like'
            or the negation of such (same string prepended with '~')
        :param value:
            The right part of the expression
        :param column:
            An instance of *sqlalchemy.orm.attributes.InstrumentedAttribute*.
            Giving the left part of the expression
        :param attr_key:
            If I am looking at an attribute, than the attr_key is the key
            to look for in db_dbattributes table.

        :returns:
            An SQLAlchemy expression
            (*sqlalchemy.sql.selectable.Exists*,
            *sqlalchemy.sql.elements.BinaryExpression*, etc)
            that can be evaluated by a query intance.
        """
        def get_attribute_column(mapped_class, dtype, castas=None):
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

        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        else:
            negation = False
        if attr_key:
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
            #   (which column in the dbattribtues)
            # If the user specified in what to cast, he wants an operation to
            #   be performed to cast the value to a different type
            if types is None:
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
            else:
                #some checks
                pass
            expressions = []
            for dtype, castas in types_n_casts:
                expressions.append(
                    cls._get_expr(
                        operator, value,
                        get_attribute_column(mapped_class, dtype, castas=castas),
                        None
                    )
                )
            expr = column.any(and_(mapped_class.key == attr_key, or_(*expressions)))
        else:
            if operator == '==':
                expr = column == value
            elif operator == '>':
                expr = column > value
            elif operator == '<':
                expr = column < value
            elif operator == '>=':
                expr = column >= value
            elif operator == '<=':
                expr = column <= value
            elif operator == 'like':
                expr = column.like(value)
            elif operator == 'ilike':
                expr = column.ilike(value)
            elif operator == 'in':
                expr = column.in_(value)
            elif operator == 'and':
                and_expressions_for_this_path = []
                for filter_operation_dict in value:
                    for newoperator, newvalue in filter_operation_dict.items():
                        and_expressions_for_this_path.append(
                                cls._get_expr(
                                        newoperator, newvalue,
                                        column, attr_key
                                    )
                            )
                expr = and_(*and_expressions_for_this_path)
            elif operator == 'or':
                or_expressions_for_this_path = []
                for filter_operation_dict in value:
                    # Attention: Multiple expression inside
                    # one direction are joint by and!
                    # Default will and should always be kept AND
                    or_expressions_for_this_path.append(and_(*[
                            cls._get_expr(
                                newoperator, newvalue,
                                column, attr_key
                            )
                            for newoperator, newvalue
                            in filter_operation_dict.items()
                        ]
                    ))
                expr = or_(*or_expressions_for_this_path)
            else:
                raise Exception('Unkown operator %s' % operator)
        if negation:
            return not_(expr)
        return expr

    def _analyze_filter_spec(self, alias, filter_spec):

        expressions = []
        for path_spec, filter_operation_dict in filter_spec.items():
            if path_spec in  ('and', 'or', '~or', '~and'):
                subexpressions = [
                    self._analyze_filter_spec(alias, sub_filter_spec)
                    for sub_filter_spec in filter_operation_dict
                ]
                if path_spec == 'and':
                    expressions.append(and_(*subexpressions))
                elif path_spec == 'or':
                    expressions.append(or_(*subexpressions))
                elif path_spec == '~and':
                    expressions.append(not_(and_(*subexpressions)))
                elif path_spec == '~or':
                    expressions.append(not_(or_(*subexpressions)))
            else:
                column_name = path_spec.split('.')[0]
                column =  self.get_column(column_name, alias)
                attr_key = '.'.join(path_spec.split('.')[1:])
                is_attribute = bool(attr_key)
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==':filter_operation_dict}
                [
                    expressions.append(
                        self._get_expr(
                            operator, value, column, attr_key
                        )
                    )
                    for operator, value
                    in filter_operation_dict.items()
                ]
        return and_(*expressions)

    def _get_entity(self, aliased_node, column_name, attrkey, dtype='undefined', **kwargs):
        if attrkey:
            if aliased_node._aliased_insp.class_ == self.Node:
                if column_name == 'attributes':
                    aliased_attributes = aliased(DummyAttribute)
                elif column_name == 'extras':
                    aliased_attributes = aliased(DummyExtra)
            else:
                NotImplementedError(
                    "Other classes than Nodes are not implemented yet"
                )

            exists_stmt = exists(select([1], correlate=True).select_from(
                    aliased_attributes
                ).where(and_(
                    aliased_attributes.key==attrkey,
                    aliased_attributes.dbnode_id==aliased_node.id
                )))

            select_stmt = select(
                    [aliased_attributes.datatype], correlate=True
                ).select_from(aliased_attributes).where(and_(
                    aliased_attributes.key==attrkey,
                    aliased_attributes.dbnode_id==aliased_node.id
                )).label('miao')

            entity = case([(exists_stmt, select_stmt), ], else_=None)

#~ 
            #~ if dtype =='t':
                #~ pass
            #~ elif dtype == 'f':
                #~ entity = cast(entity, Float)
            #~ elif dtype == 'i':
                #~ entity = cast(entity, Integer)
            #~ elif dtype == 'b':
                #~ entity = cast(entity,  Boolean)
            #~ elif dtype == 'd':
                #~ entity = cast(entity, DateTime)
            #~ else:
                #~ raise InputValidationError(
                        #~ "Invalid dtype {}".format(dtype)
                    #~ )
        else:
            entity = self.get_column(column_name, aliased_node)
        #~ return None
        return entity

    def _add_projectable_entity(self, alias, projectable_entity, dtype='undefined', func=None):
        """
        :param alias:
            A instance of *sqlalchemy.orm.util.AliasedClass*, alias for an ormclass
        :param projectable_entity:
            User specification of what to project.
            Appends to query's entities what the user wants to project
            (have returned by the query)

        """
        column_name = projectable_entity.split('.')[0]
        attrkey = '.'.join(projectable_entity.split('.')[1:])


        if column_name == '*':
            if func is not None:
                raise InputValidationError(

                        "Very sorry, but functions on the aliased class\n"
                        "(You specified '*')\n"
                        "will not work!\n"
                        "I suggest you apply functions on a column, e.g. ('id')\n"
                    )
            self.que = self.que.add_entity(alias)
        else:
            entity_to_project = self._get_entity(alias, column_name, attrkey, dtype)
            if func is None:
                pass
            elif func == 'max':
                entity_to_project = sa_func.max(entity_to_project)
            elif func == 'min':
                entity_to_project = sa_func.max(entity_to_project)
            elif func == 'count':
                entity_to_project = sa_func.count(entity_to_project)
            else:
                raise InputValidationError(
                        "\nInvalid function specification {}".format(func)
                    )

            self.que =  self.que.add_columns(entity_to_project)

