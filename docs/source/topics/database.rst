.. _topics:database:

********
Database
********

.. todo::

    .. _#4019: https://github.com/aiidateam/aiida-core/issues/4019

.. _topics:database:advancedquery:

=================
Advanced querying
=================

The basics on using the :class:`~aiida.orm.querybuilder.QueryBuilder` to find the data you are interested in is explained in the :ref:`finding and querying how-to<how-to:query>`.
This section explains some more advanced methods for querying your database and the :ref:`QueryBuilder dictionary<topics:database:advancedquery>`.

.. _topics:database:advancedquery:edges:

Working with edges
------------------

Filters and projections can be applied to both the vertices of the query path and the edges that connect them.
Applying a filter or projection to an edge works the same way as for vertices, but the relevant keyword is now preceded by ``edge_``.
Using the ``ArithmeticAddCalculation`` calculation job as an example, let's say we want to query for the first input of the addition, i.e. the ``Int`` nodes which have been provided as the input with label ``x``:

.. code-block:: python

    from aiida.orm import QueryBuilder
    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_outgoing='calcjob', edge_filters={'label': 'x'})

By using the ``edge_filters`` keyword argument, we can query for only the inputs that have the label ``x``.
Note that any operator that can be used to filter vertices can also be applied to edges.
Say we want to find all input ``Int`` nodes that are **not** connected to the ``CalcJobNode``'s via an edge with label ``x``:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_outgoing='calcjob', edge_filters={'label': {'!==': 'x'}})

Here, the equality operator ``==`` is negated by prepending an exclamation mark ``!``.
See the :ref:`reference table below<topics:database:advancedquery:tables:operators>` for a table with all operators.
Similar to filters, we can *project* information of the edge using the ``edge_project`` keyword argument:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_outgoing='calcjob', edge_project='label')

In the example above, we are querying for the edge labels of the incoming ``Int`` nodes of all ``CalcJobNode``'s.

.. _topics:database:advancedquery:ordering:

Ordering and limiting results
-----------------------------

You can order the results of your query by the properties of the entity.
Say you want to return the list of ``Int`` outputs from all ``CalcJobNode``'s, sorted by the time they were created in *descending* order, i.e. the most recent first:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')
    qb.order_by({Int: {'ctime': 'desc'}})

This can also be used to order your results based on values in a (nested) dictionary, such as the ``attributes`` column.
However, as the :class:`~aiida.orm.querybuilder.QueryBuilder` cannot infer the type of the value in this case, you have to *cast* the type:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')
    qb.order_by({Int: {'attributes.value': {'order': 'asc', 'cast': 'i'}}})

The query above will return all ``Int`` nodes that are output of all ``CalcJobNode``'s, in *ascending* order of their value, i.e. from small to big.
Note that in this case you have to specify the order operation with a dictionary, where the ``order`` key details how you want to order the query results and the ``cast`` key informs the ``QueryBuilder`` of the attribute type.
A list of the available cast types and their aliases can be found in the table below:

.. _topics:database:advancedquery:tables:casttypes:

+-------------------+-----------+---------------------+
| **Python type**   | **Alias** | **SQLAlchemy type** |
+===================+===========+=====================+
| int               | i         | Integer             |
+-------------------+-----------+---------------------+
| float             | f         | Float               |
+-------------------+-----------+---------------------+
| bool              | b         | Boolean             |
+-------------------+-----------+---------------------+
| str               | t         | String              |
+-------------------+-----------+---------------------+
| dict              | j         | JSONB               |
+-------------------+-----------+---------------------+
| datetime.datetime | d         | DateTime            |
+-------------------+-----------+---------------------+

You can also order using multiple properties by providing a list of dictionaries that each specify one sorting operation:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')
    qb.order_by({Int: [{'attributes.value': {'order': 'asc', 'cast': 'f'}}, {'ctime': 'desc'}]})

Here the ``Int`` nodes will first be sorted by their value in ascending order.
Nodes for which the value is equal are subsequently sorted by their modification time in descending order.

Finally, you can also limit the number of query results returned with the ``limit()`` method.
Suppose you only want the first three results from our query:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode)
    qb.limit(3)

This can be easily combined with the ``order_by`` method in order to get the last three ``CalcJobNode``'s that were created in the database:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode)
    qb.limit(3)
    qb.order_by({CalcJobNode: {'ctime': 'desc'}})

.. _topics:database:advancedquery:tables:

Reference tables
----------------

.. _topics:database:advancedquery:tables:operators:

List of all operators:

+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
|**Operator**  |**Datatype** |  **Example**                                          | Explanation                                                                  |
+==============+=============+=======================================================+==============================================================================+
|   ``==``     |      all    | ``'id': {'==': 123}``                                 | Filter for equality                                                          |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
|   ``in``     |      all    | ``'name': {'in': ['foo', 'bar']}``                    | Filter for values that are in the given list.                                |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``>,<,<=,>=``| float,      | ``'ctime': {'<': datetime(2016, 03, 03)}``            | Filter for values that are greater or smaller than a certain value           |
|              | integer,    |                                                       |                                                                              |
|              | date        |                                                       |                                                                              |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``like``     | string      | ``'name': {'like': 'label%'}``                        | Filter for matching substrings where ``%`` and ``_`` are wildcards.          |
|              |             |                                                       | To match a literal ``%`` or ``_`` escape it by prefixing it with ``\\``.     |
|              |             |                                                       |                                                                              |
|              |             |                                                       |                                                                              |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``ilike``    | string      | ``'name': {'ilike': 'lAbEl%'}``                       | Case insensitive version of ``like``.                                        |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``or``       | list of     | ``'id': {'or': [{'<': 12}, {'==': 199}]}``            | A list of expressions where at least one should be matched.                  |
|              | expressions |                                                       |                                                                              |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``and``      | list of     | ``'id': {'and': [{'<': 12}, {'>': 1}]}``              | A list of expressions where all should be matched.                           |
|              | expressions |                                                       |                                                                              |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``has_key``  | dict        | ``'attributes': {'has_key': 'some_key'}``             | Filter for dictionaries that contain a certain key.                          |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``of_type``  |    any      | ``'attributes.some_key': {'of_type': 'bool'}``        | Filter for values of a certain type.                                         |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``of_length``|    lists    | ``'attributes.some_list': {'of_length': 4}``          | Filter for lists of a certain length.                                        |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``shorter``  |    lists    | ``'attributes.some_list': {'shorter': 4}``            | Filter for lists that are shorter than a certain length.                     |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``longer``   |    lists    | ``'attributes.some_list': {'longer': 4}``             | Filter for lists that are longer than a certain length.                      |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+
| ``contains`` |    lists    | ``'attributes.some_key': {'contains': ['a', 'b']}``   | Filter for lists that should contain certain values.                         |
+--------------+-------------+-------------------------------------------------------+------------------------------------------------------------------------------+

As mentioned in the :ref:`section about operatior negations<how-to:query:filters:operator-negations>` all operators can be turned into their associated negation (``NOT`` operator) by adding a ``!`` in front of the operator.

.. note::
    The form of (negation) operators in the rendered SQL may differ from the ones specified in the ``QueryBuilder`` instance.
    For example, the ``!==`` operator of the ``QueryBuilder`` will be rendered to ``!=`` in SQL.


.. _topics:database:advancedquery:tables:relationships:

List of all relationships:

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

.. _topics:database:advancedquery:queryhelp:
.. _topics:database:advancedquery:querydict:

Converting the QueryBuilder to/from a dictionary
------------------------------------------------

.. important::

    In aiida-core version 1, this dictionary was accessed with ``QueryBuilder.queryhelp``, which is now deprecated.

The :class:`~aiida.orm.querybuilder.QueryBuilder` class can be converted to a dictionary and also loaded from a dictionary, for easy serialisation and storage.
Once you have built your query using the appender method explained in the :ref:`finding and querying for data how-to<how-to:query>` and the advanced sections above, you can easily store your query by saving the ``QueryBuilder.as_dict()`` dictionary as a JSON file for later use:

.. code-block:: python

    import json
    from aiida.orm import QueryBuilder

    qb = QueryBuilder()
    qb.append(CalcJobNode)

    with open("querydict.json", "w") as file:
        file.write(json.dumps(qb.as_dict(), indent=4))

To use this dictionary to instantiate the :class:`~aiida.orm.querybuilder.QueryBuilder`, you can use the ``from_dict`` class method:

.. code-block:: python

    with open("querydict.json", "r") as file:
        query_dict = json.load(file)

    qb = QueryBuilder.from_dict(query_dict)

Alternatively, you can also use a dictionary to set up your query by specifying the path, filters and projections and constructing the dictionary by hand.
To do this, you have to specify:

*   the ``path``:
    Here, the user specifies the path along which to join tables as a list of dictionaries, where each list item identifies a vertex in your path.
    You define the vertex class with the ``cls`` key::

        query_dict = {
            'path':[
                {'cls': Data}
            ]
        }

    Each entity in the query has to have a unique tag.
    If the tag is not provided, it is set to the name of the class.
    However, this will not work if you choose the same class twice in the query.
    In this case you have to provide the tag using the ``tag`` key::

        query_dict = {
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

    You also have to detail some information on the vertex edges, in order to connect them correctly.
    There are several redundant ways this can be done:

    *   You can specify that this node is an input or output of another node preceding the current one in the list.
        That other node can be specified by an integer or the class or type.
        The following examples are all valid joining instructions, assuming there is a structure defined at index 2 of the path with tag "struc1"::

            edge_specification = query_dict['path'][3]
            edge_specification['with_incoming'] = 2
            edge_specification['with_incoming'] = StructureData
            edge_specification['with_incoming'] = 'struc1'
            edge_specification['with_outgoing']  = 2
            edge_specification['with_outgoing']  = StructureData
            edge_specification['with_outgoing']  = 'struc1'

    *   ``query_dict['path'][<i>]['direction'] = integer``

        If any of the above specs ("with_outgoing", "with_incoming") were not specified, the key "direction" is looked for.
        Directions are defined as distances in the tree.
        1 is defined as one step down the tree along a link.
        This means that 1 joins the node specified in this dictionary to the node specified on list-item before **as an output**.
        Direction defaults to 1, which is why, if nothing is specified, this node is joined to the previous one as an output by default.
        A negative number reverse the direction of the link.
        The absolute value of the direction defines the table to join to with respect to your own position in the list.
        An absolute value of 1 joins one table above, a value of 2 to the table defined 2 indices above.
        The two following dictionaries yield the same query::

            from aiida.orm import TrajectoryData
            from aiida_quantumespresso.calculations.pw import PwCalculation
            from aiida.orm import Dict
            query_dict_1 = {
                'path': [
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

            query_dict_2 = {
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

            query_dict_3 = {
                'path':[
                    Dict,
                    PwCalculation,
                    TrajectoryData,
                ]
            }

*   what to ``project``: Determining which columns the query will return::

        query_dict = {
            'path':[PwCalculation],
            'project':{
                PwCalculation:['user_id', 'id'],
            }
        }

    If you are using JSONB columns, you can also project a value stored inside the json::

        query_dict = {
            'path':[
                PwCalculation,
                StructureData,
            ],
            'project':{
                PwCalculation:['state', 'id'],
            }
        }

    Returns the state and the id of all instances of ``PwCalculation`` where a structures is linked as output of a relax-calculation.
    The strings that you pass have to be name of the columns.
    If you pass an asterisk ('*'), the query will return the instance of the AiidaClass.

*   the ``filters``:
    Filters enable you to further specify the query.
    This is an example for a query for structures that were added after a certain time (say last 4 days) and have an id larger than 50::

        from aiida.common import timezone
        from datetime import timedelta

        query_dict = {
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

If you want to include filters and projections on links between nodes, you will have to add these to filters and projections in the query dictionary.
Let's take an example from before and add a few filters on the link::

    query_dict = {
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

Notice that the tag for the link, by default, is the tag of the two connecting nodes delimited by two dashes '--' and the order DOES matter.

Alternatively, you can choose the tag for the edge in the path when defining the entity to join using ``edge_tag``::

    query_dict = {
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

Limits and offset can be set directly like this::

    query_dict = {
        'path':[Node],
        'limit':10,
        'offset':20
    }

That ``query_dict`` would tell the QueryBuilder to return 10 rows after the first 20 have been skipped.
