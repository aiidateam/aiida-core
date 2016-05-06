# -*- coding: utf-8 -*-

from aiida.backends.querybuild.querybuilder_base import QueryBuilderBase
from sa_init import (
        and_, or_, not_, except_, func as sa_func,
        aliased, Integer, Float, Boolean, JSONB, jsonb_array_length
    )

from sqlalchemy_utils.types.choice import Choice
from aiida.backends.sqlalchemy import session as sa_session
from aiida.backends.sqlalchemy.models.node import DbNode, DbLink, DbPath
from aiida.backends.sqlalchemy.models.computer import DbComputer
from aiida.backends.sqlalchemy.models.group import DbGroup, table_groups_nodes
from aiida.backends.sqlalchemy.models.user import DbUser

from aiida.common.exceptions import InputValidationError



class QueryBuilder(QueryBuilderBase):
    """
    QueryBuilder to use with SQLAlchemy-backend and
    schema defined in backends.sqlalchemy.models
    """

    def __init__(self, *args, **kwargs):
        from aiida.orm.implementation.sqlalchemy.node import Node as AiidaNode
        from aiida.orm.implementation.sqlalchemy.group import Group as AiidaGroup
        self.Link               = DbLink
        self.Path               = DbPath
        self.Node               = DbNode
        self.Computer           = DbComputer
        self.User               = DbUser
        self.Group              = DbGroup
        self.table_groups_nodes = table_groups_nodes
        self.AiidaNode          = AiidaNode
        self.AiidaGroup         = AiidaGroup
        super(QueryBuilder, self).__init__(*args, **kwargs)


        # raise DeprecationWarning("The use of this class is still deprecated")
    def _get_session(self):
        return sa_session

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
                json_path = path_spec.split('.')[1:]
                db_path = column[(json_path)] if json_path else column
                val_in_json = bool(json_path)
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==':filter_operation_dict}
                [
                    expressions.append(
                        self._get_expr(
                            operator, value, db_path, val_in_json
                        )
                    )
                    for operator, value
                    in filter_operation_dict.items()
                ]
        return and_(*expressions)

    @classmethod
    def _get_expr(cls, operator, value, db_path, val_in_json):
        def cast_according_to_type(path_in_json, value, val_in_json):
            if not val_in_json:
                return path_in_json
            elif isinstance(value, bool):
                return path_in_json.cast(Boolean)
            elif isinstance(value, int):
                return path_in_json.cast(Integer)
            elif isinstance(value, float):
                return path_in_json.cast(Float)
            elif isinstance(value, (list, tuple, dict)) or value is None:
                return path_in_json.cast(JSONB) # BOOLEANS?
            elif isinstance(value, str):
                return path_in_json.astext

            elif isinstance(value, datetime.datetime):
                return path_in_json.cast(TIMESTAMP)
            else:
                raise Exception( ' Unknown type {}'.format(type(value)))

        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        else:
            negation = False
        if operator == '==':
            expr = cast_according_to_type(db_path, value, val_in_json) == value
        elif operator == '>':
            expr = cast_according_to_type(db_path, value, val_in_json) > value
        elif operator == '<':
            expr = cast_according_to_type(db_path, value, val_in_json) < value
        elif operator == '>=':
            expr = cast_according_to_type(db_path, value, val_in_json) >= value
        elif operator == '<=':
            expr = cast_according_to_type(db_path, value, val_in_json) <= value
        elif operator == 'like':
            if val_in_json:
                expr = db_path.astext.like(value)
            else:
                expr = db_path.like(value)
        elif operator == 'ilike':
            if val_in_json:
                expr = db_path.astext.ilike(value)
            else:
                expr = db_path.ilike(value)
        elif operator == 'in':
            value_type_set = set([type(i) for i in value])
            if len(value_type_set) > 1:
                raise InputValidationError(
                        '{}  contains more than one type'.format(value)
                    )
            elif len(value_type_set) == 0:
                if val_in_json:
                    raise InputValidationError(
                            'I was given an empty list\n'
                            'Operator {}\n'
                            'Db path {}\n'
                            ''.format(operator, db_path)
                        )
                else:
                    expr = db_path.in_(value)
            else:
                casted_column = cast_according_to_type(
                        db_path,
                        value[0],
                        val_in_json
                    )
                expr = casted_column.in_(value)
        elif operator == 'contains':
            #~ print 'I must contain', value
            # This only works for json
            expr = db_path.cast(JSONB).contains(value)
        elif operator == 'has_key':
            # print 'I must contain', value
            expr = db_path.cast(JSONB).has_key(value)
            #~ print type(expr)
        elif operator == 'of_length':
            expr = jsonb_array_length(db_path.cast(JSONB)) == value
        elif operator == 'longer':
            expr = jsonb_array_length(db_path.cast(JSONB)) > value
        elif operator == 'shorter':
            expr = jsonb_array_length(db_path.cast(JSONB)) < value
        elif operator == 'nr_of_keys':
            #~ print 'I must contain', value
            expr = jsonb_dict_length(db_path.cast(JSONB)) == value
        elif operator == 'and':
            and_expressions_for_this_path = []
            for filter_operation_dict in value:
                for newoperator, newvalue in filter_operation_dict.items():
                    and_expressions_for_this_path.append(
                            cls._get_expr(
                                    newoperator, newvalue,
                                    db_path, val_in_json
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
                            db_path, val_in_json
                        )
                        for newoperator, newvalue
                        in filter_operation_dict.items()
                    ]
                ))
            expr = or_(*or_expressions_for_this_path)
        else:
            raise Exception (' Unknown filter {}'.format(operator))
        if negation:
            return not_(expr)
        return expr


    def _add_projectable_entity(self, alias, projectable_entity, cast='j', func=None):


        column_name = projectable_entity.split('.')[0]
        json_path = projectable_entity.split('.')[1:]

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
            column = self.get_column(column_name, alias)
            if json_path:
                if cast =='j':
                    entity_to_project = column[json_path].cast(JSONB)
                elif cast == 'f':
                    entity_to_project = column[json_path].cast(Float)
                elif cast == 'i':
                    entity_to_project = column[json_path].cast(Integer)
                elif cast == 'b':
                    entity_to_project = column[json_path].cast(Boolean)
                elif cast == 't':
                    entity_to_project = column[json_path].astext
                else:
                    raise InputValidationError(
                            "Invalid type to cast {}".format(cast)
                        )
            else:
                entity_to_project = column

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



    def _get_aiida_res(self, res):
        """
        Some instance returned by ORM (django or SA) need to be converted
        to Aiida instances (eg nodes). Choice (sqlalchemy_utils)
        will return their value

        :param res: the result returned by the query

        :returns: an aiida-compatible instance
        """
        if isinstance(res, (self.Group, self.Node)):
            return res.get_aiida_class()
        elif isinstance(res, Choice):
            return res.value
        else:
            return res
