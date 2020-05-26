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

To run an external code with AiiDA, you will need to use an appropriate :ref:`calculation plugin <topics:plugins>` that knows how to transform the input nodes into the input files that the code expects, copy everything in the code's machine, run the calculation and retrieve the results.
This plugin would have already been created, either by you (see section on :ref:`interfacing external codes <how-to:codes:plugin>`) or by other AiiDA plugin-developers (available packages are listed in the `plugin registry <https://aiidateam.github.io/aiida-registry/>`_), and has been properly installed in your environment.
You can check which ones you have currently available:

.. code-block:: bash

    $ verdi plugin list aiida.calculations

As an example, we will show how to use the ``arithmetic.add`` plugin, which is a pre-installed plugin implemented in `bash` to sum two integers.
You can access it with the ``CalculationFactory``:

.. code-block:: python

    from aiida.plugins import CalculationFactory
    calculation_class = CalculationFactory('arithmetic.add')

Next, we provide the inputs for the code when running the calculation.
Use ``verdi plugin`` to determine what inputs a specific plugin expects:

.. code-block:: bash

    $ verdi plugin list aiida.calculations arithmetic.add

You will see that 3 inputs nodes are required: two containing the values to add up (``x``, ``y``) and one containing information about the specific code to execute (``code``).
If you already have these nodes in your database, you can get them by :ref:`querying for them <how-to:data:finding-data>` or using ``orm.load_node(<PK>)``.
Otherwise, you will need to create them as shown below (note that you `will` need to already have the ``localhost`` computer configured):

.. code-block:: python

    from aiida import orm
    code_node = orm.Code(remote_computer_exec=[localhost, '/bin/bash'])
    numx_node = orm.Int(17)
    numy_node = orm.Int(11)

To provide these as inputs to the calculations, we will now use the ``builder`` object that we can get from the class:

.. code-block:: python

    calculation_builder = calculation_class.get_builder()
    calculation_builder.code = code_node
    calculation_builder.x = numx_node
    calculation_builder.y = numy_node

Now everything is in place and ready to perform the calculation, which can be done in two different ways.
The first one is blocking and will return a dictionary containing all the output nodes (keyed after their label, so in this case these should be: "remote_folder", "retrieved" and "sum") that you can safely inspect and work with:

.. code-block:: python

    from aiida.engine import run
    output_dict = run(calculation_builder)
    sum_node = output_dict['sum']

The second one is non blocking, as you will be submitting it to the daemon and immediately getting control in the interpreter.
The return value in this case is the actual calculation node that is stored in the database.

.. code-block:: python

    from aiida.engine import submit
    calculation_node = submit(calculation_builder)

Note that, although you have access to the node, the underlying calculation `process` is not guaranteed to have finished when you get back control in the interpreter.
In order to keep track of it you can use the verdi command line interface:

.. code-block:: bash

    $ verdi process list

Performing a dry-run
--------------------

Additionally, you might want to check and verify your inputs before actually running or submitting a calculation.
You can do so by specifying to use a ``dry_run``, which will create all the input files in a local directory (``submit_test/[date]-0000[x]``) so you can inspect them before actually launching the calculation:

.. code-block:: python

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
