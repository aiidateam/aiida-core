.. _QueryBuilderAppend:

The appender method
===================

Selecting entities
++++++++++++++++++

Let's suppose you want to query for calculation nodes in your database::

    from aiida.orm.querybuilder import QueryBuilder
    qb = QueryBuilder()       # Instantiating instance. One instance -> one query
    qb.append(CalcJobNode)    # Setting first vertex of path

.. note ::
    Calculations are more tricky than Data, since they have both a run-time ``Process`` that steers them
    and a ``Node`` that stores their metadata in the database.
    The QueryBuilder allows you to pass either the ``Node`` class (e.g. ``CalcJobNode``)
    or the ``Process`` class (e.g. ``CalcJob``, ``PwCalculation``),
    which will automatically apply the correct filters for the type of calculation.

If you are interested in instances of different classes, you can also pass a tuple, list or set of classes.
However, they have to be of the same ORM-type (e.g. all have to be subclasses of Node)::

    from aiida.orm.querybuilder import QueryBuilder
    qb = QueryBuilder()       # Instantiating instance. One instance -> one query
    qb.append([CalcJobNode, WorkChainNode]) # Setting first vertice of path, either WorkChainNode or Job.


Retrieving results
++++++++++++++++++

Let's suppose that's what we want to query for (all job calculations in the
database). The question is how to get the results from the query::

    from aiida.orm.querybuilder import QueryBuilder
    qb = QueryBuilder()                 # Instantiating instance
    qb.append(CalcJobNode)           # Setting first vertice of path

    first_row = qb.first()              # Returns a list (!)
                                        # of the results of the first row

    all_results_d = qb.dict()           # Returns all results as
                                        # a list of dictionaries

    all_results_l = qb.all()            # Returns a list of lists


    # Also you can use generators:
    all_res_d_gen = qb.iterdict()       # Return a generator of dictionaries
                                        # of all results
    all_res_l_gen = qb.iterall()        # Returns a generator of lists


.. note ::
    Generators are useful if you have to retrieve a very large (>10000) number of results.
    This will retrieve the data in batches, and you can start working with the data before the
    query has completely finished.
    Be aware that if using generators, you should never commit (store) anything while
    iterating. The query is still going on, and might be compromised by new data in the database.


Filtering
+++++++++


Since we now know how to set an entity, we can start to filter by properties of that entity.
Suppose we do not want to all CalcJobNodes, but only the ones in state
'FINISHED'::

    qb = QueryBuilder()                 # An empty QueryBuilder instances
    qb.append(
        CalcJobNode,                 # I am appending a CalcJobNode
        filters={                       # Specifying the filters:
            'attributes.process_state':{'==':'finished'},  # the calculation has to have finished
        },
    )

How, can we have multiple filters?
Suppose you are interested in all calculations in your database that are in
state 'FINISHED' and were created in the last *n* days::

    from datetime import timedelta
    from aiida.common import timezone
    now = timezone.now()
    time_n_days_ago = now - timedelta(days=n)

    qb = QueryBuilder()                 # An empty QueryBuilder instances
    qb.append(
        CalcJobNode,                 # I am appending a CalcJobNode
        filters={                       # Specifying the filters:
            'attributes.process_state':{'==':'finished'},  # the calculation has to have finished AND
            'ctime':{'>':time_n_days_ago}     # created in the last n days
        },
    )
    result = qb.dict()                  # all results as a list of dictionaries


Let's go through the above example.
We have instantiated QueryBuilder instance.
We appended to its path a CalcJobNode (a remote calculation),
and specified that we are only interested in  calculations
that have finished **and** that were created in the last *n* days.

What if we want calculations that have finished **or** were created in the last
*n* days::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'or':[
                {'attributes.process_state':{'==':'finished'}},
                {'ctime':{'>': now - timedelta(days=n)}}
            ]
        },
    )
    res = qb.dict()

If we had written *and* instead of *or*, we would have created the exact same
query as in the first query, because *and* is the default behavior if
you attach several filters.
What if you want calculation in state 'FINISHED' or 'EXCEPTED'?
This will be the next example::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'attributes.process_state':{'in':['finished', 'excepted']}
        },
    )
    res = qb.all()

In order to negate a filter, that is to apply the not operator, precede the filter
keyword with an exclamation mark.
So, to ask for all calculations that are not in 'FINISHED' or 'EXCEPTED'::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'attributes.process_state':{'!in':['finished', 'excepted']}
        },
    )
    res = qb.all()

.. note ::
    The above rule applies strictly! You check a non-equality with !==, since this is
    the equality operator (==) with a negation prepended.

This is a list of all implemented operators:

+------------+------------+-------------------------------------+----------------------------------+
|**Operator**|**Datatype**|  **Example**                        | Explanation                      |
+============+============+=====================================+==================================+
|   ==       |      All   | 'id':{'==':123}                     | Checks equality                  |
+------------+------------+-------------------------------------+----------------------------------+
|   in       |      All   | 'name':{'in':['foo', 'bar']}        | equal to any element             |
+------------+------------+-------------------------------------+----------------------------------+
| >,<,<=,>=  | floats,    | 'ctime':{'<':datetime(2016, 03, 03)}| lower/greater (equal)            |
|            | integers,  |                                     |                                  |
|            | dates      |                                     |                                  |
+------------+------------+-------------------------------------+----------------------------------+
| like       | Strings    | 'name':{'like':'lovely_calc%'}      | substring                        |
|            |            |                                     | (% and _ are wildcards. To use % |
|            |            |                                     | and _ as part of the string      |
|            |            |                                     | prepend it with \\)              |
+------------+------------+-------------------------------------+----------------------------------+
| ilike      | Strings    | 'name':{'ilike':'loVely_Calc%'}     | case insensitive 'like'          |
+------------+------------+-------------------------------------+----------------------------------+
| or         | list of    | 'id':{'or':[{'<':12}, {'==':199}]}  |                                  |
|            | expressions|                                     |                                  |
+------------+------------+-------------------------------------+----------------------------------+
| and        | list of    | 'id':{'and':[{'<':12}, {'>':1 }]}   |                                  |
|            | expressions|                                     |                                  |
+------------+------------+-------------------------------------+----------------------------------+

There are also some advanced operators:

.. table::
    :widths: auto

    +------------+-------------+------------------------------------------+----------------------------------+
    |**Operator**|**Datatype** |  **Example**                             | Explanation                      |
    +============+=============+==========================================+==================================+
    | has_key    | dicts       | | 'attributes.mykey':{'has_key': 'foo'}  | Check that a dictionary          |
    |            |             | | 'extras':{'has_key': 'my_extra'}       | (typically stored in the         |
    |            |             |                                          | attributes or in the extras) has |
    |            |             |                                          | a given key. This can also be    |
    |            |             |                                          | used to check if a given         |
    |            |             |                                          | attribute or extra exists.       |
    +------------+-------------+------------------------------------------+----------------------------------+
    | of_type    |    any      | | 'attributes.mykey':{'of_type': 'bool'} | Check that an attribute or an    |
    |            |             |                                          | extra is of a given type. Valid  |
    |            |             |                                          | types are: ``object`` (meaning a |
    |            |             |                                          | dictionary), ``array`` (meaning a|
    |            |             |                                          | list), ``string``, ``number``    |
    |            |             |                                          | (both for integers and floats),  |
    |            |             |                                          | ``boolean`` or ``null``)         |
    |            |             |                                          | **(currently implemented only    |
    |            |             |                                          | in the SQLA backend)**           |
    +------------+-------------+------------------------------------------+----------------------------------+
    | of_length  |    lists    | | 'attributes.mylist': {'of_length': 4}  | Check that a list (typically     |
    |            |             |                                          | stored in the attributes or in   |
    |            |             |                                          | the extras) has a given length   |
    |            |             |                                          | **(currently implemented only    |
    |            |             |                                          | in the SQLA backend)**           |
    +------------+-------------+------------------------------------------+----------------------------------+
    | shorter    |    lists    | | 'attributes.mylist': {'shorter': 4}    | Check that a list (typically     |
    |            |             |                                          | stored in the attributes or in   |
    |            |             |                                          | the extras) has a length shorter |
    |            |             |                                          | than the specified value         |
    |            |             |                                          | **(currently implemented only    |
    |            |             |                                          | in the SQLA backend)**           |
    +------------+-------------+------------------------------------------+----------------------------------+
    | longer     |    lists    | | 'attributes.mylist': {'longer': 4}     | Check that a list (typically     |
    |            |             |                                          | stored in the attributes or in   |
    |            |             |                                          | the extras) has a length longer  |
    |            |             |                                          | than the specified value         |
    |            |             |                                          | **(currently implemented only    |
    |            |             |                                          | in the SQLA backend)**           |
    +------------+-------------+------------------------------------------+----------------------------------+
    | contains   |    lists    | | 'attributes.mykey': {'contains':       | Check that a list (typically     |
    |            |             |   ['a','b']}                             | stored in the attributes or in   |
    |            |             |                                          | the extras) contains some        |
    |            |             |                                          | specific elements or values      |
    |            |             |                                          | **(currently implemented only    |
    |            |             |                                          | in the SQLA backend)**           |
    +------------+-------------+------------------------------------------+----------------------------------+


This showed you how to 'filter' by properties of a node.
So far we can do that for a single a single node in the database.


Joining entities
++++++++++++++++

But we sometimes need to query relationships in graph-like database.
Let's join a node to its output, e.g. StructureData and CalcJobNode (as output)::

    qb = QueryBuilder()
    qb.append(StructureData, tag='structure')
    qb.append(CalcJobNode, with_incoming='structure')

In above example we are querying structures and calculations, with the predicate that the
calculation is an output of the structure (the same as saying that the structure is an input to the calculation)
In the above example, we have first appended StructureData to the path.
So that we can refer to that vertice later, we *tag* it with a unique keyword
of our choice, which can be used only once.
When we append another vertice to the path, we specify the relationship
to a previous entity by using one of the keywords in the above table
and as a value the tag of the vertice that it has a relationship with.
There are several relationships that entities in Aiida can have:

+------------------+---------------+--------------------+-------------------------------------------------+
| **Entity from**  | **Entity to** | **Relationship**   | **Explanation**                                 |
+==================+===============+====================+=================================================+
| Node             | Node          | *with_outgoing*    | One node as input of another node               |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | Node          | *with_incoming*    | One node as output of another node              |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | Node          | *with_descendants* | One node as the ancestor of another node (Path) |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | Node          | *with_ancestors*   | One node as descendant of another node (Path)   |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | Group         | *with_node*        | The group of a node                             |
+------------------+---------------+--------------------+-------------------------------------------------+
| Group            | Node          | *with_group*       | The node is a member of a group                 |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | Computer      | *with_node*        | The computer of a node                          |
+------------------+---------------+--------------------+-------------------------------------------------+
| Computer         | Node          | *with_computer*    | The node of a computer                          |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | User          | *with_node*        | The creator of a node is a user                 |
+------------------+---------------+--------------------+-------------------------------------------------+
| User             | Node          | *with_user*        | The node was created by a user                  |
+------------------+---------------+--------------------+-------------------------------------------------+
| User             | Group         | *with_user*        | The node was created by a user                  |
+------------------+---------------+--------------------+-------------------------------------------------+
| Group            | User          | *with_group*       | The node was created by a user                  |
+------------------+---------------+--------------------+-------------------------------------------------+
| Node             | Log           | *with_node*        | The log of a node                               |
+------------------+---------------+--------------------+-------------------------------------------------+
| Log              | Node          | *with_log*         | The node has a log                              |
| Node             | Comment       | *with_node*        | The comment of a node                           |
+------------------+---------------+--------------------+-------------------------------------------------+
| Comment          | Node          | *with_comment*     | The node has a comment                          |
+------------------+---------------+--------------------+-------------------------------------------------+
| User             | Comment       | *with_user*        | The comment was created by a user               |
+------------------+---------------+--------------------+-------------------------------------------------+
| Comment          | User          | *with_comment*     | The creator of a comment is a user              |
+------------------+---------------+--------------------+-------------------------------------------------+


Some more examples::

    # StructureData as an input of a job calculation
    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calc')
    qb.append(StructureData, with_outgoing='calc')

    # StructureData and Dict as inputs to a calculation
    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calc')
    qb.append(StructureData, with_outgoing='calc')
    qb.append(Dict, with_outgoing='calc')

    # Filtering the remote data instance by the computer it ran on (name)
    qb = QueryBuilder()
    qb.append(RemoteData, tag='remote')
    qb.append(Computer, with_node='remote', filters={'name':{'==':'mycomputer'}})

    # Find all descendants of a structure with a certain uuid
    qb = QueryBuilder()
    qb.append(StructureData, tag='structure', filters={'uuid':{'==':myuuid}})
    qb.append(Node, with_ancestors='structure')

The above QueryBuilder will join a structure to all its descendants via the
transitive closure table.



Defining the projections
++++++++++++++++++++++++

But what will the query return exactly?
If you try any of the examples, you will find that the instances of the last appended
vertice appear! That is the default behavior if nothing else was specified.
We usually do not want everything returned because it might lead to a big overhead.
You need to specify what you want to return using the keyword *project*.

Let's stick to the previous example::

    # Find all descendants of a structure with a certain uuid
    qb = QueryBuilder()
    qb.append(
        StructureData,
        tag='structure',
        filters={'uuid':{'==':myuuid}},
    )
    qb.append(
        Node,
        with_ancestors='structure',
        project=['node_type', 'uuid'],  # returns type (string) and uuid (string)
    )


In the above example, executing the query returns the type and the id of
all Node that are descendants of the structure::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        tag='structure',
        filters={'uuid':{'==':myuuid}},
    )
    qb.append(
        Node,
        with_ancestors='structure',
        project=['node_type', 'id'],  # returns type (string) and id (string)
        tag='descendant'
    )

    # Return the dictionaries:
    print("\n\nqb.iterdict()")
    for d in qb.iterdict():
        print('>>>', d)

    # Return the lists:
    print("\n\nqb.iterall()")
    for l in qb.iterall():
        print('>>>', l)

    # Return the first result:
    print("\n\nqb.first()")
    print('>>>', qb.first())



results in the following output::

    qb.iterdict()
    >>> {'descendant': {'node_type': 'calculation.job.quantumespresso.pw.PwCalculation.', 'id': 7716}}
    >>> {'descendant': {'node_type': 'data.remote.RemoteData.', 'id': 8510}}
    >>> {'descendant': {'node_type': 'data.folder.FolderData.', 'id': 9090}}
    >>> {'descendant': {'node_type': 'data.array.ArrayData.', 'id': 9091}}
    >>> {'descendant': {'node_type': 'data.array.trajectory.TrajectoryData.', 'id': 9092}}
    >>> {'descendant': {'node_type': 'data.dict.Dict.', 'id': 9093}}


    qb.iterall()
    >>> ['calculation.job.quantumespresso.pw.PwCalculation.', 7716]
    >>> ['data.remote.RemoteData.', 8510]
    >>> ['data.folder.FolderData.', 9090]
    >>> ['data.array.ArrayData.', 9091]
    >>> ['data.array.trajectory.TrajectoryData.', 9092]
    >>> ['data.dict.Dict.', 9093]


    qb.first()
    >>> ['calculation.job.quantumespresso.pw.PwCalculation.', 7716]

Asking only for the properties that you are interested in can result
in much faster queries. If you want the Aiida-ORM instance, add '*' to your list
of projections::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        tag='structure',
        filters={'uuid':{'==':myuuid}},
    )
    qb.append(
        Node,
        with_ancestors='structure',
        project=['*'],      # returns the Aiida ORM instance
        tag='desc'
    )

    # Return the dictionaries:
    print("\n\nqb.iterdict()")
    for d in qb.iterdict():
        print('>>>', d)

    # Return the lists:
    print("\n\nqb.iterall()")
    for l in qb.iterall():
        print('>>>', l)

    # Return the first result:
    print("\n\nqb.first()")
    print('>>>', qb.first())

Output::

    qb.iterdict()
    >>> {'desc': {'*': <PwCalculation: uuid: da720712-3ca3-490b-abf4-b0fb3174322e (pk: 7716)>}}
    >>> {'desc': {'*': <RemoteData: uuid: 13a378f8-91fa-42c7-8d7a-e469bbf02e2d (pk: 8510)>}}
    >>> {'desc': {'*': <FolderData: uuid: 91d5a5e8-6b88-4e43-9652-9efda4adb4ce (pk: 9090)>}}
    >>> {'desc': {'*': <ArrayData: uuid: 7c34c219-f400-42aa-8bf2-ee36c7c1dd40 (pk: 9091)>}}
    >>> {'desc': {'*': <TrajectoryData: uuid: 09288a5f-dba5-4558-b115-1209013b6b32 (pk: 9092)>}}
    >>> {'desc': {'*': <Dict: uuid: 371677e1-d7d4-4f2e-8a41-594aace02759 (pk: 9093)>}}


    qb.iterall()
    >>> [<PwCalculation: uuid: da720712-3ca3-490b-abf4-b0fb3174322e (pk: 7716)>]
    >>> [<RemoteData: uuid: 13a378f8-91fa-42c7-8d7a-e469bbf02e2d (pk: 8510)>]
    >>> [<FolderData: uuid: 91d5a5e8-6b88-4e43-9652-9efda4adb4ce (pk: 9090)>]
    >>> [<ArrayData: uuid: 7c34c219-f400-42aa-8bf2-ee36c7c1dd40 (pk: 9091)>]
    >>> [<TrajectoryData: uuid: 09288a5f-dba5-4558-b115-1209013b6b32 (pk: 9092)>]
    >>> [<Dict: uuid: 371677e1-d7d4-4f2e-8a41-594aace02759 (pk: 9093)>]


    qb.first()
    >>> [<PwCalculation: uuid: da720712-3ca3-490b-abf4-b0fb3174322e (pk: 7716)>]

.. note::
    Be aware that, for consistency, QueryBuilder.all / iterall always
    returns a list of lists, and first always a list, even if you project
    on one entity!


If you are not sure which keys to ask for, you can project with '**', and the QueryBuilder instance
will return all column properties::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        project=['**']
    )

Output::

    qb.limit(1).dict()
    >>> {'StructureData': {
            'user_id': 2,
            'description': '',
            'ctime': datetime.datetime(2016, 2, 3, 18, 20, 17, 88239),
            'label': '',
            'mtime': datetime.datetime(2016, 2, 3, 18, 20, 17, 116627),
            'id': 3028,
            'dbcomputer_id': None,
            'nodeversion': 1,
            'node_type': 'data.structure.StructureData.',
            'public': False,
            'uuid': '93c0db51-8a39-4a0d-b14d-5a50e40a2cc4'
        }}



Attributes and extras
+++++++++++++++++++++

You should know by now that you can define additional properties of nodes
in the *attributes* and the *extras* of a node.
There will be many cases where you will either want to filter or project on
those entities. The following example gives us a PwCalculation where the cutoff
for the wavefunctions has a value above 30.0 Ry::


    qb = QueryBuilder()
    qb.append(PwCalculation, project=['*'], tag='calc')
    qb.append(
        Dict,
        with_outgoing='calc',
        filters={'attributes.SYSTEM.ecutwfc':{'>':30.0}},
        project=[
            'attributes.SYSTEM.ecutwfc',
            'attributes.SYSTEM.ecutrho',
        ]
    )

The above examples filters by a certain attribute.
Notice how you expand into the dictionary using the dot (.).
That works the same for the extras.

.. note::
    Comparisons in the attributes (extras) are also implicitly done by type.

Filtering or projecting on lists works similar to dictionaries.
You expand into the list using the dot (.) and afterwards adding the list-index.
The example below filters KpointsData by the first index in the mesh of KpointsData=instance, and returns that same index in the list::

    qb = QueryBuilder()
    qb.append(
        DataFactory('array.kpoints'),
        project=['attributes.mesh.0'],
        filters={'attributes.mesh.0':{'>':2}}
    )

Let's do a last example. You are familiar with the Quantum Espresso PWscf tutorial?
Great, because this will be our use case here. (If not, you can find it on the
`documentation of the aiida-quantumespresso package <http://aiida-quantumespresso.readthedocs.io/en/latest/user_guide/get_started/examples/pw_tutorial.html>`_.
We will query for calculations that were done on a certain structure (*mystructure*),
that fulfill certain requirements, such as a cutoff above 30.0.
In our case, we have a structure (an instance of StructureData) and an instance
of Dict that are both inputs to a PwCalculation.
You need to tell the QueryBuilder that::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        filters={'uuid':{'==':mystructure.uuid}},
        tag='strucure'
    )
    qb.append(
        PwCalculation,
        with_incoming='strucure',
        project=['*'],
        tag='calc'
    )
    qb.append(
        Dict,
        filters={'attributes.SYSTEM.ecutwfc':{'>':30.0}},
        with_outgoing='calc',
        tag='params'
    )



Cheats
++++++


A few cheats to save some typing:

*   The default edge specification, if no keyword is provided, is always
    *with_incoming* the previous vertice.
*   Equality filters ('==') can be shortened, as will be shown below.
*   Tags are not necessary, you can simply use the class as a label.
    This works as long as the same Aiida-class is not used again

A shorter version of the previous example::

    qb = QueryBuilder()
    qb.append(
        StructureData,
        filters={'uuid':mystructure.uuid},
    )
    qb.append(
        PwCalculation,
        project='*',
    )
    qb.append(
        Dict,
        filters={'attributes.SYSTEM.ecutwfc':{'>':30.0}},
        with_outgoing=PwCalculation
    )


Advanced usage
++++++++++++++

Let's proceed to some more advanced stuff. If you've understood everything so far
you're in good shape to query the database, so you can skip the rest if you want.

.. ~
.. ~ Let's get the id  ``pk'' and the ORM-instances of all structures in the database::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(StructureData, project=['id', '*'])
.. ~     print list(qb.all())
.. ~
.. ~ This will return a list of result tuples, each one containing the pk and the corresponding
.. ~ StructureData instance.
.. ~ The following reverses the order inside the sublists::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(StructureData, project=['*', 'id'])
.. ~     print list(qb.all())
.. ~
.. ~ What if you want to project a certain attributes.
.. ~ That is trickier! You again need to tell the QueryBuilder the type.
.. ~ Assuming you want to get the energies returned by all PwCalculation done in the last 3 days::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             project=[{'attributes.energy':{'cast':'f'}}],
.. ~         )
.. ~     print list(qb.all())
.. ~
.. ~ You need to specify the type of the quantity, in that case a float:
.. ~
.. ~ *   'f' for floats
.. ~ *   'i' for integers
.. ~ *   't' for texts (strings, characters)
.. ~ *   'b' for booelans
.. ~ *   'd' for dates
.. ~
.. ~ So again, be consisted when storing values in the database.
.. ~ To sum up, a projection is technically a list of dictionaries.
.. ~ If you don't have to cast the type, because the value is not stored as an attribute (or extra),
.. ~ then the string is sufficient.
.. ~ If you don't care about the order (ensured by passing a list), you can also put values in
.. ~ one dictionary. Let's also get the units  of the energy::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             project={
.. ~                 'attributes.energy':{'cast':'f'},
.. ~                 'attributes.energy_units':{'cast':'t'},
.. ~             }
.. ~          )
.. ~     print list(qb.all())
.. ~
.. ~
.. ~ You can do much more with projections! You might be interested in the maximum value of an attribute
.. ~ among all results. This can be done much faster by the database than retrieving all results and
.. ~ doing it in Python. Let's get the maximum energy::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             project={
.. ~                 'attributes.energy':{'cast':'f', 'func':'max'},
.. ~             }
.. ~          )
.. ~     print list(qb.all())
.. ~
.. ~ The above query returns one row, the one with the maximum energy.
.. ~ Other functions implemented are:
.. ~
.. ~ *   *min*: get the row with the minimum value
.. ~ *   *count*: return the number of rows
.. ~
.. ~ To find out how many calculations resulted in energies above -5.0::
.. ~
.. ~     qb = QueryBuilder()
.. ~     qb.append(
.. ~             CalcJobNode,
.. ~             filters={'ctime':{'>': now - timedelta(days=3)}},
.. ~             project={'id':{'func':'count'}}
.. ~         )
.. ~     qb.append(
.. ~             Dict,
.. ~             filters={
.. ~                 'attributes.energy':{'>':-5.0},
.. ~             }
.. ~          )



Working with edges
++++++++++++++++++

Another feature that had to be added are projections, filters and labels on
the edges of the graphs, that is to say, links or paths between nodes.
It works the same way, just that the keyword is preceded by '*edge*'.
Let's take the above example, but put a filter on the label of the link and project the link label::

    qb = QueryBuilder()
    qb.append(
            CalcJobNode,
            project='id'
        )
    qb.append(
            Dict,
            filters={'attributes.energy':{'>':-5.0}},
            edge_filters={'label':{'like':'output_%'}},
            edge_project='label'
         )



Ordering results
++++++++++++++++

You can also order by properties of the node.
Assuming you want to order the above example by the time of the calculations::

    qb = QueryBuilder()
    qb.append(
            CalcJobNode,
            project=['*']
        )
    qb.append(
            Dict,
            filters={'attributes.energy':{'>':-5.0}},
         )

    qb.order_by({CalcJobNode:{'ctime':'asc'}}) # 'asc' or 'desc' (ascending/descending)

The ordering can furthermore be done in a prioritized manner for several node properties.
E.g., taking the example above and further sorting the node's by their modification time in descending order would look like this::

    qb = QueryBuilder()
    qb.append(
            CalcJobNode,
            project=['*']
        )
    qb.append(
            Dict,
            filters={'attributes.energy':{'>':-5.0}},
         )

    qb.order_by({CalcJobNode: [{'ctime': 'asc'}, {'mtime': 'desc'}]})

Here the nodes will *first* be sorted by their creation time in ascending order, and then by their modification time in descending order.

Finally, attributes and extras can be used for sorting.
However, the QueryBuilder cannot infer their value types, so you will have to cast the type::

    qb = QueryBuilder()
    qb.append(
            CalcJobNode,
            project=['*']
        )
    qb.append(
            Dict,
            filters={'attributes.energy':{'>':-5.0}},
         )

    qb.order_by({CalcJobNode: [
        {'ctime': 'asc'},
        {'attributes.energy': {'order': 'desc', 'cast': 'f'}}  # 'f' is an alias for type float
    }])

Here follows a list of the available cast types and their aliases:

+-------------------+-----------+---------------------+
| **Python type**   | **Alias** | **SQLAlchemy type** |
+===================+===========+=====================+
| float             | f         | Float               |
+-------------------+-----------+---------------------+
| int               | i         | Integer             |
+-------------------+-----------+---------------------+
| bool              | b         | Boolean             |
+-------------------+-----------+---------------------+
| str               | t         | String              |
+-------------------+-----------+---------------------+
| dict              | j         | JSONB               |
+-------------------+-----------+---------------------+
| datetime.datetime | d         | DateTime            |
+-------------------+-----------+---------------------+



Limiting the number of results
++++++++++++++++++++++++++++++

You can also limit the number of rows returned with the method *limit*::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        project=['*']
    )
    qb.append(
        Dict,
        filters={'attributes.energy':{'>':-5.0}},
     )

    # order by time descending
    qb.order_by({CalcJobNode:{'ctime':'desc'}})

    # Limit to results to the first 10 results:
    qb.limit(10)

The above query returns the latest 10 calculation that produced a final energy above -5.0.
