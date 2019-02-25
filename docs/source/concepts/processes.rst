.. _processes:

*********
Processes
*********

Anything that runs in AiiDA is an instance of the :py:class:`~aiida.engine.processes.process.Process` class.
The ``Process`` class contains all the information and logic to tell, whoever is handling it, how to run it to completion.
Typically the one responsible for running the processes is an instance of a :py:class:`~aiida.engine.runners.Runner`.
This can be a local runner or one of the daemon runners in case of the daemon running the process.

A good example of a process is the :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain` class, which is in fact a sub class of the :py:class:`~aiida.engine.processes.process.Process` class.
In the :ref:`workflows and workchains section <workchains_workfunctions>` you can see how the ``WorkChain`` defines how it needs to be run.
In addition to those run instructions, the ``WorkChain`` needs some sort of record in the database to store what happened during its execution.
For example it needs to record what its exact inputs were, the log messages that were reported and what the final outputs were.
For this purpose, every process will utilize an instance of a sub class of the :py:class:`~aiida.orm.nodes.process.ProcessNode` class.
This ``Calculation`` class is a sub class of :py:class:`~aiida.orm.nodes.Node` and serves as the record of the process' execution in the database and by extension the provenance graph.

It is very important to understand this division of labor.
A ``Process`` describes how something should be run, and the ``Calculation`` node serves as a mere record in the database of what actually happened during execution.
A good thing to remember is that while it is running, we are dealing with the ``Process`` and when it is finished we interact with the ``Calculation`` node.

The ``WorkChain`` is not the only process in AiiDA and each process uses a different node class as its database record.
The following table describes which processes exist in AiiDA and what node type they use as a database record. 

===================   =======================       =====================
Process               Database record               Used for
===================   =======================       =====================
``WorkChain``         ``WorkChainNode``             Workchain
``CalcJob``           ``CalcJobNode``               CalcJob
``FunctionProcess``   ``WorkFunctionNode``          Workfunction
``FunctionProcess``   ``CalcFunctionNode``          Calcfunction
===================   =======================       =====================

.. note::
    The concept of the ``Process`` is a later addition to AiiDA and in the beginning this division of 'how to run something` and 'serving as a record of what happened', did not exist.
    For example, historically speaking, the ``CalcJobNode`` class fulfilled both of those tasks.
    To not break the functionality of the historic ``CalcJobNode``, its implementation was kept and a ``Process`` wrapper was developed in the form of the ``JobProcess``.
    The ``process()`` class method was implemented for the ``CalcJobNode`` class, in order to automatically create a process wrapper for the calculation.

The good thing about this unification is that everything that is run in AiiDA has the same attributes concerning its running state.
The most important attribute is the process state.
In the next section, we will explain what the process state is, what values it can take and what they mean.

.. _process_state:

The process state
=================
Each ``Process`` has a process state.
This property tells you about the current status of the process.
It is stored in the instance of the ``Process`` itself and the workflow engine, the ``plumpy`` library, operates only on that value.
However, the ``Process`` instance 'dies' as soon as its is terminated, so therefore we also write the process state to the calculation node that the process uses as its database record, under the ``process_state`` attribute.
The process can be in one of six states:

 * Created
 * Running
 * Waiting
 * Killed
 * Excepted
 * Finished

The first three states are 'active' states, whereas the final three are 'terminal' states.
Once a process reaches a terminal state, it will never leave it, its execution is permanently terminated.
When a process is first created, it is put in the ``Created`` state.
As soon as it is picked up by a runner and it is active, it will be in the ``Running`` state.
If the process is waiting for another process, that it called, to be finished, it will be in the ``Waiting`` state.
A process that is in the ``Killed`` state, means that the user issued a command to kill it, or its parent process was killed.
The ``Excepted`` state indicates that during execution an exception occurred that was not caught and the process was unexpectedly terminated.
The final option is the ``Finished`` state, which means that the process was successfully executed, and the execution was nominal.
Note that this does not automatically mean that the result of the process can also considered to be successful, it just executed without any problems.

To distinghuis between a successful and a failed execution, we have introduced the 'exit status'.
This is another attribute that is stored in the node of the process and is an integer that can be set by the process.
A zero means that the result of the process was successful, and a non-zero value indicates a failure.
All the calculation nodes used by the various processes are a sub class of :py:class:`~aiida.orm.nodes.process.ProcessNode`, which defines handy properties to query the process state and exit status.

===================   ============================================================================================
Method                Explanation
===================   ============================================================================================
``process_state``     Returns the current process state
``exit_status``       Returns the exit status, or None if not set
``exit_message``      Returns the exit message, or None if not set
``is_terminated``     Returns ``True`` if the process was either ``Killed``, ``Excepted`` or ``Finished``
``is_killed``         Returns ``True`` if the process is ``Killed``
``is_excepted``       Returns ``True`` if the process is ``Excepted``
``is_finished``       Returns ``True`` if the process is ``Finished``
``is_finished_ok``    Returns ``True`` if the process is ``Finished`` and the ``exit_status`` is equal to zero
``is_failed``         Returns ``True`` if the process is ``Finished`` and the ``exit_status`` is non-zero
===================   ============================================================================================

When you load a calculation node from the database, you can use these property methods to inquire about its state and exit status.


.. _process_builder:

The process builder
===================
The process builder is essentially a tool that helps you build the object that you want to run.
To get a *builder* for a ``Calculation`` or a ``Workflow`` all you need is the ``Calculation`` or ``WorkChain`` class itself, which can be loaded through the ``CalculationFactory`` and ``WorkflowFactory``, respectively.
Let's take the :py:class:`~aiida.calculations.plugins.templatereplacer.TemplatereplacerCalculation` as an example::

    TemplatereplacerCalculation = CalculationFactory('templatereplacer')
    builder = TemplatereplacerCalculation.get_builder()

The string ``templatereplacer`` is the entry point of the ``TemplatereplacerCalculation`` and passing it to the ``CalculationFactory`` will return the corresponding class.
Calling the ``get_builder`` method on that class will return an instance of the ``ProcessBuilder`` that is tailored for the ``TemplatereplacerCalculation``.
The builder will help you in defining the inputs that the ``TemplatereplacerCalculation`` requires and has a few handy tools to simplify this process.

Defining inputs
---------------
To find out which inputs the builder exposes, you can simply use tab completion.
In an interactive python shell, by simply typing ``builder.`` and hitting the tab key, a complete list of all the available inputs will be shown.
Each input of the builder can also show additional information about what sort of input it expects.
In an interactive shell, you can get this information to display as follows::

    builder.parameters?
    Type:        property
    String form: <property object at 0x7f04c8ce1c00>
    Docstring:
        "non_db": "False"
        "help": "Parameters used to replace placeholders in the template",
        "name": "parameters",
        "valid_type": "<class 'aiida.orm.nodes.data.dict.Dict'>"

In the ``Docstring`` you will see a ``help`` string that contains more detailed information about the input port.
Additionally, it will display a ``valid_type``, which when defined shows which data types are expected.
If a default value has been defined, that will also be displayed.
The ``non_db`` attribute defines whether that particular input will be stored as a proper input node in the database, if the process is submitted.

Defining an input through the builder is as simple as assigning a value to the attribute.
The following example shows how to set the ``description`` and ``label`` inputs::

    builder.label = 'This is my calculation label'
    builder.description = 'An example calculation to demonstrate the process builder'

If you evaluate the ``builder`` instance, simply by typing the variable name and hitting enter, the current values of the builder's inputs will be displayed::

    builder
    {
        'description': 'An example calculation to demonstrate the process builder',
        'label': 'This is my calculation label',
        'options': {},
    }

In this example, you can see the value that we just set for the ``description`` and the ``label``.
In addition, it will also show any namespaces, as the inputs of processes support nested namespaces, such as the ``options`` namespace in this example.
This namespace contains all the additional options for a ``CalcJobNode`` that are not stored as input nodes, but rather have to do with how the calculation should be run.
Examples are the :ref:`job resources <job_resources>` that it should use or any other settings related to the scheduler.
Note that these options are also all autocompleted, so you can use that to discover all the options that are available, including their description.

All that remains is to fill in all the required inputs and we are ready to launch the ``Calculation`` or ``WorkChain``.

.. _launching_process_builder:

Launching the process
---------------------
When all the inputs have been defined for the builder, it can be used to actually launch the ``Process``.
The ``ProcessBuilder`` can be launched by passing it to the free functions ``run`` and ``submit`` from the ``aiida.engine.launch`` module, just as you would do a normal process.
For more details please refer to the :ref:`process builder section <running_workflows_process_builder>` in the section of the documentation on :ref:`running workflows <running_workflows>`.

Submit test
-----------
The ``ProcessBuilder`` of a ``CalcJobNode`` has one additional feature.
It has the method :py:meth:`~aiida.engine.processes.builder.CalcJobBuilder.submit_test()`.
When this method is called, provided that the inputs are valid, a directory will be created locally with all the inputs files and scripts that would be created if the builder were to be submitted for real.
This gives you a chance to inspect the generated files before actually sending them to the remote computer.
This action also will not create an actual calculation node in the database, nor do the input nodes have to be stored, allowing you to check that everything is correct without polluting the database.

By default the method will create a folder ``submit_test`` in the current working directory and within it a directory with an automatically generated unique name, each time the method is called.
The method takes two optional arguments ``folder`` and ``subfolder_name``, to change the base folder and the name of the test directory, respectively.
