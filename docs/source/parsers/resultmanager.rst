##################################
Getting parsed calculation results
##################################

In this section, we describe how to get the results of a calculation, after AiiDA
parsed the output of the calculation.

When a calculation is done on the remote computer, AiiDA will retrieve the results and
try to parse the results with the default parser, if one is available for the given calculation.
These results are stored in new nodes, and connected as output of the calculation.
Of course, it is possible for a given calculation to check output nodes and get their content, 
However, AiiDA provides a way to access directly the results, using the
:py:class:`aiida.orm.calculation.CalculationResultManager` class, described in the next section.

The CalculationResultManager
+++++++++++++++++++++++++++++
Each calculation has a ``res`` attribute that is a CalculationResultManager object and
gives direct access to parsed data. 

To use it, you can just use then::

  calc.res

that will however just return the class. You can however convert it to
a list, to get all the possible keys that were parsed. For intance, if
you consider a correctly finished Quantum ESPRESSO pw.x calculation ``calc``,
and you type (e.g. in ``verdi shell``, or in a python script)::

  print list(calc.res)

you will get something like this::

  [u'rho_cutoff', u'energy', u'energy_units', ...]

(the list of keys has been cut for clarity: you will get many more
keys).

Once you know which keys have been parsed, you can access the parsed
value simply as an attribute of the ``res`` ResultManager. For
instance, to get the final total energy, you can use::
  
  print calc.res.energy

that will print the total energy in units of eV, as also stated in the
``energy_units`` key::

  print calc.res.energy_units

Similarly, you can get any other parsed value, for any code that
provides a parser.

.. note:: the ``CalculationResultManager`` is also integrated with
   iPython/verdi shell completion mechanism: if ``calc`` is a valid
   calculation, you can type::
     
      calc.res.

   and then press the TAB key of the keyboard to get/complete the list of valid
   parsed properties for the calculation ``calc``.


