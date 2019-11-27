==================
Retrieving results
==================

In this section, we describe how to get the results of a calculation after it has been parsed by AiiDA, or the input and output of a generic Node.
When a calculation is done on the remote computer, AiiDA will retrieve the results and try to parse the results with the default parser, if one is available for the given calculation. These results are stored in new nodes, and connected as output of the calculation. Of course, it is possible to :ref:`directly check the output nodes <db_input_output>` for a given calculation and get their content. However, AiiDA provides a way to directly access the results, using the :py:class:`CalcJobResultManager<aiida.orm.utils.calcjob.CalcJobResultManager>` class, described in the next section.

The CalcJobResultManager
+++++++++++++++++++++++++++++

Prerequisites
-------------

Before getting the calculation results, we need a correctly finished and parsed
:class:`CalcJobNode<aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`.
For example this can be a Quantum ESPRESSO ``pw.x`` calculation.
You can load such a calculation -- we'll call it ``calc`` -- with the command

.. code :: python

    from aiida.orm import load_node
    calc = load_node(YOURPK)

either in ``verdi shell``, or in a python script (as described :doc:`here <../working_with_aiida/scripting>`).
``YOURPK`` should be substituted by a valid calculation ``PK`` in your database.

Using the CalcJobResultManager instance
-------------------------------------------

Each :class:`CalcJobNode<aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>` has a ``res`` attribute that is a
:class:`~aiida.orm.utils.calcjob.CalcJobResultManager` instance and
gives direct access to parsed data. You can access it as
::

    calc.res

To get all the possible keys that were parsed, you can convert the instance into a list. For instance, if you
type
::

    print(list(calc.res))

you will get something like this::

    ['rho_cutoff', 'energy', 'energy_units', ...]

(the list of keys has been cut for clarity: you will get many more
keys).

Once you know which keys have been parsed, you can access the parsed
value simply as an attribute of the ``res`` :class:`~aiida.orm.utils.calcjob.CalcJobResultManager`. For instance, to get the final total energy, you can use
::

    print(calc.res.energy)

that will print the total energy in units of eV, as also stated in the ``energy_units`` key
::

    print(calc.res.energy_units)

Similarly, you can get any other parsed value, for any code that
provides a parser.

.. hint::
    The :class:`~aiida.orm.utils.calcjob.CalcJobResultManager` is also integrated with the iPython/verdi shell completion mechanism: if ``calc`` is a valid :class:`CalcJobNode<aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`, you can type
    ::

        calc.res.

    and then press the ``TAB`` key of the keyboard to get/complete the list of valid parsed properties for the calculation ``calc``.

.. _db_input_output:

Calculations and workflows inputs and outputs
++++++++++++++++++++++++++++++++++++++++++++++

In the following, we will show the methods to access the input and output nodes of a given calculation or workflow.

Again, we start by loading a node from the database. Unlike before, this can be any type of node.
For example, if we have a the node with ``PK`` 17::

    from aiida.orm import load_node
    calc = load_node(17)

Now, we want to find the nodes which have a direct input or output link to this node.
The node has several methods to extract this information: :meth:`get_outgoing() <aiida.orm.nodes.Node.get_outgoing>`,
:meth:`get_incoming() <aiida.orm.nodes.Node.get_incoming>`.

The most practical way to access this information for a calculation (or workflow), when limiting solely to
``INPUT_CALC`` and ``CREATE`` (or ``INPUT_WORK`` and ``RETURN``, respectively), especially when working on the ``verdi shell``,
is by means of the ``.inputs`` and ``.outputs`` attributes.

The ``.inputs`` attribute can be used to list and access the input nodes.
The names of the input links can be printed by ``list(calc.inputs)``
or interactively by ``calc.inputs. + TAB``.
As an example, suppose that ``calc`` has an input ``KpointsData`` object under the linkname ``kpoints``. The command
::

    calc.inputs.kpoints

returns the ``KpointsData`` object.

Similarly the ``.outputs`` attribute can be used to display the outputs of ``calc``.
Suppose that ``calc`` has an output ``FolderData`` with linkname ``retrieved``, then the command
::

  calc.outputs.retrieved

returns the ``FolderData`` object.

