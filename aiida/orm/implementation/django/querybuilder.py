# -*- coding: utf-8 -*-
import copy, os, sys, datetime
from inspect import isclass as inspect_isclass

from dummy_model import *
from aiida.orm import from_type_to_pluginclassname
from aiida.orm.implementation.general.querybuilder import (
    QueryBuilderBase, flatten_list, replacement_dict
)


from aiida.common import aiidalogger
from aiida.common.pluginloader import load_plugin
from aiida.common.exceptions import DbContentError, MissingPluginError

from aiida.orm import Node


class QueryBuilder(QueryBuilderBase):
    """

    """
    def get_ormclass(self, ormclasstype):
        return DbNode

    @staticmethod
    def get_session():
        return session

    def join_outputs(self, toconnectwith, alias):
        link = aliased(DbLink)
        self.que = self.que.join(link,  link.input_id  == toconnectwith.id)
        self.que = self.que.join(alias, link.output_id == alias.id)

    def join_inputs(self, toconnectwith, alias):
        link = aliased(DbLink)
        self.que = self.que.join(link,  link.output_id == toconnectwith.id)
        self.que = self.que.join(alias, link.input_id  == alias.id)

    def join_ancestors(self, toconnectwith, alias):
        path = aliased(DbPath)
        self.que = self.que.join(path,  path.parent_id == toconnectwith.id)
        self.que = self.que.join(alias, path.child_id  == alias.id)

    def join_descendants(self, toconnectwith, alias):
        path = aliased(DbPath)
        self.que = self.que.join(path,  path.child_id == toconnectwith.id)
        self.que = self.que.join(alias, path.parent_id  == alias.id)

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
        """
        Return the column for the projection, if the column name is specified.
        """
        col =  super(QueryBuilder, self).get_column(colname, alias)
        return col

    @staticmethod
    def get_expr(operator, value, column, attr_key):
        """
        Applies a filter on the alias given.
        Expects the alias of the ORM-class on which to filter, and filter_spec.
        Filter_spec contains the specification on the filter.
        Expects:
        
        -   ``operator``: The operator to apply. These can be:
        
            -  for any type: 
                -   ==  (compare single value, eg: '==':5.0)
                - in    (compare whether in list, eg: 'in':[5, 6, 34]
            -  for floats and integers:
                 - >
                 - <
                 - <=
                 - >= 
            -  for strings:
                 - like  (case - sensitive)   (eg 'like':'node.calc.%'  will match node.calc.relax and node.calc.RELAX and node.calc. but node node.CALC.relax)
                 - ilike (case - unsensitive) (will also match node.CaLc.relax)
                    
                on that topic:
                The character % is a reserved special character in SQL, and acts as a wildcard.
                If you specifically want to capture a ``%`` in the string name, use:
                ``_%``
            -  for arrays and dictionaries:
                 - contains  (pass a list with all the items that the array should contain, or that should be among the keys, eg: 'contains': ['N', 'H'])
                 - has_key   (pass an element that the list has to contain or that has to be a key, eg: 'has_key':'N')
            -  for arrays only:
                 - of_length  
                 - longer
                 - shorter
            
            All the above filters invoke a negation of the expression if preceded by ~
            
            - {'name':{'~in':['halle', 'lujah']}} # Name not 'halle' or 'lujah'
            - {'id':{ '~==': 2}} # id is not 2

            
        - ``value``: The value for the right side of the expression, the value you want to compare with.
        - ``db_bath``: The path leading to the value
        - ``val_in_json``: Boolean, whether the value is in a json-column, requires type casting.


            
        TODO:
        
        -   implement redundant expressions for user-friendliness: 
        
            -   ~==: !=, not, ne 
            -   ~in: nin, !in
            -   ~like: unlike    
        """
        if operator.startswith('~'):
            negation = True
            operator = operator.lstrip('~')
        else:
            negation = False
        if attr_key:
            mapped_class = column.prop.mapper.class_
            if isinstance(value, str):
                mapped_entity = mapped_class.tval
            elif isinstance(value, float):
                mapped_entity = mapped_class.fval
            elif isinstance(value, int):
                mapped_entity = mapped_class.ival
            elif isinstance(value, bool):
                mapped_entity = mapped_class.bval
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
                'output_of':StructureData,
            },
            {
                'class':ParameterData,
                'input_of':PwCalculation
            }
        ],
        'project':{
            StructureData:['*'],
            PwCalculation:['*'],
            #~ ParameterData:['*'],
        },
        'filters':{
            StructureData:{
                'attributes.kinds.0.symbols.0':'Li',
            }
        },
        'limit':4
    }
    
    
    #~ raw_input(issubclass(StructureData, Node))
    res = QueryBuilder(qh).get_results_dict()
    print res

