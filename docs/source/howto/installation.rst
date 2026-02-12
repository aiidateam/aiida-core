.. _how-to:installation:

*******************************
How to manage your installation
*******************************


.. _how-to:installation:profile:

Managing profiles
=================

Creating profiles
-----------------
Each AiiDA installation can have multiple profiles, each of which can have its own individual database and file repository to store the contents of the :ref:`provenance graph<topics:provenance:concepts>`.
Profiles allow you to run multiple projects completely independently from one another with just a single AiiDA installation and at least one profile is required to run AiiDA.
A new profile can be created using :ref:`verdi presto<reference:command-line:verdi-presto>` or :ref:`verdi profile setup<reference:command-line:verdi-profile>`, which works similar to the former but gives more control to the user.

Listing profiles
----------------
The :ref:`verdi profile<reference:command-line:verdi-profile>` command line interface provides various commands to manage the profiles of an AiiDA installation.
To list the currently configured profiles, use ``verdi profile list``:

.. code:: bash

    Info: configuration folder: /home/user/.virtualenvs/aiida/.aiida
    * project-one
      project-two

In this particular example, there are two configured profiles, ``project-one`` and ``project-two``.
The first one is highlighted and marked with a ``*`` symbol, meaning it is the default profile.
A profile being the default means simply that any ``verdi`` command will always be executed for that profile.
You can :ref:`change the profile on a per-call basis<topics:cli:profile>` with the ``--p/--profile`` option.
To change the default profile use ``verdi profile setdefault PROFILE``.

Showing profiles
----------------
Each profile defines various parameters, such as the location of the file repository on the file system and the connection parameters for the database.
To display these parameters, use ``verdi profile show``:

.. code:: bash

    Report: Profile: a-import-sqla
    PROFILE_UUID: fede89dae42b4df3bf46ab27e2b500ca
    default_user_email: user@email.com
    process_control:
        backend: rabbitmq
        config:
            broker_host: 127.0.0.1
            broker_password: guest
            broker_port: 5672
            broker_protocol: amqp
            broker_username: guest
            broker_virtual_host: ''
    storage:
        backend: core.psql_dos
        config:
            database_engine: postgresql_psycopg
            database_hostname: localhost
            database_name: name
            database_password: abc
            database_port: 5432
            database_username: username
            repository_uri: file:///path/to/repository

By default, the parameters of the default profile are shown, but one can pass the profile name of another, e.g., ``verdi profile show project-two`` to change that.

Deleting profiles
-----------------
A profile can be deleted using the ``verdi profile delete`` command.
By default, deleting a profile will also delete its file repository and the database.
This behavior can be changed using the ``--skip-repository`` and ``--skip-db`` options.

.. note::

    In order to delete the database, the system user needs to have the required rights, which is not always guaranteed depending on the system.
    In such cases, the database deletion may fail and the user will have to perform the deletion manually through PostgreSQL.


.. _how-to:installation:configure:

Configuring your installation
=============================

.. _how-to:installation:configure:tab-completion:

Activating tab-completion
-------------------------
The ``verdi`` command line interface has many commands and parameters, which can be tab-completed to simplify its use.
To enable tab-completion, the following shell command should be executed (depending on the shell you use):

Enable tab-completion for ``verdi`` one of the following supported shells

.. tab-set::

    .. tab-item:: bash

        .. code-block:: console

            eval "$(_VERDI_COMPLETE=bash_source verdi)"

    .. tab-item:: zsh

        .. code-block:: console

            eval "$(_VERDI_COMPLETE=zsh_source verdi)"

    .. tab-item:: fish

        .. code-block:: console

            eval (env _VERDI_COMPLETE=fish_source verdi)


Place this command in your shell or virtual environment activation script to automatically enable tab completion when opening a new shell or activating an environment.
This file is shell specific, but likely one of the following:

* the startup file of your shell (``.bashrc``, ``.zsh``, ...), if aiida is installed system-wide
* the `activators <https://virtualenv.pypa.io/en/latest/user_guide.html#activators>`_ of your virtual environment
* a `startup file <https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#saving-environment-variables>`_ for your conda environment


.. important::

    After you have added the line to the start up script, make sure to restart the terminal or source the script for the changes to take effect.


.. _how-to:installation:configure:options:

Configuring profile options
---------------------------

AiiDA provides various configurational options for profiles, which can be controlled with the :ref:`verdi config<reference:command-line:verdi-config>` command.

To view all configuration options set for the current profile:

.. code:: console

    $ verdi config list
    name                                   source    value
    -------------------------------------  --------  ------------
    autofill.user.email                    global    abc@test.com
    autofill.user.first_name               global    chris
    autofill.user.institution              global    epfl
    autofill.user.last_name                global    sewell
    caching.default_enabled                default   False
    caching.disabled_for                   default
    caching.enabled_for                    default
    daemon.default_workers                 default   1
    daemon.timeout                         profile   20
    daemon.worker_process_slots            default   200
    db.batch_size                          default   100000
    logging.aiida_loglevel                 default   REPORT
    logging.alembic_loglevel               default   WARNING
    logging.circus_loglevel                default   INFO
    logging.db_loglevel                    default   REPORT
    logging.kiwipy_loglevel                default   WARNING
    logging.paramiko_loglevel              default   WARNING
    logging.plumpy_loglevel                default   WARNING
    logging.sqlalchemy_loglevel            default   WARNING
    rmq.task_timeout                       default   10
    runner.poll.interval                   profile   50
    transport.task_maximum_attempts        global    6
    transport.task_retry_initial_interval  default   20
    verdi.shell.auto_import                default
    warnings.showdeprecations              default   True

Configuration option values are taken, in order of priority, from either the profile specific setting, the global setting (applies to all profiles), or the default value.

You can also filter by a prefix:

.. code:: console

    $ verdi config list transport
    name                                   source    value
    -------------------------------------  --------  ------------
    transport.task_maximum_attempts        global    6
    transport.task_retry_initial_interval  default   20

To show the full information for a configuration option or get its current value:

.. code:: console

    $ verdi config show transport.task_maximum_attempts
    schema:
        default: 5
        description: Maximum number of transport task attempts before a Process is Paused.
        minimum: 1
        type: integer
    values:
        default: 5
        global: 6
        profile: <NOTSET>
    $ verdi config get transport.task_maximum_attempts
    6

You can also retrieve the value *via* the API:

.. code-block:: ipython

    In [1]: from aiida import get_config_option
    In [2]: get_config_option('transport.task_maximum_attempts')
    Out[2]: 6

To set a value, at the profile or global level:

.. code-block:: console

    $ verdi config set transport.task_maximum_attempts 10
    Success: 'transport.task_maximum_attempts' set to 10 for 'quicksetup' profile
    $ verdi config set --global transport.task_maximum_attempts 20
    Success: 'transport.task_maximum_attempts' set to 20 globally
    $ verdi config show transport.task_maximum_attempts
    schema:
        type: integer
        default: 5
        minimum: 1
        description: Maximum number of transport task attempts before a Process is Paused.
    values:
        default: 5
        global: 20
        profile: 10
    $ verdi config get transport.task_maximum_attempts
    10

.. tip::

    By default any option set through ``verdi config`` will be applied to the current default profile.
    To change the profile you can use the :ref:`profile option<topics:cli:profile>`.

Similarly to unset a value:

.. code-block:: console

    $ verdi config unset transport.task_maximum_attempts
    Success: 'transport.task_maximum_attempts' unset for 'quicksetup' profile
    $ verdi config unset --global transport.task_maximum_attempts
    Success: 'transport.task_maximum_attempts' unset globally
    $ verdi config show transport.task_maximum_attempts
    schema:
        type: integer
        default: 5
        minimum: 1
        description: Maximum number of transport task attempts before a Process is Paused.
    values:
        default: 5
        global: <NOTSET>
        profile: <NOTSET>
    $ verdi config get transport.task_maximum_attempts
    5

.. important::

    Changes that affect the daemon (e.g. ``logging.aiida_loglevel``) will only take affect after restarting the daemon.

.. seealso:: :ref:`How-to configure caching <how-to:run-codes:caching>`


.. _how-to:installation:configure:warnings:

Controlling warnings
--------------------

AiiDA may emit warnings for a variety of reasons, for example, warnings when a deprecated part of the code is used.
These warnings are on by default as they provide the user with important information.
The warnings can be turned off using the ``warnings.showdeprecations`` config option, for example:

.. code-block:: console

    verdi config set warnings.showdeprecations false

.. tip::

    The command above changes the option for the current profile.
    However, certain warnings are emitted before a profile can be loaded, for example, when certain modules are imported.
    To also silence these warnings, apply the option globally:

        .. code-block:: console

            verdi config set warnings.showdeprecations false --global

In addition to the config option, AiiDA also provides the dedicated environment variable ``AIIDA_WARN_v{version}`` for deprecation warnings.
Here ``{version}`` is the version number in which the deprecated code will be removed, e.g., ``AIIDA_WARN_v3``.
This environment variable can be used to enable deprecation warnings even if ``warnings.showdeprecations`` is turned off.
This can be useful to temporarily enable deprecation warnings for a single command, e.g.:

.. code-block:: console

    AIIDA_WARN_v3=1 verdi run script.py


.. _how-to:installation:configure:instance-isolation:

Isolating multiple instances
----------------------------
An AiiDA instance is defined as the installed source code plus the configuration folder that stores the configuration files with all the configured profiles.
It is possible to run multiple AiiDA instances on a single machine, simply by isolating the code and configuration in a virtual environment.

To isolate the code, make sure to install AiiDA into a virtual environment, e.g., with conda or venv.
Whenever you activate this particular environment, you will be running the particular version of AiiDA (and all the plugins) that you installed specifically for it.

This is separate from the configuration of AiiDA, which is stored in the configuration directory which is always named ``.aiida`` and by default is stored in the home directory.
Therefore, the default path of the configuration directory is ``~/.aiida``.
By default, each AiiDA instance (each installation) will store associated profiles in this folder.
A best practice is to always separate the profiles together with the code to which they belong.
The typical approach is to place the configuration folder in the virtual environment itself and have it automatically selected whenever the environment is activated.

The location of the AiiDA configuration folder can be controlled with the ``AIIDA_PATH`` environment variable.
This allows us to change the configuration folder automatically, by adding the following lines to the activation script of a virtual environment.
For example, if the path of your virtual environment is ``/home/user/.virtualenvs/aiida``, add the following line:

.. code:: bash

    $ export AIIDA_PATH='/home/user/.virtualenvs/aiida'

Make sure to reactivate the virtual environment, if it was already active, for the changes to take effect.

.. note::

   For ``conda``, create a directory structure ``etc/conda/activate.d`` in the root folder of your conda environment (e.g. ``/home/user/miniconda/envs/aiida``), and place a file ``aiida-init.sh`` in that folder which exports the ``AIIDA_PATH``.

You can test that everything works by first echoing the environment variable with ``echo $AIIDA_PATH`` to confirm it prints the correct path.
Finally, you can check that AiiDA know also properly realizes the new location for the configuration folder by calling ``verdi profile list``.
This should display the current location of the configuration directory:

.. code:: bash

    Info: configuration folder: /home/user/.virtualenvs/aiida/.aiida
    Critical: configuration file /home/user/.virtualenvs/aiida/.aiida/config.json does not exist

The second line you will only see if you haven't yet setup a profile for this AiiDA instance.
For information on setting up a profile, refer to :ref:`creating profiles<how-to:installation:profile>`.

Besides a single path, the value of ``AIIDA_PATH`` can also be a colon-separated list of paths.
AiiDA will go through each of the paths and check whether they contain a configuration directory, i.e., a folder with the name ``.aiida``.
The first configuration directory that is encountered will be used as the configuration directory.
If no configuration directory is found, one will be created in the last path that was considered.
For example, the directory structure in your home folder ``~/`` might look like this::

    .
    ├── .aiida
    └── project_a
        ├── .aiida
        └── subfolder

If you leave the ``AIIDA_PATH`` variable unset, the default location ``~/.aiida`` will be used.
However, if you set:

.. code:: bash

    $ export AIIDA_PATH='~/project_a:'

the configuration directory ``~/project_a/.aiida`` will be used.

.. warning::

    If there was no ``.aiida`` directory in ``~/project_a``, AiiDA would have created it for you, so make sure to set the ``AIIDA_PATH`` correctly.


.. _how-to:installation:configure:daemon-as-service:

Daemon as a service
===================

The daemon can be set up as a system service, such that it automatically starts at system startup.
How to do this, is operating system specific.
For Ubuntu, here is `a template for the service file <https://github.com/marvel-nccr/ansible-role-aiida/blob/c709088dff74d1e1ae4d8379e740aba35fb2ef97/templates/aiida-daemon%40.service>`_ and `ansible instructions to install the service <https://github.com/marvel-nccr/ansible-role-aiida/blob/c709088dff74d1e1ae4d8379e740aba35fb2ef97/tasks/aiida-daemon.yml>`_.


Tuning performance
==================

Performance tuning for large, high-throughput workloads has been moved to the dedicated :doc:`High-throughput configuration <high_throughput>` guide.


.. _how-to:installation:update:

Updating your installation
==========================

Whenever updating your AiiDA installation, make sure you follow these instructions **very carefully**, even when merely upgrading the patch version!
Failing to do so, may leave your installation in a broken state, or worse may even damage your data, potentially irreparably.

1. Activate the Python environment where AiiDA is installed.
2. Finish all running processes.
    All finished processes will be automatically migrated, but it is not possible to resume unfinished processes.
3. Stop the daemon using ``verdi daemon stop``.
4. :ref:`Create a backup of your database and repository<how-to:installation:backup>`.

   .. warning::

       Once you have migrated your database, you can no longer go back to an older version of ``aiida-core`` (unless you restore your database and repository from a backup).

5. Update your ``aiida-core`` installation.

   * If you have installed AiiDA through ``conda`` simply run: ``conda update aiida-core``.
   * If you have installed AiiDA through ``pip`` simply run: ``pip install --upgrade aiida-core``.
   * If you have installed from the git repository using ``pip install -e .``, first delete all the ``.pyc`` files (``find . -name "*.pyc" -delete``) before updating your branch with ``git pull``.

6. Migrate your database with ``verdi -p <profile_name> storage migrate``.
    Depending on the size of your database and the number of migrations to perform, data migration can take time, so please be patient.

After the database migration finishes, you will be able to continue working with your existing data.

.. note::
    If the update involved a change in the major version number of ``aiida-core``, expect backwards incompatible changes and check whether you also need to update installed plugin packages.

Updating from 0.x.* to 1.*
--------------------------
- `Additional instructions on how to migrate from 0.12.x versions <https://aiida.readthedocs.io/projects/aiida-core/en/v1.2.1/install/updating_installation.html#updating-from-0-12-to-1>`_.
- `Additional instructions on how to migrate from versions 0.4 -- 0.11 <https://aiida.readthedocs.io/projects/aiida-core/en/v1.2.1/install/updating_installation.html#older-versions>`_.
- For a list of breaking changes between the 0.x and the 1.x series of AiiDA, `see here <https://aiida.readthedocs.io/projects/aiida-core/en/v1.2.1/install/updating_installation.html#breaking-changes-from-0-12-to-1>`_.

Updating from 1.* to 2.*
------------------------

See the :doc:`../reference/_changelog` for a list of breaking changes.

.. _how-to:installation:backup:

Backing up your data
============================

General information
-----------------------------------------

The most convenient way to back up the data of a single AiiDA profile is to use

.. code:: bash

    $ verdi --profile <profile_name> storage backup /path/to/destination

This command automatically manages a subfolder structure of previous backups, and new backups are done in an efficient way (using ``rsync`` hard-link functionality to the previous backup).
The command backs up everything that's needed to restore the profile later:

* the AiiDA configuration file ``.aiida/config.json``, from which other profiles are removed (see ``verdi status`` for exact location);
* all the data of the backed up profile (which depends on the storage backend).

The specific procedure of the command and whether it even is implemented depends on the storage backend.

.. note::
    The ``verdi storage backup`` command is implemented in a way to be as safe as possible to use when AiiDA is running, meaning that it will most likely produce an uncorrupted backup even when data is being modified. However, the exact conditions depend on the specific storage backend and to err on the safe side, only perform a backup when the profile is not in use.

Storage backend specific information
-----------------------------------------

Alternatively to the CLI command, one can also manually create a backup. This requires a backup of the configuration file  ``.aiida/config.json`` and the storage backend. The panels below provide instructions for storage backends provided by ``aiida-core``. To determine what storage backend a profile uses, call ``verdi profile show``.

.. tip:: Before creating a backup, it is recommended to run ``verdi storage maintain``.
    This will optimize the storage which can significantly reduce the time required to create the backup.
    For optimal results, run ``verdi storage maintain --full``.
    Note that this requires the profile to not be in use by any other process.

.. tab-set::

    .. tab-item:: psql_dos

        The ``psql_dos`` storage backend is the default backend for AiiDA.
        It stores its data in a PostgreSQL database and a file repository on the local filesystem.
        To fully backup the data stored for a profile, you should backup the associated database and file repository.

        **PostgreSQL database**

        To export the entire database, we recommend to use the `pg_dump <https://www.postgresql.org/docs/12/app-pgdump.html>`_ utility:

        .. code-block:: console

            pg_dump -h <database_hostname> -p <database_port> -d <database_name> -U <database_username> -W > aiida_backup.psql

        The ``-W`` flag will ensure to prompt for the database password.
        The parameters between brackets should be replaced with the values that have been configured for the profile.
        You can retrieve these from the ``storage.config`` returned by the ``verdi profile show`` command.

        .. tip::

            In order to avoid having to enter your database password each time you use the script, you can create a file ``.pgpass`` in your home directory containing your database credentials, as described `in the PostgreSQL documentation <https://www.postgresql.org/docs/12/libpq-pgpass.html>`_.

        **File repository**

        The file repository is a directory on the local file system.
        The most efficient way to create a backup is to use the `rsync <https://en.wikipedia.org/wiki/Rsync>`_ utility.
        The path of the repository is shown in the ``storage.config.repository_uri`` key returned by the ``verdi profile show`` command.
        To create a backup, simply run:

        .. code-block:: console

            rsync -arvz <storage.config.repository_uri> /some/path/aiida_backup


.. _how-to:installation:backup:restore:

Restoring data from a backup
============================

Restoring a backed up AiiDA profile requires:

* restoring the profile information in the AiiDA ``config.json`` file. Simply copy the`profiles` entry from
  the backed up ``config.json`` to the one of the running AiiDA instance (see ``verdi status`` for exact location).
  Some information (e.g. the database parameters) might need to be updated.

* restoring the data of of the backed up profile according to the ``config.json`` entry.
  Like the backup procedure, this is dependent on the storage backend used by the profile.

The panels below provide instructions for storage backends provided by ``aiida-core``.
To determine what storage backend a profile uses, call ``verdi profile show``.
To test if the restoration worked, run ``verdi -p <profile-name> status`` to verify that AiiDA can successfully connect to the data storage.

.. tab-set::

    .. tab-item:: psql_dos

        To restore the backed up data for a profile using the ``core.psql_dos`` backend, you should restore the associated database and file repository.

        **PostgreSQL database**

        To restore the PostgreSQL database from the ``db.psql`` file that was backed up, first you should create an empty database following the instructions described in :ref:`the installation guide <installation:guide-complete:create-profile:core-psql-dos>`.
        The backed up data can then be imported by calling:

        .. code-block:: console

            psql -h <db_hostname> -p <db_port> - U <db_user> -d <db_name> -W < db.psql

        where the parameters need to match with the corresponding AiiDA `config.json` profile entry.

        **File repository**

        To restore the file repository, simply copy the directory that was backed up to the location indicated in AiiDA `config.json` (or the ``storage.config.repository_uri`` key returned by the ``verdi profile show`` command).
        Like the backing up process, we recommend using ``rsync`` for this:

        .. code-block:: console

            rsync -arvz /path/to/backup/container <storage.config.repository_uri>


.. _how-to:installation:multi-user:

Managing multiple users
=======================
AiiDA currently does not support multiple users running concurrently on the same AiiDA profile.
While AiiDA will tag any node with the :py:class:`~aiida.orm.users.User` who created it (the default user is specified in the profile), this information is currently not used internally.
In particular, there is currently no permission system in place to limit the operations that can be performed by a given user.

The typical setup involves each user individually installing AiiDA on their operating system account.
Data can be shared between private AiiDA profiles through :ref:`AiiDA's export and import functionality <how-to:share:archives>`.

Note that while the configuration file of an AiiDA instance contains access credentials (e.g. for the postgresql database or the rabbitmq service), AiiDA does not store sensitive data in the database or file repository, and AiiDA export archives never contain such data.

.. _#4122: https://github.com/aiidateam/aiida-core/issues/4122
.. |Computer| replace:: :py:class:`~aiida.orm.Computer`
