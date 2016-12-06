##################################
Getting parsed calculation results
##################################

In this section, we describe how to get the results of a calculation, after AiiDA
parsed the output of the calculation.

When a calculation is done on the remote computer, AiiDA will retrieve the results and try to parse the results with the default parser, if one is available for the given calculation. These results are stored in new nodes, and connected as output of the calculation. Of course, it is possible for a given calculation to check output nodes and get their content. However, AiiDA provides a way to directly access the results, using the :py:class:`aiida.orm.calculation.job.CalculationResultManager<.CalculationResultManager>` class, described in the next section.

The CalculationResultManager
+++++++++++++++++++++++++++++

Prerequisites
-------------

Before getting the calculation results, we need a correctly finished and parsed :class:`.JobCalculation`. For example this can be a Quantum ESPRESSO ``pw.x`` calculation. You can load such a calculation -- we'll call it ``calc`` -- with the command

.. code :: python

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


