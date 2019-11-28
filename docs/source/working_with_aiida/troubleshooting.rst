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

While AiiDA supports running hundreds of thousands of calculations and graphs with millions of nodes, scaling out may put increased load on your CPU and disk.
There are a couple of things you can do in order to keep AiiDA running smoothly:

 1. :ref:`Move the Postgresql database<move_postgresql>` to a fast disk (SSD), ideally on a large partition.

 2. Use AiiDA's tools for making :ref:`efficient incremental backups<repository_backup>` of the file repository.

 3. Your operating system may be indexing the file repository. :ref:`Disable this<disable_repo_indexing>`.

 4. If ``verdi daemon status`` shows the daemon worker(s) constantly at high CPU usage, use ``verdi daemon incr X`` to add ``X`` daemon workers.
    Don't use more workers than CPU cores.


Various tips & tricks
=====================

.. toctree::
  :maxdepth: 1

  tips/ssh_proxycommand
  tips/move_db
  tips/repo_indexing

