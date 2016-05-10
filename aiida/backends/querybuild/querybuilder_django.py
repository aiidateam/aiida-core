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
    func as sa_func
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



    @staticmethod
    def _get_session():
        return session

    @classmethod
    def _get_expr(cls, operator, value, column, attr_key):
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
        def get_mapped_entity(mapped_class, value):
            if isinstance(value, str):
                mapped_entity = mapped_class.tval
            elif isinstance(value, bool):
                mapped_entity = mapped_class.bval
            elif isinstance(value, float):
                mapped_entity = mapped_class.fval
            elif isinstance(value, int):
                mapped_entity = mapped_class.ival
            elif isinstance(value, datetime):
                mapped_entity = mapped_class.dval
            elif isinstance(value, (list, tuple)):
                value_type_set = set([type(i) for i in value])
                if len(value_type_set) > 1:
                    raise InputValidationError( '{}  contains more than one type'.format(value))
                elif len(value_type_set) == 0:
                    raise InputValidationError('Given list is empty, cannot determine type')
                else:
                    mapped_entity = get_mapped_entity(mapped_class, value[0])
            else:
                raise InputValidationError(
                    "I don't know what to do with value {}".format(value)
                )
            return mapped_entity

        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        else:
            negation = False
        if attr_key:
            mapped_class = column.prop.mapper.class_
            expr = column.any(
                and_(
                    mapped_class.key.like(attr_key),
                    cls._get_expr(
                            operator, value,
                            get_mapped_entity(mapped_class, value),
                            None
                        )
                )
            )
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

    def _get_entity(self, alias, column_name, attrpath, cast='undefined', **kwargs):
        if attrpath:
            if alias._aliased_insp.class_ == self.Node:
                if column_name == 'attributes':
                    addalias = aliased(DummyAttribute)
                elif column_name == 'extras':
                    addalias = aliased(DummyExtra)
            else:
                NotImplementedError(
                    "Other classes than Nodes are not implemented yet"
                )
            self.que = self.que.join(
                    addalias,
                    addalias.dbnode_id == alias.id
                )
            self.que = self.que.filter(addalias.key == attrpath)

            if cast =='t':
                entity = self.get_column('tval', addalias)
            elif cast == 'f':
                entity = self.get_column('fval', addalias)
            elif cast == 'i':
                entity = self.get_column('ival', addalias)
            elif cast == 'b':
                entity = self.get_column('bval', addalias)
            elif cast == 'd':
                entity = self.get_column('dval', addalias)
            else:
                raise InputValidationError(
                        "Invalid type to cast {}".format(cast)
                    )
        else:
            entity = self.get_column(column_name, alias)
        return entity

    def _add_projectable_entity(self, alias, projectable_entity, cast='undefined', func=None):
        """
        :param alias:
            A instance of *sqlalchemy.orm.util.AliasedClass*, alias for an ormclass
        :param projectable_entity:
            User specification of what to project.
            Appends to query's entities what the user wants to project
            (have returned by the query)

        """
        column_name = projectable_entity.split('.')[0]
        attrpath = '.'.join(projectable_entity.split('.')[1:])


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
            entity_to_project = self._get_entity(alias, column_name, attrpath, cast)
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

