.. _installation:

************
Installation
************

With all prerequisites in place, we can now install AiiDA and its python dependencies.

.. _virtual_environment:

Virtual python environment
==========================

AiiDA depends on a number of third party python packages, and usually on specific versions of those packages.
In order not to interfere with third party packages needed by
other software on your system, we *strongly* recommend
isolating AiiDA in a `virtual python environment <https://docs.python.org/tutorial/venv.html>`_.
In the following, we describe how to create a virtual python environment using the `virtualenv <https://virtualenv.pypa.io/en/latest/>`_ tool, but feel free to use your preferred environment manager (e.g. `conda <https://conda.io/docs/>`_).

Creating the virtual environment
--------------------------------

To create and activate a new virtual environment, run the following commands::

    pip install --user --upgrade virtualenv      # install virtualenv tool
    virtualenv ~/.virtualenvs/aiida              # create "aiida" environment
    source ~/.virtualenvs/aiida/bin/activate     # activate "aiida" environment

.. note:: We recommend setting up a **python 3** virtual environment.
   If your system runs python 2 by default but has a ``python3`` executable, you can still set up a python 3 virtual environment using::

       virtualenv --python python3 ~/.virtualenvs/aiida

This will create a directory in your home directory named ``.virtualenvs``, and a directory ``aiida`` inside of it where all the packages will be installed.
After activation, your prompt should have ``(aiida)`` in front of it, indicating that you are working inside the virtual environment.
The activation script ensures that the python executable of the virtualenv is the first in ``PATH``, and that python programs have access only to packages installed inside the virtualenv.

To leave or deactivate the environment, simply run::

    (aiida) $ deactivate

.. note:: You may need to install ``pip`` and ``setuptools`` in your virtual environment in case the system or user version of these tools is old::

    (aiida) $ pip install -U setuptools pip


Aiida python package
====================

.. _PyPI: https://pypi.python.org/pypi/aiida
.. _github repository: https://github.com/aiidateam/aiida-core

AiiDA can be installed either from the python package index `PyPI`_ (good for general use) or directly from the aiida-core `github repository`_ (good for developers).

Install the ``aiida`` python package from `PyPI`_ using:

.. code-block:: bash

    pip install --pre aiida

.. note::
    If you are installing AiiDA in your system environment,
    consider adding the ``--user`` flag to avoid the need for
    administrator privileges.

This will install the ``aiida-core`` package along with the four base plugins:

    * ``aiida-ase``
    * ``aiida-codtools``
    * ``aiida-nwchem``
    * ``aiida-quantumespresso``

Alternatively, you can create a directory where to clone the AiiDA source code and install AiiDA from source::

    mkdir <your_directory>
    cd <your_directory>
    git clone https://github.com/aiidateam/aiida-core
    pip install -e aiida-core


.. _install_optional_dependencies:

There are additional optional packages that you may want to install, which are grouped in the following categories:

    * ``atomic_tools``: packages that allow importing and manipulating crystal structure from various formats
    * ``ssh_kerberos``: adds support for ssh transport authentication through Kerberos
    * ``REST``: allows a REST server to be ran locally to serve AiiDA data
    * ``docs``: tools to build the documentation
    * ``advanced_plotting``: tools for advanced plotting
    * ``notebook``: jupyter notebook - to allow it to import AiiDA modules
    * ``testing``: python modules required to run the automatic unit tests

In order to install any of these package groups, simply append them as a comma separated list in the ``pip`` install command::

    (aiida) $ pip install -e aiida-core[atomic_tools,docs,advanced_plotting]

.. note:: If you are installing the optional ``ssh_kerberos`` and you are on Ubuntu you might encounter an error related to the ``gss`` package.
  To fix this you need to install the ``libffi-dev`` and ``libkrb5-dev`` packages::

    sudo apt-get install libffi-dev libkrb5-dev


.. _setup_aiida:

AiiDA profile setup
===================

After successful installation, you need to create an AiiDA profile via AiiDA's command line interface ``verdi``.

Most users should use the interactive quicksetup:

.. code-block:: bash

    verdi quicksetup <profile_name>

which leads through the installation process and takes care of creating the corresponding AiiDA database.

For maximum control and customizability, one can use ``verdi setup``
and set up the database manually as explained below.

.. _database:

Database setup
--------------

AiiDA uses a database to store the nodes, node attributes and other
information, allowing the end user to perform fast queries of the results.
Currently, only `PostgreSQL`_ is allowed as a database backend.

.. _PostgreSQL: https://www.postgresql.org/downloads

To manually create the database for AiiDA, you need to run the program ``psql``
to interact with postgres.
On most operating systems, you need to do so as the ``postgres`` user that was
created upon installing the software.
To assume the role of ``postgres`` run as root::

    su - postgres

and launch the postgres program::

    psql

Create a new database user account for AiiDA by running::

    CREATE USER aiida WITH PASSWORD '<password>';

replacing ``<password>`` with a password of your choice.
Make sure to remember it, as you will need it again when you configure AiiDA to use this database through ``verdi setup``.
If you want to change the password you just created use the command::

    ALTER USER aiida PASSWORD '<password>';

Next we create the database itself. Keep in mind that we enforce the UTF-8 encoding and specific locales::

    CREATE DATABASE aiidadb OWNER aiida ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8' TEMPLATE=template0;

and grant all privileges on this DB to the previously-created ``aiida`` user::

    GRANT ALL PRIVILEGES ON DATABASE aiidadb to aiida;

You have now created a database for AiiDA and you can close the postgres shell by typing ``\q``.
To test if the database was created successfully, you can run the following command as a regular user in a bash terminal::

    psql -h localhost -d aiidadb -U aiida -W

and type the password you inserted before, when prompted.
If everything worked well, you should get no error and see the prompt of the ``psql`` shell.

If you uses the same names used in the example commands above, during the ``verdi setup`` phase you want to use the following parameters to use the database you just created::

    Database engine: postgresql_psycopg2
    PostgreSQL host: localhost
    PostgreSQL port: 5432
    AiiDA Database name: aiidadb
    AiiDA Database user: aiida
    AiiDA Database password: <password>

.. note:: Do not forget to backup your database (instructions :ref:`here<backup_postgresql>`).

.. note:: If you want to move the physical location of the data files
  on your hard drive AFTER it has been created and filled, look at the
  instructions :ref:`here<move_postgresql>`.


Database setup using Unix sockets
+++++++++++++++++++++++++++++++++

Instead of using passwords to protect access to the database
(which could be used by other users on the same machine),
PostgreSQL allows password-less logins via Unix sockets.

In this scenario PostgreSQL compares the user connecting to the socket with its
own database of users and will allow a connection if a matching user exists.

Assume the role of ``postgres`` by running the following as root::

    su - postgres

Create a database user with the **same name** as the user you are using to run AiiDA (usually your login name)::

    createuser <username>

replacing ``<username>`` with your username.

Next, create the database itself making sure that your user is the owner::

    createdb -O <username> aiidadb

To test if the database was created successfully, you can run the following command as your user in a bash terminal::

    psql aiidadb


Make sure to leave the host, port and password empty when specifying the parameters during the ``verdi setup`` phase
and specify your username as the *AiiDA Database user*::

    Database engine: postgresql_psycopg2
    PostgreSQL host:
    PostgreSQL port:
    AiiDA Database name: aiidadb
    AiiDA Database user: <username>
    AiiDA Database password:


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
     ✓ repository:  /repo/aiida_dev/quicksetup
     ✓ postgres:    Connected to aiida@localhost:5432
     ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
     ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

In the example output, all service have a green check mark and so should be running as expected.

At this point, you're ready to :ref:`get started<get_started>`.

For configuration of tab completion , using AiiDA in jupyter & more, see the :ref:`configuration instructions <configure_aiida>` before moving on.
