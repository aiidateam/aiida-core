.. _QueryBuilderQueryHelp:

The queryhelp
=============

As mentioned above, there are two possibilities to tell the QueryBuilder what to do.
The second uses one big dictionary that we can call the queryhelp in the following.
It has the same functionalities as the appender method. But you could save this dictionary in a
JSON or in the database and use it over and over.
Using the queryhelp, you have to specify the path, the filter and projections beforehand and
instantiate the QueryBuilder with that dictionary::

    qb = QueryBuilder(**queryhelp)

What do you have to specify:

*   Specifying the path:
    Here, the user specifies the path along which to join tables as a list,
    each list item being a vertice in your path.
    You can define the vertice in two ways:
    The first is to give the AiiDA-class::

        queryhelp = {
            'path':[Data]
        }

        # or  (better)

        queryhelp = {
            'path':[
                {'cls': Data}
            ]
        }

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


            from aiida.orm import TrajectoryData
            from aiida_quantumespresso.calculations.pw import PwCalculation
            from aiida.orm import Dict
            qh1 = {
                'path':[
                    {
                        'cls':PwCalculation
                    },
                    {
                        'cls':TrajectoryData
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
                        'cls':TrajectoryData
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
                    TrajectoryData,
                ]
            }

*   Project: Determing which columns the query will return::

        queryhelp = {
            'path':[PwCalculation],
            'project':{
                PwCalculation:['user_id', 'id'],
            }
        }

    If you are using JSONB columns,
    you can also project a value stored inside the json::

        queryhelp = {
            'path':[
                PwCalculation,
                StructureData,
            ],
            'project':{
                PwCalculation:['state', 'id'],
            }
        }

    Returns the state and the id of all instances of ``PwCalculation``
    where a structures is linked as output of a relax-calculation.
    The strings that you pass have to be name of the columns.
    If you pass a star ('*'),
    the query will return the instance of the AiidaClass.

*   Filters:
    What if you want not every structure,
    but only the ones that were added
    after a certain time (say last 4 days) and have an id higher than 50::

        from aiida.common import timezone
        from datetime import timedelta

        queryhelp = {
            'path':[
                {'cls':PwCalculation}, # PwCalculation with structure as output
                {'cls':StructureData}
            ],
            'filters':{
                StructureData:{
                    'ctime':{'>':  timezone.now() - timedelta(days=4)},
                    'id':{'>': 50}
                }
            }
        }



If you want to include filters and projections on links between nodes, you
will have to add these to filters and projections in the queryhelp.
Let's take an example that we had and add a few filters on the link::

    queryhelp = {
        'path':[
            {'cls':PwCalculation, 'tag':'relax'}, # PwCalculation with structure as output
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
nodes delimited by two dashes '--' and the order DOES matter.


If you dislike that way to tag the link, you can choose the tag for the edge in the
path when definining the entity to join using ``edge_tag``::

    queryhelp = {
        'path':[
            {'cls':PwCalculation, 'tag':'relax'},         # Relaxation with structure as output
            {
                'cls':StructureData,
                'tag':'structure',
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
