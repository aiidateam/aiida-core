.. _intro:troubleshooting:

***************
Troubleshooting
***************

If you experience any problems, first check that all services are up and running:

.. code-block:: console

   $ verdi status

   ✓ profile:     On profile django
   ✓ repository:  /repo/aiida_dev/django
   ✓ postgres:    Connected to aiida@localhost:5432
   ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
   ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

In the example output, all service have a green check mark and so should be running as expected.
If all services are up and running and you are still experiencing problems or if you have trouble with the installation of aiida-core and related services, consider the commonly encountered problems below.

Installation issues
-------------------

numpy dependency
.................

On a clean Ubuntu 16.04 install the pip install command ``pip install -e aiida-core`` may fail due to a problem with dependencies on the ``numpy`` package.
In this case you may be presented with a message like the following:

.. code-block:: python

   from numpy.distutils.misc_util import get_numpy_include_dirs
   ImportError: No module named numpy.distutils.misc_util

To fix this, simply install ``numpy`` individually through pip in your virtual env, i.e.:

.. code-block:: console

   $ pip install numpy

followed by executing the original install command once more:

.. code-block:: console

   $ pip install -e aiida-core

This should fix the dependency error.

Database installation and location
..................................

If the installation fails while installing the packages related to the database, you may have not installed or set up the database libraries.

In particular, on Mac OS X, if you installed the binary package of PostgreSQL, it is possible that the PATH environment variable is not set correctly, and you get a "Error: pg_config executable not found." error.
In this case, discover where the binary is located, then add a line to your ``~/.bashrc`` file similar to the following:

.. code-block:: bash

   export PATH=/the/path/to/the/pg_config/file:${PATH}

and then open a new bash shell.
Some possible paths can be found at this `Stackoverflow link`_ and a non-exhaustive list of possible paths is the following (version number may change):

* ``/Applications/Postgres93.app/Contents/MacOS/bin``
* ``/Applications/Postgres.app/Contents/Versions/9.3/bin``
* ``/Library/PostgreSQL/9.3/bin/pg_config``

Similarly, if the package installs but then errors occur during the first of AiiDA (with ``Symbol not found`` errors or similar), you may need to point to the path where the dynamical libraries are.
A way to do it is to add a line similar to the following to the ``~/.bashrc`` and then open a new shell:

.. code-block:: bash

   export DYLD_FALLBACK_LIBRARY_PATH=/Library/PostgreSQL/9.3/lib:$DYLD_FALLBACK_LIBRARY_PATH

(you should of course adapt the path to the PostgreSQL libraries).

.. _Stackoverflow link: http://stackoverflow.com/questions/21079820/how-to-find-pg-config-pathlink

RabbitMQ Installation (Unix)
.............................

If in ``verdi status`` RabbitMQ is not connected, first check that RabbitMQ is actually running:

.. code-block:: console

   $ sudo rabbitmqctl status
   Status of node rabbit@ph-tsm15-025 ...
   [{pid,86960},
   ...
   {listeners,[{clustering,25672,"::"},{amqp,5672,"::"},{http,15672,"::"}]},

By default, AiiDA profiles are configured to connect to RabbitMQ *via* ``amqp://guest:guest@127.0.0.1:5672``, hence this port should be open for connections.
In Linux / Mac OSX you can also check which ports a PID has open using:

.. code-block:: console

   $ sudo lsof -Pan -p 86960 -i
   COMMAND    PID  USER   FD   TYPE             DEVICE SIZE/OFF NODE NAME
   beam.smp 98979 user1   75u  IPv4 0x9d838dc03d5a2485      0t0  TCP *:25672 (LISTEN)
   beam.smp 98979 user1   76u  IPv4 0x9d838dc047588625      0t0  TCP 127.0.0.1:58316->127.0.0.1:4369 (ESTABLISHED)
   beam.smp 98979 user1   86u  IPv6 0x9d838dc034033ea5      0t0  TCP *:5672 (LISTEN)
   beam.smp 98979 user1   87u  IPv4 0x9d838dc018071a15      0t0  TCP *:15672 (LISTEN)

If a connection cannot be found, try starting ``rabbitmq-server`` in non-detached mode.
If you encounter an output similar to that below, it may be that your versions of RabbitMQ and erlang (the programming language which RabbitMQ is written in) are incompatible.

.. code-block:: console

   $ rabbitmq-server
   BOOT FAILED

   ===========


   Error description:

      noproc


   Stack trace:

      []

   Error description:

      noproc

   {"init terminating in do_boot",noproc}

   init terminating in do_boot (noproc)


   Crash dump is being written to: erl_crash.dump...done

You can check your version of erlang using:

.. code-block:: console

   $ erl -eval '{ok, Version} = file:read_file(filename:join([code:root_dir(), "releases", erlang:system_info(otp_release), "OTP_VERSION"])), io:fwrite(Version), halt().' -noshell
   21.3

and your version of rabbitmq-server with:

.. code-block:: console

   $ rabbitmqctl --version
   3.7.16

Then see `RabbitMQ Erlang Version Requirements <https://www.rabbitmq.com/which-erlang.html>`__, to check if these are compatible, and reinstall as appropriate.

See also the `RabbitMQ Troubleshooting <https://www.rabbitmq.com/troubleshooting.html>`__ for further information.

Ensuring a UTF-8 locale
.......................

For some reasons, on some machines (notably often on Mac OS X) there is no default locale defined, and when you run ``verdi setup`` for the first time it fails (see also `this issue`_ of django).
Run in your terminal (or maybe even better, add to your ``.bashrc``, but then remember to open a new shell window!):

.. code-block:: bash

   export LANG="en_US.UTF-8"
   export LC_ALL="en_US.UTF-8"

and then run ``verdi setup`` again.

.. _this issue: https://code.djangoproject.com/ticket/16017

Possible Ubuntu dependencies
.............................

Several users reported the need to install also ``libpq-dev`` (header files for libpq5 - PostgreSQL library):

.. code-block:: console

   $ apt-get install libpq-dev

But under Ubuntu 12.04 this is not needed.

verdi not in PATH
-----------------

Installing the ``aiida-core`` python package *should* add the ``verdi`` CLI to your ``PATH`` automatically.

If the ``verdi`` executable is not available in your terminal, the folder where ``pip`` places binaries may not be added to your ``PATH``

For Linux systems, this folder is usually something like ``~/.local/bin``:

.. code-block:: bash

   export PATH=~/.local/bin:${PATH}

For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``:

.. code-block:: bash

   export PATH=~/Library/Python/2.7/bin:${PATH}

After updating your ``PATH``, the ``verdi`` command should be available.

.. note::

   A preprequisite for ``verdi`` to work is that the ``aiida`` python package is importable.
   Test this by opening a ``python`` or ``ipython`` shell and typing:

   .. code-block:: python

      import aiida

   If you get an ``ImportError`` (and you are in the environment where AiiDA was installed), you can add it to the ``PYTHONPATH`` manually:

   .. code-block:: bash

      export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"


Configuring remote SSH computers
--------------------------------

ssh_kerberos installation
.........................

When installing the ``ssh_kerberos`` *optional* requirement through Anaconda you may encounter the following error on Ubuntu machines:

.. code-block:: console

   version 'GFORTRAN_1.4' not found (required by /usr/lib/libblas.so.3)

This is related to an open issue in anaconda `ContinuumIO/anaconda-issues#686`_.
A potential solution is to run the following command:

.. code-block:: console

   $ export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libgfortran.so.3

.. _ContinuumIO/anaconda-issues#686: https://github.com/ContinuumIO/anaconda-issues/issues/686

Output from .bashrc and/or .bash_profile on remote computers
............................................................

.. note::

   This also applies to computers configured via ``local`` transport.

When connecting to remote computers, AiiDA (like other codes as ``sftp``) can get confused if you have code in your ``.bashrc`` or ``.bash_profile`` that produces output or e.g. runs commands like ``clean`` that require a terminal.

For instance, if you add a ``echo "a"`` in your ``.bashrc`` and then try to SFTP a file from it, you will get an error like ``Received message too long 1091174400``.

If you still want to have code that needs an interactive shell (``echo``, ``clean``, ...), but you want to disable it for non-interactive shells, put at the top of your file a guard like this:

.. code-block:: bash

   if [[ $- != *i* ]] ; then
   # Shell is non-interactive.  Be done now!
   return
   fi

Everything below this will not be executed in a non-interactive shell.

.. note::

   Still, you might want to have some code on top, like e.g. setting the PATH or similar, if this needs to be run also in the case of non-interactive shells.

To test if a the computer does not produce spurious output, run (after configuring):

.. code-block:: console

   $ verdi computer test <COMPUTERNAME>

which checks and, in case of problems, suggests how to solve the problem.

.. _StackExchange thread: https://apple.stackexchange.com/questions/51036/what-is-the-difference-between-bash-profile-and-bashrc


Improvements for dependencies
-----------------------------

Activating the ASE visualizer
..............................

Within a virtual environment, attempt to visualize a structure with ``ase`` (either from the shell, or using the command ``verdi data structure show --format=ase <PK>``), might end up with the following error message::

   ImportError: No module named pygtk

The issue is that ``pygtk`` is currently not pip-installable. One has to install it separately and create the appropriate bindings manually in the virtual environment.
You can follow the following procedure to get around this issue:

Install the ``python-gtk2`` package. Under Ubuntu, do:

.. code-block:: console

   $ sudo apt-get install python-gtk2

Create the ``lib/python2.7/dist-packages`` folder within your virtual environment:

.. code-block:: console

   $ mkdir <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
   $ chmod 755 <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages

where ``<AIIDA_VENV_FOLDER>`` is the virtual environment folder you have created
during the installation process.

Create several symbolic links from this folder, pointing to a number of files in ``/usr/lib/python2.7/dist-packages/``:

.. code-block:: console

   $ cd <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
   $ ln -s /usr/lib/python2.7/dist-packages/glib glib
   $ ln -s /usr/lib/python2.7/dist-packages/gobject gobject
   $ ln -s /usr/lib/python2.7/dist-packages/gtk-2.0 gtk-2.0
   $ ln -s /usr/lib/python2.7/dist-packages/pygtk.pth pygtk.pth
   $ ln -s /usr/lib/python2.7/dist-packages/pygtk.py pygtk.py
   $ ln -s /usr/lib/python2.7/dist-packages/cairo cairo

After that, ``verdi data structure show --format=ase <PK>`` should work.

Use in ipython/jupyter
----------------------

In order to use the AiiDA objects and functions in Jupyter, this latter has to be instructed to use the iPython kernel installed in the AiiDA virtual environment.
This happens by default if you install AiiDA with ``pip`` including the ``notebook`` option and run Jupyter from the AiiDA virtual environment.

If, for any reason, you do not want to install Jupyter in the virtual environment, you might consider to install it out of the virtual environment, if not already done:

.. code-block:: console

   $ pip install jupyter

Then, activate the AiiDA virtual environment:

.. code-block:: console

   $ source ~/<aiida.virtualenv>/bin/activate

and setup the AiiDA iPython kernel:

.. code-block:: console

   $ pip install ipykernel
   $ python -m ipykernel install --user --name=<aiida.kernel.name>

where you have chosen a meaningful name for the new kernel.

Finally, start a Jupyter server:

.. code-block:: console

   $ jupyter notebook

and from the newly opened browser tab select ``New -> <aiida.kernel.name>``

.. _intro:increase-logging-verbosity:

Increasing the logging verbosity
--------------------------------

By default, the logging level of AiiDA is minimal to avoid too much noise in the logfiles.
Only warnings and errors are logged to the daemon log files, while info and debug messages are discarded.

If you are experiencing a problem, you can increase the default minimum logging level of AiiDA messages, with:

.. code-block:: console

    $ verdi config logging.aiida_loglevel DEBUG

You might also be interested in reviewing the circus log messages (the ``circus`` library is the daemonizer that manages the daemon runners),

.. code-block:: console

    $ verdi config logging.circus_loglevel DEBUG

however those messages are usually only relevant to debug AiiDA internals.

For each profile that runs a daemon, there are two unique logfiles, one for AiiDA log messages (named ``aiida-<profile_name>.log``) and one for the circus logs (named ``circus-<profile_name>.log``).
Those files can be found in the ``~/.aiida/daemon/log`` folder.

After restarting the daemon (``verdi daemon restart``), the number of messages logged will increase significantly and may help in determining the source of the problem.

.. note::

    Besides ``DEBUG``, you can also use the levels defined in the `standard Python logging module <https://docs.python.org/3/library/logging.html#logging-levels>`_.
    In addition to those, AiiDA defines the custom ``REPORT`` level, which, with a value of ``23``, is more verbose than the ``WARNING`` level, but less verbose than ``INFO``.
    The ``REPORT`` level is AiiDA's default logging level.

When the problem is solved, we suggest to reset the default logging level, with:

.. code-block:: console

    $ verdi config logging.circus_loglevel --unset
    $ verdi config logging.aiida_loglevel --unset

to avoid too much noise in the logfiles.

The config options set for the current profile can be viewed using

.. code-block:: console

    $ verdi profile show

in the ``options`` row.
