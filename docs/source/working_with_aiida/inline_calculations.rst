Inline calculations
+++++++++++++++++++
If an operation is extremely fast to be run, this can be done directly in
Python, without being submitted to a cluster.
However, this operation takes one (or more) input data nodes, and creates new
data nodes, the operation itself is not recorded in the database, and provenance
is lost. In order to put a Calculation object inbetween, we define the
:py:class:`CalcFunctionNode <aiida.orm.nodes.process.calculation.calcfunction.CalcFunctionNode>`
class, that is used as the class for these calculations that are run "in-line".

We also provide a wrapper (that also works as a decorator of a function),
:py:func:`~aiida.engine.processes.functions.calcfunction`. This can be used
to wrap suitably defined function, so that after their execution,
a node representing their execution is stored in the DB, and suitable input
and output nodes are also stored.

.. note:: See the documentation of this function for further documentation of
  how it should be used, and of the requirements for the wrapped function.
