.. _how-to:workflows:

*******************************
How to run multi-step workflows
*******************************


.. _how-to:workflows:write:

Writing workflows
=================

`#3991`_


.. _how-to:workflows:run:

Running a predefined workflow
=============================

The first step to running a predefined workflow is loading the work function or work chain class that defines the workflow you want to run.
The recommended method for loading a workflow is using the ``WorkflowFactory``, for example:

.. code-block:: python

    from aiida.plugins import WorkflowFactory
    add_and_multiply = WorkflowFactory('arithmetic.add_multiply')
    MultiplyAndAddWorkChain = WorkflowFactory('arithmetic.multiply_add')

This is essentially the same as importing the workflow from its respective module, but using the ``WorkflowFactory`` has the advantage that the entry point will not change when the packages or plugins are reorganised.
This means your code is less likely to break when updating AiiDA or the plugin that supplies the workflow.
The input argument of the ``WorkflowFactory`` is the so-called *entry point*.
For each workflow, the entry point usually starts with the name of the plugin package (here ``arithmetic``), followed by a dot and the string identifying the workflow (here ``multiplyadd``).

The list of installed plugins can be easily accessed via the verdi CLI:

.. code-block:: console

    $ verdi plugin list

To see the list of ``WorkChain`` entry points, simply use:

.. code-block:: console

    $ verdi plugin list aiida.workflows

By further specifying the entry point of the workflow, you can see its description, inputs, outputs and exit codes:

.. code-block:: console

    $ verdi plugin list aiida.workflows arithmetic.multiplyadd

Work functions
--------------

Running a work function is as simple as calling a typical Python function: simply call it with the required input arguments:

.. code-block:: python

    add_and_multiply = WorkflowFactory('arithmetic.add_multiply')
    Int = DataFactory('int')

    result = add_and_multiply(Int(2), Int(3), Int(5))

Here, the ``add_and_multiply`` work function returns the output ``Int`` node and we assign it to the variable ``result``.
Note that the input arguments of a work function must be an instance of ``Data`` node, or any of its subclasses.
Just calling the ``add_and_multiply`` function with regular integers will result in a ``ValueError``, as these cannot be stored in the provenance graph.

.. note::

    Although the example above shows the most straightforward way to run the ``add_and_multiply`` work function, there are several other ways of running processes that can return more than just the result.
    For example, the ``run_get_node`` function from the AiiDA engine returns both the result of the workflow and the work function node.
    See the :ref:`corresponding topics section for more details <topics:processes:usage:launching>`.

Work chains
-----------

To launch a work chain, you can either use the ``run`` or ``submit`` functions from the AiiDA engine.
For either function, you need to provide the class of the work chain as the first argument, followed by the inputs as keyword arguments.
Using the ``run`` function, or "running", a work chain means it is executed in the same system process as the interpreter in which it is launched:

.. code-block:: python

    from aiida.engine import run
    from aiida.plugins import WorkflowFactory, DataFactory
    Int = DataFactory('int')
    MultiplyAndAddWorkChain = WorkflowFactory('arithmetic.multiply_add')

    add_code = load_code(label='add')

    results = run(MultiplyAndAddWorkChain, x=Int(2), y=Int(3), z=Int(5), code=add_code)

Alternatively, you can first construct a dictionary of the inputs, and pass it to the ``run`` function by taking advantage of `Python's automatic keyword expansion <https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists>`_:

.. code-block:: python

    inputs = {'x': Int(1), 'y': Int(2), 'z': Int(3), 'code': add_code}
    results = run(MultiplyAndAddWorkChain, **inputs)

This is particularly useful in case you have a workflow with a lot of inputs.
In both cases, running the ``MultiplyAddWorkChain`` workflow returns the **results** of the workflow, i.e. a dictionary of the nodes that are produced as outputs, where the keys of the dictionary correspond to the labels of each respective output.

.. note::

    Similar to other processes, there are multiple functions for launching a work chain.
    See the section on :ref:`launching processes for more details<topics:processes:usage:launching>`.

Since *running* a workflow will block the interpreter, you will have to wait until the workflow is finished before you get back control.
Moreover, you won't be able to turn your computer or even your terminal off until the workflow has fully terminated, and it is difficult to run multiple workflows in parallel.
So, it is advisable to *submit* more complex or longer work chains to the daemon:

.. code-block:: python

    from aiida.engine import submit
    Int = DataFactory('int')
    MultiplyAndAddWorkChain = WorkflowFactory('arithmetic.multiplyadd')

    add_code = load_code(label='add')
    inputs = {'x': Int(1), 'y': Int(2), 'z': Int(3), 'code': add_code}

    workchain_node = submit(MultiplyAndAddWorkChain, **inputs)

Note that when using ``submit`` the work chain is not run in the local interpreter but is sent off to the daemon and you get back control instantly.
This allows you to submit multiple work chains at the same time and the daemon will start working on them in parallel.
Once the ``submit`` call returns, you will not get the result as with ``run``, but you will get the **node** that represents the work chain.
This is because at that point in time, the results do not exist yet, because the work chain has not finished.
In addition to making it easy to execute multiple work chains in parallel, submitting work chains also allows you to shut down your computer.
The daemon will always save the progress of the work chains that it is managing such that if it is stopped, it can restart where it left off.

.. important::

    In contrast to work chains, work *functions* cannot be submitted to the daemon, and hence can only be *run*.

If you are unfamiliar with the inputs of a particular ``WorkChain``, a convenient tool for setting up the work chain is the :ref:`process builder<topics:processes:usage:builder>`.
This can be obtained by using the ``get_builder()`` method, which is implemented for every ``CalcJob`` and ``WorkChain``:

.. code-block:: python

    MultiplyAddWorkChain = WorkflowFactory('arithmetic.multiplyadd')
    builder = MultiplyAddWorkChain.get_builder()

To explore the inputs of the work chain, you can use tab autocompletion by typing ``builder.`` and then hitting ``TAB``.
If you want to get more details on a specific input, you can simply add a ``?`` and press enter:

.. code-block:: ipython

    In [3]: builder.x?
    Type:        property
    String form: <property object at 0x119ad2dd0>
    Docstring:   {"name": "x", "required": "True", "valid_type": "<class 'aiida.orm.nodes.data.int.Int'>", "non_db": "False"}

Here you can see that the ``x`` input is required, needs to be of the ``Int`` type and is stored in the database (``"non_db": "False"``).

Using the builder, the inputs of the ``WorkChain`` can be provided one by one:

.. code-block:: python

    builder.code = load_code(label='add')
    builder.x = Int(2)
    builder.y = Int(3)
    builder.z = Int(5)

Once the *required* inputs of the workflow have been provided to the builder, you can either run the work chain or submit it to the daemon:

.. code-block:: python

    from aiida.engine import submit

    workchain_node = submit(builder)

.. note::

    For more detail on the process builder, see the :ref:`corresponding topics section<topics:processes:usage:builder>`.


.. _how-to:workflows:extend:

Extending workflows
===================

`#3993`_


.. _#3991: https://github.com/aiidateam/aiida-core/issues/3991
.. _#3992: https://github.com/aiidateam/aiida-core/issues/3992
.. _#3993: https://github.com/aiidateam/aiida-core/issues/3993
