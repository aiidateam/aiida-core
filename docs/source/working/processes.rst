.. _working_processes:

*********
Processes
*********

Before you start working with processes, make sure you have read and understood the :ref:`basic concept<concepts_processes>`.
This section will explain the aspects of working with processes that apply to all the various types of processes.
Details that only pertain to a specific sub type of process, will be documented in their respective sections:

    * :ref:`calculation functions<working_calcfunctions>`
    * :ref:`calculation jobs<working_calcjobs>`
    * :ref:`work functions<working_workfunctions>`
    * :ref:`work chains<working_workchains>`


.. _working_processes_defining:

Defining processes
==================

.. _working_process_spec:

Process specification
---------------------
How a process defines the inputs that it requires or can optionally take, depends on the process type.
The inputs of :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` and :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain` are given by the :py:class:`~aiida.engine.processes.process_spec.ProcessSpec` class, which is defined though  the :py:meth:`~aiida.engine.processes.process.Process.define` method.
For process functions, the :py:class:`~aiida.engine.processes.process_spec.ProcessSpec` is dynamically generated from the signature of the decorated function.
Therefore, to determine what inputs a process takes, one simply has to look at the process specification in the ``define`` method or the function signature.
For the :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` and :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain` there is also the concept of the :ref:`process builder<working_process_builder>`, which will allow one to inspect the inputs with tab-completion and help strings in the shell.

`Issue [#2625] <https://github.com/aiidateam/aiida_core/issues/2625>`_

.. _working_process_metadata:

Process metadata
----------------

Each process, in addition to the normal inputs defined through its process specifcation, can take optional 'metadata'.
These metadata differ from inputs in the sense that they are not nodes that will show up as inputs in the provenance graph of the executed process.
Rather, these are inputs that slightly modify the behavior of the process or allow to set attributes on the process node that represents its execution.
The following metadata inputs are available for *all* process classes:

    * ``label``: will set the label on the ``ProcessNode``
    * ``description``: will set the description on the ``ProcessNode``
    * ``store_provenance``: boolean flag, by default ``True``, that when set to ``False``, will ensure that the execution of the process **is not** stored in the provenance graph

Sub classes of the :py:class:`~aiida.engine.processes.process.Process` class can specify further metadata inputs, refer to their specific documentation for details.
To pass any of these metadata options to a process, simply pass them in a dictionary under the key ``metadata`` in the inputs when launching the process.
How a process can be launched is explained the following section.


.. _working_processes_launching:

Launching processes
===================
Any process can be launched by 'running' or 'submitting' it.
Running means to run the process in the current python interpreter in a blocking way, whereas submitting means to send it to a daemon worker over RabbitMQ.
For long running processes, such as calculation jobs or complex workflows, it is best advised to submit to the daemon.
This has the added benefit that it will directly return control to your interpreter and allow the daemon to save intermediate progress during checkpoints and reload the process from those if it has to restart.
Running processes can be useful for trivial computational tasks, such as simple calcfunctions or workfunctions, or for debugging and testing purposes.

.. _working_processes_launch:

Process launch
--------------

To launch a process, one can use the free functions that can be imported from the :py:mod:`aiida.engine` module.
There are four different functions:

    * :py:func:`~aiida.engine.launch.run`
    * :py:func:`~aiida.engine.launch.run_get_node`
    * :py:func:`~aiida.engine.launch.run_get_pk`
    * :py:func:`~aiida.engine.launch.submit`

As the name suggest, the first three will 'run' the process and the latter will 'submit' it to the daemon.
Running means that the process will be executed in the same interpreter in which it is launched, blocking the interpreter, until the process is terminated.
Submitting to the daemon, in contrast, means that the process will be sent to the daemon for execution, and the interpreter is released straight away.

All functions have the exact same interface ``launch(process, **inputs)`` where:

    * ``process`` is the process class or process function to launch
    * ``inputs`` are the inputs as keyword arguments to pass to the process.

What inputs can be passed depends on the exact process class that is to be launched.
For example, when we want to run an instance of the :py:class:`~aiida.calculations.plugins.arithmetic.add.ArithmeticAddCalculation` process, which takes two :py:class:`~aiida.orm.nodes.data.int.Int` nodes as inputs under the name ``x`` and ``y`` [#f1]_, we would do the following:

.. include:: include/snippets/processes/launch/launch_submit.py
    :code: python

The function will submit the calculation to the daemon and immediately return control to the interpreter, returning the node that is used to represent the process in the provenance graph.

.. warning::
    Process functions, i.e. python functions decorated with the ``calcfunction`` or ``workfunction`` decorators, **cannot be submitted** but can only be run.

The ``run`` function is called identically:

.. include:: include/snippets/processes/launch/launch_run.py
    :code: python

except that it does not submit the process to the daemon, but executes it in the current interpreter, blocking it until the process is terminated.
The return value of the ``run`` function is also **not** the node that represents the executed process, but the results returned by the process, which is a dictionary of the nodes that were produced as outputs.
If you would still like to have the process node or the pk of the process node you can use one of the following variants:

.. include:: include/snippets/processes/launch/launch_run_alternative.py
    :code: python

Finally, the :py:func:`~aiida.engine.launch.run` launcher has two attributes ``get_node`` and ``get_pk`` that are simple proxies to the :py:func:`~aiida.engine.launch.run_get_node` and :py:func:`~aiida.engine.launch.run_get_pk` methods.
This is a handy shortcut, as now you can choose to use any of the three variants with just a single import:

.. include:: include/snippets/processes/launch/launch_run_shortcut.py
    :code: python

If you want to launch a process class that takes a lot more inputs, often it is useful to define them in a dictionary and use the python syntax ``**`` that automatically expands it into keyword argument and value pairs.
The examples used above would look like the following:

.. include:: include/snippets/processes/launch/launch_submit_dictionary.py
    :code: python

Process functions, i.e. :ref:`calculation functions<concepts_calcfunctions>` and :ref:`work functions<concepts_workfunctions>`, can be launched like any other process as explained above, with the only exception that they **cannot be submitted**.
In addition to this limitation, process functions have two additional methods of being launched:

 * Simply *calling* the function
 * Using the internal run method attributes

Using a calculation function to add two numbers as an example, these two methods look like the following:

.. include:: include/snippets/processes/launch/launch_process_function.py
    :code: python


.. _working_process_builder:

Process builder
---------------
As explained in a :ref:`previous section<working_process_spec>`, the inputs for a :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob` and :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain` are defined in the :py:meth:`~aiida.engine.processes.process.Process.define` method.
To know then what inputs they take, one would have to read the implementation, which can be annoying if you are not a developer.
To simplify this process, these two process classes provide a utility called the 'process builder'.
The process builder is essentially a tool that helps you build the inputs for the specific process class that you want to run.
To get a *builder* for a particular ``CalcJob`` or a ``WorkChain`` implementation, all you need is the class itself, which can be loaded through the :py:class:`~aiida.plugins.factories.CalculationFactory` and :py:class:`~aiida.plugins.factories.WorkflowFactory`, respectively.
Let's take the :py:class:`~aiida.calculations.plugins.arithmetic.add.ArithmeticAddCalculation` as an example::

    ArithmeticAddCalculation = CalculationFactory('arithmetic.add')
    builder = ArithmeticAddCalculation.get_builder()

The string ``arithmetic.add`` is the entry point of the ``ArithmeticAddCalculation`` and passing it to the ``CalculationFactory`` will return the corresponding class.
Calling the ``get_builder`` method on that class will return an instance of the :py:class:`~aiida.engine.processes.builder.ProcessBuilder` class that is tailored for the ``ArithmeticAddCalculation``.
The builder will help you in defining the inputs that the ``ArithmeticAddCalculation`` requires and has a few handy tools to simplify this process.

To find out which inputs the builder exposes, you can simply use tab completion.
In an interactive python shell, by simply typing ``builder.`` and hitting the tab key, a complete list of all the available inputs will be shown.
Each input of the builder can also show additional information about what sort of input it expects.
In an interactive shell, you can get this information to display as follows::

    builder.code?
    Type:        property
    String form: <property object at 0x7f04c8ce1c00>
    Docstring:
        "name": "code",
        "required": "True"
        "non_db": "False"
        "valid_type": "<class 'aiida.orm.nodes.data.code.Code'>"
        "help": "The Code to use for this job.",

In the ``Docstring`` you will see a ``help`` string that contains more detailed information about the input port.
Additionally, it will display a ``valid_type``, which when defined shows which data types are expected.
If a default value has been defined, that will also be displayed.
The ``non_db`` attribute defines whether that particular input will be stored as a proper input node in the database, if the process is submitted.

Defining an input through the builder is as simple as assigning a value to the attribute.
The following example shows how to set the ``parameters`` input, as well as the ``description`` and ``label`` metadata inputs::

    builder.metadata.label = 'This is my calculation label'
    builder.metadata.description = 'An example calculation to demonstrate the process builder'
    builder.x = Int(1)
    builder.y = Int(2)

If you evaluate the ``builder`` instance, simply by typing the variable name and hitting enter, the current values of the builder's inputs will be displayed::

    builder
    {
        'metadata': {
            'description': 'An example calculation to demonstrate the process builder',
            'label': 'This is my calculation label',
            'options': {},
        },
        'x': Int<uuid='a1798492-bbc9-4b92-a630-5f54bb2e865c' unstored>,
        'y': Int<uuid='39384da4-6203-41dc-9b07-60e6df24e621' unstored>
    }

In this example, you can see the value that we just set for the ``description`` and the ``label``.
In addition, it will also show any namespaces, as the inputs of processes support nested namespaces, such as the ``metadata.options`` namespace in this example.
Note that nested namespaces are also all autocompleted, and you can traverse them recursively with tab-completion.

All that remains is to fill in all the required inputs and we are ready to launch the process builder.
When all the inputs have been defined for the builder, it can be used to actually launch the ``Process``.
The process can be launched by passing the builder to any of the free functions :py:mod:`~aiida.engine.launch` module, just as you would do a normal process as :ref:`described above<working_processes_launching>`, i.e.:

.. include:: include/snippets/processes/launch/launch_builder.py
    :code: python

Note that the process builder is in principle designed to be used in an interactive shell, as there is where the tab-completion and automatic input documentation really shines.
However, it is perfectly possible to use the same builder in scripts where you simply use it as an input container, instead of a plain python dictionary.


.. _working_processes_monitoring:

Monitoring processes
====================
When you have launched a process, you may want to investigate its status, progression and the results.
The :ref:`verdi<verdi_overview>` command line tool provides various commands to do just this.

verdi process list
------------------
Your first point of entry will be the ``verdi`` command ``verdi process list``.
This command will print a list of all active processes through the ``ProcessNode`` stored in the database that it uses to represent its execution.
A typical example may look something like the following:

.. code-block:: bash

      PK  Created     State           Process label                 Process status
    ----  ----------  ------------    --------------------------    ----------------------
     151  3h ago      ⏵ Running       ArithmeticAddCalculation
     156  1s ago      ⏹ Created       ArithmeticAddCalculation


    Total results: 2

The 'State' column is a concatenation of the ``process_state`` and the ``exit_status`` of the ``ProcessNode``.
By default, the command will only show active items, i.e. ``ProcessNodes`` that have not yet reached a terminal state.
If you want to also show the nodes in a terminal states, you can use the ``-a`` flag and call ``verdi process list -a``:

.. code-block:: bash

      PK  Created     State              Process label                  Process status
    ----  ----------  ---------------    --------------------------     ----------------------
     143  3h ago      ⏹ Finished [0]     add
     146  3h ago      ⏹ Finished [0]     multiply
     151  3h ago      ⏵ Running          ArithmeticAddCalculation
     156  1s ago      ⏹ Created          ArithmeticAddCalculation


    Total results: 4

For more information on the meaning of the 'state' column, please refer to the documentation of the :ref:`process state <concepts_process_state>`.
The ``-S`` flag let's you query for specific process states, i.e. issuing ``verdi process list -S created`` will return:

.. code-block:: bash

      PK  Created     State           Process label                  Process status
    ----  ----------  ------------    --------------------------     ----------------------
     156  1s ago      ⏹ Created       ArithmeticAddCalculation


    Total results: 1

To query for a specific exit status, one can use ``verdi process list -E 0``:

.. code-block:: bash

      PK  Created     State             Process label                 Process status
    ----  ----------  ------------      --------------------------    ----------------------
     143  3h ago      ⏹ Finished [0]    add
     146  3h ago      ⏹ Finished [0]    multiply


    Total results: 2

This simple tool should give you a good idea of the current status of running processes and the status of terminated ones.
For a complete list of all the available options, please refer to the documentation of :ref:`verdi process<verdi_process>`.

If you are looking for information about a specific process node, the following three commands are at your disposal:

 * ``verdi process report`` gives a list of the log messages attached to the process
 * ``verdi process status`` print the call hierarchy of the process and status of all its nodes
 * ``verdi process show`` print details about the status, inputs, outputs, callers and callees of the process

In the following sections, we will explain briefly how the commands work.
For the purpose of example, we will show the output of the commands for a completed ``PwBaseWorkChain`` from the ``aiida-quantumespresso`` plugin, which simply calls a ``PwCalculation``.

verdi process report
--------------------
The developer of a process can attach log messages to the node of a process through the :py:meth:`~aiida.engine.processes.process.Process.report` method.
The ``verdi process report`` command will display all the log messages in chronological order:

.. code-block:: bash

    2018-04-08 21:18:51 [164 | REPORT]: [164|PwBaseWorkChain|run_calculation]: launching PwCalculation<167> iteration #1
    2018-04-08 21:18:55 [164 | REPORT]: [164|PwBaseWorkChain|inspect_calculation]: PwCalculation<167> completed successfully
    2018-04-08 21:18:56 [164 | REPORT]: [164|PwBaseWorkChain|results]: work chain completed after 1 iterations
    2018-04-08 21:18:56 [164 | REPORT]: [164|PwBaseWorkChain|on_terminated]: remote folders will not be cleaned

The log message will include a timestamp followed by the level of the log, which is always ``REPORT``.
The second block has the format ``pk|class name|function name`` detailing information about, in this case, the work chain itself and the step in which the message was fired.
Finally, the message itself is displayed.
Of course how many messages are logged and how useful they are is up to the process developer.
In general they can be very useful for a user to understand what has happened during the execution of the process, however, one has to realize that each entry is stored in the database, so overuse can unnecessarily bloat the database.


verdi process status
--------------------
This command is most useful for ``WorkChain`` instances, but also works for ``CalcJobs``.
One of the more powerful aspect of work chains, is that they can call ``CalcJobs`` and other ``WorkChains`` to create a nested call hierarchy.
If you want to inspect the status of a work chain and all the children that it called, ``verdi process status`` is the go-to tool.
An example output is the following:

.. code-block:: bash

    PwBaseWorkChain <pk=164> [ProcessState.FINISHED] [4:results]
        └── PwCalculation <pk=167> [FINISHED]

The command prints a tree representation of the hierarchical call structure, that recurses all the way down.
In this example, there is just a single ``PwBaseWorkChain`` which called a ``PwCalculation``, which is indicated by it being indented one level.
In addition to the call tree, each node also shows its current process state and for work chains at which step in the outline it is.
This tool can be very useful to inspect while a work chain is running at which step in the outline it currently is, as well as the status of all the children calculations it called.


verdi process show
------------------
Finally, there is a command that displays detailed information about the ``ProcessNode``, such as its inputs, outputs and the optional other processes it called and or was called by.
An example output for a ``PwBaseWorkChain`` would look like the following:

.. code-block:: bash

    Property       Value
    -------------  ------------------------------------
    type           WorkChainNode
    pk             164
    uuid           08bc5a3c-da7d-44e0-a91c-dda9ddcb638b
    label
    description
    ctime          2018-04-08 21:18:50.850361+02:00
    mtime          2018-04-08 21:18:50.850372+02:00
    process state  ProcessState.FINISHED
    exit status    0
    code           pw-v6.1

    Inputs            PK  Type
    --------------  ----  -------------
    parameters       158  Dict
    structure        140  StructureData
    kpoints          159  KpointsData
    pseudo_family    161  Str
    max_iterations   163  Int
    clean_workdir    160  Bool
    options          162  Dict

    Outputs              PK  Type
    -----------------  ----  -------------
    output_band         170  BandsData
    remote_folder       168  RemoteData
    output_parameters   171  Dict
    output_array        172  ArrayData

    Called      PK  Type
    --------  ----  -------------
    CALL       167  PwCalculation

    Log messages
    ---------------------------------------------
    There are 4 log messages for this calculation
    Run 'verdi process report 164' to see them

This overview should give you all the information if you want to inspect a process' inputs and outputs in closer detail as it provides you their pk's.


.. _working_processes_manipulating:

Manipulating processes
======================
To understand how one can manipulate running processes, one has to understand the principles of a :ref:`process' lifetime<concepts_process_lifetime>` and :ref:`checkpoints<concepts_process_checkpoints>` first, so be sure to have read those sections first.

verdi process pause/play/kill
-----------------------------

`Issue [#2626] <https://github.com/aiidateam/aiida_core/issues/2626>`_

.. rubric:: Footnotes

.. [#f1] Note that the :py:class:`~aiida.calculations.plugins.arithmetic.add.ArithmeticAddCalculation` process class also takes a ``code`` as input, but that has been omitted for the purposes of the example.