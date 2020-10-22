.. _how-to:faq:

==========================
Frequently Asked Questions
==========================

If the problem you are facing is not addressed below, you can send an email to the `mailing list <http://www.aiida.net/mailing-list/>`_, or `open an issue on Github <https://github.com/aiidateam/aiida-core/issues/new/choose>`_ if you think it concerns a bug.


I have updated the version of AiiDA and now it is no longer working. What should I do?
======================================================================================
First, make sure that your daemon is not running.
You can check this with ``verdi daemon status``.
If you find that your daemon was actually still running, that is likely the problem, so stop it first using ``verdi daemon stop``.
It is very important that each time you want to :ref:`update your AiiDA installation<how-to:installation:update>`, you should *always* first finish all running processes and stop the daemon before doing so.
After you have stopped the daemon, make sure to run ``reentry scan`` before you restart the daemon with ``verdi daemon start``.


I get a :py:class:`~aiida.common.exceptions.MissingEntryPointError` or :py:class:`~aiida.common.exceptions.MultipleEntryPointError` exception, saying that a particular entry point cannot be found. How can I fix this?
========================================================================================================================================================================================================================
Often this is caused by an outdated entry point cache.
This can happen for example when you have updated your AiiDA installation or installed a new plugin using ``pip install``.
In both cases, you can fix the problem by running ``reentry scan``.
Make sure to also restart all daemons, to ensure that the changes are picked up by the daemons as well.


I have updated the code of a :py:class:`~aiida.engine.processes.workchains.WorkChain`, :py:class:`~aiida.engine.processes.calcjobs.CalcJob` or whatever other Python code, but the daemon does not seem to pick up the changes?
===============================================================================================================================================================================================================================
Each time that you change your code, you should restart the daemon for the changes to take effect.
Each daemon worker actually is its own system process with its own Python interpreter instance, and since we don't support automated hot==swapping, the daemon workers will not automatically detect the changes in the code.
Simply calling ``verdi daemon restart`` will do the trick.


I have updated the code of a :py:class:`~aiida.engine.processes.workchains.WorkChain`, :py:class:`~aiida.engine.processes.calcjobs.CalcJob` or whatever other Python code, but my Python shell instance does not seem to pick up the changes?
=============================================================================================================================================================================================================================================
The ``verdi shell`` is its own Python interpreter and does not automatically detect code changes.
Simply reloading your shell will solve the problem.


Why are calculation jobs taking very long to run on remote machines even though the actual computation time should be fast?
===========================================================================================================================
First make sure that the calculation is not actually waiting in the queue of the scheduler, but it is actually running or has already completed.
If it then still takes seemingly a lot of time for AiiDA to update your calculations, there are a couple of explanations.
First, if you are running many processes, your daemon workers may simply be busy managing other calculations and workflows.
If that is not the case, you may be witnessing the effects of the built in throttling mechanisms of AiiDA's engine.
To ensure that the AiiDA daemon does not overload remote computers or their schedulers, there are built in limits to how often the daemon workers are allowed to open an SSH connection, or poll the scheduler.
To determine the minimum transport and job polling interval, use ``verdi computer configure show <COMPUTER>`` and ``computer.get_minimum_job_poll_interval()``, respectively.
You can lower these values using:

.. code-block:: console

    $ verdi computer configure <TRANSPORT_TYPE> <COMPUTER> --safe-interval=<NUMBER_OF_SECONDS>

and

.. code-block:: ipython

    In [1]: computer.set_minimum_job_poll_interval(NUMBER_OF_SECONDS)

respectively.
However, be careful, if you make these intervals too short, the daemon workers may spam the remote machine and/or scheduler, which could have adverse effects on the machine itself or can get your account banned, depending on the policy of the remote machine.
An additional note of importance is that each interval is guaranteed to be respected per daemon worker individually, but not as a collective.
That is to say, if the safe interval is set to 60 seconds, any single worker is guaranteed to open a connection to that machine at most once every minute, however, if you have multiple active daemon workers, the machine may be accessed more than once per minute.


Why would a process that runs fine locally raise an exception when submitted to the daemon?
===========================================================================================
This is almost always caused by an import issue.
To determine exactly what might be going wrong, first :ref:`set the loglevel <intro:increase-logging-verbosity>` to ``DEBUG`` by executing the command:

.. code-block:: console

    $ verdi config logging.aiida_loglevel DEBUG

Then restart the daemon with ``verdi daemon restart`` for the changes to take effect.
Run the command ``verdi daemon logshow`` in a separate terminal to see the logging output of the daemon and then submit the problematic calculation or workflow again.
If the root cause is indeed due to an import problem, it will probably appear as an ``ImportError`` exception in the daemon log.
To solve these issues, make sure that all the Python code that is being run is properly importable, which means that it is part of the `PYTHONPATH <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_.
Make sure that the PYTHONPATH is correctly defined automatically when starting your shell, so for example if you are using bash, add it to your ``.bashrc``.
