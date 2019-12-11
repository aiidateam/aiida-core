Increasing the debug level
==========================

By default, the logging level of AiiDA is minimal to avoid filling logfiles.
Only warnings and errors are logged to the daemon log files, while info and debug
messages are discarded.

If you are experiencing a problem, you can change the default minimum logging
level of AiiDA messages::

  verdi config logging.aiida_loglevel DEBUG

You might also be interested in circus log messages (the ``circus`` library is the daemonizer that manages the daemon runners) but most often it is used by AiiDA developers::

  verdi config logging.circus_loglevel DEBUG


For each profile that runs a daemon, there will be two unique logfiles, one for
AiiDA log messages (named ``aiida-<profile_name>.log``) and one for the circus logs (named ``circus-<profile_name>.log``). Those files can be found
in the ``~/.aiida/daemon/log`` folder.

After rebooting the daemon (``verdi daemon restart``), the number of messages
logged will increase significantly and may help in understanding
the source of the problem.

.. note:: In the command above, you can use a different level than ``DEBUG``.
  The list of the levels and their order is the same of the `standard python
  logging module <https://docs.python.org/3/library/logging.html#logging-levels>`_.
  In addition to the standard logging levels, we define our custom ``REPORT`` level,
  which, with a value of ``23``, sits between the standard ``INFO`` and ``WARNING``
  levels. The ``REPORT`` level is the default logging level as this is what is used
  by messages from, among other things, the work chain report..

When the problem is solved, we suggest to bring back the default logging level, using the two commands::

    verdi config logging.circus_loglevel --unset
    verdi config logging.aiida_loglevel --unset

to avoid to fill the logfiles.

The config options set for the current profile can be viewed using::

  verdi profile show

in the ``options`` row.

.. _repo_troubleshooting:

AiiDA performance tuning
========================

AiiDA supports running hundreds of thousands of calculations and graphs with
millions of nodes. However, to scale to this amount, you might need to properly
configure some variables in AiiDA to balance the load on your CPU and disk.

Here are a few things you can do in order to keep AiiDA running smoothly:

  1. :ref:`Move the Postgresql database<move_postgresql>` to a fast disk (SSD),
     ideally on a large partition.

  2. Use AiiDA's tools for making :ref:`efficient incremental
     backups<repository_backup>` of the file repository.

  3. Your operating system may be indexing the file repository.
     :ref:`Disable this<disable_repo_indexing>`.

  4. The verdi deamon can manage an arbitrary number of parallel workers;
     by default only one is activated. If ``verdi daemon status`` shows
     the daemon worker(s) constantly at high CPU usage, use
     ``verdi daemon incr X`` to add ``X`` daemon workers.
     However, don't use many more workers than CPU cores on your machine
     (or ideally, if you have many cores, leave one or two available for the
     database).

  5. If you submit to a supercomputer shared by many users (e.g., in a
     supercomputer center), be careful not to overload the supercomputer with
     too many jobs:

     - keep the number of jobs in the queue under control (the exact number
       depends on the supercomputer: discuss this with your supercomputer
       administrators, and you can redirect them to
       :ref:`this page<for_cluster_admins>` that may contain useful information
       for them).
       While in the future `this might be dealt by AiiDA
       automatically <https://github.com/aiidateam/aiida-core/issues/88>`_,
       you are responsible for this at the moment. This can be achieved for
       instance by submitting only a maximum number of workflows to AiiDA,
       and submitting new ones only when the previous ones complete.
     - Tune the parameters that AiiDA uses to avoid overloading the
       supercomputer with connections or batch requests. For SSH transports,
       the default is 30 seconds, which means that when each worker opens
       a SSH connection to a computer, it will reuse it as long as there are
       tasks to execute and then close it. Opening a new connection will not
       happen before 30 seconds has passed from the opening of the previous
       one. We stress that this is *per daemon worker*, so that if you have
       10 workers, your supercomputer will on average see 10 connections every
       30 seconds. Therefore, if you are using many workers and you mostly have
       long-running jobs, you can set a longer time (e.g., 120 seconds)
       by reconfiguring the computer with
       ``verdi computer configure ssh <COMPUTER_NAME>`` and changing the value
       of the *Connection cooldown time* or, alternatively, by running::

         verdi computer configure ssh --non-interactive --safe-interval <SECONDS> <COMPUTER_NAME>
     - In addition to the connection cooldown time described above, AiiDA also
       avoids running too often the command to get the list of jobs in the queue
       (``squeue``, ``qstat``, ...), as this can also impact the
       performance of the scheduler. For a given computer, you can increase
       how many seconds must pass between requests. First load the
       computer in a shell with ``computer = load_computer(<COMPUTER_NAME>)``.
       You can check the current value in seconds (by default, 10) with
       ``computer.get_minimum_job_poll_interval()``.
       You can then set it to a higher value using::

         computer.set_minimum_job_poll_interval(<NEW_VALUE_SECONDS>)

Various tips & tricks
=====================

.. toctree::
  :maxdepth: 1

  tips/ssh_proxycommand
  tips/move_db
  tips/repo_indexing
  tips/for_cluster_admins

