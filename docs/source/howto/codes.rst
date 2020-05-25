.. _how-to:codes:

*************************
How to run external codes
*************************


.. _how-to:codes:plugin:

Interfacing external codes
==========================

`#3986`_

In order to work with an external simulation code in AiiDA, you need a calculation input plugin (subclassing the :py:class:`~aiida.engine.CalcJob` class) and an output parser plugin (subclassing the :py:class:`~aiida.parsers.Parser` class):

Before starting to write a plugin, check on the `aiida plugin registry <https://aiidateam.github.io/aiida-registry/>`_ whether a plugin for your code is already available.

Design guidelines
------------------

 * | **Start simple.**
   | Make use of existing classes like :py:class:`~aiida.orm.nodes.data.dict.Dict`, :py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...
   | Write only what is necessary to pass information from and to AiiDA.
 * | **Don't break data provenance.**
   | Store *at least* what is needed for full reproducibility.
 * | **Parse what you want to query for.**
   | Make a list of which information to:

     #. parse into the database for querying (:py:class:`~aiida.orm.nodes.data.dict.Dict`, ...)
     #. store in the file repository for safe-keeping (:py:class:`~aiida.orm.nodes.data.singlefile.SinglefileData`, ...)
     #. leave on the computer where the calculation ran (:py:class:`~aiida.orm.nodes.data.remote.RemoteData`, ...)

 * | **Expose the full functionality.**
   | Standardization is good but don't artificially limit the power of a code you are wrapping - or your users will get frustrated.
   | If the code can do it, there should be *some* way to do it with your plugin.

 * | **Don't rely on AiiDA internals.**
   | AiiDA's :ref:`public python API<python_api_public_list>` includes anything that you can import via ``from aiida.module import thing``.
   | Functionality at deeper nesting levels is not considered part of the public API and may change between minor AiiDA releases, breaking your plugin.


.. _how-to:codes:run:

Running external codes
======================

The process of running an external code through AiiDA involves loading and instantiating the appropriate ``CalcJob`` wrapping class for the code, filling the inputs necessary, and then running or submitting the constructed object.

If the ``CalcJob`` has been registered in AiiDA (see section :ref:`on how to register plugins<how-to:plugins:entrypoints>`) you can use the ``CalculationFactory``:

.. code-block:: python

    from aiida.plugins import CalculationFactory
    calculation_builder = CalculationFactory('arithmetic.add').get_builder()

Otherwise, you can just load the class and get the builder directly:

.. code-block:: python

    from aiida.calculations.plugins.arithmetic.add import ArithmeticAddCalculation
    calculation_builder = ArithmeticAddCalculation.get_builder()

Then you need to start filling out the builder with all the inputs that you need to specify to run your calculation.
In the case of the ``ArithmeticAddCalculation``, there are 4 required inputs:

.. code-block:: python
    :linenos:

    # Specific for ArithmeticAdd
    spec.input('x', valid_type=(orm.Int, orm.Float), help='The left operand.')
    spec.input('y', valid_type=(orm.Int, orm.Float), help='The right operand.')

    # General for all CalcJobs
    spec.input('code', valid_type=orm.Code, help='The `Code` to use for this job.')
    spec.input('metadata.options.resources', valid_type=dict, required=True, validator=validate_resources,
        help='Set the dictionary of resources to be used by the scheduler plugin, like the number of nodes, '
             'cpus etc. This dictionary is scheduler-plugin dependent. Look at the documentation of the '
             'scheduler for more details.')

The first three are input nodes (lines 2, 3 and 6), so you can either use nodes that are already in your database (you can query for them, load them, etc.) or you can create new nodes and these will be automatically stored when starting the calculation.

.. code-block:: python

    code_node = orm.load_node(100)
    num1_node = orm.Int(17)
    num2_node = orm.Int(11)

    calculation_builder.code = code_node
    calculation_builder.x = num1_node
    calculation_builder.y = num2_node

The last input (line 7) is not a node but a dictionary containing information about the resources required from the remote machine to run the code.
It will be stored as a property of the ``CalcJob`` node, and should at least contain the following two keys:

.. code-block:: python

    calculation_builder.metadata.options.resources = {
        'num_machines': 1,
        'tot_num_mpiprocs': 1,
    }

Now everything is in place and you are ready to perform the calculation, which you can do in two different ways.
The first one is blocking and will return a dictionary containing all the output nodes (keyed after their label, so in this case these should be: "remote_folder", "retrieved" and "sum") that you can safely inspect and work with:

.. code-block:: python

    from aiida.engine import run
    output_dict = run(calculation_builder)
    sum_node = output_dict['sum']

The second one is non blocking, as you will be submitting it to the daemon and immediately getting control in the interpreter:

.. code-block:: python

    from aiida.engine import submit
    calculation_node = submit(calculation_builder)

As the variable name suggests, the return value for the submit method is the calculation node that is stored in the database.
In this case the underlying calculation is not guaranteed to have finished, so it is often convenient to keep track of it using the verdi command line interface:

.. code-block:: bash

    $ verdi process list

Additionally, you might want to check and verify your inputs before actually running or submitting a calculation.
You can do so by specifying to use a ``dry_run``, which will create the running folder in the current directory (``submit_test/[date]-0000[x]``) so the user can inspect the integrity of the inputs generated:

.. code-block:: bash

    calculation_builder.metadata.dry_run = True
    calculation_builder.metadata.store_provenance = False
    run(calculation_builder)

.. _how-to:codes:caching:

Using caching to save computational resources
=============================================

`#3988`_


.. _how-to:codes:scheduler:

Adding support for a custom scheduler
=====================================

`#3989`_


.. _how-to:codes:transport:

Adding support for a custom transport
=====================================

`#3990`_


.. _#3986: https://github.com/aiidateam/aiida-core/issues/3986
.. _#3987: https://github.com/aiidateam/aiida-core/issues/3987
.. _#3988: https://github.com/aiidateam/aiida-core/issues/3988
.. _#3989: https://github.com/aiidateam/aiida-core/issues/3989
.. _#3990: https://github.com/aiidateam/aiida-core/issues/3990
