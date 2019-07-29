.. _QueryBuilderQueryHelp:

The queryhelp
=============

As mentioned above, there are two possibilities to tell the QueryBuilder what to do.
The second uses one big dictionary that we can call the queryhelp in the following.
It has the same functionalities as the appender method. But you could save this dictionary in a
JSON or in the database and use it over and over.
Using the queryhelp, you have to specify the path, the filter and projections beforehand and
instantiate the QueryBuilder with that dictionary::

    qb = Querybuilder(**queryhelp)

What do you have to specify:

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

    Another way is to give the polymorphic identity of this class, in our case stored in type::

        queryhelp = {
            'path':[
                {'type':"data."}
            ]
        }

    .. note::
        In Aiida, polymorphism is not strictly enforced, but
        done with *type* specification.
        Type-discrimination when querying is achieved by attaching a filter on the
        type every time a subclass of Node is given.

    Each node has to have a unique tag.
    If not given, the tag is chosen to be equal to the name of the class.
    This will not work if the user chooses the same class twice.
    In this case he has to provide the tag::

        queryhelp = {
            'path':[
                {
                    'cls':Node,
                    'tag':'node_1'
                },
                {
                    'cls':Node,
                    'tag':'node_2'
                }
            ]
        }

    There also has to be some information on the edges,
    in order to join correctly.
    There are several redundant ways this can be done:

    *   You can specify that this node is an input or output of another node
        preceding the current one in the list.
        That other node can be specified by an
        integer or the class or type.
        The following examples are all valid joining instructions,
        assuming there is a structure defined at index 2
        of the path with tag "struc1"::

            edge_specification = queryhelp['path'][3]
            edge_specification['with_incoming'] = 2
            edge_specification['with_incoming'] = StructureData
            edge_specification['with_incoming'] = 'struc1'
            edge_specification['with_outgoing']  = 2
            edge_specification['with_outgoing']  = StructureData
            edge_specification['with_outgoing']  = 'struc1'

    *   queryhelp_item['direction'] = integer

        If any of the above specs ("with_outgoing", "with_incoming")
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
                        'cls':Dict,
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
                        'cls':Dict,
                        'with_outgoing':PwCalculation
                    }
                ]
            }

            # Shorter version:

            qh3 = {
                'path':[
                    Dict,
                    PwCalculation,
                    Trajectory,
                ]
            }

*   Project: Determing which columns the query will return::

        queryhelp = {
            'path':[Relax],
            'project':{
                Relax:['user_id', 'id'],
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
                Relax:['state', 'id'],
            }
        }

    Returns the state and the id of all instances of Relax
    where a structures is linked as output of a relax-calculation.
    The strings that you pass have to be name of the columns.
    If you pass a star ('*'),
    the query will return the instance of the AiidaClass.

*   Filters:
    What if you want not every structure,
    but only the ones that were added
    after a certain time `t` and have an id higher than 50::

        from aiida.common import timezone
        from datetime import timedelta

        queryhelp = {
            'path':[
                {'cls':Relax}, # Relaxation with structure as output
                {'cls':StructureData}
            ],
            'filters':{
                StructureData:{
                    'ctime':{'>':  timezone.now() - timedelta(days=4)},
                    'id':{'>': 50}
                }
            }
        }

.. ~     With the key 'filters', we instruct the querybuilder to
.. ~     build filters and attach them to the query.
.. ~     Filters are passed as dictionaries.
.. ~     In each key-value pair, the key is the column-name
.. ~     (as a string) to filter on.
.. ~     The value is another dictionary,
.. ~     where the operator is a key and the value is the
.. ~     value to check against.
.. ~
.. ~     .. note:: This follows (in some way) the MongoDB-syntax.
.. ~
.. ~     But what if the user wants to filter
.. ~     by key-value pairs defined inside the structure?
.. ~     In that case,
.. ~     simply specify the path with the dot (`.`) being a separator.
.. ~     If you want to get to the volume of the structure,
.. ~     stored in the attributes, you can specify::
.. ~
.. ~         queryhelp = {
.. ~             'path':[{'cls':StructureData}],  # or 'path':[StructureData]
.. ~             'filters':{
.. ~                 'attributes.volume': {'<':6.0}
.. ~             }
.. ~         }
.. ~
.. ~     The above queryhelp would build a query
.. ~     that returns all structures with a volume below 6.0.
.. ~
.. ~     .. note::
.. ~         A big advantage of SQLAlchemy is that it support
.. ~         the storage of jsons.
.. ~         It is convenient to dump the structure-data
.. ~         into a json and store that as a column.
.. ~         The querybuilder needs to be told how to query the json.
.. ~
.. ~ Let's get to a really complex use-case,
.. ~ where we need to reconstruct a workflow:
.. ~
.. ~ #.  The MD-simulation with the parameters and structure used as input
.. ~ #.  The trajectory that was returned as an output
.. ~ #.  We are only interested in calculations with a convergence threshold
.. ~     smaller than 1e-5 and cutoff larger 60 (stored in the parameters)
.. ~ #.  In the parameters, we only want to load the temperature
.. ~ #.  The MD simulation has to be in state "parsing" or "finished"
.. ~ #.  We want the length of the trajectory
.. ~ #.  We filter for structures that:
.. ~
.. ~     *   Have any lattice vector smaller than 3.0 or between 5.0 and 7.0
.. ~     *   Contain Nitrogen
.. ~     *   Have 4 atoms
.. ~     *   Have less than 3 types of atoms (elements)
.. ~
.. ~ This would be the queryhelp::
.. ~
.. ~     queryhelp =  {
.. ~         'path':[
.. ~             Dict,
.. ~             {'cls':PwCalculation, 'tag':'md'},
.. ~             {'cls':Trajectory},
.. ~             {'cls':StructureData, 'with_outgoing':'md'},
.. ~             {'cls':Relax, 'with_outgoing':StructureData},
.. ~             {'cls':StructureData,'tag':'struc2','with_outgoing':Relax}
.. ~         ],
.. ~         'project':{
.. ~             Dict:{'attributes.IONS.tempw':{'cast':'f'}},
.. ~             'md':['id', 'time'],
.. ~             Trajectory:['id', 'attributes.length'],
.. ~             StructureData:'*',
.. ~             'struc2':['*']    # equivalent, the two!
.. ~         },
.. ~         'filters':{
.. ~             Dict:{
.. ~                 'attributes.SYSTEM.econv':{'<':1e-5},
.. ~                 'attributes.SYSTEM.ecut':{'>':60},
.. ~             },
.. ~             'md':{
.. ~                 'state':{'in':['PARSING', 'FINISHED']},
.. ~             },
.. ~             StructureData:{
.. ~                 'or':[
.. ~                     {
.. ~                         'attributes.cell.0.0':{
.. ~                             'or':[
.. ~                                 {'<':3.0},
.. ~                                 {'>':5., '<':7.}
.. ~                             ]
.. ~                         },
.. ~                     },
.. ~                     {
.. ~                         'attributes.cell.1.1':{
.. ~                             'or':[
.. ~                                 {'<':3.0},
.. ~                                 {'>':5., '<':7.}
.. ~                             ]
.. ~                         },
.. ~                     },
.. ~                     {
.. ~                         'attributes.cell.2.2':{
.. ~                             'or':[
.. ~                                 {'<':3.0},
.. ~                                 {'>':5., '<':7.}
.. ~                             ]
.. ~                         },
.. ~                     },
.. ~                 ],
.. ~                 'attributes.sites':{
.. ~                     'of_length':4
.. ~                 },
.. ~                 'attributes.kinds':{
.. ~                     'shorter':3,
.. ~                     'has_key':'N',
.. ~                 }
.. ~             }
.. ~         }
.. ~     }


If you want to include filters and projections on links between nodes, you
will have to add these to filters and projections in the queryhelp.
Let's take an example that we had and add a few filters on the link::

    queryhelp = {
        'path':[
            {'cls':Relax, 'tag':'relax'}, # Relaxation with structure as output
            {'cls':StructureData, 'tag':'structure'}
        ],
        'filters':{
            'structure':{
                'id':{'>': 50}
            },
            'relax--structure':{
                'label':{'like':'output_%'},
            }
        },
        'project':{
            'relax--structure':['label'],
            'structure':['label'],
            'relax':['label', 'uuid'],
        }
    }

Notice that the tag for the link, by default, is the tag of the two connecting
nodes delimited by two dashes '--'.


.. ~The order does not matter, the following queryhelp would results in the same query::
.. ~
.. ~    queryhelp = {
.. ~        'path':[
.. ~            {'cls':Relax, 'tag':'relax'},         # Relaxation with structure as output
.. ~            {'cls':StructureData, 'tag':'structure'}
.. ~        ],
.. ~        'filters':{
.. ~            'structure':{
.. ~                'time':{'>': t},
.. ~                'id':{'>': 50}
.. ~            },
.. ~            'relax--structure':{
.. ~                'time':{'>': t},
.. ~                'label':{'like':'output_%'},
.. ~            }
.. ~        },
.. ~        'project':{
.. ~            'relax--structure':['label'],
.. ~            'structure':['label'],
.. ~            'relax':['label', 'state'],
.. ~        }
.. ~    }

If you dislike that way to tag the link, you can choose the tag for the edge in the
path when definining the entity to join using ``edge_tag``::

    queryhelp = {
        'path':[
            {'cls':Relax, 'label':'relax'},         # Relaxation with structure as output
            {
                'cls':StructureData,
                'label':'structure',
                'edge_tag':'ThisIsMyLinkTag'     # Definining the link tag
            }
        ],
        'filters':{
            'structure':{
                'id':{'>': 50}
            },
            'ThisIsMyLinkTag':{                  # Using this link tag
                'label':{'like':'output_%'},
            }
        },
        'project':{
            'ThisIsMyLinkTag':['label'],
            'structure':['label'],
            'relax':['label', 'uuid'],
        }
    }


You can set a limit and an offset in the queryhelp::

    queryhelp = {
        'path':[Node],
        'limit':10,
        'offset':20
    }

That queryhelp would tell the QueryBuilder to return 10 rows after the first 20
have been skipped.
