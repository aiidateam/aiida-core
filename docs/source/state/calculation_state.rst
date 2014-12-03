###############################
Check the state of calculations
###############################

Once a calculation has been submitted to AiiDA, everything else will be
managed by AiiDA: the inputs will be checked to verify
that they are consistent. If the inputs are complete, the input
files will be prepared, sent on cluster, and a job will be
submitted. The AiiDA daemon with then monitor the scheduler, and after
execution the outputs automatically retrieved and parsed.

During these phases, it is useful to be able to check and verify the state of
a calculation. There are different ways to perform such an operation, described
below.

The ``verdi calculation`` command
+++++++++++++++++++++++++++++++++
The simplest way to check the state of submitted calculations is to use 
the ``verdi calculation list`` command from the command line.
To get help on its use and command line options, run it with the ``-h``
or ``--help`` option::

  verdi calculation list --help

Possible calculation states
---------------------------

The calculation could be in several states.
The most common you should see:

1. ``NEW``: the calculation node has been created, but has not been submitted
   yet.

2. ``WITHSCHEDULER``: the job is in some queue on the remote computer.
   Note that this does not mean that the job is waiting in
   a queue, but it may be running or finishing,
   but it did not finish yet. AiiDA has to wait.

3. ``FINISHED``: the job on the cluster was finished, AiiDA already retrieved
   it and stored the results in the database.
   In most cases, this also means that the parser managed to 
   parse the output file.

4. ``FAILED``: something went wrong, and AiiDA rose an exception.
   The error could be of various nature: the inputs were not enough
   or were not correct, the execution on the cluster failed,
   or (depending on the output plugin) the code ended without
   completing successfully or producing a valid output file. Other possible
   more specific "failed" states include ``SUBMISSIONFAILED``,
   ``RETRIEVALFAILED`` and ``PARSINGFAILED``.

5. For very short times, when the job completes on the remote computer and AiiDA
   retrieves and parses it, you may happen to see a calculation in the
   ``COMPUTED``, ``RETRIEVING`` and ``PARSING`` states.

Eventually, when the calculation has finished, you will find the computed
quantities in the database, and you will be able to query the database for
the results that were parsed!

Directly in python
++++++++++++++++++
If you prefer to have more flexibility or to check the state of a calculation
programmatically, you can execute a script like the following, where you just
need to specify the ID of the calculation you are interested in::

  from aiida import load_dbenv
  load_dbenv()

  from aiida.orm import Calculation

  ## pk must be a valid integer pk
  calc = Calculation.get_subclass_from_pk(pk)
  ## Alternatively, with the UUID (uuid must be a valid UUID string)
  # calc = Calculation.get_subclass_from_uuid(uuid)
  print "AiiDA state:", calc.get_state()  
  print "Last scheduler state seen by the AiiDA deamon:", calc.get_scheduler_state()

Note that, as specified in the comments, you can also get a code by knowing its
UUID; the advantage is that, while the numeric ID will typically change after
a sync of two databases, the UUID is a unique identifier and will be preserved
across different AiiDA instances.

.. note :: ``calc.get_scheduler_state()`` returns the state on the scheduler
   (queued, held, running, ...) as seen the last time that the daemon connected
   to the remote computer. The time at which the last check was performed is
   returned by the ``calc.get_scheduler_lastchecktime()`` method (that returns
   ``None`` if no check has been performed yet).


The ``verdi calculation gotocomputer`` command
++++++++++++++++++++++++++++++++++++++++++++++

Sometimes, it may be useful to directly go to the folder on
which the calculation is running, for instance to check if the 
output file has been created.

In this case, it is possible to run::

  verdi calculation gotocomputer CALCULATIONPK
  
where ``CALCULATIONPK`` is the PK of the calculation. This will
open a new connection to the computer (either simply a bash shell
or a ssh connection, depending on the transport) and directly
change directory to the appropriate folder where the code is
running.

.. note:: Be careful not to change any file that AiiDA created,
  nor to modify the output files or resubmit the calculation, 
  unless you **really** know what you are doing, 
  otherwise AiiDA may get very confused!   









 



