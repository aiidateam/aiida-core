==========================
Troubleshooting and tricks
==========================

Increasing the log level
========================

By default, AiiDA logs only warnings and errors, while info and debug messages
are discarded in order to keep log files lean.

If you are experiencing a problem, you may want to change the default minimum
logging level of AiiDA messages (and celery messages -- celery is the library
that manages the daemon process)::

  verdi devel setproperty logging.celery_loglevel DEBUG
  verdi devel setproperty logging.aiida_loglevel DEBUG

.. note:: AiiDA supports the same log levels
  as the `standard python logging module <https://docs.python.org/2/library/logging.html#logging-levels>`_.

The log file is found in the AiiDA log folder with default location ``~/.aiida/daemon/log/aiida_daemon.log``.
After restarting the daemon (``verdi daemon restart``), the new log level will take effect and may help pinpointing the source of the problem.

Once the problem is solved, we suggest you return to the default log level::

    verdi devel delproperty logging.celery_loglevel
    verdi devel delproperty logging.aiida_loglevel

.. _repo_troubleshooting:

Reduce hard drive load (large databases)
========================================

The following tips may be useful for AiiDA databases containing several 100k
nodes or more, which may put significant load both on the hard drive and the
processor.

Increase PostgreSQL work memory
-------------------------------

By default, the work memory of PostgreSQL is 4 MB.
Individual operations (such as sorting) that require more memory than this will cause postgres to write temporary files,
which can result in a lot of overhead from disk I/O (and high CPU usage from `postgresql`).

In order to check whether your PostgreSQL cluster is creating temporary files, 
enable logging of those by setting::

    log_temp_files = 0

in your `postgresql.conf` configuration file.

.. note::

    On Ubuntu, this file is located at `/etc/postgresql/<version>/main/postgresql.conf`.

If the logs show that temporary files are created, you may avoid this by increasing the PostgreSQL work memory::

    sudo su postgres -c psql
    postgres=# ALTER system SET work_mem='128MB';
    postgres=# select * from pg_reload_conf();

The settings should take effect immediately.

One known issue that can cause high memory requirements unnecessarily is the kombu message table overflowing with outdated messages.
Use the following to check the size of your ``kombu_message`` table and prune it:

.. code:: sql

    sudo su postgres -c psql
    postgres=# \c my_aiida_database
    postgres=# SELECT pg_size_pretty( pg_total_relation_size('kombu_message') );
     792 MB
    postgres=# DELETE FROM kombu_message WHERE timestamp < (NOW() - INTERVAL '1 DAYS');
    postgres=# VACUUM kombu_message;


Exclude repository from ``locate``
----------------------------------

Typical Linux distributions have a cron job ``updatedb.mlocate`` that runs once a day to update the database of files and folders on the hard drive (to be used by the ``locate`` command).
When the file repository is large, this cron job can take a long time to complete.

To avoid this issue, edit as root the file ``/etc/updatedb.conf``
and put the name of the repository folder in ``PRUNEPATHS``.

Use incremental backups
-----------------------

A full backup of the file repository using ``rsync`` or other backup software can take a long time and is not efficient.
Use incremental backup instead, as described in the :ref:`repository backup section<repository_backup>`.

Further tricks
==============

.. toctree::
  :maxdepth: 1

  ../setup/ssh_proxycommand

