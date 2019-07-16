Some tricks
===========

.. toctree::
  :maxdepth: 1

  ../setup/ssh_proxycommand
  
   
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

Tips to ease the life of the hard drive (for large databases)
=============================================================

Those tips are useful when your database is very large, i.e. several hundreds of
thousands of nodes or more. With such large databases the hard drive
may be constantly working and the computer slowed down a lot. Below are some
solutions to take care of the most typical reasons.

Repository backup
-----------------

The backup of the repository takes an extensively long time if it is done through
a standard rsync or backup software, since it contains as many folders as the number
of nodes (and each folder can contain many files!).
A solution is to use instead the incremental
backup described in the :ref:`repository backup section<repository_backup>`.


mlocate cron job
----------------

Under typical Linux distributions, there is a cron job (called 
``updatedb.mlocate``) running every day to update a database of files and 
folders -- this is to be used by the ``locate`` command. This might become 
problematic since the repository contains many folders and 
will be scanned everyday. The net effect is a hard drive almost constantly 
working.

To avoid this issue, edit as root the file ``/etc/updatedb.conf``
and put in ``PRUNEPATHS`` the name of the repository folder.
