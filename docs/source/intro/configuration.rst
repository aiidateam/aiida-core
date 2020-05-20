.. _configure_aiida:

=================
Configuring AiiDA
=================

.. _tab-completion:

Verdi tab-completion
--------------------

The ``verdi`` command line interface has many commands and options, which can be tab-completed to simplify your life.
Enable tab-completion with the following shell command:

.. code-block:: bash

   eval "$(_VERDI_COMPLETE=source verdi)"

Place this command in your startup file, i.e. one of

* the startup file of your shell (``.bashrc``, ``.zsh``, ...), if aiida is installed system-wide
* the `activate script <https://virtualenv.pypa.io/en/latest/userguide/#activate-script>`_ of your virtual environment
* a `startup file <https://conda.io/docs/user-guide/tasks/manage-environments.html#saving-environment-variables>`_ for your conda environment

In order to enable tab completion in your current shell, make sure to source the start-up file once.

.. note::

    This line replaces the ``eval "$(verdi completioncommand)"`` line that was used in ``aiida-core<1.0.0``. While this continues to work, support for the old line may be dropped in the future.


.. _setup_aiida:

AiiDA profile setup
===================

After successful installation, you need to create an AiiDA profile via AiiDA's command line interface ``verdi``.

Most users should use the interactive quicksetup:

.. code-block:: console

    $ verdi quicksetup <profile_name>

which leads through the installation process and takes care of creating the corresponding AiiDA database.

For maximum control and customizability, one can use ``verdi setup`` and set up the database manually as explained below.

.. _database:

Database setup
--------------

AiiDA uses a database to store the nodes, node attributes and other information, allowing the end user to perform fast queries of the results.
Currently, the highly performant `PostgreSQL`_ database is supported as a database backend.

.. _PostgreSQL: https://www.postgresql.org/downloads

To manually create the database for AiiDA, you need to run the program ``psql`` to interact with postgres.
On most operating systems, you need to do so as the ``postgres`` user that was created upon installing the software.
To assume the role of ``postgres`` run as root::

    su - postgres

(or, equivalently, type ``sudo su - postgres``, depending on your distribution) and launch the postgres program::

    psql

Create a new database user account for AiiDA by running::

    CREATE USER aiida WITH PASSWORD '<password>';

replacing ``<password>`` with a password of your choice.

You will need to provide the password again when you configure AiiDA to use this database through ``verdi setup``.
If you want to change the password you just created use the command::

    ALTER USER aiida PASSWORD '<password>';

Next, we create the database itself. We enforce the UTF-8 encoding and specific locales::

    CREATE DATABASE aiidadb OWNER aiida ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0;

and grant all privileges on this DB to the previously-created ``aiida`` user::

    GRANT ALL PRIVILEGES ON DATABASE aiidadb to aiida;

You have now created a database for AiiDA and you can close the postgres shell by typing ``\q``.
To test if the database was created successfully, you can run the following command as a regular user in a bash terminal::

    psql -h localhost -d aiidadb -U aiida -W

and type the password you inserted before, when prompted.
If everything worked well, you should get no error and see the prompt of the ``psql`` shell.

If you use the same names as in the example commands above, then during the ``verdi setup`` phase the following parameters will apply to the newly created database::

    Database engine: postgresql_psycopg2
    Database host: localhost
    Database port: 5432
    AiiDA Database name: aiidadb
    AiiDA Database user: aiida
    AiiDA Database password: <password>

.. note:: Do not forget to backup your database (instructions :ref:`here<backup_postgresql>`).

.. note:: If you want to move the physical location of the data files
  on your hard drive AFTER it has been created and filled, look at the
  instructions :ref:`here<move_postgresql>`.


Database setup using 'peer' authentication
++++++++++++++++++++++++++++++++++++++++++

On Ubuntu Linux, the default PostgreSQL setup is configured to use ``peer`` authentication, which allows password-less login via local Unix sockets.
In this mode, PostgreSQL compares the Unix user connecting to the socket with its own database of users and allows a connection if a matching user exists.

.. note::
    This is an alternative route to set up your database - the standard approach will work on Ubuntu just as well.

Below we are going to take advantage of the command-line utilities shipped on Ubuntu to simplify creating users and databases compared to issuing the SQL commands directly.

Assume the role of ``postgres``::

    sudo su postgres

Create a database user with the **same name** as the UNIX user who will be running AiiDA (usually your login name)::

    createuser <username>

replacing ``<username>`` with your username.

Next, create the database itself with your user as the owner::

    createdb -O <username> aiidadb

Exit the shell to go back to your login user.
To test if the database was created successfully, try::

    psql aiidadb


During the ``verdi setup`` phase, use ``!`` to leave host empty and specify your Unix user name as the *AiiDA Database user*.::

    Database engine: postgresql_psycopg2
    Database host: !
    Database port: 5432
    AiiDA Database name: aiidadb
    AiiDA Database user: <username>
    AiiDA Database password: ""


Setup instructions
------------------

After the database has been created, do


.. code-block:: bash

    verdi setup <profile_name>

where `<profile_name>` is a profile name of your choosing.
The ``verdi setup`` command will guide you through the setup process through a series of prompts.

The first information asked is your email, which will be used to associate the calculations to you.
In AiiDA, the email is your username, and acts as a unique identifier when importing/exporting data from AiiDA.

.. note:: The password, in the current version of AiiDA, is not used (it will
    be used only in the REST API and in the web interface). If you leave the
    field empty, no password will be set and no access will be granted to the
    user via the REST API and the web interface.

Then, the following prompts will help you configure the database. Typical settings are::

    Default user email: richard.wagner@leipzig.de
    Database engine: postgresql_psycopg2
    PostgreSQL host: localhost
    PostgreSQL port: 5432
    AiiDA Database name: aiida_dev
    AiiDA Database user: aiida
    AiiDA Database password: <password>
    AiiDA repository directory: /home/wagner/.aiida/repository/
    [...]
    Configuring a new user with email 'richard.wagner@leipzig.de'
    First name: Richard
    Last name: Wagner
    Institution: BRUHL, LEIPZIG
    The user has no password, do you want to set one? [y/N] y
    Insert the new password:
    Insert the new password (again):


Remember that in order to work with AiiDA through for example the ``verdi``
command, you need to be in your virtual environment.
If you open a new terminal for example, be sure to activate it first with::

    source ~/.virtualenvs/aiida/bin/activate

.. _start_daemon:

Start the daemon
================

The AiiDA daemon process runs in the background and takes care of processing your submitted calculations and workflows, checking their status, retrieving their results once they are finished and storing them in the AiiDA database.

The AiiDA daemon is controlled using three simple commands:

 * ``verdi daemon start``: start the daemon
 * ``verdi daemon status``: check the status of the daemon
 * ``verdi daemon stop``: stop the daemon

.. note::
    While operational, the daemon logs its activity to a file in ``~/.aiida/daemon/log/`` (or, more generally, ``$AIIDA_PATH/.aiida/daemon/log``).
    Get the latest log messages via ``verdi daemon logshow``.


Final checks
============

Use the ``verdi status`` command to check that all services are up and running:

.. code-block:: bash

    verdi status

     ✓ profile:     On profile quicksetup
     ✓ repository:  /repo/aiida_dev/quicksetu
     ✓ postgres:    Connected to aiida@localhost:5432
     ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
     ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

In the example output, all service have a green check mark and so should be running as expected.

At this point, you're ready to :ref:`get started<get_started>`.

For configuration of tab completion , using AiiDA in jupyter & more, see the :ref:`configuration instructions <configure_aiida>` before moving on.


Using AiiDA in Jupyter
----------------------

`Jupyter <http://jupyter.org>`_ is an open-source web application that allows you to create in-browser notebooks containing live code, visualizations and formatted text.

Originally born out of the iPython project, it now supports code written in many languages and customized iPython kernels.

If you didn't already install AiiDA with the ``[notebook]`` option (during ``pip install``), run ``pip install jupyter`` **inside** the virtualenv, and then run **from within the virtualenv**::

    jupyter notebook

This will open a tab in your browser. Click on ``New -> Python`` and type::

    import aiida

followed by ``Shift-Enter``. If no exception is thrown, you can use AiiDA in Jupyter.

If you want to set the same environment as in a ``verdi shell``,
add the following code to a ``.py`` file (create one if there isn't any) in ``<home_folder>/.ipython/profile_default/startup/``::



  try:
      import aiida
  except ImportError:
      pass
  else:
      import IPython
      from aiida.tools.ipython.ipython_magics import load_ipython_extension

      # Get the current Ipython session
      ipython = IPython.get_ipython()

      # Register the line magic
      load_ipython_extension(ipython)

This file will be executed when the ipython kernel starts up and enable the line magic ``%aiida``.
Alternatively, if you have a ``aiida-core`` repository checked out locally,
you can just copy the file ``<aiida-core>/aiida/tools/ipython/aiida_magic_register.py`` to the same folder.
The current ipython profile folder can be located using::

  ipython locate profile

After this, if you open a Jupyter notebook as explained above and type in a cell::

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."
This line magic should also be enabled in standard ipython shells.
