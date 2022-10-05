.. _how-to:run-workflows:

*******************************
How to run multi-step workflows
*******************************

Launching a predefined workflow
===============================

The first step to launching a predefined workflow is loading the work function or work chain class that defines the workflow you want to run.
The recommended method for loading a workflow is using the ``WorkflowFactory``, for example:

.. code-block:: python

    from aiida.plugins import WorkflowFactory
    add_and_multiply = WorkflowFactory('core.arithmetic.add_multiply')
    MultiplyAddWorkChain = WorkflowFactory('core.arithmetic.multiply_add')

This is essentially the same as importing the workflow from its respective module, but using the ``WorkflowFactory`` has the advantage that the so called *entry point* (e.g. ``'core.arithmetic.multiply_add'``) will not change when the packages or plugins are reorganised.
This means your code is less likely to break when updating AiiDA or the plugin that supplies the workflow.

The list of installed plugins can be easily accessed via the verdi CLI:

.. code-block:: console

    $ verdi plugin list

To see the list of workflow entry points, simply use:

.. code-block:: console

    $ verdi plugin list aiida.workflows

By further specifying the entry point of the workflow, you can see its description, inputs, outputs and exit codes:

.. code-block:: console

    $ verdi plugin list aiida.workflows core.arithmetic.multiply_add

Work functions
--------------

Running a work function is as simple as calling a typical Python function: simply call it with the required input arguments:

.. code-block:: python

    from aiida.plugins import WorkflowFactory, DataFactory
    add_and_multiply = WorkflowFactory('core.arithmetic.add_multiply')
    Int = DataFactory('core.int')

    result = add_and_multiply(Int(2), Int(3), Int(5))

Here, the ``add_and_multiply`` work function returns the output ``Int`` node and we assign it to the variable ``result``.
Note that the input arguments of a work function must be an instance of ``Data`` node, or any of its subclasses.
Just calling the ``add_and_multiply`` function with regular integers will result in a ``ValueError``, as these cannot be stored in the provenance graph.

.. versionadded:: 2.1

    If a function argument is a Python base type (i.e. a value of type ``bool``, ``dict``, ``Enum``, ``float``, ``int``, ``list`` or ``str``), it can be passed straight away to the function, without first having to wrap it in the corresponding AiiDA data type.
    That is to say, you can run the example above also as:

    .. code-block:: python

        result = add_and_multiply(2, 3, 5)

    and AiiDA will recognize that the arguments are of type ``int`` and automatically wrap them in an ``Int`` node.


.. note::

    Although the example above shows the most straightforward way to run the ``add_and_multiply`` work function, there are several other ways of running processes that can return more than just the result.
    For example, the ``run_get_node`` function from the AiiDA engine returns both the result of the workflow and the work function node.
    See the :ref:`corresponding topics section for more details <topics:processes:usage:launching>`.

Work chains
-----------

To launch a work chain, you can either use the ``run`` or ``submit`` functions.
For either function, you need to provide the class of the work chain as the first argument, followed by the inputs as keyword arguments.
When "running the work chain" (using the ``run`` function), it will be executed in the same system process as the interpreter in which it is launched:

.. code-block:: python

    from aiida.engine import run
    from aiida.plugins import WorkflowFactory, DataFactory
    Int = DataFactory('core.int')
    MultiplyAddWorkChain = WorkflowFactory('core.arithmetic.multiply_add')

    add_code = load_code(label='add')

    results = run(MultiplyAddWorkChain, x=Int(2), y=Int(3), z=Int(5), code=add_code)

Alternatively, you can first construct a dictionary of the inputs, and pass it to the ``run`` function by taking advantage of `Python's automatic keyword expansion <https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists>`_:

.. code-block:: python

    inputs = {'x': Int(1), 'y': Int(2), 'z': Int(3), 'code': add_code}
    results = run(MultiplyAddWorkChain, **inputs)

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
    from aiida.plugins import WorkflowFactory, DataFactory
    Int = DataFactory('core.int')
    MultiplyAddWorkChain = WorkflowFactory('core.arithmetic.multiply_add')

    add_code = load_code(label='add')
    inputs = {'x': Int(1), 'y': Int(2), 'z': Int(3), 'code': add_code}

    workchain_node = submit(MultiplyAddWorkChain, **inputs)

Note that when using ``submit`` the work chain is not run in the local interpreter but is sent off to the daemon and you get back control instantly.
This allows you to submit multiple work chains at the same time and the daemon will start working on them in parallel.
Once the ``submit`` call returns, you will not get the result as with ``run``, but you will get the **node** that represents the work chain.
Submitting a work chain instead of directly running it not only makes it easier to execute multiple work chains in parallel, but also ensures that the progress of a workchain is not lost when you restart your computer.

.. note::

    As of AiiDA v1.5.0, it is possible to submit both work *chains* and work *functions* to the daemon. Older versions only allow the submission of work *chains*, whereas work *functions* cannot be submitted to the daemon, and hence can only be *run*.

If you are unfamiliar with the inputs of a particular ``WorkChain``, a convenient tool for setting up the work chain is the :ref:`process builder<topics:processes:usage:builder>`.
This can be obtained by using the ``get_builder()`` method, which is implemented for every ``CalcJob`` and ``WorkChain``:

.. code-block:: ipython

    In [1]: from aiida.plugins import WorkflowFactory, DataFactory
       ...: Int = DataFactory('core.int')
       ...: MultiplyAddWorkChain = WorkflowFactory('core.arithmetic.multiply_add')
       ...: builder = MultiplyAddWorkChain.get_builder()

To explore the inputs of the work chain, you can use tab autocompletion by typing ``builder.`` and then hitting ``TAB``.
If you want to get more details on a specific input, you can simply add a ``?`` and press enter:

.. code-block:: ipython

    In [2]: builder.x?
    Type:        property
    String form: <property object at 0x119ad2dd0>
    Docstring:   {"name": "x", "required": "True", "valid_type": "<class 'aiida.orm.nodes.data.int.Int'>", "non_db": "False"}

Here you can see that the ``x`` input is required, needs to be of the ``Int`` type and is stored in the database (``"non_db": "False"``).

Using the builder, the inputs of the ``WorkChain`` can be provided one by one:

.. code-block:: ipython

    In [3]: builder.code = load_code(label='add')
       ...: builder.x = Int(2)
       ...: builder.y = Int(3)
       ...: builder.z = Int(5)

Once the *required* inputs of the workflow have been provided to the builder, you can either run the work chain or submit it to the daemon:

.. code-block:: ipython

    In [4]: from aiida.engine import submit
       ...: workchain_node = submit(builder)

.. note::

    For more detail on the process builder, see the :ref:`corresponding topics section<topics:processes:usage:builder>`.

Now that you know how to run a pre-defined workflow, you may want to start :ref:`writing your own<how-to:write-workflows>`.
