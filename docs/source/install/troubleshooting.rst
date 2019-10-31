.. _troubleshooting:

Troubleshooting
===============

If you experience any problems, first check that all services are up and running:

.. code-block:: bash

    verdi status

     ✓ profile:     On profile django
     ✓ repository:  /repo/aiida_dev/django
     ✓ postgres:    Connected to aiida@localhost:5432
     ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
     ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

In the example output, all service have a green check mark and so should be running as expected.
If all services are up and running and you are still experiencing problems, consider the commonly encountered problems below.

Installation phase
------------------

* [**numpy dependency**] On a clean Ubuntu 16.04 install the pip install command ``pip install -e aiida-core``
  may fail due to a problem with dependencies on the ``numpy`` package. In this case
  you may be presented with a message like the following::

    from numpy.distutils.misc_util import get_numpy_include_dirs
    ImportError: No module named numpy.distutils.misc_util

  To fix this, simply install ``numpy`` individually through pip in your virtual env, i.e.::

    pip install numpy

  followed by executing the original install command once more::

    pip install -e aiida-core

  This should fix the dependency error.

* [**Database installation and location**] If the installation fails while installing the packages related
  to the database, you may have not installed or set up the database
  libraries.

  In particular, on Mac OS X, if you installed the binary package of
  PostgreSQL, it is possible that the PATH environment variable is not
  set correctly, and you get a "Error: pg_config executable not found." error.
  In this case, discover where the binary is located, then add a line to
  your ``~/.bashrc`` file similar to the following::

    export PATH=/the/path/to/the/pg_config/file:${PATH}

  and then open a new bash shell.
  Some possible paths can be found at this
  `Stackoverflow link`_ and a non-exhaustive list of possible
  paths is the following (version number may change):

  * ``/Applications/Postgres93.app/Contents/MacOS/bin``
  * ``/Applications/Postgres.app/Contents/Versions/9.3/bin``
  * ``/Library/PostgreSQL/9.3/bin/pg_config``

  Similarly, if the package installs but then errors occur during the first
  of AiiDA (with ``Symbol not found`` errors or similar), you may need to
  point to the path where the dynamical libraries are. A way to do it is to
  add a line similar to the following to the ``~/.bashrc`` and then open
  a new shell::

    export DYLD_FALLBACK_LIBRARY_PATH=/Library/PostgreSQL/9.3/lib:$DYLD_FALLBACK_LIBRARY_PATH

  (you should of course adapt the path to the PostgreSQL libraries).

.. _Stackoverflow link: http://stackoverflow.com/questions/21079820/how-to-find-pg-config-pathlink

* [**ensuring a UTF-8 locale**]For some reasons, on some machines
  (notably often on Mac OS X) there is no
  default locale defined, and when you run ``verdi setup`` for the first
  time it fails (see also `this issue`_ of django).
  Run in your terminal (or maybe even better, add to your ``.bashrc``, but
  then remember to open a new shell window!)::

     export LANG="en_US.UTF-8"
     export LC_ALL="en_US.UTF-8"

  and then run ``verdi setup`` again.

.. _this issue: https://code.djangoproject.com/ticket/16017

* [**possible Ubuntu dependencies**] Several users reported the need to install
  also ``libpq-dev`` (header files for libpq5 - PostgreSQL library)::

    apt-get install libpq-dev

  But under Ubuntu 12.04 this is not needed.

verdi not in PATH
-----------------

Installing the ``aiida-core`` python package *should* add the ``verdi`` CLI to your ``PATH`` automatically.

If the ``verdi`` executable is not available in your terminal, the folder where ``pip`` places binaries may not be added to your ``PATH``

For Linux systems, this folder is usually something like ``~/.local/bin``::

    export PATH=~/.local/bin:${PATH}

For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::

    export PATH=~/Library/Python/2.7/bin:${PATH}

After updating your ``PATH``, the ``verdi`` command should be available.

.. note::
    A preprequisite for ``verdi`` to work is that the ``aiida`` python package is importable.
    Test this by opening a ``python`` or ``ipython`` shell and typing::

        import aiida

   If you get an ``ImportError`` (and you are in the environment where AiiDA was installed),
   you can add it to the ``PYTHONPATH`` manually::

       export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"



Configuring remote SSH computers
--------------------------------

* [**ssh_kerberos installation**] When installing the ``ssh_kerberos`` *optional*
  requirement through Anaconda you may encounter the following error on Ubuntu machines::

    version 'GFORTRAN_1.4' not found (required by /usr/lib/libblas.so.3)

  This is related to an open issue in anaconda `ContinuumIO/anaconda-issues#686`_.
  A potential solution is to run the following command::

    export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libgfortran.so.3

.. _ContinuumIO/anaconda-issues#686: https://github.com/ContinuumIO/anaconda-issues/issues/686

* [**Output from .bashrc and/or .bash_profile on remote computers**]
  (**NOTE** This applies also computers configured via ``local`` transport!)

  When connecting to remote computers, AiiDA (like other codes as ``sftp``)
  can get confused if you have code in your ``.bashrc`` or
  ``.bash_profile`` that produces output or e.g. runs commands like ``clean``
  that require a terminal.

  For instance, if you add a ``echo "a"`` in your ``.bashrc`` and then try to SFTP
  a file from it, you will get an error like ``Received message too long 1091174400``.

  If you still want to have code that needs an interactive shell (``echo``,
  ``clean``, ...), but you want to disable it for non-interactive shells, put
  at the top of your file a guard like this::

    if [[ $- != *i* ]] ; then
      # Shell is non-interactive.  Be done now!
      return
    fi

  Everything below this will not be executed in a non-interactive shell.
  **Note**: Still, you might want to have some code on top, like e.g. setting the PATH or
  similar, if this needs to be run also in the case of non-interactive shells.

  To test if a the computer does not produce spurious output, run (after
  configuring)::

     verdi computer test <COMPUTERNAME>

  which checks and, in case of problems, suggests how to solve the problem.
  You can track the discussion on this issue in `aiidateam/aiida-core#1890`_.

.. _aiidateam/aiida-core#1890: https://github.com/aiidateam/aiida-core/issues/1890
.. _StackExchange thread: https://apple.stackexchange.com/questions/51036/what-is-the-difference-between-bash-profile-and-bashrc


Improvements for dependencies
-----------------------------
* [**Activating the ASE visualizer**] Within a virtual environment,
  attempt to visualize a structure
  with ``ase`` (either from the shell, or using the
  command ``verdi data structure show --format=ase <PK>``),
  might end up with the following error message::

     ImportError: No module named pygtk

  The issue is that ``pygtk`` is currently not pip-installable. One has to install it
  separately and create the appropriate bindings manually in the virtual environment.
  You can follow the following procedure to get around this issue:

  + Install the ``python-gtk2`` package. Under Ubuntu, do::

     sudo apt-get install python-gtk2

  + Create the ``lib/python2.7/dist-packages`` folder within your virtual
    environment::

     mkdir <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
     chmod 755 <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages

    where ``<AIIDA_VENV_FOLDER>`` is the virtual environment folder you have created
    during the installation process.

  + Create several symbolic links from this folder, pointing to a number of files
    in ``/usr/lib/python2.7/dist-packages/``::

     cd <AIIDA_VENV_FOLDER>/lib/python2.7/dist-packages
     ln -s /usr/lib/python2.7/dist-packages/glib glib
     ln -s /usr/lib/python2.7/dist-packages/gobject gobject
     ln -s /usr/lib/python2.7/dist-packages/gtk-2.0 gtk-2.0
     ln -s /usr/lib/python2.7/dist-packages/pygtk.pth pygtk.pth
     ln -s /usr/lib/python2.7/dist-packages/pygtk.py pygtk.py
     ln -s /usr/lib/python2.7/dist-packages/cairo cairo

  After that, ``verdi data structure show --format=ase <PK>`` should work.

Use in ipython/jupyter
----------------------

* In order to use the AiiDA objects and functions in Jupyter, this latter has to be instructed to use the iPython kernel installed in the AiiDA virtual environment. This happens by default if you install AiiDA with ``pip`` including the ``notebook`` option and run Jupyter from the AiiDA virtual environment.

  If, for any reason, you do not want to install Jupyter in the virtual environment, you might consider to install it out of the virtual environment, if not already done::

      pip install jupyter

  Then, activate the AiiDA virtual environment::

      source ~/<aiida.virtualenv>/bin/activate

  and setup the AiiDA iPython kernel::

      pip install ipykernel
      python -m ipykernel install --user --name=<aiida.kernel.name>

  where you have chosen a meaningful name for the new kernel.

  Finally, start a Jupyter server::

      jupyter notebook

  and from the newly opened browser tab select ``New -> <aiida.kernel.name>``

Postgres restart problem
------------------------

Due to a `bug <https://wiki.postgresql.org/wiki/May_2015_Fsync_Permissions_Bug>` affecting older postgres versions (<9.4),
PostgreSQL could refuse to restart after a crash or after a restore from binary backup.

The error message would be something like::

    * Starting PostgreSQL 9.1 database server
    * The PostgreSQL server failed to start. Please check the log output:
    2015-05-26 03:27:20 UTC [331-1] LOG:  database system was interrupted; last known up at 2015-05-21 19:56:58 UTC
    2015-05-26 03:27:20 UTC [331-2] FATAL:  could not open file "/etc/ssl/certs/ssl-cert-snakeoil.pem": Permission denied
    2015-05-26 03:27:20 UTC [330-1] LOG:  startup process (PID 331) exited with exit code 1
    2015-05-26 03:27:20 UTC [330-2] LOG:  aborting startup due to startup process failure

If this happens you should change the permissions on any symlinked files
to being writable by the Postgres user. For example, on Ubuntu, with PostgreSQL 9.1,
the following should work (**WARNING**: Make sure these configuration files are
symbolic links before executing these commands! If someone has customized the server.crt
or server.key file, you can erase them by following these steps.
It's a good idea to make a backup of the server.crt and server.key files before removing them)::

    (as root)
    # go to PGDATA directory
    cd /var/lib/postgresql/9.1/main
    ls -l server.crt server.key
    # confirm both of those files are symbolic links
    # to files in /etc/ssl before going further
    # remove symlinks to SSL certs
    rm server.crt
    rm server.key
    # copy the SSL certs to the local directory
    cp /etc/ssl/certs/ssl-cert-snakeoil.pem server.crt
    cp /etc/ssl/private/ssl-cert-snakeoil.key server.key
    # set permissions on ssl certs
    # and postgres ownership on everything else
    # just in case
    chown postgres *
    chmod 640 server.crt server.key

    service postgresql start
