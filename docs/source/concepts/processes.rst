.. _concepts_processes:

*********
Processes
*********

Anything that runs in AiiDA is an instance of the :py:class:`~aiida.engine.processes.process.Process` class.
The ``Process`` class contains all the information and logic to tell, whoever is handling it, how to run it to completion.
Typically the one responsible for running the processes is an instance of a :py:class:`~aiida.engine.runners.Runner`.
This can be a local runner or one of the daemon runners in case of the daemon running the process.

In addition to those run instructions, any ``Process`` that has been executed needs some sort of record in the database to store what happened during its execution.
For example it needs to record what its exact inputs were, the log messages that were reported and what the final outputs were.
For this purpose, every process will utilize an instance of a sub class of the :py:class:`~aiida.orm.nodes.process.ProcessNode` class.
This ``ProcessNode`` class is a sub class of :py:class:`~aiida.orm.nodes.Node` and serves as the record of the process' execution in the database and by extension the provenance graph.

It is very important to understand this division of labor.
A ``Process`` describes how something should be run, and the ``ProcessNode`` serves as a mere record in the database of what actually happened during execution.
A good thing to remember is that while it is running, we are dealing with the ``Process`` and when it is finished we interact with the ``ProcessNode``.

.. _concepts_process_types:

Process types
=============

Processes in AiiDA come in two flavors:

 * Calculation-like
 * Workflow-like

The calculation-like processes have the capability to *create* data, whereas the workflow-like processes orchestrate other processes and have the ability to *return* data produced by other calculations.
Again, this is a distinction that plays a big role in AiiDA and is crucial to understand.
For this reason, these different types of processes also get a different sub class of the ``ProcessNode`` class.
The hierarchy of these node classes and the link types that are allowed between them and ``Data`` nodes, is explained in detail in the :ref:`provenance implementation<concepts_provenance_implementation>` documentation.

Currently, there are four types of processes in ``aiida-core`` and the following table shows with which node class it is represented in the provenance graph and what the process is used for.

===================================================================   ==============================================================================  ===============================================================
Process class                                                         Node class                                                                      Used for
===================================================================   ==============================================================================  ===============================================================
:py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`          :py:class:`~aiida.orm.nodes.process.calculation.calcjob.CalcJobNode`            Calculations performed by external codes
:py:class:`~aiida.engine.processes.workchains.workchain.WorkChain`    :py:class:`~aiida.orm.nodes.process.workflow.workchain.WorkChainNode`           Workflows that run multiple calculations
:py:class:`~aiida.engine.processes.functions.FunctionProcess`         :py:class:`~aiida.orm.nodes.process.calculation.calcfunction.CalcFunctionNode`  Python functions decorated with the ``calcfunction`` decorator
:py:class:`~aiida.engine.processes.functions.FunctionProcess`         :py:class:`~aiida.orm.nodes.process.workflow.workfunction.WorkFunctionNode`     Python functions decorated with the ``workfunction`` decorator
===================================================================   ==============================================================================  ===============================================================

For basic information on the concept of a ``CalcJob`` or ``calcfunction``, refer to the :ref:`calculations concept<concepts_calculations>` and the same for the ``WorkChain`` and ``workfunction`` is described in the :ref:`workflows concept<concepts_workflows>`.
After having read and understood the basic concept of calculation and workflow processes, detailed information on how to implement and use them can be found in the dedicated developing sections for :ref:`calculations<working_calculations>` and :ref:`workflows<working_workflows>`, respectively.

.. note:: A ``FunctionProcess`` is never explicitly implemented but will be generated dynamically by the engine when a python function decorated with a :py:meth:`~aiida.engine.processes.functions.calcfunction` or :py:meth:`~aiida.engine.processes.functions.workfunction` is run.


.. _concepts_process_state:

Process state
=============
Each instance of a ``Process`` class that is being executed has a process state.
This property tells you about the current status of the process.
It is stored in the instance of the ``Process`` itself and the workflow engine, the ``plumpy`` library, operates only on that value.
However, the ``Process`` instance 'dies' as soon as its is terminated, so therefore we also write the process state to the calculation node that the process uses as its database record, under the ``process_state`` attribute.
The process can be in one of six states:

========  ============
*Active*  *Terminated*
========  ============
Created   Killed
Running   Excepted
Waiting   Finished
========  ============

The three states in the left column are 'active' states, whereas the right column displays the three 'terminal' states.
Once a process reaches a terminal state, it will never leave it, its execution is permanently terminated.
When a process is first created, it is put in the ``Created`` state.
As soon as it is picked up by a runner and it is active, it will be in the ``Running`` state.
If the process is waiting for another process, that it called, to be finished, it will be in the ``Waiting`` state.
A process that is in the ``Killed`` state, means that the user issued a command to kill it, or its parent process was killed.
The ``Excepted`` state indicates that during execution an exception occurred that was not caught and the process was unexpectedly terminated.
The final option is the ``Finished`` state, which means that the process was successfully executed, and the execution was nominal.
Note that this does not automatically mean that the result of the process can also considered to be successful, it just executed without any problems.

To distinghuis between a successful and a failed execution, there is the :ref:`exit status<concepts_process_exit_codes>`.
This is another attribute that is stored in the node of the process and is an integer that can be set by the process.
A zero means that the result of the process was successful, and a non-zero value indicates a failure.
All the process nodes used by the various processes are a sub class of :py:class:`~aiida.orm.nodes.process.ProcessNode`, which defines handy properties to query the process state and exit status.

===================   ============================================================================================
Property              Meaning
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


.. _concepts_process_exit_codes:

Process exit codes
==================
The previous section about the process state showed that a process that is ``Finished`` does not say anything about whether the result is 'successful' or 'failed'.
The ``Finished`` state means nothing more than that the engine managed to run the process to the end of execution without it encountering exceptions or being killed.
To distinguish between a 'successful' and 'failed' process, an 'exit status' can be defined.
The `exit status is a common concept in programming <https://en.wikipedia.org/wiki/Exit_status>`_ and is a small integer, where zero means that the result of the process was successful, and a non-zero value indicates a failure.
By default a process that terminates nominally will get a zero exit status.
To mark a process as failed, one can return an instance of the :py:class:`~aiida.engine.processes.exit_code.ExitCode` named tuple, which allows to set an integer ``exit_status`` and a string message as ``exit_message``.
When the engine receives such an ``ExitCode`` as the return value from a process, it will set the exit status and message on the corresponding attributes of the process node representing the process in the provenance graph.
How exit codes can be defined and returned depends on the process type and will be documented in detail in the respective :ref:`calculation<working_calculations>` and :ref:`workflow<working_workflows>` development sections.


.. _concepts_process_lifetime:

Process lifetime
================
A section that explain the lifetime of a process, how it is instantiated, represented in memory and database, sent as a 'task' to and maintained by RabbitMQ and when it terminates.

`Issue [#2623] <https://github.com/aiidateam/aiida_core/issues/2623>`_

.. _concepts_process_checkpoints:

Process checkpoints
===================
Explain the concept of a process checkpoint, how it allows the daemon to restart a process from one of the checkpoints and how it is currently implemented, with limitations.

`Issue [#2624] <https://github.com/aiidateam/aiida_core/issues/2624>`_
