# -*- coding: utf-8 -*-


"""
The general functionalities that all querybuilders need to have
are found in this module.
:func:`QueryBuilderBase` is the Base class for QueryBuilder classes
adapted to the SQLAlchemy or Django schema.

"""


import copy
from abc import abstractmethod
from inspect import isclass as inspect_isclass
from sa_init import aliased

from aiida.common.exceptions import InputValidationError

replacement_dict = dict(
    float   = 'float', 
    int     = 'int',
    JSONB   = 'jsonb',
    str     = 'str'
)


class QueryBuilderBase(object):
    """
    QueryBuilderBase is the base class for QueryBuilder classes,
    which are than adapted to the individual schema and ORM used.
    In here, general graph traversal functionalities are implemented,
    the specific type of node and link is dealt in subclasses.
    """
    def __init__(self,  queryhelp, **kwargs):
        """
        :param queryhelp: The queryhelp is my API.
            It is a dictionary that tells me:

            *   what to join (key **path**)
            *   what to project (key **project**)
            *   how to filter   (key **filters**)

        *   Specifying the path: Here, the user specifies the path along which to join tables.
            The value is a list, each list item being a vertice in your path.
            You can define the vertice in two ways:
            The first is to give the orm-class::

                queryhelp = {
                    'path':[
                        {'class':Data}
                    ]
                }

            The second is to give the polymorphic identity
            of this class, in our case stored in type::

                queryhelp = {
                    'path':[
                        {'class':"data"}
                    ]
                }

            .. note:: 
                In Aiida, polymorphism is not strictly enforced, but
                achieved with *type* specification in a column.
                Type-discrimination is achieved by attaching a filter on the
                type every time a subclass of Node is given,
                in above example this would results in::

                    ...filter(DbNode.type.like("%data%"))...

                Make sure this is a unique way...

            Each node has to have a unique label.
            The label is chosen to be equal to the type of the class.
            This will not work user chooses the same class twice.
            In this case he has to provide a label::
            
                queryhelp = {
                    'path':[
                        {
                            'class':Node,
                            'label':'node_1'
                        }
                        {
                            'class':"Node",
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
                  
                    qh2 = {
                        'path':[
                            {'class':PwCalculation}, 
                            {'class':Trajectory}, 
                            {
                                'class':ParameterData 
                                'direction':-2
                            }
                        ]
                    }
                    
                    # returns same query as:
                    
                    qh3 = {
                        'path':[
                            {'class':PwCalculation}, 
                            {'class':Trajectory}, 
                            {
                                'class':ParameterData,
                                'input_of':PwCalculation
                            }
                        ]
                    }

        *   Projecting: 
            Determing which columns the query will return::

                queryhelp = {
                    'path':[{'class':Relax}],
                    'project':{
                        Relax:['state', 'id'],
                    }
                }

            If you are using JSONB columns,
            you can also project a value stored inside the json::

                queryhelp = {
                    'path':[
                        {'class':Relax},
                        {'class':StructureData}
                        
                        ],
                    'project':{
                        'node.calc.relax':['state', 'id'],
                        StructureData:['attributes.cell']
                    }
                }

            Returns the state and the id of all instances of Relax and 
            the cells of all structures given that the structures are linked as output of a relax-calculation.
            The strings that you pass have to be name of the columns.
            If you pass a star ('*') or ``True``, the query will return the instance of the ormclass.

        *   Filtering:
            What if I want not every structure, 
            but only the ones that were added after a certain time `t` and have an id higher than 50::
                
                queryhelp = {
                    'path':[
                        {'class':Relax}, # Relaxation with structure as output
                        {'class':StructureData}
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
                    'path':[{'class':Struc}],
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
                    {'class':ParameterData}, 
                    {
                        'class':MD,
                        'label':'md'
                    },
                    {'class':Trajectory}, 
                    {
                        'class':StructureData, 
                        'input_of':'md'
                    },
                    {
                        'class':Relax,
                        'input_of':StructureData
                    },
                    {
                        'class':StructureData,
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
                    'md':[
                        {
                            'state':{   
                                'in':(
                                    'computing', 
                                    'parsing', 
                                    'finished',
                                    'new'
                                )
                            }
                        }
                    ],
                    StructureData:[
                        {
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
                            ]
                            
                        },
                        {
                            'attributes.sites':{
                                'of_length':4
                            }
                        },
                        {
                            'attributes.kinds':{
                                'shorter':3,
                                'has_key':'N',
                            }
                        }
                    ],
                    
                }
            }
            
            
        """

        self.path = []
        self.alias_dict = {}
        queryhelp = copy.deepcopy(queryhelp)
        
        if not isinstance(queryhelp, dict):
            queryhelp = {
                'path':queryhelp
            }

        self.projection_dict_user = self.make_json_compatible(queryhelp.pop('project', {}))
        self.filters = self.make_json_compatible(queryhelp.pop('filters', {}))
        # Confuse this myself, whether it's filter or filters
        #self.filters = self.filters.update(make_json_compatible(queryhelp.pop('filter', {})))
        self.ormclass_list = []
        self.label_list = []
        self.alias_list = []
        self.alias_dict = {}
        if not isinstance(queryhelp['path'], (tuple, list)):
            queryhelp['path'] = [queryhelp['path']]
        for path_spec in queryhelp.pop('path'):
            self._add_to_path(path_spec)
        self.limit = queryhelp.pop('limit', False)
        self.order_by = queryhelp.pop('order_by', False)

    def _add_to_path(self, path_spec, autolabel =  False):
        """
        Any iterative procedure to build the path of a graph query needs to
        invoke this method to append to the path.

        :param path_spec: The specification of what this node looks like
        :param autolabel: Whether to automatically search for a unique label, default to False
        """
        path_spec = self.make_json_compatible(path_spec)
        if isinstance(path_spec, dict):
            assert 'class' in path_spec.keys(), 'You need to provide a key "class" with the value being an ORMClass or a unique type'
        else:
            path_spec = {'class': path_spec}

        ormclass_type =  path_spec['class']

        if autolabel:
            i = 1
            while True:
                label = '{}_{}'.format(ormclass_type, i)
                if label not in self.label_list:
                    break
                i  += 1
        else:
            label = path_spec.get('label',ormclass_type)
            if label in self.label_list:
                raise Exception (' Label {} is not unique, choose different label'.format(label))

        self.label_list.append(label)
        path_spec['label'] = label
        self.filters[label] = self.filters.get(label, {})
        # This way to attach the filter is not ideal
        # You have the type of the calculation being 
        #   a) the label
        #   b) the filter on type
        # A long type name as in Aiida makes a cumbersome label,
        # but shortening it will results in slower queries (like instead of =)
        # and ambiguouty when the class name is the same, but in different module...
        # How to solve that?

        self.filters[label]['type'] = self.filters[label].get('type', {'like':'%{}%'.format(ormclass_type)})
        ormclass = self.get_ormclass(ormclass_type)
        self.ormclass_list.append(ormclass)
        alias = aliased(ormclass)
        self.alias_list.append(alias)
        self.alias_dict[label] = alias
        self.path.append(path_spec)
        return label

    @staticmethod
    @abstractmethod
    def get_session():
        pass
    @abstractmethod
    def get_expr(*args):
        """
        Applies a filter on the alias given.
        Expects the alias of the ORM-class on which to filter, and filter_spec.
        Filter_spec contains the specification on the filter.
        Expects:
        
        *   ``operator``: The operator to apply. These can be:
        
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

            All the above filters invoke a negation of the expression if preceded by ~

            - {'name':{'~in':['halle', 'lujah']}} # Name not 'halle' or 'lujah'
            - {'id':{ '~==': 2}} # id is not 2

        - ``value``: The 
            value for the right side of the expression,
            the value you want to compare with.
        - ``path``: The path leading to the value
        - ``attr_key``: Boolean, whether the value is in a json-column,
            or in an attribute like table.

        """
        pass
    @abstractmethod
    def analyze_filter_spec(*args):
        pass

    def _join_slaves(self, joined_entity, entity_to_join):
        raise NotImplementedError
        #~ call = aliased(Call)
        #~ self.que = self.que.join(call,  call.caller_id == joined_entity.id)
        #~ self.que = self.que.join(entity_to_join, call.called_id == entity_to_join.id)

    def _join_masters(self, joined_entity, entity_to_join):
        raise NotImplementedError
        #~ call = aliased(Call)
        #~ self.que = self.que.join(call,  call.called_id == joined_entity.id)
        #~ self.que = self.que.join(entity_to_join, call.caller_id == entity_to_join.id)
    def _join_outputs(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) ORMclass that is an input
        :param entity_to_join: The (aliased) ORMClass that is an output.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as input to **enitity_to_join** as output
        (**enitity_to_join** is an *output_of* **joined_entity**)
        """
        aliased_link = aliased(self.Link)
        self.que = self.que.join(
            aliased_link,
            aliased_link.input_id  == joined_entity.id
        ).join(
            entity_to_join,
            aliased_link.output_id == entity_to_join.id
        )

    def _join_inputs(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) ORMclass that is an output
        :param entity_to_join: The (aliased) ORMClass that is an input.

        **joined_entity** and **entity_to_join** are joined with a link
        from **joined_entity** as output to **enitity_to_join** as input
        (**enitity_to_join** is an *input_of* **joined_entity**)
        """
        aliased_link = aliased(self.Link)
        self.que = self.que.join(
            aliased_link,
            aliased_link.output_id == joined_entity.id
        ).join(
            entity_to_join,
            aliased_link.input_id  == entity_to_join.id
        )

    def _join_descendants(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) ORMclass that is an ancestor
        :param entity_to_join: The (aliased) ORMClass that is a descendant .

        **joined_entity** and **entity_to_join** are joined via the DbPath table.
        from **joined_entity** as parent to **enitity_to_join** as child
        (**enitity_to_join** is a *descendant_of* **joined_entity**)
        """
        aliased_path = aliased(self.Path)
        self.que = self.que.join(
            aliased_path,
            aliased_path.parent_id == joined_entity.id
        ).join(
            entity_to_join,
            aliased_path.child_id  == entity_to_join.id
        )

    def _join_ancestors(self, joined_entity, entity_to_join):
        """
        :param joined_entity: The (aliased) ORMclass that is a descendant
        :param entity_to_join: The (aliased) ORMClass that is an ancestor.

        **joined_entity** and **entity_to_join** are joined via the DbPath table.
        from **joined_entity** as child to **enitity_to_join** as parent
        (**enitity_to_join** is an *ancestor_of* **joined_entity**)
        """
        aliased_path = aliased(self.Path)
        self.que = self.que.join(
            aliased_path,
            aliased_path.child_id == joined_entity.id
        ).join(
            entity_to_join,
            aliased_path.parent_id  == entity_to_join.id
        )


    def _get_connecting_node(self, querydict, index):
        """
        :param querydict:
            A dictionary specifying how the current node
            is linked to other nodes.
        :param index: Index of this node within the path specification

        Valid (currently implemented) keys are:

        *   *input_of*
        *   *output_of*
        *   *descendant_of*
        *   *ancestor_of*
        *   *direction*

        Future:

        *   *master_of*
        *   *slave_of*
        """
        if [
            'input_of' in querydict,
            'output_of' in querydict,
            'slave_of' in querydict,
            'master_of' in querydict,
            'ancestor_of' in querydict,
            'descendant_of' in querydict,
            'direction' in querydict,
            ].count(True) > 1:
            raise Exception( 'Too many specification to join in {}'.format(querydict))
        if 'input_of' in querydict:
            func = self._join_inputs
            val = querydict['input_of']
        elif 'output_of' in querydict:
            func = self._join_outputs
            val = querydict['output_of']
        elif 'slave_of' in querydict:
            func = self._join_slaves
            val  = querydict['slave_of']
        elif 'master_of' in querydict:
            func = self._join_masters
            val  = querydict['master_of']
        elif 'descendant_of' in querydict:
            func = self._join_descendants
            val  = querydict['descendant_of']
        elif 'ancestor_of' in querydict:
            func = self._join_ancestors
            val  = querydict['ancestor_of']
        else:
            direction = querydict.get('direction', 1)
            if direction > 0:
                func = self._join_outputs
                val  = index  - direction
            elif direction < 0:
                func = self._join_inputs
                val  = index + direction
            else:
                raise Exception(
                    "Direction 0 is not valid"
                )
        if isinstance(val, int):
            return self.alias_list[val], func
        elif isinstance(val, str):
            try:
                
                val = self.labels_location_dict[val]
                return self.alias_list[val], func
            except AttributeError:
                raise Exception (   'List of types is not unique, '
                                    'therefore you cannot specify types to determine node to connect with. '
                                    'Give the position (integer) in the queryhelp')
            except KeyError:
                raise Exception (   'Key {} is unknown to the types I know about:\n {}'.format(val, self.labels_location_dict.keys()))
            
        raise Exception('Unrecognized connection specification {}'.format(val))

    def make_json_compatible(self, inp):
        """
        Makes the a dictionary json - compatible.
        In this way, the queryhelp can be stored in a node in the database and
        retrieved or shared.

        :param inp:
            The input value that will be converted.
            Recurses into each value if **inp** is an iterable.

        :returns: A json-compatible value of **inp**

        All classes defined in the input are converted to strings specifying the type,
        for example:
        
        *   ``float`` --> "float"
        *   ``StructureData`` --> "StructureData"
        """
        
        if isinstance(inp, dict):
            for key, val in inp.items():
                inp[self.make_json_compatible(key)] = self.make_json_compatible(inp.pop(key))
        elif isinstance(inp, (list, tuple)):
            inp = [self.make_json_compatible(val) for val in inp]
        elif inspect_isclass(inp) and issubclass(inp, self.AiidaNode):
            return inp._plugin_type_string.strip('.').split('.')[-1]
        else:
            try:
                inp = replacement_dict.get(inp, inp)
            except Exception as e:
                raise Exception("""
                Exception thrown: {}\n
                while replacing {}""".format(e, inp))
        return inp




    def get_column(self, colname, alias):
        """
        Return the column for the projection, if the column name is specified.
        """
        try:
            return getattr(alias, colname)
        except KeyError:
            raise InputValidationError(
                '{} is not a column of {}'.format(colname, alias)
            )
        if isinstance(col, InstrumentedAttribute):
            return col 
        raise InputValidationError(
            '{} is not a column'.format(colname)
        )


    def _build_query(self):
        """
        build the query and return a sqlalchemy.Query instance
        """

        ####################### ALIASING ####################
        # First I need to alias everything,
        # because I might be joining the same table multiple times,
        # check also
        # http://dself.ocs.sqlalchemy.org/en/rel_1_0/orm/query.html


        if not len(self.label_list) == len(set(self.label_list)):
            raise InputValidationError(
                "Labels are not unique:\n"
                "{}".format(self.label_list)
            )


        # self.labels_location_dict is a dictionary that 
        # maps the label to its index in the list
        # this is basically the mapping between the count
        # of nodes traversed
        # and the label used for that node 
        self.labels_location_dict = {
            label:index
            for index, label
            in enumerate(self.label_list)
        }

        #Starting the query by receiving a session
        # Every subclass needs to have get_session and give me the
        # right session
        self.que = self.get_session().query(self.alias_list[0])


        ######################### JOINS ################################

        for index,  alias, querydict in  zip(
                range(
                    len(self.alias_list)
                ),
                self.alias_list,
                self.path
            ):
            #looping through the queryhelp
            if index:
                #There is nothing to join if that is the first table
                (
                    toconnectwith,
                    connection_func
                ) = self._get_connecting_node(querydict, index)
                connection_func(toconnectwith, alias)

        ######################### FILTERS ##############################

        for label, filter_specs in self.filters.items():
            try:
                alias = self.alias_dict[label]
            except KeyError:
                # TODO Check KeyError before?
                raise InputValidationError(
                    ' You looked for label {} among the alias list\n'
                    'The labels I know are:\n{}'
                    ''.format(label,self.alias_dict.keys())
                )

            if not isinstance(filter_specs, (list, tuple)):
                filter_specs = [filter_specs]

            for filter_spec in filter_specs:
                expr  =  self.analyze_filter_spec(alias, filter_spec)
                self.que = self.que.filter(expr)

        ######################### PROJECTIONS ##########################
        # first clear the entities in the case the first item in the
        # path was not meant to be projected

        # attribute of Query instance storing entities to project:
        self.que._entities = []
        # Will be later set to this list:
        entities = []
        # Mapping between enitites and the label used/ given by user:
        self.label_to_projected_entity_dict = {}

        if not self.projection_dict_user: 
            # If user has not set projection,
            # I will simply project the last item specified!
            # Don't change, path traversal querying
            # relies on this behavior!
            self.projection_dict_user =  {self.label_list[-1]:'*'}

        position_index = -1
        for vertice in self.path:
            label = vertice['label']
            items_to_project = self.projection_dict_user.get(label, [])
            if not items_to_project:
                continue
            alias = self.alias_dict[label]
            #~ raw_input(alias)
            if not isinstance(items_to_project, (list, tuple)):
                items_to_project = [items_to_project]
            self.label_to_projected_entity_dict[label] = {}
            for projectable_spec in items_to_project:
                projectable_spec = self.add_projectable_entity(projectable_spec, alias)
                position_index += 1
                self.label_to_projected_entity_dict[label][projectable_spec]  = position_index

        ######################### LIMIT ################################
        if self.limit:
            self.que = self.que.limit(self.limit)

        ######################### ORDER ################################
        if self.order_by:
            # TODO
            raise NotImplementedError('order_by is not implemented')
        return self.que

    def _make_counterquery(self,calc_class, code_inst = None, session = None):
        input_alias_list = []
        for node in self.path:
            label = node['label']
            if label not in  self.projection_dict_user.keys():
                continue
            #~ if label in exclude_list:
                #~ continue
            assert flatten_list(self.projection_dict_user[label]) == ['*'], "Only '*' allowed for input spec"
            input_alias_list.append(aliased(self.alias_dict[label]))
        
        if issubclass(calc_class, self.Node):
            orm_calc_class  = calc_class
            type_spec = None
        elif issubclass(calc_class, self.AiidaNode):
            orm_calc_class  = self.Node
            type_spec = calc_class._plugin_type_string
        else:
            raise Exception(
                'You have given me {}\n'
                'of type {}\n'
                "and I don't know what to do with that"
                ''.format(calc_class, type(calc_class))
            )
        counterquery =  self.get_session().query(orm_calc_class)
        if type_spec:
            counterquery = counterquery.filter(orm_calc_class.type == type_spec)
        for alias in input_alias_list:
            link = aliased(self.Link)
            counterquery = counterquery.join(
                link,
                orm_calc_class.id == link.output_id
            ).join(
                alias,
                alias.id == link.input_id)
            counterquery = counterquery.add_entity(alias)
        counterquery._entities.pop(0)
        return counterquery

    def except_if_input_to(self, calc_class):
        self.que = self.get_query()
        self.que = self.que.except_(self._make_counterquery(calc_class))
        return self

    def get_calculations_todo(self, calc_class):
        return self._build_query().except_(self._make_counterquery(calc_class)).all()


    def outputs_p(self, user_filter = []):
        label = self._add_to_path({'class':'node', 'output_of':self.path[-1]['label']}, autolabel = True)
        self.filters.update({label:user_filter})
        return self
        
    def inputs_p(self, user_filter = []):
        label = self._add_to_path({'class':'node', 'input_of':self.path[-1]['label']}, autolabel = True)
        self.filters.update({label:user_filter})
        return self

    def get_aliases(self):
        return self.alias_list

    def get_dict(self):
        """
        Returns the json-compatible list
        """
        return {
            'path':self.path, 
            'filters':self.filters,
            'project':self.projection_dict_user
        }

    def first(self):
        """
        Returns the first item of the query result
        """
        return self.get_query().first()

    def get_query(self):
        """
        Checks if query instance is
        set as attribute of instance,
        if not invokes :func:`~_build_query` 
        """
        if hasattr(self, 'que'):
            return self.que
        return self._build_query()

    def all(self):
        """
        Returns all results
        """
        return self.get_query().all()

    def get_results_dict(self):
        """
        Returns all results as a list of  dictionaries.
        Also replaces ORM instances with their corresponding 
        Aiida instance by calling get_aiida_class.
        
        Each item of the list corresponds to one row of a SQL-query.
        Each key-pair value of that dictionary corresponds to
        a label (eg 'id', 'label', 'attributes') and the corresponding
        value.
        '*' is the key for an ORMClass being returned.
        """
        def get_result(res, pos):
            if hasattr(res,'__iter__'):
                return res[pos]
            else:
                return res
        def get_aiida_res(res, key):
            if key == '*':
                return res.get_aiida_class()
            return res

        all_results = self.get_query().all()

        return_list = [
            {
                label:{
                    key : get_aiida_res(get_result(this_result, position), key)
                    for key, position in val.items()
                }
                for label, val in self.label_to_projected_entity_dict.items()
            }
            for this_result in all_results
        ]
        return return_list



def flatten_list ( value ):
    """
    Flattens a list or a tuple
    In [2]: flatten_list([[[[[4],3]],[3],['a',[3]]]])
    Out[2]: [4, 3, 3, 'a', 3]

    :param value: A value, whether iterable or not
    :returns: a list of nesting level 1
    """

    if isinstance(value, (list, tuple)):
        return_list = []
        [[return_list.append(i) for i in flatten_list(item)] for item in value]
        return return_list
    return [value]
