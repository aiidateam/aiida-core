.. _how-to:faq:

==========================
Frequently Asked Questions
==========================

If the problem you are facing is not addressed below, please refer to the `Discourse server <https://aiida.discourse.group/>`_.
To file a bug report or open a feature request, please `open an issue on Github <https://github.com/aiidateam/aiida-core/issues/new/choose>`_.


I have updated the version of AiiDA and now it is no longer working. What should I do?
======================================================================================
First, make sure that your daemon is not running.
You can check this with ``verdi daemon status``.
If you find that your daemon was actually still running, that is likely the problem, so stop it first using ``verdi daemon stop``.
It is very important that each time you want to :ref:`update your AiiDA installation<how-to:installation:update>`, you should *always* first finish all running processes and stop the daemon before doing so.
Restart the daemon with ``verdi daemon start``.


I get a :py:class:`~aiida.common.exceptions.MissingEntryPointError` or :py:class:`~aiida.common.exceptions.MultipleEntryPointError` exception, saying that a particular entry point cannot be found. How can I fix this?
========================================================================================================================================================================================================================
Often this is caused by an outdated entry point cache.
This can happen for example when you have updated your AiiDA installation or installed a new plugin using ``pip install``.
Make sure to also restart all daemons, to ensure that the changes are picked up by the daemons as well.


I have updated the code of a :py:class:`~aiida.engine.WorkChain`, :py:class:`~aiida.engine.CalcJob` or whatever other Python code, but the daemon does not seem to pick up the changes?
===============================================================================================================================================================================================================================
Each time that you change your code, you should restart the daemon for the changes to take effect.
Each daemon worker actually is its own system process with its own Python interpreter instance, and since we don't support automated hot==swapping, the daemon workers will not automatically detect the changes in the code.
Simply calling ``verdi daemon restart`` will do the trick.


I have updated the code of a :py:class:`~aiida.engine.WorkChain`, :py:class:`~aiida.engine.CalcJob` or whatever other Python code, but my Python shell instance does not seem to pick up the changes?
=============================================================================================================================================================================================================================================
The ``verdi shell`` is its own Python interpreter and does not automatically detect code changes.
Simply reloading your shell will solve the problem.


Why are calculation jobs taking very long to run on remote machines even though the actual computation time should be fast?
===========================================================================================================================
First, make sure that the calculation is not actually waiting in the queue of the scheduler, but it is actually running or has already completed.
If it then still takes seemingly a lot of time for AiiDA to update your calculations, there are a couple of explanations.
First, if you are running many processes, your daemon workers may simply be busy managing other calculations and workflows.
If that is not the case, you may be witnessing the effects of the built-in throttling mechanisms of AiiDA's engine.
To ensure that the AiiDA daemon does not overload remote computers or their schedulers, there are built-in limits to how often the daemon workers are allowed to open an SSH connection, or poll the scheduler.
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

.. _how-to:faq:process-not-importable-daemon:

Why would a process that runs fine locally raise an exception when submitted to the daemon?
===========================================================================================
This is almost always caused by an import issue.
To determine exactly what might be going wrong, first :ref:`set the loglevel <intro:increase-logging-verbosity>` to ``DEBUG`` by executing the command:

.. code-block:: console

    $ verdi config set logging.aiida_loglevel DEBUG

Then restart the daemon with ``verdi daemon restart`` for the changes to take effect.
Run the command ``verdi daemon logshow`` in a separate terminal to see the logging output of the daemon and then submit the problematic calculation or workflow again.

If the root cause is indeed due to an import problem, it will probably appear as an ``ImportError`` exception in the daemon log.
To solve these issues, make sure that all the Python code that is being run is properly importable, which means that it is part of the `PYTHONPATH <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_.
Make sure that the PYTHONPATH is correctly defined automatically when starting your shell, so for example if you are using bash, add it to your ``.bashrc`` and completely reset daemon.
For example, go to the directory that contains the file where you defined the process and run:

.. code-block:: console

    $ echo "export PYTHONPATH=\$PYTHONPATH:$PWD" >> $HOME/.bashrc
    $ source $HOME/.bashrc
    $ verdi daemon restart --reset

.. _how-to:faq:caching-not-enabled:

Why is caching not enabled by default?
======================================

Caching is designed to work in an unobtrusive way and simply save time and valuable computational resources.
However, this design is a double-egded sword, in that a user that might not be aware of this functionality, can be caught off guard by the results of their calculations.

The caching mechanism comes with some limitations and caveats that are important to understand.
Refer to the :ref:`topics:provenance:caching:limitations` section for more details.

.. _how-to:faq:mfa-key-expired:

What happens when an SSH key pair expires for an MFA-enabled remote computer?
=============================================================================

In some supercomputing centres, Multi-Factor Authentication (MFA) is required to connect to the remote computer.
Often, when establishing a connection to such a computer, one needs to generate an SSH key pair with a limited lifetime.
This is the case of Swiss National Supercomputing Centre (CSCS), for example.

When the SSH key pair expires, AiiDA will fail to connect to the remote computer.
This will cause all calculations submitted on that computer to pause.
To restart them, one needs to generate a new SSH key pair and play the paused processes using ``verdi process play --all``.
Typically, this is all one needs to do - AiiDA will re-establish the connection to the computer and will continue following the calculations.
