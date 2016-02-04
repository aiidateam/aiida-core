# -*- coding: utf-8 -*-


# SA querying functionalities


from querybuilder_base import (
    QueryBuilderBase, replacement_dict
)

from dummy_model import (
    DbNode      as DummyNode,
    DbLink      as DummyLink,
    DbAttribute as DummyAttribute,
    DbCalcState as DummyState,
    DbPath      as DummyPath,
    DbUser      as DummyUser,
    DbComputer  as DummyComputer,
    session, and_, or_, not_, except_, aliased,
    DjangoAiidaNode
)



class QueryBuilder(QueryBuilderBase):
    """
    The QueryBuilder class for the Django backend
    and corresponding schema.
    In order to use SQLAlchemy's querying functionalities, 
    a :func:`~aiida.backends.querybuild.dummy_model`
    was written which can create a session with the aiidadb and
    query the tables defined there.
    """

    def __init__(self, queryhelp, **kwargs):
        self.Link       = DummyLink
        self.Path       = DummyPath
        self.Node       = DummyNode
        self.Computer   = DummyComputer
        self.User       = DummyUser
        self.AiidaNode  = DjangoAiidaNode
        super(QueryBuilder, self).__init__(queryhelp, **kwargs)

    def get_ormclass(self, ormclasstype):
        """
        Return the valid ormclass for the connections
        """
        return DummyNode

    @staticmethod
    def get_session():
        return session

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
                attr_key = '.'.join(path_spec.split('.')[1:])
                is_attribute = bool(attr_key)
                if not isinstance(filter_operation_dict, dict):
                    filter_operation_dict = {'==':filter_operation_dict}
                [
                    expressions.append(
                        self.get_expr(
                            operator, value, column, attr_key
                        )
                    ) 
                    for operator, value 
                    in filter_operation_dict.items()
                ]
        return and_(*expressions)

    def get_dict(self):
        """
        Returns the json-compatible list
        """
        return {
            'path':self.path, 
            'filters':self.filters,
            'project':self.projection_dict_user
        }

    def get_column(self, colname, alias):

        col =  super(QueryBuilder, self).get_column(colname, alias)
        return col

    @staticmethod
    def get_expr(operator, value, column, attr_key):
        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        else:
            negation = False
        if attr_key:
            mapped_class = column.prop.mapper.class_
            if isinstance(value, str):
                mapped_entity = mapped_class.tval
            elif isinstance(value, bool):
                mapped_entity = mapped_class.bval
            elif isinstance(value, float):
                mapped_entity = mapped_class.fval
            elif isinstance(value, int):
                mapped_entity = mapped_class.ival
            elif isinstance(value, dval):
                mapped_entity = mapped_class.dval
            
            expr = column.any(
                and_(
                    mapped_class.key.like(attr_key),
                    QueryBuilder.get_expr(operator, value, mapped_entity , None)
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
                expr = column.like(value)
            elif operator == 'in':
                expr = column.in_(value)
            else:
                raise Exception('Unkown operator %s' % operator)
        if negation:
            return not_(expr)
        return expr

    def add_projectable_entity(self, projectable_spec, alias):
        if projectable_spec == '*': # project the entity
            self.que = self.que.add_entity(alias)
        else:
            if isinstance(projectable_spec, dict):
                type_to_cast, = projectable_spec.values()
                projectable_spec, = projectable_spec.keys()
            column_name = projectable_spec.split('.')[0] 
            attr_key    = projectable_spec.split('.')[1:]
            if attr_key:
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
                self.que =  self.que.add_columns(self.get_column(column_name, alias))
        return projectable_spec

        
if __name__ == '__main__':
    from aiida.orm.calculation.inline import InlineCalculation
    from aiida.orm.data.parameter import ParameterData
    from aiida.orm.data.structure import StructureData
    from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
    # from aiida.orm.calculation.job.plugins.quantumespresso 
    qh = {
        'path':[

            StructureData,
            {
                'class':PwCalculation,
                'descendant_of':StructureData,
            },

        ],
        'project':{
            StructureData:['*'],
            PwCalculation:['*'],
        },
        'filters':{
            StructureData:{
                'attributes.kinds.0.symbols.0':'Li',
            }
        },
        'limit':4.,
        'order_by':1
    }

    #~ raw_input(issubclass(StructureData, Node))
    res = QueryBuilder(qh).get_results_dict()
    print res

