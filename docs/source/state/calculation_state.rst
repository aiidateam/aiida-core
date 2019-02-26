.. _calculation_state:

AiiDA calculations can be of two kinds:

* :py:class:`CalcJobNode <aiida.orm.nodes.process.calculation.calcjob.CalcJobNode>`: those who need to be run on a scheduler

* :py:class:`CalcFunctionNode <aiida.orm.nodes.process.calculation.calcfunction.CalcFunctionNode>`: rapid executions that are executed by the daemon itself, on your local machine.

In the following, we will refer to the CalcJobNodes as a Calculation for the sake of simplicity, unless we explicitly say otherwise. In the same way, the command ``verdi calculation`` refers to CalcJobNodes.

The calculation state
=====================

Once a calculation has been submitted to AiiDA, everything else will be managed by AiiDA:

#. The inputs are **checked** for consistency
#. The input files are **prepared**, **sent** to the cluster, and a job is **submitted**
#. The status of the job is **monitored** by the AiiDA daemon
#. When the calculation is finished, the outputs are **retrieved** and **parsed**

During these phases, it is useful to be able to check and verify the state of a calculation. The possible states and the different ways to access them are described in the following.

Possible states
+++++++++++++++

The calculation could be in several states.
The most common ones are the following:

1. ``NEW``: the calculation node has been created, but has not been submitted yet.

2. ``WITHSCHEDULER``: the job is in some queue on the remote computer. Note that this does not mean that the job is waiting in a queue, but it may be running or finishing, but it did not finish yet. AiiDA has to wait.

3. ``FINISHED``: the job on the cluster was finished, AiiDA already retrieved it and stored the results in the database. In most cases, this also means that the parser managed to parse the output file.

4. ``FAILED``: something went wrong, and AiiDA raised an exception. There are different reasons why this might happen:

    * there were not enough inputs, or they were not correct
    * the execution on the cluster failed
    * the code ended without completing successfully or producing a valid output file
    
    Other, more specific "failed" states are possible, including ``SUBMISSIONFAILED``, ``RETRIEVALFAILED`` and ``PARSINGFAILED``.

5. For very short times, when the job completes on the remote computer and AiiDA retrieves and parses it, you may happen to see a calculation in the ``RETRIEVING`` and ``PARSING`` states.

Eventually, when the calculation has finished, you will find the computed quantities in the database, and you will be able to query the database for the results that were parsed.

Determining the state
+++++++++++++++++++++

There are multiple ways to determine the state a calculation is in.

The ``verdi calculation`` command
---------------------------------
The simplest way to check the state of submitted calculations is to use  the ``verdi calculation list`` command from the command line. To get help on its use and command line options, run it with the ``-h`` or ``--help`` option::

  verdi calculation list --help

Directly within python
----------------------
If you prefer, you can check the state of a calculation from within python. For this, you need to specify the ID of the calculation you are interested in::

    from aiida import load_dbenv
    load_dbenv()

    from aiida.orm import CalcJobNode

    ## pk must be a valid integer pk
    calc = load_node(pk)
    ## Alternatively, with the UUID (uuid must be a valid UUID string)
    # calc = load_node(uuid)
    print "AiiDA state:", calc.get_state()  
    print "Last scheduler state seen by the AiiDA deamon:", calc.get_scheduler_state()

Note that you can also get a code by knowing its UUID, as specified in the comments. The advantage of the UUID is that will be preserved across different AiiDA databases, while the numeric ID typically changes when databases are merged.

.. note :: 
    ``calc.get_scheduler_state()`` returns the state on the scheduler (queued, held, running, ...) as seen the last time that the daemon connected to the remote computer. The time at which the last check was performed is returned by the ``calc.get_scheduler_lastchecktime()`` method. If no such check has been performed yet, this returns ``None``.


The ``verdi calculation gotocomputer`` command
++++++++++++++++++++++++++++++++++++++++++++++

Sometimes it is useful to go directly to the folder where the calculation is running, for example to check if the  output file has been created.

In this case, it is possible to run::

    verdi calculation gotocomputer CALCULATIONPK
  
where ``CALCULATIONPK`` is the PK of the calculation. This will open a new connection to the computer (either simply a bash shell or a ssh connection, depending on the transport) and directly change directory to the appropriate folder where the code is running.

.. warning:: 
    Be careful not to change any file that AiiDA created, modify the output files, or resubmit the calculation unless you **really** know what you are doing. Otherwise AiiDA may get very confused!   



Setting calculation properties
==============================

There are various options that can be set that control the behavior of a calculation.
They can be set through the :meth:~`aiida.orm.nodes.process.calculation.calcjob.CalcJobNode.set_option`` method.
Here follows a brief documentation of their action. You can also find them in the  :class:`aiida.orm.nodes.process.calculation.calcjob.CalcJobNode` API reference.

* ``max_memory_kb``: require explicitely the memory to be allocated to the scheduler job.
* ``append_text``: write a set of bash commands to be executed after the call to the executable. These commands are executed only for this instance of calculations. Look also at the computer and code append_text to write bash commands for any job run on that  computer or with that code.
* ``max_wallclock_seconds``: set (as integer) the scheduler-job wall-time in seconds.
* ``computer``: set the computer on which the calculation is run. Unnecessary if the calculation has been created from a code.
* ``mpirun_extra_params``: set as a list of strings the parameters to be passed to  the mpirun command.  Example: ``mpirun -np 8 extra_params[0] extra_params[1] ... exec.x`` Note: the process number is set by the resources.
* ``custom_scheduler_commands``: set a string (even multiline) which contains  personalized job-scheduling commands. These commands are set at the beginning of the  job-scheduling script, before any non-scheduler command. (prepend_texts instead are set after all job-scheduling commands).
* ``parser_name``: set the name of the parser to be used on the output. Typically, a plugin will have already a default plugin set, use this command to change it.
* ``environment_variables``: set a dictionary, whose key and values will be used to  set new environment variables in the job-scheduling script before the execution of the  calculation. The dictionary is translated to: ``export 'keys'='values'``.
* ``prepend_text``: set a string that contains bash commands, to be written in the job-scheduling script for this calculation, right before the call to the executable. (it is used for example to load modules). Note that there are also prepend text for the  computer (that are used for any job-scheduling script on the given computer) and for the code (that are used for any scheduling script using the given code), the prepend_text here is used only for this instance of the calculation: be careful in  avoiding duplication of bash commands.
* ``extra``: pass a key and a value, to be stored in the ``Extra`` attribute table in  the database. 
* ``extras``: like set extra, but you can pass a dictionary with multiple keys and values.
* ``priority``: set the job-scheduler priority of the calculation (AiiDA does not  have internal priorities). The function accepts a value that depends on the scheduler. plugin (but typically is an integer).
* ``queue_name``: pass in a string the name of the queue to use on the job-scheduler.
* ``account``: pass in a string the name of the account/project to use on the job-scheduler.
* ``qos``: pass in a string the name of the quality-of-service to use on the job-scheduler.
* ``import_sys_environment``: default=True. If True, the job-scheduling script will load the environment variables.
* ``resources``: set the resources to be used by the calculation like the number of nodes, wall-time, ..., by passing a dictionary to  this method. The keys of this dictionary, i.e. the resources, depend  on the specific scheduler plugin that has to run them. Look at the  documentation of the scheduler (type is given by: ``calc.computer.get_scheduler_type()``).
* ``withmpi``: True or False, if True (the default) it will  call the executable as a parallel run.
