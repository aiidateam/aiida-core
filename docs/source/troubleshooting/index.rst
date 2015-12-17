==========================
Troubleshooting and tricks
==========================

Some tricks
===========

.. toctree::
  :maxdepth: 1

  ../setup/ssh_proxycommand
  

Connection problems
===================

* **When AiiDA tries to connect to the remote computer, it says**
  ``paramiko.SSHException: Server u'FULLHOSTNAME' not found in known_hosts``

  AiiDA uses the ``paramiko`` library to establish SSH connections.
  ``paramiko`` is able to read the remote host keys
  from the ``~/.ssh/known_hosts`` of the
  user under which the AiiDA daemon is running. You therefore have to make
  sure that the key of the remote host is stored in the file.

  * As a first check, login as the user under which the AiiDA daemon is running
    and run a::

      ssh FULLHOSTNAME

    command, where ``FULLHOSTNAME`` is the complete
    host name of the remote computer configured in AiiDA. If the key of the 
    remote host is not in the ``known_hosts`` file, SSH will ask confirmation
    and then add it to the file.

  * If the above point is not sufficient, check the format of the remote host
    key. On some machines (we know that this issue happens at least on recent
    Ubuntu distributions) the default format is not RSA but ECDSA. However,
    ``paramiko`` is still not able to read keys written in this format.
    
    To discover the format, run the following command::

      ssh-keygen -F FULLHOSTNAME

    that will print the remote host key. If the output contains the string 
    ``ecdsa-sha2-nistp256``, then ``paramiko`` will not be able to use this
    key (see below for a solution).
    If instead ``ssh-rsa``, the key should be OK and
    paramiko will be able to use it.

    In case your key is in *ecdsa* format, you have to first delete the key
    by using the command::

      ssh-keygen -R FULLHOSTNAME

    Then, in your ``~/.ssh/config`` file (create it if it does not exist)
    add the following lines::

      Host *
        HostKeyAlgorithms ssh-rsa

    (use the same indentation, and leave an empty line before and one after).
    This will set the RSA algorithm as the default one for all remote hosts.
    In case, you can set the ``HostKeyAlgorithms`` attribute only to the 
    relevant computers (use ``man ssh_config`` for more information).

    Then, run a::

      ssh FULLHOSTNAME

    command. SSH will ask confirmation and then add it to the file, but 
    this time it should use the ``ssh-rsa`` format (it will say so in the
    prompt messsage). You can also double-check that the host key was 
    correctly inserted using the ``ssh-keygen -F FULLHOSTNAME`` command
    as described above. Now, the error messsage should not appear anymore.
    
Increasing the debug level
==========================

By default, the logging level of AiiDA is minimal to avoid filling logfiles.
Only warnings and errors are logged (to the
``~/.aiida/daemon/log/aiida_daemon.log`` file), while info and debug
messages are discarded.

If you are experiencing a problem, you can change the default minimum logging
level of AiiDA messages (and celery messages -- celery is the library that we
use to manage the daemon process) using, on the command line, the two
following commands::

  verdi devel setproperty logging.celery_loglevel DEBUG
  verdi devel setproperty logging.aiida_loglevel DEBUG

After rebooting the daemon (``verdi daemon restart``), the number of messages
logged will increase significantly and may help in understanding
the source of the problem. 

.. note:: In the command above, you can use a different level than ``DEBUG``.
  The list of the levels and their order is the same of the `standard python
  logging module <https://docs.python.org/2/library/logging.html#logging-levels>`_.

.. note:: When the problem is solved, we suggest to bring back the default
  logging level, using the two commands::

    verdi devel delproperty logging.celery_loglevel
    verdi devel delproperty logging.aiida_loglevel

  to avoid to fill the logfiles.
  
.. _repo_troubleshooting:

Tips to ease the life of the hard drive (for large databases)
=============================================================

Those tips are useful when your database is very large, i.e. several hundreds of
thousands of nodes and workflows or more. With such large databases the hard drive
may be constantly working and the computer slowed down a lot. Below are some
solutions to take care of the most typical reasons.

Repository backup
-----------------

The backup of the repository takes an extensively long time if it is done through
a standard rsync or backup software, since it contains as many folders as the number
of nodes plus the number of workflows (and each folder can contain many files!).
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
