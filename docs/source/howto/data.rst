.. _how-to:data:

*********************
How to work with data
*********************


.. _how-to:data:import:

Importing data
==============

AiiDA allows users to export data from their database into an export archive file, which can be imported in any other AiiDA database.
If you have an AiiDA export archive that you would like to import, you can use the ``verdi import`` command (see :ref:`the reference section<reference:command-line:verdi-import>` for details).

.. note:: More detailed information on exporting and importing data from AiiDA databases can be found in :ref:`"How to share data"<how-to:data:share>`.

If, instead, you have existing data that are not yet part of an AiiDA export archive, such as files, folders, tabular data, arrays or any other kind of data, this how-to guide will show you how to import them into AiiDA.

To store any piece of data in AiiDA, it needs to be wrapped in a :py:class:`~aiida.orm.nodes.data.Data` node, such that it can be represented in the :ref:`provenance graph <topics:provenance>`.
There are different varieties, or subclasses, of this ``Data`` class that are suited for different types of data.
AiiDA ships with a number of built-in data types.
You can list these using the :ref:`verdi plugin<reference:command-line:verdi-plugin>` command.
Executing ``verdi plugin list aiida.data`` should display something like::

    Registered entry points for aiida.data:
    * array
    * bool
    * code
    * dict
    * float
    * folder
    * list
    * singlefile

    Info: Pass the entry point as an argument to display detailed information

As the output suggests, you can get more information about each type by appending the name to the command, for example, ``verdi plugin list aiida.data singlefile``::

    Description:

    The ``singlefile`` data type is designed to store a single file in its entirety.
    A ``singlefile`` node can be created from an existing file on the local filesystem in two ways.
    By passing the absolute path of the file:

        singlefile = SinglefileData(file='/absolute/path/to/file.txt')

    or by passing a filelike object:

        with open('/absolute/path/to/file.txt', 'rb') as handle:
            singlefile = SinglefileData(file=handle)

    The filename of the resulting file in the database will be based on the filename passed in the ``file`` argument.
    This default can be overridden by passing an explicit name for the ``filename`` argument to the constructor.

As you can see, the ``singlefile`` type corresponds to the :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData` class and is designed to wrap a single file that is stored on your local filesystem.
If you have such a file that you would like to store in AiiDA, you can use the ``verdi shell`` to create it:

.. code:: python

    SinglefileData = DataFactory('singlefile')
    singlefile = SinglefileData(file='/absolute/path/to/file.txt')
    singlefile.store()

The first step is to load the class that corresponds to the data type, which you do by passing the name (listed by ``verdi plugin list aiida.data``) to the :py:class:`~aiida.plugins.factories.DataFactory`.
Then we just construct an instance of that class, passing the file of interest as an argument.

.. note:: The exact manner of constructing an instance of any particular data type is type dependent.
    Use the ``verdi plugin list aiida.data <ENTRY_POINT>`` command to get more information for any specific type.

Note that after construction, you will get an *unstored* node.
This means that at this point your data is not yet stored in the database and you can first inspect it and optionally modify it.
If you are happy with the results, you can store the new data permanently by calling the :py:meth:`~aiida.orm.nodes.node.Node.store` method.
Every node is assigned a Universal Unique Identifer (UUID) upon creation and once stored it is also assigned a primary key (PK), which can be retrieved through the ``node.uuid`` and ``node.pk`` properties, respectively.
You can use these identifiers to reference and or retrieve a node.
Ways to find and retrieve data that have previously been imported are described in section :ref:`"How to find data"<how-to:data:find>`.

If none of the currently available data types, as listed by ``verdi plugin list``, seem to fit your needs, you can also create your own custom type.
For details refer to the next section :ref:`"How to add support for custom data types"<how-to:data:plugin>`.


.. _how-to:data:plugin:

Adding support for custom data types
====================================

The nodes in the :ref:`provenance graph<topics:provenance>` that are the inputs and outputs of processes are referred to as `data` and are represented by :class:`~aiida.orm.nodes.data.data.Data` nodes.
Since data can come in all shapes and forms, the :class:`~aiida.orm.nodes.data.data.Data` class can be sub classed.
AiiDA ships with some basic data types such as the :class:`~aiida.orm.nodes.data.int.Int` which represents a simple integer and the :class:`~aiida.orm.nodes.data.dict.Dict`, representing a dictionary of key-value pairs.
There are also more complex data types such as the :class:`~aiida.orm.nodes.data.array.array.ArrayData` which can store multidimensional arrays of numbers.
These basic data types serve most needs for the majority of applications, but more specific solutions may be useful or even necessary.
In the next sections, we will explain :ref:`how a new data type can be created<how-to:data:plugin:create>` and what :ref:`guidelines<how-to:data:plugin:design-guidelines>` should ideally be observed during the design process.


.. _how-to:data:plugin:create:

Creating a data plugin
----------------------

Creating a new data type is as simple as creating a new sub class of the base :class:`~aiida.orm.nodes.data.data.Data` class.

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

At this point, our new data type does nothing special.
Typically, one creates a new data type to represent a specific type of data.
For the purposes of this example, let's assume that the goal of our ``NewData`` type is to store a single numerical value.
To allow one to construct a new ``NewData`` data node with the desired ``value``, for example:

.. code:: python

    node = NewData(value=5)

we need to allow passing that value to the constructor of the node class.
Therefore, we have to override the constructor :meth:`~aiida.orm.nodes.node.Node.__init__`:

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

        def __init__(self, **kwargs)
            value = kwargs.pop('value')
            super().__init__(**kwargs)
            self.set_attribute('value', value)

.. warning::

    For the class to function properly, the signature of the constructor **cannot be changed** and the constructor of the parent class **has to be called**.

Before calling the construtor of the base class, we have to remove the ``value`` keyword from the keyword arguments ``kwargs``, because the base class will not expect it and will raise an exception if left in the keyword arguments.
The final step is to actually *store* the value that is passed by the caller of the constructor.
A new node has two locations to permanently store any of its properties:

    * the database
    * the file repository

The section on :ref:`design guidelines<how-to:data:plugin:design-guidelines>` will go into more detail what the advantages and disadvantages of each option are and when to use which.
For now, since we are storing only a single value, the easiest and best option is to use the database.
Each node has *attributes* that can store any key-value pair, as long as the value is JSON serializable.
By adding the value to the node's attributes, they will be queryable in the database once an instance of the ``NewData`` node is stored.

.. code:: python

    node = NewData(value=5)   # Creating new node instance in memory
    node.set_attribute('value', 6)  # While in memory, node attributes can be changed
    node.store()  # Storing node instance in the database

After storing the node instance in the database, its attributes are frozen, and ``node.set_attribute('value', 7)`` will fail.
By storing the ``value`` in the attributes of the node instance, we ensure that that ``value`` can be retrieved even when the node is reloaded at a later point in time.

Besides making sure that the content of a data node is stored in the database or file repository, the data type class can also provide useful methods for users to retrieve that data.
For example, with the current state of the ``NewData`` class, in order to retrieve the ``value`` of a stored ``NewData`` node, one needs to do:

.. code:: python

    node = load_node(<IDENTIFIER>)
    node.get_attribute('value')

In other words, the user of the ``NewData`` class needs to know that the ``value`` is stored as an attribute with the name 'value'.
This is not easy to remember and therefore not very user-friendly.
Since the ``NewData`` type is a class, we can give it useful methods.
Let's introduce one that will return the value that was stored for it:

.. code:: python

    from aiida.orm import Data

    class NewData(Data)
        """A new data type that wraps a single value."""

        @property
        def value(self):
            """Return the value stored for this instance."""
            return self.get_attribute('value')

The addition of the instance property ``value`` makes retrieving the value of a ``NewData`` node a lot easier:

.. code:: python

    node = load_node(<IDENTIFIER)
    value = node.value

As said before, in addition to their attributes, data types can also store their properties in the file repository.
Here is an example for a custom data type that needs to wrap a single text file:

.. code:: python

    import os
    from aiida.orm import Data


    class TextFileData(Data):
        """Data class that can be used to wrap a single text file by storing it in its file repository."""

        def __init__(self, filepath, **kwargs):
            """Construct a new instance and set the contents to that of the file.

            :param file: an absolute filepath of the file to wrap
            """
            super().__init__(**kwargs)

            filename = os.path.basename(filepath)  # Get the filename from the absolute path
            self.put_object_from_file(filepath, filename)  # Store the file in the repository under the given filename
            self.set_attribute('filename', filename)  # Store in the attributes what the filename is

        def get_content(self):
            """Return the content of the single file stored for this data node.

            :return: the content of the file as a string
            """
            filename = self.get_attribute('filename')
            return self.get_object_content(filename)

To create a new instance of this data type and get its content:

.. code-block:: python
    node = TextFileData(filepath='/some/absolute/path/to/file.txt')
    node.get_content()  # This will return the content of the file

This example is a simplified version of the :class:`~aiida.orm.nodes.data.singlefile.SinglefileData` data class that ships with ``aiida-core``.
If this happens to be your use case (or very close to it), it is of course better to use that class, or you can sub class it and adapt it where needed.

The just presented examples for new data types are of course trivial, but the concept is always the same and can easily be extended to more complex custom data types.
The following section will provide useful guidelines on how to optimally design new data types.


.. _how-to:data:plugin:design-guidelines:

Database or repository?
-----------------------

When deciding where to store a property of a data type, one has the option to choose between the database and the file repository.
All node properties that are stored in the database (such as the attributes), are directly searchable as part of a database query, whereas data stored in the file repository cannot be queried for.
What this means is that, for example, it is possible to search for all nodes where a particular database-stored integer attribute falls into a certain value range, but the same value stored in a file within the file repository would not be directly searchable in this way.
However, storing large amounts of data within the database comes at the cost of slowing down database queries.
Therefore, big data (think large files), whose content does not necessarily need to be queried for, is better stored in the file repository.
A data type may safely use both the database and file repository in parallel for individual properties.
Properties stored in the database are stored as *attributes* of the node.
The node class has various methods to set these attributes, such as :py:`~aiida.orm.node.Node.set_attribute` and :py:`~aiida.orm.node.Node.set_attribute_many`.

.. _how-to:data:find:

Finding and querying for data
=============================

Once you have successfully completed a series of workflows for your project, or have imported a dataset you are interested in, you want to quickly find the data that is relevant for your analysis.
The data in an AiiDA database is stored as a graph of connected entities, which can be easily *queried* with the ``QueryBuilder`` class.

The ``QueryBuilder`` lets you query your AiiDA database independently of the backend used under the hood.
Before starting to write a query, it helps to:

*   know what you want to query for.
    In the language of databases, you need to tell the backend what to *project*.
    For example, you might be interested in the label of a calculation and the PK's of all its outputs.
*   know the relationships between entities you are interested in.
    Nodes of an AiiDA graph (vertices) are connected with links (edges).
    A node can for example be either the input or output of another node, but also an ancestor or a descendant.
*   know how you want to filter the results of your query.

Once you are clear about what you want and how you can get it, the QueryBuilder will build an SQL-query for you.

There are two ways of using the QueryBuilder:

#.  In the :ref:`appender method <how-to:data:find:appender>`, you construct your query step by step using the ``QueryBuilder.append()`` method.
#.  In the :ref:`queryhelp approach <QueryBuilderQueryhelp>`, you construct a dictionary that defines your query and pass it to the ``QueryBuilder``.

Both APIs provide the same functionality - the appender method may be more suitable for interactive use, e.g., in the ``verdi shell``, whereas the queryhelp method can be useful in scripting.

.. _how-to:data:find:appender:

The appender method
-------------------

Selecting entities
^^^^^^^^^^^^^^^^^^

Using the ``append()`` method of the ``QueryBuilder``, you can query for the entities you are interested in.
Suppose you want to query for calculation job nodes in your database::

    from aiida.orm.querybuilder import QueryBuilder
    qb = QueryBuilder()       # Instantiating instance. One instance -> one query
    qb.append(CalcJobNode)    # Setting first vertex of path

If you are interested in instances of different classes, you can also pass a tuple, list or set of classes.
However, they have to be of the same ORM-type (e.g. all have to be subclasses of ``Node``)::

    qb = QueryBuilder()       # Instantiating instance. One instance -> one query
    qb.append([CalcJobNode, WorkChainNode]) # Setting first vertice of path, either WorkChainNode or Job.

.. note::
    Remember that :ref:`processes<topics:processes:concepts:types>` have both a run-time ``Process`` that steers them and a ``Node`` that stores their metadata in the database.
    The QueryBuilder allows you to pass either the ``Node`` class (e.g. ``CalcJobNode``) or the ``Process`` class (e.g. ``CalcJob``), which will automatically apply the correct filters for the type of calculation.

.. _how-to:data:find:appender:results:

Retrieving results
^^^^^^^^^^^^^^^^^^

Once you have *appended* the entity you want to query for to the ``QueryBuilder``, the next question is how to get the results.
There are several ways to obtain data from a query::

    qb = QueryBuilder()                 # Instantiating instance
    qb.append(CalcJobNode)              # Setting first vertice of path

    first_row = qb.first()              # Returns a list (!)
                                        # of the results of the first row

    all_results_d = qb.dict()           # Returns all results as
                                        # a list of dictionaries

    all_results_l = qb.all()            # Returns a list of lists

In case you are working with a large dataset, you can also return your query as a generator::

    all_res_d_gen = qb.iterdict()       # Return a generator of dictionaries
                                        # of all results
    all_res_l_gen = qb.iterall()        # Returns a generator of lists

This will retrieve the data in batches, and you can start working with the data before the query has completely finished.

.. warning::

    Complete the iteration of the query before committing (storing) new data to avoid race conditions.

.. _how-to:data:find:appender:filters:

Filters
^^^^^^^

Usually you do not want to query for *all* entities of a certain class, but rather *filter* the results based on certain properties.
Suppose you do not want to all ``CalcJobNode`` data, but only the ones that are ``finished``::

    qb = QueryBuilder()                 # Initialize a QueryBuilder instance
    qb.append(
        CalcJobNode,                    # Append a CalcJobNode
        filters={                       # Specify the filters:
            'attributes.process_state': 'finished',  # the process is finished
        },
    )

You can apply multiple filters to one entity in a query.
Say you are interested in all calculation jobs in your database that are ``finished`` **and** have the ``process_label`` ``ArithmeticAddCalculation``::

    qb = QueryBuilder()                 # Initialize a QueryBuilder instance
    qb.append(
        CalcJobNode,                    # Append a CalcJobNode
        filters={                       # Specify the filters:
            'attributes.process_state': 'finished',                   # the process is finished AND
            'attributes.process_label': 'ArithmeticAddCalculation'    # has process_label ArithmeticAddCalculation
        },
    )

In case you want to query for calculation jobs that satisfy one of these conditions, you can use the ``or`` operator::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'or':[
                {'attributes.process_state': 'excepted'},
                {'attributes.process_label': 'ArithmeticAddCalculation'}
            ]
        },
    )

If we had written *and* instead of *or* in the example above, we would have performed the exact same query as the previous one, because *and* is the default behavior if you provide several filters as key-value pairs in a dictionary to the ``filters`` argument.
In case you want all calculation jobs with state ``finished`` or ``excepted``, you can also use the ``in`` operator::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'attributes.process_state': {'in': ['finished', 'excepted']}
        },
    )

You can also negate a filter by adding an exclamation mark in front of the operator.
So, to query for all calculation jobs that are not a 'finished' or 'excepted' state::

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'attributes.process_state': {'!in': ['finished', 'excepted']}
        },
    )

.. note::
    The above rule applies to all operators.
    For example, you can check non-equality with ``!==``, since this is the equality operator (``==``) with a negation prepended.

This is a list of all implemented operators:

.. _how-to:data:find:appender:operators:

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

.. _how-to:data:find:appender:relationships:

Relationships
^^^^^^^^^^^^^

It is possible to query for data based on its relationship to another entity in the database.
Assuming you are not interested in the calculation jobs themselves, but in one of the outputs they create.
You can build upon your initial query for all ``CalcJobNode``'s in the database using the relationship of the output to the first step in the query::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')

In the first ``append`` call, we query for all ``CalcJobNode``'s in the database, and *tag* this step with the *unique* identifier ``'calcjob'``.
Next, we look for all ``Int`` nodes that are an output of the ``CalcJobNode``'s found in the first step, using the ``with_incoming`` relationship argument.
Since the ``CalcJobNode`` *created* the ``Int`` node, it is an *incoming* node from the ``Int`` node's perspective.

In the context of our query, we are building a *path* consisting of *vertices* (i.e. the entities we query for) connected by *edges* defined by the relationships between them.
Here is a list of all the relationships you can use for your query, as well as the entities that they connect:

.. In above example we are querying calculation jobs and ``Int`` nodes, with the predicate that the ``Int`` is an output of the calculation (the same as saying that the calculation   is an input to the ``Int``).
    In the above example, we have first appended ``CalcJobNode`` to the path.
    To be able to refer to that vertex later, we *tag* it with a unique keyword
    of our choice, which can be used only once.
    When we append another vertex to the path, we specify the relationship
    to a previous entity by using one of the keywords in the table below
    and as a value the tag of the vertex that it has the specified relationship with.
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

.. Some more examples::

..     # StructureData as an input of a job calculation
..     qb = QueryBuilder()
..     qb.append(CalcJobNode, tag='calc')
..     qb.append(StructureData, with_outgoing='calc')

..     # StructureData and Dict as inputs to a calculation
..     qb = QueryBuilder()
..     qb.append(CalcJobNode, tag='calc')
..     qb.append(StructureData, with_outgoing='calc')
..     qb.append(Dict, with_outgoing='calc')

..     # Filtering the remote data instance by the computer it ran on (name)
..     qb = QueryBuilder()
..     qb.append(RemoteData, tag='remote')
..     qb.append(Computer, with_node='remote', filters={'name':{'==':'mycomputer'}})

..     # Find all descendants of a structure with a certain uuid
..     qb = QueryBuilder()
..     qb.append(StructureData, tag='structure', filters={'uuid':{'==':myuuid}})
..     qb.append(Node, with_ancestors='structure')

.. The above QueryBuilder will join a structure to all its descendants via the
.. transitive closure table.

.. _how-to:data:find:appender:projections:

Projections
^^^^^^^^^^^

When no *projection* is specified, the default behavior of the ``QueryBuilder`` is to project the entities corresponding to the final vertex of the query path.
However, in many cases we are not interested in the entities themselves, but rather their PK, UUID, *attributes* or some other piece of information stored by the entity.
This can be achieved using the ``project`` keyword argument::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob', project='id')

In the above example, executing the query returns all PK's of the ``Int`` nodes which are outputs of all ``CalcJobNode``'s in the database.
However, you can project more than one piece of information for one vertex by using a list::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob', project=['id', 'attributes.value'])

Moreover, you can project information for multiple vertices along the query path::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob', project='uuid)
    qb.append(Int, with_incoming='calcjob', project=['id', 'attributes.value'])

Asking only for the properties that you are interested in can result in much faster queries.
If you want the Aiida-ORM instance, add ``'*'`` to your list of projections::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob', project='uuid')
    qb.append(Int, with_incoming='calcjob', project=['id', '*', 'attributes.value'])

All projections must start with one of the *columns* of the entities in the database.
Examples of columns we have encountered so far are ``id``, ``uuid`` and ``attributes``.
If the column is a dictionary, you can expand the dictionary values using a dot notation, as we have done in the previous example to obtain the ``attributes.value``.
This can be used to project the values of nested dictionaries as well.

.. note::
    Be aware that, for consistency, ``QueryBuilder.all()`` / ``iterall()`` always returns a list of lists, even if you project on one entity.
    A convenient boolean keyword argument for the ``all()`` method is ``flat``, which returns the query as a flat list if set to ``True``.

.. _how-to:data:find:appender:edges:

Working with edges
^^^^^^^^^^^^^^^^^^

So far the filters and projections have been applied to the vertices of the query path.
However, it is also possible to apply filters and projections on the edges that connect the vertices.
This works the same way as for vertices, but the relevant keyword is now preceded by ``edge_``.
Returning to the ``ArithmeticAddCalculation`` example, let's say we want to query for the first input of the addition, i.e. the ``Int`` nodes which have been provided as the input with label ``x``::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_outgoing='calcjob', edge_filters={'label': 'x'})

By using the ``edge_filters`` keyword argument, we can query for only the inputs that have the label ``x``.
Similarly, we can project information of the edge using the ``edge_project`` keyword argument::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_outgoing='calcjob', edge_project='label')

In the example above, we are querying for the edge labels of the incoming ``Int`` nodes of all ``CalcJobNode``'s.
Note that you can use the :ref:`operators from the table above <how-to:data:find:appender:operators>` to filter edges as well.
Say we want to find all input ``Int`` nodes that do are **not** connected to the ``CalcJobNode``'s via an edge with label ``x``::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_outgoing='calcjob', edge_filters={'label': {'!==': 'x'}})

.. how-to:data:find:appender:ordering:

Ordering and limiting results
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can order the results of your query by the properties of the entity.
Say you want to return the list of ``Int`` outputs from all ``CalcJobNode``'s, sorted by the time they were created in *descending* order, i.e. the most recent first::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')
    qb.order_by({Int: {'ctime': 'desc'}})
    qb.all()

This can also be used to order your results based on values in a (nested) dictionary, such as the ``attributes`` column.
However, as the ``QueryBuilder`` cannot infer the type of the value in this case, you have to *cast* the type::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')
    qb.order_by({Int: {'attributes.value': {'order': 'asc', 'cast': 'i'}}})
    qb.all()

The query above will return all ``Int`` nodes that are output of all ``CalcJobNode``'s, in *ascending* order of their value, i.e. from small to big.
Note that in this case you have to specify the order operation with a dictionary, where the ``order`` key details the way you want to order the query results and the ``cast`` key informs the ``QueryBuilder`` of the attribute type.
Below is a list of the available cast types and their aliases:

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

You can also order using multiple properties by providing a list of dictionaries that each specify one sorting operation::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')
    qb.order_by({Int: [{'attributes.value': {'order': 'asc', 'cast': 'f'}}, {'ctime': 'desc'}]})
    qb.all()

Here the ``Int`` nodes will first be sorted by their value in ascending order.
Nodes for which the value is equal are subsequently sorted by their modification time in descending order.

Finally, you can also limit the number of query results returned with the ``limit`` method.
Suppose you only want the first three results from our query::

    qb = QueryBuilder()
    qb.append(CalcJobNode)
    qb.limit(3)

This can be easily combined with the ``order_by`` method in order to get the last three ``CalcJobNode``'s that were created in the database::

    qb = QueryBuilder()
    qb.append(CalcJobNode)
    qb.limit(3)
    qb.order_by({CalcJobNode: {'ctime': 'desc'}})

.. how-to:data:find:queryhelp:

The queryhelp
-------------

As mentioned at the start of this how-to, there are two possibilities to query for data with the ``QueryBuilder``.
The second uses a single dictionary called the ``queryhelp`` that contains all the details of your query.
It has the same functionality as the appender method, but you can save this dictionary in a JSON file or in the database and use it at some later date.

.. note::

    The ``queryhelp`` dictionary is a property of the ``QueryBuilder`` class. So, in case you have built your query using the appender method, you can store your query by saving the ``QueryBuilder.queryhelp`` dictionary as a JSON file for later use.

To use the queryhelp, you have to specify the path, filters and projections beforehand and instantiate the QueryBuilder with that dictionary::

    qb = QueryBuilder(**queryhelp)

To construct the queryhelp dictionary, you have to specify:

*   the ``path``:
    Here, the user specifies the path along which to join tables as a list of dictionaries, where each list item identifies a vertex in your path.
    You define the vertex class with the ``cls`` key::

        queryhelp = {
            'path':[
                {'cls': Data}
            ]
        }

    Each entity in the query has to have a unique tag.
    If the tag is not provided, it is set to the name of the class.
    However, this will not work if you choose the same class twice in the query.
    In this case you have to provide the tag using the ``tag`` key::

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

    You also have to detail some information on the vertex edges, in order to connect them correctly.
    There are several redundant ways this can be done:

    *   You can specify that this node is an input or output of another node preceding the current one in the list.
        That other node can be specified by an integer or the class or type.
        The following examples are all valid joining instructions, assuming there is a structure defined at index 2 of the path with tag "struc1"::

            edge_specification = queryhelp['path'][3]
            edge_specification['with_incoming'] = 2
            edge_specification['with_incoming'] = StructureData
            edge_specification['with_incoming'] = 'struc1'
            edge_specification['with_outgoing']  = 2
            edge_specification['with_outgoing']  = StructureData
            edge_specification['with_outgoing']  = 'struc1'

    *   queryhelp_item['direction'] = integer

        If any of the above specs ("with_outgoing", "with_incoming") were not specified, the key "direction" is looked for.
        Directions are defined as distances in the tree.
        1 is defined as one step down the tree along a link.
        This means that 1 joins the node specified in this dictionary to the node specified on list-item before **as an output**.
        Direction defaults to 1, which is why, if nothing is specified, this node is joined to the previous one as an output by default.
        A negative number reverse the direction of the link.
        The absolute value of the direction defines the table to join to with respect to your own position in the list.
        An absolute value of 1 joins one table above, a value of 2 to the table defined 2 indices above.
        The two following queryhelps yield the same query::

            from aiida.orm import TrajectoryData
            from aiida_quantumespresso.calculations.pw import PwCalculation
            from aiida.orm import Dict
            qh1 = {
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

*   what to ``project``: Determing which columns the query will return::

        queryhelp = {
            'path':[PwCalculation],
            'project':{
                PwCalculation:['user_id', 'id'],
            }
        }

    If you are using JSONB columns, you can also project a value stored inside the json::

        queryhelp = {
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

If you want to include filters and projections on links between nodes, you will have to add these to filters and projections in the queryhelp.
Let's take an example from before and add a few filters on the link::

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

Notice that the tag for the link, by default, is the tag of the two connecting nodes delimited by two dashes '--' and the order DOES matter.

Alternatively, you can choose the tag for the edge in the path when defining the entity to join using ``edge_tag``::

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

Limits and offset can be set directly like this::

    queryhelp = {
        'path':[Node],
        'limit':10,
        'offset':20
    }

That queryhelp would tell the QueryBuilder to return 10 rows after the first 20 have been skipped.

.. _how-to:data:organize:

Organizing data
===============

`#3997`_


.. _how-to:data:share:

Sharing data
============

`#3998`_


.. _how-to:data:delete:

Deleting data
=============

By default, every time you run or submit a new calculation, AiiDA will create for you new nodes in the database, and will never replace or delete data.
There are cases, however, when it might be useful to delete nodes that are not useful anymore, for instance test runs or incorrect/wrong data and calculations.
For this case, AiiDA provides the ``verdi node delete`` command to remove the nodes from the provenance graph.

.. caution::
   Once the data is deleted, there is no way to recover it (unless you made a backup).

Critically, note that even if you ask to delete only one node, ``verdi node delete`` will typically delete a number of additional linked nodes, in order to preserve a consistent state of the provenance graph.
For instance, if you delete an input of a calculation, AiiDA will delete also the calculation itself (as otherwise you would be effectively changing the inputs to that calculation in the provenance graph).
The full set of consistency rules are explained in detail :ref:`here <topics:provenance:consistency>`.

Therefore: always check the output of ``verdi node delete`` to make sure that it is not deleting more than you expect.
You can also use the ``--dry-run`` flag of ``verdi node delete`` to see what the command would do without performing any actual operation.

In addition, there are a number of additional rules that are not mandatory to ensure consistency, but can be toggled by the user.
For instance, you can set ``--create-forward`` if, when deleting a calculation, you want to delete also the data it produced (using instead ``--no-create-forward`` will delete the calculation only, keeping the output data: note that this effectively strips out the provenance information of the output data).
The full list of these flags is available from the help command ``verdi node delete -h``.

Deleting computers
------------------
To delete a computer, you can use ``verdi computer delete``.
This command is mostly useful if, right after creating a computer, you realise that there was an error and you want to remove it.
In particular, note that ``verdi computer delete`` will prevent execution if the computer has been already used by at least one node. In this case, you will need to use ``verdi node delete`` to delete first the corresponding nodes.

Deleting mutable data
---------------------
A subset of data in AiiDA is mutable also after storing a node, and is used as a convenience for the user to tag/group/comment on data.
This data can be safely deleted at any time.
This includes, notably:

* *Node extras*: These can be deleted using :py:meth:`~aiida.orm.nodes.node.Node.delete_extra` and :py:meth:`~aiida.orm.nodes.node.Node.delete_extra_many`.
* *Node comments*: These can be removed using :py:meth:`~aiida.orm.nodes.node.Node.remove_comment`.
* *Groups*: These can be deleted using :py:meth:`Group.objects.delete() <aiida.orm.groups.Group.Collection.delete>`.
  This command will only delete the group, not the nodes contained in the group.

Completely deleting an AiiDA profile
------------------------------------
If you don't want to selectively delete some nodes, but instead want to delete a whole AiiDA profile altogether, use the ``verdi profile delete`` command.
This command will delete both the file repository and the database.

.. danger::

  It is not possible to restore a deleted profile unless it was previously backed up!


Serving your data to others
===========================

The AiiDA REST API allows to query your AiiDA database over HTTP(S), e.g. by writing requests directly or via a JavaScript application as on `Materials Cloud <http://materialscloud.org/explore>`_.

The ``verdi restapi`` command runs the REST API through the ``werkzeug`` python-based HTTP server.
In order to deploy production instances of the REST API for serving your data to others, we recommend using a fully fledged web server, such as `Apache <https://httpd.apache.org/>`_ or `NGINX <https://www.nginx.com/>`_.

.. note::
    One Apache/NGINX server can host multiple APIs, e.g. connecting to different AiiDA profiles.

In the following, we assume you have a working installation of Apache with the ``mod_wsgi`` `WSGI module <modwsgi.readthedocs.io/>`_ enabled.

The goal of the example is to hookup the APIs ``django`` and ``sqlalchemy`` pointing to two AiiDA profiles, called for simplicity ``django`` and ``sqlalchemy``.

All the relevant files are enclosed under the path ``/docs/wsgi/`` starting from the AiiDA source code path.
In each of the folders ``app1/`` and ``app2/``, there is a file named ``rest.wsgi`` containing a python script that instantiates and configures a python web app called ``application``, according to the rules of ``mod_wsgi``.
For how the script is written, the object ``application`` is configured through the file ``config.py`` contained in the same folder.
Indeed, in ``app1/config.py`` the variable ``aiida-profile`` is set to ``"django"``, whereas in ``app2/config.py`` its value is ``"sqlalchemy"``.

Anyway, the path where you put the ``.wsgi`` file as well as its name are irrelevant as long as they are correctly referred to in the Apache configuration file, as shown later on.
Similarly, you can place ``config.py`` in a custom path, provided you change the variable ``config_file_path`` in the ``wsgi file`` accordingly.

In ``rest.wsgi`` probably the only options you might want to change is ``catch_internal_server``.
When set to ``True``, it lets the exceptions thrown during the execution of the app propagate all the way through until they reach the logger of Apache.
Especially when the app is not entirely stable yet, one would like to read the full python error traceback in the Apache error log.

Finally, you need to setup the Apache site through a proper configuration file.
We provide two template files: ``one.conf`` or ``many.conf``.
The first file tells Apache to bundle both apps in a unique Apache daemon process.
Apache usually creates multiple process dynamically and with this configuration each process will handle both apps.

The script ``many.conf``, instead, defines two different process groups, one for each app.
So the processes created dynamically by Apache will always be handling one app each.
The minimal number of Apache daemon processes equals the number of apps, contrarily to the first architecture, where one process is enough to handle two or even a larger number of apps.

Let us call the two apps for this example ``django`` and ``sqlalchemy``.
In both ``one.conf`` and ``many.conf``, the important directives that should be updated if one changes the paths or names of the apps are:

    - ``WSGIProcessGroup`` to define the process groups for later reference.
      In ``one.conf`` this directive appears only once to define the generic group ``profiles``, as there is only one kind of process handling both apps.
      In ``many.conf`` this directive appears once per app and is embedded into a "Location" tag, e.g.::

        <Location /django>
            WSGIProcessGroup sqlalchemy
        <Location/>

    - ``WSGIDaemonProcess`` to define the path to the AiiDA virtual environment.
      This appears once per app in both configurations.

    - ``WSGIScriptAlias`` to define the absolute path of the ``.wsgi`` file of each app.

    - The ``<Directory>`` tag mainly used to grant Apache access to the files used by each app, e.g.::

        <Directory "<aiida.source.code.path>/aiida/restapi/wsgi/app1">
                Require all granted
        </Directory>

The latest step is to move either ``one.conf`` or ``many.conf`` into the Apache configuration folder and restart the Apache server.
In Ubuntu, this is usually done with the commands:

.. code-block:: bash

    cp <conf_file>.conf /etc/apache2/sites-enabled/000-default.conf
    sudo service apache2 restart

We believe the two basic architectures we have just explained can be successfully applied in many different deployment scenarios.
Nevertheless, we suggest users who need finer tuning of the deployment setup to look into to the official documentation of `Apache <https://httpd.apache.org/>`_ and, more importantly, `WSGI <wsgi.readthedocs.io/>`__.

The URLs of the requests handled by Apache must start with one of the paths specified in the directives ``WSGIScriptAlias``.
These paths identify uniquely each app and allow Apache to route the requests to their correct apps.
Examples of well-formed URLs are:

.. code-block:: bash

    curl http://localhost/django/api/v4/computers -X GET
    curl http://localhost/sqlalchemy/api/v4/computers -X GET

The first (second) request will be handled by the app ``django`` (``sqlalchemy``), namely will serve results fetched from the profile ``django`` (``sqlalchemy``).
Notice that we haven't specified any port in the URLs since Apache listens conventionally to port 80, where any request lacking the port is automatically redirected.


.. _#3996: https://github.com/aiidateam/aiida-core/issues/3996
.. _#3997: https://github.com/aiidateam/aiida-core/issues/3997
.. _#3998: https://github.com/aiidateam/aiida-core/issues/3998
