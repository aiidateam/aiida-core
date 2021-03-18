.. _how-to:exploring:

***********************************
How to explore the provenance graph
***********************************

.. _how-to:exploring:incoming-outgoing:

Incoming and outgoing links
===========================

The provenance graph in AiiDA is a :ref:`directed graph <topics:provenance:concepts>`.
The vertices of the graph are the *nodes*, and the edges that connect them are called *links*.
Since the graph is directed, any node can have *incoming* and *outgoing* links that connect it to neighboring nodes.

To discover the neighbors of a given node, you can use the methods :meth:`~aiida.orm.nodes.node.Node.get_incoming` and :meth:`~aiida.orm.nodes.node.Node.get_outgoing`.
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

The :meth:`~aiida.orm.nodes.node.Node.get_incoming` and :meth:`~aiida.orm.nodes.node.Node.get_outgoing` methods accept various arguments that allow one to filter what neighboring nodes should be matched:

 * ``node_class``: accepts a subclass of :class:`~aiida.orm.nodes.node.Node`, only neighboring nodes with a class that matches this will be returned
 * ``link_type``: accepts a value of :class:`~aiida.common.links.LinkType`, only neighboring nodes that are linked with this link type will be returned
 * ``link_label_filter``: accepts a string  expression (with optional wildcards using the syntax of SQL ``LIKE`` patterns, see below), only neighboring nodes that are linked with a link label that matches the pattern will be returned

As an example:

.. code-block:: python

    node.get_incoming(node_class=Data, link_type=LinkType.INPUT_CALC, link_label_filter='output%node_').all_nodes()

will return only neighboring data nodes that are linked to the ``node`` with a link of type ``LinkType.INPUT_CALC`` and where the link label matches the pattern ``'output%node_'``.
Reminder on the syntax of SQL `LIKE` patterns: the ``%`` character matches any string of zero or more characters, while the ``_`` character matches exactly one character.
These two special characters can be escaped by prepending them with a backslash (note that when putting a backslash in a Python string you have to escape the backslash itself, so you will need two backslashes: e.g., to match exactly a link label ``a_b`` you need to pass ``link_label_filter='a\\_b'``).


.. _how-to:exploring:inputs-outputs:

Inputs and outputs
==================

The :meth:`~aiida.orm.nodes.node.Node.get_incoming` and :meth:`~aiida.orm.nodes.node.Node.get_outgoing` methods, described in the :ref:`previous section <how-to:exploring:incoming-outgoing>`, can be used to access all neighbors from a certain node and provide advanced filtering options.
However, often one doesn't need this expressivity and simply wants to retrieve all neighboring nodes with a syntax that is as succint as possible.
A prime example is to retrieve the *inputs* or *outputs* of :ref:`a process <topics:processes:concepts>`.
Instead of using :meth:`~aiida.orm.nodes.node.Node.get_incoming` and :meth:`~aiida.orm.nodes.node.Node.get_outgoing`, to get the inputs and outputs of a ``process_node`` one can do:

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
    This means that you cannot *chain* these calls, because an input or output of a process node is guaranteed to be a :class:`~aiida.orm.nodes.data.Data` node, which does not have inputs or outputs.


.. _how-to:exploring:creator-caller-called:

Creator, caller and called
==========================

Similar to the ``inputs`` and ``outputs`` properties of process nodes, there are some more properties that make exploring the provenance graph easier:

    * :meth:`~aiida.orm.nodes.process.process.ProcessNode.called`: defined for :class:`~aiida.orm.nodes.process.process.ProcessNode`'s and returns the list of process nodes called by this node.
      If this process node did not call any other processes, this property returns an empty list.
    * :meth:`~aiida.orm.nodes.process.process.ProcessNode.caller`: defined for :class:`~aiida.orm.nodes.process.process.ProcessNode`'s and returns the process node that called this node.
      If this node was not called by a process, this property returns ``None``.
    * :meth:`~aiida.orm.nodes.data.Data.creator`: defined for :class:`~aiida.orm.nodes.data.Data` nodes and returns the process node that created it.
      If the node was not created by a process, this property returns ``None``.

.. note::

    Using the ``creator`` and ``inputs`` properties, one can easily move *up* the provenance graph.
    For example, starting from some data node that represents the result of a long workflow, one can move up the provenance graph to find an initial input node of interest: ``result.creator.inputs.some_input.creator.inputs.initial_input``.

.. _how-to:exploring:calcjob-results:

Calculation job results
=======================

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
