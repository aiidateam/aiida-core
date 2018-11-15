==================
Retrieving results
==================

In this section, we describe how to get the results of a calculation after it has been parsed by AiiDA, or the input and output of a generic Node.
When a calculation is done on the remote computer, AiiDA will retrieve the results and try to parse the results with the default parser, if one is available for the given calculation. These results are stored in new nodes, and connected as output of the calculation. Of course, it is possible to :ref:`directly check the output nodes <db_input_output>` for a given calculation and get their content. However, AiiDA provides a way to directly access the results, using the :py:class:`CalculationResultManager<aiida.orm.node.process.calculation.calcjob.CalculationResultManager>` class, described in the next section.

The CalculationResultManager
+++++++++++++++++++++++++++++

Prerequisites
-------------

Before getting the calculation results, we need a correctly finished and parsed
:class:`CalcJobNode<aiida.orm.node.process.calculation.calcjob.CalcJobNode>`.
For example this can be a Quantum ESPRESSO ``pw.x`` calculation.
You can load such a calculation -- we'll call it ``calc`` -- with the command

.. code :: python
    
    from aiida.orm import load_node
    calc = load_node(YOURPK)

either in ``verdi shell``, or in a python script (as described :doc:`here <../working_with_aiida/scripting>`).
``YOURPK`` should be substituted by a valid calculation PK in your database.

Using the CalculationResultManager instance
-------------------------------------------

Each :class:`CalcJobNode<aiida.orm.node.process.calculation.calcjob.CalcJobNode>` has a ``res`` attribute that is a 
:class:`~aiida.orm.node.process.calculation.calcjob.CalculationResultManager` instance and
gives direct access to parsed data. You can access it as
::

    calc.res

To get all the possible keys that were parsed, you can convert the instance into a list. For instance, if you
type
::

    print list(calc.res)

you will get something like this::

    [u'rho_cutoff', u'energy', u'energy_units', ...]

(the list of keys has been cut for clarity: you will get many more
keys).

Once you know which keys have been parsed, you can access the parsed
value simply as an attribute of the ``res`` :class:`~aiida.orm.node.process.calculation.calcjob.CalculationResultManager`. For instance, to get the final total energy, you can use
::

    print calc.res.energy

that will print the total energy in units of eV, as also stated in the ``energy_units`` key
::

    print calc.res.energy_units

Similarly, you can get any other parsed value, for any code that
provides a parser.

.. hint:: 
    The :class:`~aiida.orm.node.process.calculation.calcjob.CalculationResultManager` is also integrated with the iPython/verdi shell completion mechanism: if ``calc`` is a valid :class:`CalcJobNode<aiida.orm.node.process.calculation.calcjob.CalcJobNode>`, you can type
    ::

        calc.res.

    and then press the TAB key of the keyboard to get/complete the list of valid parsed properties for the calculation ``calc``.

.. _db_input_output:

Node input and output
=====================

In the following, we will show the methods to access the input and output nodes of a given node.

Again, we start by loading a node from the database. Unlike before, this can be any type of node. For example, we can load the node with PK 17::

    from aiida.orm import load_node
    node = load_node(17)

Now, we want to find the nodes which have a direct link to this node. The node has several methods to extract this information: :meth:`get_outputs() <aiida.orm.implementation.general.node.AbstractNode.get_outputs>`, :meth:`get_outputs_dict() <aiida.orm.implementation.general.node.AbstractNode.get_outputs_dict>`, :meth:`get_inputs() <aiida.orm.implementation.general.node.AbstractNode.get_inputs>` and :meth:`get_inputs_dict() <aiida.orm.implementation.general.node.AbstractNode.get_inputs_dict>`. The most practical way to access this information, especially when working on the ``verdi shell``, is by means of the ``inp`` and ``out`` attributes.

The ``inp`` attribute can be used to list and access the nodes with a direct link to 
``node`` in input. The names of the input links can be printed by ``list(node.inp)`` or interactively by ``node.inp. + TAB``. As an example, suppose that ``node`` has an input ``KpointsData`` object under the linkname ``kpoints``. The command
::

    node.inp.kpoints
  
returns the ``KpointsData`` object.

Similarly the ``out`` attribute can be used to display the names of links in output from ``node`` and access these nodes. Suppose that ``node`` has an output ``FolderData`` with linkname ``retrieved``, then the command
::

  node.out.retrieved
  
returns the ``FolderData`` object. 

.. note:: 
    For the input, there can be only one object for a given linkname. In contrast, there can be more than one output object with the same linkname. For example, a code object can be used by several calculations with the same linkname ``code``. For this reason, we append the string ``_pk`` indicating the pk of the output code to the linkname. A linkname without ``_pk`` still exists, and refers to the oldest link. 
    
    As an example, imagine that ``node`` is a code, which is used by calculation #18 and #19. The linknames shown by ``node.out`` are
    ::
  
        node.out.  >>
          * code
          * code_18
          * code_19
    
    The attributes ``node.out.code_18`` and ``node.out.code_19`` will return two different calculation objects, and ``node.out.code`` will return the older one of the two. 

