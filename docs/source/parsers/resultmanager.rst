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
:py:class:`aiida.orm.calculation.CalculationResourceManager` class, described in the next section.

The Calculation ResultManager
+++++++++++++++++++++++++++++
Each calculation has a ``res`` attribute that is a CalculationResourceManager object and
gives direct access to parsed data. 


