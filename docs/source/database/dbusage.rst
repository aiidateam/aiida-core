=================================
Getting results, input and output
=================================

In this section, we describe how to get the results of a calculation after it has been parsed by AiiDA, or the input and output of a generic Node.

.. contents :: Contents
    :local:

Calculation results
===================

When a calculation is done on the remote computer, AiiDA will retrieve the results and try to parse the results with the default parser, if one is available for the given calculation. These results are stored in new nodes, and connected as output of the calculation. Of course, it is possible to :ref:`directly check the output nodes <db_input_output>` for a given calculation and get their content. However, AiiDA provides a way to directly access the results, using the :py:class:`aiida.orm.calculation.job.CalculationResultManager<.CalculationResultManager>` class, described in the next section.

The CalculationResultManager
+++++++++++++++++++++++++++++

Prerequisites
-------------

Before getting the calculation results, we need a correctly finished and parsed :class:`.JobCalculation`. For example this can be a Quantum ESPRESSO ``pw.x`` calculation. You can load such a calculation -- we'll call it ``calc`` -- with the command

.. code :: python
    
    from aiida.orm import load_node
    calc = load_node(YOURPK)

either in ``verdi shell``, or in a python script (as described :doc:`here <../examples/scripting>`). ``YOURPK`` should be substituted by a valid calculation PK in your database.

Using the :class:`.CalculationResultManager` instance
-----------------------------------------------------

Each :class:`.JobCalculation` has a ``res`` attribute that is a 
:class:`.CalculationResultManager` instance and
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
value simply as an attribute of the ``res`` :class:`.CalculationResultManager`. For instance, to get the final total energy, you can use
::

    print calc.res.energy

that will print the total energy in units of eV, as also stated in the ``energy_units`` key
::

    print calc.res.energy_units

Similarly, you can get any other parsed value, for any code that
provides a parser.

.. hint:: 
    The :class:`.CalculationResultManager` is also integrated with the iPython/verdi shell completion mechanism: if ``calc`` is a valid :class:`.JobCalculation`, you can type
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

Now, we want to find the nodes which have a direct link to this node. There are several methods to extract this information (for developers see all the methods and their docstring: ``get_outputs``, ``get_outputs_dict``, ``c.get_inputs`` and ``c.get_inputs_dict``). The most practical way to access this information, especially when working on the ``verdi shell``, is by means of the ``inp`` and ``out`` methods.

The ``inp`` method is used to list and access the nodes with a direct link to 
``node`` in input. The names of the input links can be printed by ``list(n.inp)`` or interactively by ``node.inp. + TAB``. As an example, suppose that ``node`` has an input ``KpointsData`` object under the linkname ``kpoints``. The command
::

  node.inp.kpoints
  
returns the ``KpointsData`` object.

Similar methods exists for the ``out`` method, which will display the names of links in output from ``node`` and can be used to access such output nodes. Suppose that ``node`` has an output ``FolderData`` with linkname ``retrieved``, than the command
::

  node.out.retrieved
  
returns the FolderData object. 

.. note:: 
    At variance with input, there can be more than one output objects with the same linkname (for example: a code object can be used by several calculations always with the same linkname ``code``). As such, for every output linkname, we append the string ``_pk``, with the pk of the output node. There is also a linkname without pk appended, which is assigned to the oldest link. As an example, imagine that ``node`` is a code, which is used by calculation #18 and #19, the linknames shown by ``node.out`` are::
  
        node.out.  >>
          * code
          * code_18
          * code_19
    
    The method ``node.out.code_18`` and ``node.out.code_19`` will return two different calculation objects, and ``node.out.code`` will return the oldest (the reference is the creation time) between calculation 18 and 19. If one calculation (say 18) exist only in output, there is then less ambiguity, and you are sure that the output of ``node.out.code`` coincides with ``node.out.code_18``. 

