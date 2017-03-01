.. _get-started:

===========
Get started
===========

In this section, we assume you have successfully installed AiiDA.
If this is not the case, please refer to instructions in the :ref:`installation` section.
With AiiDA up and running, this section will explain how to get started and put AiiDA to good use.
First we will launch the daemon, which is a process that runs in the background and takes care of a lot of tasks for you.

###################
Starting the daemon
###################
Starting the daemon is relatively straight forward by issuing the command::

	$ verdi daemon start

If you run the ``verdi quicksetup`` to setup AiiDA and you entered your own personal email address, you will see the following error message::

	You are not the daemon user! I will not start the daemon.
	(The daemon user is 'aiida@localhost', you are 'richard.wagner@leipzig.de')

	** FOR ADVANCED USERS ONLY: **
	To change the current default user, use 'verdi install --only-config'
	To change the daemon user, use 'verdi daemon configureuser'

This is a safeguard, because AiiDA detects that the person whose profile is active is not the same as the one configured for the daemon.
If you are working in a single-user mode, and you are sure that nobody else is going to run the daemon, you can configure your user as the (only) one who can run the daemon.
To configure the deamon for your profile, first make sure the daemon is stopped::

	$ verdi daemon stop

and then run the command::

    $ verdi daemon configureuser

This will prompt you with a warning which you can accept and then fill in the email address of your profile.
If all went well, it will confirm that the new email address was set for the daemon::

	The new user that can run the daemon is now Richard Wagner.

Now that the daemon is properly configured, you can start it with::

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

	$ verdi daemon logshow

The daemon is a fundamental component of AiiDA, and it is for example in charge of submitting new calculations, checking their status on the cluster, retrieving and parsing the results of finished calculations, and managing the workflow steps.
But in order to actually be able to launch calculations on a computer, we will first have to register them with AiiDA.
This will be shown in detail in the next section.


.. include:: ../setup/computerandcodes.rst