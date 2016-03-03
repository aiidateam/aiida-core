# -*- coding: utf-8 -*-

from querybuilder_base import QueryBuilderBase

class QueryBuilder(QueryBuilderBase):
    """
    QueryBuilder to use with SQLAlchemy-backend and 
    schema defined in backends.sqlalchemy.models
    """

    def __init__(self, *args, **kwargs):
        raise DeprecationWarning("The use of this class is still deprecated")

    def analyze_filter_spec(self, alias, filter_spec):
        expressions = []
        for path_spec, filter_operation_dict in filter_spec.items():
            if path_spec in  ('and', 'or', '~or', '~and'):
                subexpressions = [
                    analyze_filter_spec(alias, sub_filter_spec)
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
                        get_expr(
                            operator, value, db_path, val_in_json
                        )
                    ) 
                    for operator, value 
                    in filter_operation_dict.items()
                ]
        return and_(*expressions)

    def get_expr(operator, value, db_path, val_in_json):
        def cast_according_to_type(path_in_json, value, val_in_json):
            if not val_in_json:
                return path_in_json
            
            elif isinstance(value, int):
                return path_in_json.cast(Integer)
            
            elif isinstance(value, float):
                return path_in_json.cast(Float)
            
            elif isinstance(value, (list, tuple, dict, bool)) or value is None:
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
                raise Exception( '{}  contains more than one type'.format(value))
            elif len(value_type_set) == 0:
                if val_in_json:
                    raise Exception( 'Given list is empty, cannot cast')
                else:
                    expr = db_path.in_(value)
            else:
                casted_column = cast_according_to_type(db_path, value[0], val_in_json)
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
                    and_expressions_for_this_path.append(get_expr(newoperator, newvalue, db_path, val_in_json))
            expr = and_(*and_expressions_for_this_path)
        elif operator == 'or':
            or_expressions_for_this_path = []
            for filter_operation_dict in value:
                # Attention: Multiple expression inside one direction are joint by and!
                # Default will and should always be kept AND
                or_expressions_for_this_path.append(and_(*[get_expr(newoperator, newvalue, db_path, val_in_json)
                    for newoperator, newvalue in filter_operation_dict.items()]))
                #~ for newoperator, newvalue in filter_operation_dict.items():
                    #~ or_expressions_for_this_path.append(get_expr(newoperator, newvalue, db_path, val_in_json))
            expr = or_(*or_expressions_for_this_path)
        else:
            raise Exception (' Unknown filter {}'.format(operator))
        if negation:
            return not_(expr)
        return expr


    def add_projectable_entity(self, projectable_spec, alias):
        if projectable_spec == '*': # 
            self.que = self.que.add_entity(alias)
        else:
            if isinstance(path_to_value, dict):
                type_to_cast, = path_to_value.values()
                path_to_value, = path_to_value.keys()
            else:
                type_to_cast = 'json'
            column_name = path_to_value.split('.')[0] 
            json_path = path_to_value.split('.')[1:]
            if json_path:
                if type_to_cast in ('json', 'int', 'float', 'bool'):
                    self.que = self.que.add_columns(
                        get_column(
                            column_name, alias
                        )[json_path].cast(JSONB)
                    )
                elif type_to_cast == 'str':
                    self.que = self.que.add_columns(
                        get_column(
                            column_name, alias
                        )[json_path].astext
                    )
                else:
                    raise Exception(
                        "invalid type to cast {}".format(
                            type_to_cast
                        )
                    )
            else:
                self.que =  self.que.add_columns(get_column(column_name, alias))

