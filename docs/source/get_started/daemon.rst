.. _setup_daemon:

****************
Setup the daemon
****************

Starting the daemon is relatively straight forward by issuing the command::

  verdi daemon start

If everything was done correctly, the daemon should start.
You can inspect the status of the daemon by running::

  verdi daemon status

and, if the daemon is running, you should see something like the following::

  * aiida-daemon[0]        RUNNING    pid 12076, uptime 0:39:05
  * aiida-daemon-beat[0]   RUNNING    pid 12075, uptime 0:39:05


To stop the daemon once again, use::

  verdi daemon stop

A log of the warning/error messages of the daemon can be found in ``in ~/.aiida/daemon/log/``.
The log can also be retrieved through ``verdi`` with the command::

  verdi daemon logshow

The daemon is a fundamental component of AiiDA, and it is for example in charge of submitting new calculations, checking their status on the cluster, retrieving and parsing the results of finished calculations.
But in order to actually be able to launch calculations on a computer, we will first have to register them with AiiDA.
This will be shown in detail in the next section.
