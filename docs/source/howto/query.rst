.. _how-to:query:

*******************************
How to find and query for data
*******************************

An AiiDA database stores a graph of connected entities, which can be *queried* with the :class:`~aiida.orm.querybuilder.QueryBuilder` class.

Before starting to write a query, it helps to:

*   | Know what you want to query for.
    | In the language of databases, you need to tell the backend what *entity* you are looking for and optionally which of its properties you want to *project*.
    | For example, you might be interested in the label of a calculation and the PKs of all its outputs.
*   | Know the relationships between entities you are interested in.
    | Nodes of an AiiDA graph (vertices) are connected with links (edges).
    | A node can for example be either the input or output of another node, but also an ancestor or a descendant.
*   | Know how you want to filter the results of your query.

Once you are clear about what you want and how you can get it, the :class:`~aiida.orm.querybuilder.QueryBuilder` will build an SQL-query for you.

There are two ways of using the :class:`~aiida.orm.querybuilder.QueryBuilder`:

#.  In the *appender* method, you construct your query step by step using the ``QueryBuilder.append()`` method.
#.  In the *dictionary* approach, you construct a dictionary that defines your query and pass it to the :class:`~aiida.orm.querybuilder.QueryBuilder`.

Both APIs provide the same functionality - the appender method may be more suitable for interactive use, e.g., in the ``verdi shell``, whereas the dictionary method can be useful in scripting.
In this section we will focus on the basics of the appender method.
For more advanced queries or more details on the query dictionary, see the :ref:`topics section on advanced querying <topics:database:advancedquery>`.

.. _how-to:query:select:

Selecting entities
==================

Using the ``append()`` method of the :class:`~aiida.orm.querybuilder.QueryBuilder`, you can query for the entities you are interested in.
Suppose you want to query for calculation job nodes in your database:

.. code-block:: python

    from aiida.orm import QueryBuilder
    qb = QueryBuilder()       # Instantiating instance. One instance -> one query
    qb.append(CalcJobNode)    # Setting first vertex of path

If you are interested in instances of different classes, you can also pass an iterable of classes.
However, they have to be of the same ORM-type (e.g. all have to be subclasses of :class:`~aiida.orm.nodes.node.Node`):

.. code-block:: python

    qb = QueryBuilder()       # Instantiating instance. One instance -> one query
    qb.append([CalcJobNode, WorkChainNode]) # Setting first vertices of path, either WorkChainNode or Job.

.. note::

    Processes have both a run-time :class:`~aiida.engine.processes.process.Process` that executes them and a :class:`~aiida.orm.nodes.node.Node` that stores their data in the database (see the :ref:`corresponding topics section<topics:processes:concepts:types>` for a detailed explanation).
    The :class:`~aiida.orm.querybuilder.QueryBuilder` allows you to pass either the :class:`~aiida.orm.nodes.node.Node` class (e.g. :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`) or the :class:`~aiida.engine.processes.process.Process` class (e.g. :class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`), which will automatically select the right entity for the query.
    Using either :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` or :class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` will produce the same query results.

.. _how-to:query:results:

Retrieving results
==================

Once you have *appended* the entity you want to query for to the :class:`~aiida.orm.querybuilder.QueryBuilder`, the next question is how to get the results.
There are several ways to obtain data from a query:

.. code-block:: python

    qb = QueryBuilder()                 # Instantiating instance
    qb.append(CalcJobNode)              # Setting first vertices of path

    first_row = qb.first()              # Returns a list (!) of the results of the first row

    all_results_d = qb.dict()           # Returns all results as a list of dictionaries

    all_results_l = qb.all()            # Returns a list of lists

.. tip::

    If your query only has a single projection, use ``flat=True`` in the ``first`` and ``all`` methods to return a single value or a flat list, respectively.

You can also return your query as a generator:

.. code-block:: python

    all_res_d_gen = qb.iterdict()       # Return a generator of dictionaries
    all_res_l_gen = qb.iterall()        # Returns a generator of lists

This will retrieve the data in batches, and you can start working with the data before the query has completely finished.
For example, you can iterate over the results of your query in a for loop:

.. code-block:: python

    for entry in qb.iterall():
        # do something with a single entry in the query result

.. important::

    When looping over the result of a query, use the ``iterall`` (or ``iterdict``) generator instead of ``all`` (or ``dict``).
    This avoids loading the entire query result into memory, and it also delays committing changes made to AiiDA objects inside the loop until the end of the loop is reached.
    If an exception is raised before the loop ends, all changes are reverted.


.. _how-to:query:filters:

Filters
=======

Usually you do not want to query for *all* entities of a certain class, but rather *filter* the results based on certain properties.
Suppose you do not want all :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` data, but only those that are ``finished``:

.. code-block:: python

    qb = QueryBuilder()                 # Initialize a QueryBuilder instance
    qb.append(
        CalcJobNode,                    # Append a CalcJobNode
        filters={                       # Specify the filters:
            'attributes.process_state': 'finished',  # the process is finished
        },
    )

You can apply multiple filters to one entity in a query.
Say you are interested in all calculation jobs in your database that are ``finished`` **and** have ``exit_status == 0``:

.. code-block:: python

    qb = QueryBuilder()                 # Initialize a QueryBuilder instance
    qb.append(
        CalcJobNode,                    # Append a CalcJobNode
        filters={                       # Specify the filters:
            'attributes.process_state': 'finished',     # the process is finished AND
            'attributes.exit_status': 0                 # has exit_status == 0
        },
    )

In case you want to query for calculation jobs that satisfy one of these conditions, you can use the ``or`` operator:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'or':[
                {'attributes.process_state': 'finished'},
                {'attributes.exit_status': 0}
            ]
        },
    )

If we had written ``and`` instead of ``or`` in the example above, we would have performed the exact same query as the previous one, because ``and`` is the default behavior if you provide several filters as key-value pairs in a dictionary to the ``filters`` argument.
In case you want all calculation jobs with state ``finished`` or ``excepted``, you can also use the ``in`` operator:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(
        CalcJobNode,
        filters={
            'attributes.process_state': {'in': ['finished', 'excepted']}
        },
    )

.. _how-to:query:filters:operator-negations:

Operator negations
------------------

A filter can be turned into its associated **negation** by adding an exclamation mark, ``!``, in front of the operator.
So, to query for all calculation jobs that are not a ``finished`` or ``excepted`` state:

.. code-block:: python

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

A complete list of all available operators can be found in the :ref:`advanced querying section<topics:database:advancedquery:tables:operators>`.

.. _how-to:query:relationships:

Relationships
=============

It is possible to query for data based on its relationship to another entity in the database.
Imagine you are not interested in the calculation jobs themselves, but in one of the outputs they create.
You can build upon your initial query for all  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`'s in the database using the relationship of the output to the first step in the query:

.. code-block::

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')

In the first ``append`` call, we query for all  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`'s in the database, and *tag* this step with the *unique* identifier ``'calcjob'``.
Next, we look for all ``Int`` nodes that are an output of the  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`'s found in the first step, using the ``with_incoming`` relationship argument.
The ``Int`` node was created by the  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` and as such has an *incoming* create link.

In the context of our query, we are building a *path* consisting of *vertices* (i.e. the entities we query for) connected by *edges* defined by the relationships between them.
The complete set of all possible relationships you can use query for, as well as the entities that they connect to, can be found in the :ref:`advanced querying section<topics:database:advancedquery:tables:relationships>`.

.. note::

    The ``tag`` identifier can be any alphanumeric string, it is simply a label used to refer to a previous vertex along the query path when defining a relationship.

.. _how-to:query:projections:

Projections
===========

By default, the :class:`~aiida.orm.querybuilder.QueryBuilder` returns the instances of the entities corresponding to the final append to the query path.
For example:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob')

The above code snippet will return all ``Int`` nodes that are outputs of any  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`.
However, you can also *project* other entities in the path by adding ``project='*'`` to the corresponding ``append()`` call:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob', project='*')
    qb.append(Int, with_incoming='calcjob')

This will return all  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`'s that have an ``Int`` output node.

However, in many cases we are not interested in the entities themselves, but rather their PK, UUID, *attributes* or some other piece of information stored by the entity.
This can be achieved by providing the corresponding *column* to the ``project`` keyword argument:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob', project='id')

In the above example, executing the query returns all *PK's* of the ``Int`` nodes which are outputs of all  :class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`'s in the database.
Moreover, you can project more than one piece of information for one vertex by providing a list:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob')
    qb.append(Int, with_incoming='calcjob', project=['id', 'attributes.value'])

For the query above, ``qb.all()`` will return a list of lists, for which each element corresponds to one entity and contains two items: the PK of the ``Int`` node and its value.
Finally, you can project information for multiple vertices along the query path:

.. code-block:: python

    qb = QueryBuilder()
    qb.append(CalcJobNode, tag='calcjob', project='*')
    qb.append(Int, with_incoming='calcjob', project=['id', 'attributes.value'])

All projections must start with one of the *columns* of the entities in the database, or project the instances themselves using ``'*'``.
Examples of columns we have encountered so far are ``id``, ``uuid`` and ``attributes``.
If the column is a dictionary, you can expand the dictionary values using a dot notation, as we have done in the previous example to obtain the ``attributes.value``.
This can be used to project the values of nested dictionaries as well.

.. note::

    Be aware that for consistency, ``QueryBuilder.all()`` / ``iterall()`` always returns a list of lists, even if you only project one property of a single entity.
    Use ``QueryBuilder.all(flat=True)`` to return the query result as a flat list in this case.

As mentioned in the beginning, this section provides only a brief introduction to the :class:`~aiida.orm.querybuilder.QueryBuilder`'s basic functionality.
To learn about more advanced queries, please see :ref:`the corresponding topics section<topics:database:advancedquery>`.



.. _how-to:query:shortcuts:

Shortcuts
=========

The :class:`~aiida.orm.querybuilder.QueryBuilder` is the generic way of querying for data in AiiDA.
For certain common queries, shortcuts have been added to the AiiDA python API to save you a couple of lines of code.

.. _how-to:query:shortcuts:incoming-outgoing:

Incoming and outgoing links
----------------------------

The provenance graph in AiiDA is a :ref:`directed graph <topics:provenance:concepts>`.
The vertices of the graph are the *nodes*, and the edges that connect them are called *links*.
Since the graph is directed, any node can have *incoming* and *outgoing* links that connect it to neighboring nodes.

To discover the neighbors of a given node, you can use the methods :meth:`~aiida.orm.nodes.links.NodeLinks.get_incoming` and :meth:`~aiida.orm.nodes.links.NodeLinks.get_outgoing`.
They have the exact same interface but will return the neighbors connected to the current node with a link coming into it or with links going out of it, respectively.
For example, for a given ``node``, to inspect all the neighboring nodes from which a link is incoming to the ``node``:

.. code-block:: python

    node.get_incoming()

This will return an instance of the :class:`~aiida.orm.utils.links.LinkManager`.
From that manager, you can request the results in a specific format.
If you are only interested in the neighboring nodes themselves, you can call the :class:`~aiida.orm.utils.links.LinkManager.all_nodes` method:

.. code-block:: python

    node.get_incoming().all_nodes()

This will return a list of :class:`~aiida.orm.nodes.node.Node` instances that correspond to the nodes that are neighbors of ``node``, where the link is going towards ``node``.
Calling the :meth:`~aiida.orm.utils.links.LinkManager.all` method of the manager instead will return a list of :class:`~aiida.orm.utils.links.LinkTriple` named tuples.
These tuples contain, in addition to the neighboring node, also the link label and the link type with which they are connected to the origin ``node``.
For example, to list all the neighbors of a node from which a link is incoming:

.. code-block:: python

    for link_triple in node.get_incoming().all():
        print(link_triple.node, link_triple.link_type, link_triple.link_label)

Note that the :class:`~aiida.orm.utils.links.LinkManager` provides many convenience methods to get information from the neigboring nodes, such as :meth:`~aiida.orm.utils.links.LinkManager.all_link_labels` if you only need the list of link labels.

The :meth:`~aiida.orm.nodes.links.NodeLinks.get_incoming` and :meth:`~aiida.orm.nodes.links.NodeLinks.get_outgoing` methods accept various arguments that allow one to filter what neighboring nodes should be matched:

* ``node_class``: accepts a subclass of :class:`~aiida.orm.nodes.node.Node`, only neighboring nodes with a class that matches this will be returned
* ``link_type``: accepts a value of :class:`~aiida.common.links.LinkType`, only neighboring nodes that are linked with this link type will be returned
* ``link_label_filter``: accepts a string  expression (with optional wildcards using the syntax of SQL ``LIKE`` patterns, see below), only neighboring nodes that are linked with a link label that matches the pattern will be returned

As an example:

.. code-block:: python

    node.get_incoming(node_class=Data, link_type=LinkType.INPUT_CALC, link_label_filter='output%node_').all_nodes()

will return only neighboring data nodes that are linked to the ``node`` with a link of type ``LinkType.INPUT_CALC`` and where the link label matches the pattern ``'output%node_'``.
Reminder on the syntax of SQL `LIKE` patterns: the ``%`` character matches any string of zero or more characters, while the ``_`` character matches exactly one character.
These two special characters can be escaped by prepending them with a backslash (note that when putting a backslash in a Python string you have to escape the backslash itself, so you will need two backslashes: e.g., to match exactly a link label ``a_b`` you need to pass ``link_label_filter='a\\_b'``).


.. _how-to:query:shortcuts:inputs-outputs:

Inputs and outputs of processes
-------------------------------

The :meth:`~aiida.orm.nodes.links.NodeLinks.get_incoming` and :meth:`~aiida.orm.nodes.links.NodeLinks.get_outgoing` methods, described in the :ref:`previous section <how-to:query:shortcuts:incoming-outgoing>`, can be used to access all neighbors from a certain node and provide advanced filtering options.
However, often one doesn't need this expressivity and simply wants to retrieve all neighboring nodes with a syntax that is as succint as possible.
A prime example is to retrieve the *inputs* or *outputs* of :ref:`a process <topics:processes:concepts>`.
Instead of using :meth:`~aiida.orm.nodes.links.NodeLinks.get_incoming` and :meth:`~aiida.orm.nodes.links.NodeLinks.get_outgoing`, to get the inputs and outputs of a ``process_node`` one can do:

.. code-block:: python

    inputs = process_node.inputs
    outputs = process_node.outputs

These properties do not return the actual inputs and outputs directly, but instead return an instance of :class:`~aiida.orm.utils.managers.NodeLinksManager`.
The reason is because through the manager, the inputs or outputs are accessible through their link label (that, for inputs and outputs of processes, is unique) and can be tab-completed.
For example, if the ``process_node`` has an output with the label ``result``, it can be retrieved as:

.. code-block:: python

    process_node.outputs.result

The inputs or outputs can also be accessed through key dereferencing:

.. code-block:: python

    process_node.outputs['result']

If there is no neighboring output with the given link label, a :class:`~aiida.common.exceptions.NotExistentAttributeError` or :class:`~aiida.common.exceptions.NotExistentKeyError` will be raised, respectively.

.. note::

    The ``inputs`` and ``outputs`` properties are only defined for :class:`~aiida.orm.nodes.process.process.ProcessNode`'s.
    This means that you cannot *chain* these calls, because an input or output of a process node is guaranteed to be a :class:`~aiida.orm.Data` node, which does not have inputs or outputs.


.. _how-to:query:shortcuts:creator-caller-called:

Creator, caller and called
--------------------------

Similar to the ``inputs`` and ``outputs`` properties of process nodes, there are some more properties that make exploring the provenance graph easier:

* :meth:`~aiida.orm.nodes.process.process.ProcessNode.called`: defined for :class:`~aiida.orm.nodes.process.process.ProcessNode`'s and returns the list of process nodes called by this node.
  If this process node did not call any other processes, this property returns an empty list.
* :meth:`~aiida.orm.nodes.process.process.ProcessNode.caller`: defined for :class:`~aiida.orm.nodes.process.process.ProcessNode`'s and returns the process node that called this node.
  If this node was not called by a process, this property returns ``None``.
* :meth:`~aiida.orm.Data.creator`: defined for :class:`~aiida.orm.Data` nodes and returns the process node that created it.
  If the node was not created by a process, this property returns ``None``.

.. note::

    Using the ``creator`` and ``inputs`` properties, one can easily move *up* the provenance graph.
    For example, starting from some data node that represents the result of a long workflow, one can move up the provenance graph to find an initial input node of interest: ``result.creator.inputs.some_input.creator.inputs.initial_input``.

.. _how-to:query:shortcuts:calcjob-results:

Calculation job results
-----------------------

:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`'s provide the :meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.res` property, that can give easy access to the results of the calculation job.
The requirement is that the :class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` class that produced the node, defines a *default output node* in its spec.
This node should be a :class:`~aiida.orm.nodes.data.dict.Dict` output that will always be created.
An example is the :class:`~aiida.calculations.templatereplacer.TemplatereplacerCalculation` plugin, that has the ``output_parameters`` output that is specified as its default output node.

The :meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.res` property will give direct easy access to all the keys within this dictionary output.
For example, the following:

.. code-block:: python

    list(node.res)

will return a list of all the keys in the output node.
Individual keys can then be accessed through attribute dereferencing:

.. code-block:: python

    node.res.some_key

In an interactive shell, the available keys are also tab-completed.
If you type ``node.res.`` followed by the tab key twice, a list of the available keys is printed.

.. note::

    The :meth:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.res` property is really just a shortcut to quickly and easily access an attribute of the default output node of a calculation job.
    For example, if the default output node link label is ``output_parameters``, then ``node.res.some_key`` is exactly equivalent to ``node.outputs.output_parameters.dict.some_key``.
    That is to say, when using ``res``, one is accessing attributes of one of the output nodes, and not of the calculation job node itself.
