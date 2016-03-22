# -*- coding: utf-8 -*-

from querybuilder_base import (
    QueryBuilderBase,
    datetime,
    InputValidationError
)

from dummy_model import (
    # Tables:
    DbNode      as DummyNode,
    DbLink      as DummyLink,
    DbAttribute as DummyAttribute,
    DbCalcState as DummyState,
    DbPath      as DummyPath,
    DbUser      as DummyUser,
    DbComputer  as DummyComputer,
    DbGroup     as DummyGroup,
    table_groups_nodes  as Dummy_table_groups_nodes,
    and_, or_, not_, except_, aliased,      # Queryfuncs
    session,                                # session with DB
)


class QueryBuilder(QueryBuilderBase):
    """
    The QueryBuilder class for the Django backend,
    working with SQLAlchemy's querying functionalities using
    a :func:`~aiida.backends.querybuild.dummy_model`.

    Usage::

        qb  =   Querybuilder(**queryhelp)

    The queryhelp:The queryhelp is my API.
            
            It is a dictionary that tells me:

            *   what to join (key **path**)
            *   what to project (key **project**)
            *   how to filter (key **filters**)
            *   how many rows to return (key **limit**)
            *   how to order the rows (key **order_by**)

    What do you have to specify when you want to query:

    *   Specifying the path:
        Here, the user specifies the path along which to join tables as a list,
        each list item being a vertice in your path.
        You can define the vertice in two ways:
        The first is to give the Aiida-class::

            queryhelp = {
                'path':[Data]
            }

            # or  (better)

            queryhelp = {
                'path':[
                    {'cls': Data}
                ]
            }

        The second is to give the polymorphic identity
        of this class, in our case stored in type::

            queryhelp = {
                'path':[
                    {'type':"data."}
                ]
            }

        .. note:: 
            In Aiida, polymorphism is not strictly enforced, but
            achieved with *type* specification in a column.
            Type-discrimination is achieved by attaching a filter on the
            type every time a subclass of Node is given,
            in above example this would results in::

                ...filter(DbNode.type.like("data%"))...

        Each node has to have a unique label.
        If not given, the label is chosen to be equal to the type of the class.
        This will not work if the user chooses the same class twice.
        In this case he has to provide a label::

            queryhelp = {
                'path':[
                    {
                        'cls':Node,
                        'label':'node_1'
                    },
                    {
                        'cls':Node
                        'label':'node_2'
                    }
                ]
            }

        There also hast to be some information on the edges, in order to join correctly.
        There are several redundant ways this can be done:

        *   You can specify that this node is an input or output of another node 
            preceding the current one in the list.
            That other node can be specified by an integer or the class or type.
            The following examples are all valid joining instructions, 
            assuming there is a structure defined at index 2 of the path with label "struc1"::

                edge_specification = queryhelp['path'][3]
                edge_specification['output_of'] = 2
                edge_specification['output_of'] = StructureData
                edge_specification['output_of'] = 'struc1'
                edge_specification['input_of']  = 2
                edge_specification['input_of']  = StructureData
                edge_specification['input_of']  = 'struc1'

        *   queryhelp_item['direction'] = integer

            If any of the above specs ("input_of", "output_of") 
            were not specified, the key "direction" is looked for.
            Directions are defined as distances in the tree. 
            1 is defined as one step down the tree along a link.
            This means that 1 joins the node specified in this dictionary
            to the node specified on list-item before **as an output**.
            Direction defaults to 1, which is why, if nothing is specified,
            this node is joined to the previous one as an output by default.
            A minus sign reverse the direction of the link.
            The absolute value of the direction defines the table to join to
            with respect to your own position in the list.
            An absolute value of 1 joins one table above, a
            value of 2 to the table defined 2 indices above.
            The two following queryhelps yield the same  query::

                qh1 = {
                    'path':[
                        {
                            'cls':PwCalculation
                        }, 
                        {
                            'cls':Trajectory
                        }, 
                        {
                            'cls':ParameterData,
                            'direction':-2
                        }
                    ]
                }

                # returns same query as:

                qh2 = {
                    'path':[
                        {
                            'cls':PwCalculation
                        }, 
                        {
                            'cls':Trajectory
                        }, 
                        {
                            'cls':ParameterData,
                            'input_of':PwCalculation
                        }
                    ]
                }

                # Shorter version:

                qh3 = {
                    'path':[
                        ParameterData,
                        PwCalculation,
                        Trajectory,
                    ]
                }

    *   Project: Determing which columns the query will return::

            queryhelp = {
                'path':[Relax],
                'project':{
                    Relax:['state', 'id'],
                }
            }

        If you are using JSONB columns,
        you can also project a value stored inside the json::

            queryhelp = {
                'path':[
                    Relax,
                    StructureData,
                ],
                'project':{
                    'Relax':['state', 'id'],  # Yes you can put the type string here!
                    StructureData:['attributes.cell']
                }
            }

        Returns the state and the id of all instances of Relax and 
        the cells of all structures given that the structures are linked as output of a relax-calculation.
        The strings that you pass have to be name of the columns.
        If you pass a star ('*') , the query will return the instance of the AiidaClass.

    *   Filtering:
        What if I want not every structure, 
        but only the ones that were added after a certain time `t` and have an id higher than 50::
            
            queryhelp = {
                'path':[
                    {'cls':Relax}, # Relaxation with structure as output
                    {'cls':StructureData}
                ],
                'filters':{
                    StructureData:[
                        {
                            'time':{'>': t},
                            'id':{'>': 50}
                        }
                    ]
                }
            }

        With the key 'filters', we instruct the querytool to build filters and attach them to the query.
        Filters are passed as dictionaries.
        In each key, value, the key is presents the column-name (as a string) to filter on.
        The value is another dictionary, where the operator is a key and the value is the 
        value to check against.
        
        .. note:: This follows the MongoDB-syntax and is necessary to deal with "and" and "or"-clauses
        
        But what if the user wants to filter by key-value pairs defined inside the structure?
        In that case, simply specify the path with the dot (`.`) being a separator.
        If you want to get to the volume of the structure, stored in the attributes, you can specify::
            
            queryhelp = {
                'path':[{'cls':StructureData}],  # or 'path':[StructureData]
                'filters':{
                    'attributes.volume': {'<':6.0}
                }
            }

        The above queryhelp would build a query that returns all structures with a volume below 6.0.

        .. note:: A big advantage of SQLAlchemy is that it support the storing of jsons. 
                  It is convenient to dump the structure-data into a json and store that as a column.
                  The querytool needs to be told how to query the json.

    Let's get to a really complex use-case,
    where we need to reconstruct a workflow:

    #.  The MD-simulation with the parameters and structure that were used as input
    #.  The trajectory that was returned as an output
    #.  We are only interested in calculations that had a convergence threshold
        smaller than 1e-5 and cutoff larger 60 (quantities stored in the parameters)
    #.  In the parameters, we only want to load the temperature
    #.  The MD simulation has to be in state "parsing" or "finished"
    #.  We want the length of the trajectory
    #.  We filter for structures that:

        *   Have any lattice vector smaller than 3.0 or between 5.0 and 7.0
        *   Contain Nitrogen
        *   Have 4 atoms
        *   Have less than 3 types of atoms (elements)

    This would be the queryhelp::

        queryhelp =  {
            'path':[
                ParameterData,
                {
                    'class':MD,
                    'label':'md'
                },
                {'cls':Trajectory}, 
                {
                    'class':StructureData, 
                    'input_of':'md'
                },
                {
                    'cls':Relax,
                    'input_of':StructureData
                },
                {
                    'cls':StructureData,
                    'label':'struc2',
                    'input_of':Relax
                }
            ],
            'project':{
                ParameterData:'attributes.IONS.tempw',
                'md':['id', 'time'], 
                Trajectory:[
                    'id', 
                    'attributes.length'
                ],  
                StructureData:[
                    'id',
                    'name', 
                    'attributes.sites',
                    'attributes.cell'
                ], 
                'struc2':[
                    'id',
                    'name', 
                    'attributes.sites',
                    'attributes.cell'
                ],
            },
            'filters':{
                Param:{   
                    'and':[
                        {
                            'attributes.SYSTEM.econv':{
                                '<':1e-5
                            }
                        },
                        {
                            'attributes.SYSTEM.ecut':{
                                '>':60
                            }
                        }
                    ]
                        
                },
                'md':{
                    'state':{   
                        'in':(
                            'computing', 
                            'parsing', 
                            'finished',
                            'new'
                        )
                    }
                },
                StructureData:{
                    'or':[
                        {
                            'attributes.cell.0.0':{
                                'or':[
                                    {'<':3.0},
                                    {'>':5., '<':7.}
                                ]
                            },
                        },
                        {
                            'attributes.cell.1.1':{
                                'or':[
                                    {'<':3.0},
                                    {'>':5., '<':7.}
                                ]
                            },
                        },
                        {
                            'attributes.cell.2.2':{
                                'or':[
                                    {'<':3.0},
                                    {'>':5., '<':7.}
                                ]
                            },
                        },
                    ],
                    'attributes.sites':{
                        'of_length':4
                    }
                    'attributes.kinds':{
                        'shorter':3,
                        'has_key':'N',
                    }
                }
            }
        }
    """

    def __init__(self, *args, **kwargs):        
        from aiida.orm.implementation.django.node import Node as DjangoAiidaNode
        from aiida.orm.implementation.django.group import Group as DjangoAiidaGroup
        self.Link               = DummyLink
        self.Path               = DummyPath
        self.Node               = DummyNode
        self.Computer           = DummyComputer
        self.User               = DummyUser
        self.Group              = DummyGroup
        self.table_groups_nodes = Dummy_table_groups_nodes
        self.AiidaNode          = DjangoAiidaNode
        self.AiidaGroup         = DjangoAiidaGroup
        
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
            elif isinstance(value, datetime.datetime):
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
                    _analyze_filter_spec(alias, sub_filter_spec)
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


    def add_projectable_entity(self, alias, projectable_spec):
        """
        :param alias: 
            A instance of *sqlalchemy.orm.util.AliasedClass*, alias for an ormclass
        :param projectable_spec:
            User specification of what to project.
            Appends to query's entities what the user want to project
            (have returned by the query)
        
        """
        #~ raw_input(projectable_spec)
        if projectable_spec == '*': # project the entity
            self.que = self.que.add_entity(alias)
        else:
            column_name = projectable_spec
            if column_name == 'attributes':
                raise InputValidationError(
                    "\n\nI cannot project on Attribute table\n"
                    "Please use the SA backend for that functionality"
                )
            elif '.' in column_name:
                raise InputValidationError(
                    "\n\n"
                    "I cannot project on other entities\n"
                    "Please use the SA backend for that functionality"
                )
            self.que =  self.que.add_columns(self.get_column(column_name, alias))
        return projectable_spec


    def _execute_with_django(self):
        """
        Does not work because of the params 
        """
        from django.db import connection
        cursor = connection.cursor()
        #~ sql_query = str(self.que)
        c = self.que.statement.compile()
        sql_query_txt = str(c)
        params = c.params
        
        cursor.execute(sql_query_txt, params)
        res = cursor.fetchall()
        return res
