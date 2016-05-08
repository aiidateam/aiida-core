Using the QueryBuilder
======================

.. toctree::
   :maxdepth: 2

This section describes the use of the QueryBuilder, which
is meant to help you querying the database
with a Python interface and regardless of backend and schema used.
Before jumping into the specifics, let's discuss what you should be clear about
before writing a query:

*   You should know which quantities you want to query for.
    In database-speek, you need to tell the backend what to *project*.
    For example, you might only be interested in the label of a calculation and the pks of 
    all its outputs, and nothing else.
*   In many use-cases, you will query for relationships between entities that are
    connected in a graph-like fashion, with links as edges and nodes as vertices.
    You have to know how to describe a *path* between your entities.
*   In almost all cases, you will be interested in a subset of all possible
    entities that could be returned based on the joins between the entities of
    your graph. In other ways, you need to have an idea of how to filter the
    results.

If you are clear about what you want and how you can get it,
you will have to provide this information to QueryBuilder, who will build
an SQL-query for you.
There are possible APIs that you can use, and the have the exact same functionalities,
it's up to you what to use:

#.  The appender-method
#.  Using the queryhelp 

Let's first discuss the appender-method using some concrete examples.
Suppose you are interested in all calculations in your database that are in 
state 'FINISHED' and were created in the last *n* days::

    from datetime import timedelta
    from aiida.utils import timezone
    now = timezone.now()
    qb = QueryBuilder()    # An empty QueryBuilder instances
    qb.append(
        JobCalculation,  # I am appending a JobCalculation to the path
        filters={            # Specifying the filters, such as
            'state':{'==':'FINISHED'},   # the calculation has to have finished
            'ctime':{'>': now - timedelta(days=n)}  # created in the last n days
        },
        project=['label']       # Only need the label of the calculations
    )
    resultgen = qb.all()     # Give me all results (returns a generator)
    resultslist = list(resultgen) # Making it a list (of labels)

.. note::
    How to get the results back will be described later.
    But in general, a generator is returned to speed up the process.

Let's go through the above example.
We have instantiated QueryBuilder instance.
We appended to its path a JobCalculation (a remote calculation),
and specified that we are only interested in  calculations 
that have finished **and** that were created in the last *n* days.

What if we want calculations that have finished **or** were created in the last
*n* days::

    qb = QueryBuilder()
    qb.append(
            JobCalculation,
            filters={
                'or':[
                    {'state':{'==':'FINISHED'}},
                    {'ctime':{'>': now - timedelta(days=n)}}
                ]
            },
            project=['label']
        )
    print list(qb.all())

If we'd have written *and* instead of *or*, we would have created the exact same
query as in the first query, because *and* is the default behavior if
you attach several filters.
What if you want calculation in state 'FINISHED' or 'RETRIEVING'?
This will be the next example. We will not filter by creation time,
but have the time returned to as::

    qb = QueryBuilder()
    qb.append(
            JobCalculation,
            filters={
                'state':{'in':['FINISHED', 'RETRIEVING']}
            },
            project=['label', 'ctime']
        )
    print list(qb.all())

Got it? This was the query for a single node in the database.
Let's make it more complicated by querying relationships in graph-like database.
You are familiar with the :ref:`sec.quantumespresso` tutorial? Great, because this will be
our usecase here.

A common query is to query for calculations that were done on a certain structure (*mystructure*),
that fulfill certain requirements, such as a cutoff above 30.0.
In our case, we have a structure (an instance of StructureData) and an instance
of ParameterData that are both inputs to a PwCalculation.
You need to tell the QueryBuilder that::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        filters={
            'uuid':{'==':mystructure.uuid}
        },
        label='strucure'
    )
    qb.append(
        PwCalculation,
        output_of='strucure',
        project='*',
        label='calc'
    )
    qb.append(
        ParameterData,
        filters={
            'attributes.SYSTEM.ecutwfc':{'>':30.0}
        },
        input_of='calc'
    )
    
A few notes on the above examples:

*   We specify a path in the graph by vertices of a path. We
    need to tell the QueryBuilder how two vertices are connected.
    This we do with keywords such as:

    *   *input_of* if this node is the input of a node previously specified in
        the path
    *   *output_of* if this node is an output.
*   The projection '*' returns an instance of an ORM-class
*   You should provide a unique label for each vertice in the path, and 
    refer to that label if you specify a relation between two nodes


*Should* because you can omit a few specification to save some typing:

*   The default edge specification, if no keyword is provided, is always
    *output_of* the previous vertice.
*   Equality filters ('==') can be shortened, as will be shown below.
*   Labels are not necessary, you can simply use the class as a label.
    This works as long as the same Aiida-class is not used again

A shorter version of the previous example::

    qb = QueryBuilder()
    qb.append(StructureData,
        filters={'uuid':mystructure.uuid},
    )
    qb.append(
        PwCalculation,
        project='*',
    )
    qb.append(
        ParameterData,
        filters={
            'attributes.SYSTEM.ecutwfc':{'>':30.0}
        },
        input_of=PwCalculation
    )

.. note:: 
    A warning on filtering and projections in the attributes (or extras).
    Here, the type of a data value is not predetermined.
    But the QueryBuilder needs to know the type of the value stored in the database
    to give the correct value.
    In principle, the same value will be taken as the value to compair with.
    But if for the above example the cutoff was stored as an integer in the database,
    the above query will not return any results.
    **Be consistent using types**.
    When something could be a float, store a float, and if a value is meant to store a boolean,
    store a boolean and not 0 and 1 (integers).

Let's get to the projections.
You already might have guessed that you provide the name of columns as a list of strings.
If you want instances of the ORM-class, you specify '*'.
Let's get the id  ``pk'' and the ORM-instances of all structures in the database::

    qb = QueryBuilder()
    qb.append(StructureData, project=['id', '*'])
    print list(qb.all())

This will return a list of result tuples, each one containing the pk and the corresponding 
StructureData instance.
The following reverses the order inside the sublists::

    qb = QueryBuilder()
    qb.append(StructureData, project=['*', 'id'])
    print list(qb.all())

What if you want to project a certain attributes.
That is trickier! You again need to tell the QueryBuilder the type.
Assuming you want to get the energies returned by all PwCalculation done in the last 3 days::

    qb = QueryBuilder()
    qb.append(
            JobCalculation,
            filters={'ctime':{'>': now - timedelta(days=3)}}
        )
    qb.append(
            ParameterData,
            project=[{'attributes.energy':{'cast':'f'}}],
        )
    print list(qb.all())

You need to specify the type of the quantity, in that case a float:

*   'f' for floats
*   'i' for integers
*   't' for texts (strings, characters)
*   'b' for booelans
*   'd' for dates

So again, be consisted when storing values in the database.
To sum up, a projection is technically a list of dictionaries.
If you don't have to cast the type, because the value is not stored as an attribute (or extra),
then the string is sufficient.
If you don't care about the order (ensured by passing a list), you can also put values in
one dictionary. Let's also get the units  of the energy::

    qb = QueryBuilder()
    qb.append(
            JobCalculation,
            filters={'ctime':{'>': now - timedelta(days=3)}}
        )
    qb.append(
            ParameterData,
            project={
                'attributes.energy':{'cast':'f'},
                'attributes.energy_units':{'cast':'t'},
            }
         )
    print list(qb.all())


You can do much more with projections! You might be interested in the maximum value of an attribute
among all results. This can be done much faster by the database than retrieving all results and
doing it in Python. Let's get the maximum energy::

    qb = QueryBuilder()
    qb.append(
            JobCalculation,
            filters={'ctime':{'>': now - timedelta(days=3)}}
        )
    qb.append(
            ParameterData,
            project={
                'attributes.energy':{'cast':'f', 'func':'max'},
            }
         )
    print list(qb.all())

The above query returns one row, the one with the maximum energy.
Other functions implemented are:

*   *min*: get the row with the minimum value
*   *count*: return the number of rows

To find out how many calculations resulted in energies above -5.0::

    qb = QueryBuilder()
    qb.append(
            JobCalculation,
            filters={'ctime':{'>': now - timedelta(days=3)}}
            project={'id':{'func':'count'}}
        )
    qb.append(
            ParameterData,
            filters={
                'attributes.energy':{'>':-5.0},
            }
         )


All right, we said before there are two possibilities to tell the QueryBuilder what to do.
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

    Each node has to have a unique label.
    If not given, the label is chosen to be equal to the name of the class.
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

    There also has to be some information on the edges,
    in order to join correctly.
    There are several redundant ways this can be done:

    *   You can specify that this node is an input or output of another node
        preceding the current one in the list.
        That other node can be specified by an
        integer or the class or type.
        The following examples are all valid joining instructions,
        assuming there is a structure defined at index 2
        of the path with label "struc1"::

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

    With the key 'filters', we instruct the querytool to
    build filters and attach them to the query.
    Filters are passed as dictionaries.
    In each key-value pair, the key is the column-name
    (as a string) to filter on.
    The value is another dictionary,
    where the operator is a key and the value is the
    value to check against.

    .. note:: This follows (in some way) the MongoDB-syntax.

    But what if the user wants to filter
    by key-value pairs defined inside the structure?
    In that case,
    simply specify the path with the dot (`.`) being a separator.
    If you want to get to the volume of the structure,
    stored in the attributes, you can specify::

        queryhelp = {
            'path':[{'cls':StructureData}],  # or 'path':[StructureData]
            'filters':{
                'attributes.volume': {'<':6.0}
            }
        }

    The above queryhelp would build a query
    that returns all structures with a volume below 6.0.

    .. note::   
        A big advantage of SQLAlchemy is that it support
        the storage of jsons.
        It is convenient to dump the structure-data
        into a json and store that as a column.
        The querytool needs to be told how to query the json.

Let's get to a really complex use-case,
where we need to reconstruct a workflow:

#.  The MD-simulation with the parameters and structure used as input
#.  The trajectory that was returned as an output
#.  We are only interested in calculations with a convergence threshold
    smaller than 1e-5 and cutoff larger 60 (stored in the parameters)
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
                'cls':PwCalculation,
                'label':'md'
            },
            {
                'cls':Trajectory
            },
            {
                'cls':StructureData,
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
            ParameterData:{'attributes.IONS.tempw':{'cast':'f'}},
            'md':['id', 'time'],
            Trajectory:[
                'id',
                {'attributes.length':{'cast':'i'}}
            ],
            StructureData:'*',
            'struc2':['*'] # equivalent, the two!
        },
        'filters':{
            ParameterData:{
                'attributes.SYSTEM.econv':{'<':1e-5},
                'attributes.SYSTEM.ecut':{'>':60},
            },
            'md':{
                'state':{'in':['PARSING', 'FINISHED']},
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
                },
                'attributes.kinds':{
                    'shorter':3,
                    'has_key':'N',
                }
            }
        }
    }

