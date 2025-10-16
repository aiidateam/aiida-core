.. _installation:guide-complete:

===========================
Complete installation guide
===========================

The :ref:`quick installation guide <installation:guide-quick>` is designed to make the setup as simple and portable as possible.
However, the resulting setup has some :ref:`limitations <installation:guide-quick:limitations>` concerning the available functionality and performance.
This guide provides detailed information and instructions to set up a feature-complete and performant installation.

Setting up a working installation of AiiDA, involves the following steps:

#. :ref:`Install the Python Package <installation:guide-complete:python-package>`
#. :ref:`(Optional) RabbitMQ <installation:guide-complete:rabbitmq>`
#. :ref:`Create a profile <installation:guide-complete:create-profile>`


.. _installation:guide-complete:python-package:

Install Python Package
======================

.. important::
    AiiDA requires a recent version of Python.
    Please refer to the `Python Package Index (PyPI) <https://pypi.org/project/aiida-core/>`_ for the minimum required version.

To install AiiDA, the ``aiida-core`` Python package needs to be installed which can be done in a number of ways:


.. tab-set::

    .. tab-item:: pip

        Installing ``aiida-core`` from PyPI.

        #. Install `pip <https://pip.pypa.io/en/stable/installation/>`_.
        #. Install ``aiida-core``:

           .. code-block:: console

               pip install aiida-core

    .. tab-item:: conda

        Installing ``aiida-core`` using Conda.

        #. Install `conda <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_.

        #. Create an environment and install ``aiida-core``:

           .. code-block:: console

               conda create -n aiida -c conda-forge aiida-core

           .. tip::
               As of conda v23.10, the `dependency solver <https://conda.org/blog/2023-11-06-conda-23-10-0-release/#with-this-23100-release-we-are-changing-the-default-solver-of-conda-to-conda-libmamba-solver-->`_ has been significantly improved.
               If you are experiencing long installation times, you may want to consider updating conda.

    .. tab-item:: source

        Installing ``aiida-core`` directory from source.

        #. Install `git <https://www.git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
        #. Clone the repository from Github

           .. code-block:: console

               git clone https://github.com/aiidateam/aiida-core

        #. Install `pip <https://pip.pypa.io/en/stable/installation/>`_.
        #. Install ``aiida-core``:

           .. code-block:: console

               cd aiida-core
               pip install -e .

           The ``-e`` flag installs the package in editable mode which is recommended for development.
           Any changes made to the source files are automatically picked up by the installation.


.. _installation:guide-complete:python-package:optional-requirements:

Optional requirements
---------------------

The ``aiida-core`` Python package defines a number of optional requirements, subdivided in the following categories:

* ``atomic_tools`` : Requirements to deal with atomic data and structures
* ``docs`` : Requirements to build the documentation
* ``notebook`` : Requirements to run AiiDA in Jupyter notebooks
* ``pre-commit`` :  Requirements to automatically format and lint source code for development
* ``rest`` : Requirements to run the REST API
* ``ssh_kerberos`` : Requirements for enabling SSH authentication through Kerberos
* ``tests`` : Requirements to run the test suite
* ``tui`` : Requirements to provide a textual user interface (TUI)

These optional requirements can be installed using pip by adding them as comma separated list, for example:

.. code-block:: console

    pip install aiida-core[atomic_tools,docs]


.. _installation:guide-complete:rabbitmq:

RabbitMQ
========

`RabbitMQ <https://www.rabbitmq.com/>`_ is an optional but recommended service for AiiDA.
It is a messsage broker that is required to run AiiDA's daemon.
The daemon is a system process that runs in the background that manages one or multiple daemon workers that can run AiiDA processes.
This way, the daemon helps AiiDA to scale as it is possible to run many processes in parallel on the daemon workers instead of blockingly in a single Python interpreter.
To facilitate communication with the daemon workers, RabbitMQ is required.

Although it is possible to run AiiDA without a daemon it does provide significant benefits and therefore it is recommended to install RabbitMQ.

.. tab-set::

    .. tab-item:: conda

        #. Install `conda <https://conda.io/projects/conda/en/latest/user-guide/install/index.html>`_.

        #. Create an environment and install ``aiida-core.services``:

           .. code-block:: console

               conda create -n aiida -c conda-forge aiida-core.services

        .. important::

            The ``aiida-core.services`` package ensures that RabbitMQ is installed in the conda environment.
            However, it is not a *service*, in the sense that it is not automatically started, but has to be started manually.

            .. code-block:: console

                rabbitmq-server -detached

            Note that this has to be done each time after the machine has been rebooted.
            The server can be stopped with:

            .. code-block:: console

                rabbitmqctl stop


    .. tab-item:: Ubuntu

        #. Install RabbitMQ through the ``apt`` package manager:

           .. code-block:: console

                sudo apt install rabbitmq-server

        This should automatically install startup scripts such that the server is automatically started when the machine boots.


    .. tab-item:: MacOS X

        #. Install `Homebrew <https://docs.brew.sh/Installation>`__.

        #. Install RabbitMQ:

           .. code-block:: console

                brew install rabbitmq
                brew services start rabbitmq

        .. important::

            The service has to manually be started each time the machine reboots.

    .. tab-item:: Other

        For all other cases, please refer to the `official documentation <https://www.rabbitmq.com/docs/download>`_ of RabbitMQ.



.. _installation:guide-complete:create-profile:

Create a profile
================

After the ``aiida-core`` package is installed, a profile needs to be created.
A profile defines where the data generated by AiiDA is to be stored.
The data storage can be customized through plugins and so the required configuration changes based on the selected storage plugin.

To create a new profile, run:

.. code-block:: console

    verdi profile setup <storage_entry_point>

where ``<storage_entry_point>`` is the entry point name of the storage plugin selected for the profile.
To list the available storage plugins, run:

.. code-block:: console

    verdi plugin list aiida.storage

AiiDA ships with a number of storage plugins and it is recommended to select one of the following:

.. grid:: 1 2 2 2
   :gutter: 3

   .. grid-item-card:: :fa:`feather;mr-1` ``core.sqlite_dos``
      :text-align: center
      :shadow: md

      Use this for use-cases to explore AiiDA where performance is not critical.

      This storage plugin does not require any services, making it easy to install and use.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: installation:guide-complete:create-profile:core-sqlite-dos
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Create a ``core.sqlite_dos`` profile

   .. grid-item-card:: :fa:`bolt;mr-1` ``core.psql_dos``
      :text-align: center
      :shadow: md

      Use this for production work where database performance is important.

      This storage plugin uses PostgreSQL for the database and provides the greatest performance.

      +++++++++++++++++++++++++++++++++++++++++++++

      .. button-ref:: installation:guide-complete:create-profile:core-psql-dos
         :click-parent:
         :expand:
         :color: primary
         :outline:

         Create a ``core.psql_dos`` profile


.. seealso::

    See the :ref:`topic on storage <topics:storage>` to see a more detailed overview of the storage plugins provided by ``aiida-core`` with their strengths and weaknesses.

Other packages may provide additional storage plugins, which are also installable through ``verdi profile setup``.


.. _installation:guide-complete:create-profile:common-options:

Common options
--------------

The exact options available for the ``verdi profile setup`` command depend on the selected storage plugin, but there are a number of common options and functionality:

* ``--profile-name``: The name of the profile.
* ``--set-as-default``: Whether the new profile should be defined as the new default.
* ``--email``: Email for the default user that is created.
* ``--first-name``: First name for the default user that is created.
* ``--last-name``: Last name for the default user that is created.
* ``--institution``: Institution for the default user that is created.
* ``--use-rabbitmq/--no-use-rabbitmq``: Whether to configure the RabbitMQ broker.
  Required to enable the daemon and submitting processes to it.
  The default is ``--use-rabbitmq``, in which case the command tries to connect to RabbitMQ running on the localhost with default connection parameters.
  If this fails, a warning is issued and the profile is configured without a broker.
  Once the profile is created, RabbitMQ can still be enabled through ``verdi profile configure-rabbitmq`` which allows to customize the connection parameters.
* ``--non-interactive``: By default, the command prompts to specify a value for all options.
  Alternatively, the ``--non-interactive`` flag can be specified, in which case the command never prompts and the options need to be specified directly on the command line.
  This is useful when using ``verdi profile setup`` is used in non-interactive environments, such as scripts.
* ``--config``: Instead of passing all options through command line options, the value can be defined in a YAML file and pass its filepath through this option.


.. _installation:guide-complete:create-profile:core-sqlite-dos:

``core.sqlite_dos``
-------------------

.. tip::

    The ``verdi presto`` command provides a fully automated way to set up a profile with the ``core.sqlite_dos`` storage plugin if no configuration is required.

This storage plugin uses `SQLite <https://sqlite.org/>`_ and the `disk-objectstore <https://disk-objectstore.readthedocs.io/en/latest/>`_ to store data.
The ``disk-objectstore`` is a Python package that is automatically installed as a dependency when installing ``aiida-core``, which was covered in the :ref:`Python package installation section <installation:guide-complete:python-package>`.
The installation instructions for SQLite depend on your system; please visit the `SQLite website <https://www.sqlite.org/download.html>`_ for details.

Once the prerequisistes are met, create a profile with:

.. code-block:: console

    verdi profile setup core.sqlite_dos

The options specific to the ``core.sqlite_dos`` storage plugin are:

* ``--filepath``: Filepath of the directory in which to store data for this backend.


.. _installation:guide-complete:create-profile:core-psql-dos:

``core.psql_dos``
-----------------

.. tip::

    The creation of the PostgreSQL user and database as explained below is implemented in an automated way in the ``verdi presto`` command.
    Instead of performing the steps below manually and running ``verdi profile setup core.psql_dos``, it is possible to run:

    .. code-block::

        verdi presto --use-postgres

    The ``verdi presto`` command also automatically tries to configure RabbitMQ as the broker if it is running locally.
    Therefore, if the command succeeds in connecting to both PostgreSQL and RabbitMQ, ``verdi presto --use-postgres`` provides a fully automated way to create a profile suitable for production workloads.

This storage plugin uses `PostgreSQL <https://www.postgresql.org/>`_ and the `disk-objectstore <https://disk-objectstore.readthedocs.io/en/latest/>`_ to store data.
The ``disk-objectstore`` is a Python package that is automatically installed as a dependency when installing ``aiida-core``, which was covered in the :ref:`Python package installation section <installation:guide-complete:python-package>`.
The storage plugin can connect to a PostgreSQL instance running on the localhost or on a server that can be reached over the internet.
Instructions for installing PostgreSQL is beyond the scope of this guide. You can find the installation instructions for your system on the `PostgreSQL website <https://www.postgresql.org/docs/current/tutorial-install.html>`__.

Before creating a profile, a database (and optionally a custom database user) has to be created.
First, connect to PostgreSQL using ``psql``, the `native command line client for PostgreSQL <https://www.postgresql.org/docs/current/app-psql.html>`_:

.. code-block:: console

    psql -h <hostname> -U <username> -W

If PostgreSQL is installed on the localhost, ``<hostname>`` can be replaced with ``localhost``, and the default ``<username>`` is ``postgres``.
While possible to use the ``postgres`` default user for the AiiDA profile, it is recommended to create a custom user:

.. code-block:: sql

   CREATE USER aiida-user WITH PASSWORD '<password>';

replacing ``<password>`` with a secure password.
The name ``aiida-user`` is just an example name and can be customized.
Note the selected username and password as they are needed when creating the profile later on.

After the user has been created, create a database:

.. code-block:: sql

   CREATE DATABASE aiida-database OWNER aiida-user ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';

Again, the selected database name ``aiida-database`` is purely an example and can be customized.
Make sure that the ``OWNER`` is set to the user that was created in the previous step.
Next, grant all privileges on this database to the user:

.. code-block:: sql

   GRANT ALL PRIVILEGES ON DATABASE aiida-database to aiida-user;

After the database has been created, the interactive ``psql`` shell can be closed.
To test if the database was created successfully, run the following command:

.. code-block:: console

    psql -h <hostname> -d <database> -U <username> -W

replacing ``<database>`` and ``<username>`` with the chosen names for the database and user in the previous steps, and providing the chosen password when prompted.

Once the database has been created, create a profile with:

.. code-block:: console

    verdi profile setup core.psql_dos

The options specific to the ``core.psql_dos`` storage plugin are:

* ``--database-engine``   The engine to use to connect to the database.
* ``--database-hostname`` The hostname of the PostgreSQL server.
* ``--database-port``     The port of the PostgreSQL server.
* ``--database-username`` The username with which to connect to the PostgreSQL server.
* ``--database-password`` The password with which to connect to the PostgreSQL server.
* ``--database-name``     The name of the database in the PostgreSQL server.
* ``--repository-uri``    URI to the file repository.

.. _installation:guide-complete:validate-installation:


Validate installation
=====================

Once a profile has been created, validate that everything is correctly set up with:

.. code-block:: console

    verdi status

The output should look something like the following::

    ✔ version:     AiiDA v2.5.1
    ✔ config:      /path/.aiida
    ✔ profile:     profile-name
    ✔ storage:     SqliteDosStorage[/path/.aiida/repository/profile-name]: open,
    ✔ broker:      RabbitMQ v3.8.2 @ amqp://guest:guest@127.0.0.1:5672?heartbeat=600
    ⏺ daemon:      The daemon is not running.

If no lines show red crosses, AiiDA has been correctly installed and is ready to go.
When a new profile is created, the daemon will not yet be running, but it can be started using:

.. code-block:: console

    verdi daemon start

.. note::

    The storage information depends on the storage plugin that was selected.
    The broker may be shown as not having been configured which occurs for profiles created with the :ref:`quick installation method <installation:guide-quick>`.
    This is fine, however, :ref:`some functionality is not supported <installation:guide-quick:limitations>` for broker-less profiles.


.. admonition:: Not all green?
    :class: warning

    If the status reports any problems, please refer to the :ref:`troubleshooting section <installation:troubleshooting>`.
