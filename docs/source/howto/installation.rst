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
A new profile can be created using :ref:`verdi quicksetup<reference:command-line:verdi-quicksetup>` or :ref:`verdi setup<reference:command-line:verdi-setup>`, which works similar to the former but gives more control to the user.

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

    Info: Profile: project-one
    ----------------------  ------------------------------------------------
    aiidadb_backend         django
    aiidadb_engine          postgresql_psycopg2
    aiidadb_host            localhost
    aiidadb_name            aiida_project_one
    aiidadb_pass            correcthorsebatterystaple
    aiidadb_port            5432
    aiidadb_repository_uri  file:///home/user/.virtualenvs/aiida/repository/
    aiidadb_user            aiida
    default_user_email      user@email.com
    options                 {'daemon_default_workers': 3}
    profile_uuid            4c272a87d7f543b08da9fe738d88bb13
    ----------------------  ------------------------------------------------

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
To enable tab-completion, the following shell command should be executed:

.. code:: bash

    $ eval "$(_VERDI_COMPLETE=source verdi)"

Place this command in your shell or virtual environment activation script to automatically enable tab completion when opening a new shell or activating an environment.
This file is shell specific, but likely one of the following:

    * the startup file of your shell (``.bashrc``, ``.zsh``, ...), if aiida is installed system-wide
    * the `activation script <https://virtualenv.pypa.io/en/latest/userguide/#activate-script>`_ of your virtual environment
    * a `startup file <https://conda.io/docs/user-guide/tasks/manage-environments.html#saving-environment-variables>`_ for your conda environment


.. important::

    After you have added the line to the start up script, make sure to restart the terminal or source the script for the changes to take effect.


.. _how-to:installation:configure:options:

Configuring profile options
---------------------------
AiiDA provides various configurational options for profiles, which can be controlled with the :ref:`verdi config<reference:command-line:verdi-config>` command.
To set a configurational option, simply pass the name of the option and the value to set ``verdi config OPTION_NAME OPTION_VALUE``.
The available options are tab-completed, so simply type ``verdi config`` and thit <TAB> twice to list them.

For example, if you want to change the default number of workers that are created when you start the daemon, you can run:

.. code:: bash

    $ verdi config daemon.default_workers 5
    Success: daemon.default_workers set to 5 for profile-one

You can check the currently defined value of any option by simply calling the command without specifying a value, for example:

.. code:: bash

    $ verdi config daemon.default_workers
    5

If no value is displayed, it means that no value has ever explicitly been set for this particular option and the default will always be used.
By default any option set through ``verdi config`` will be applied to the current default profile.
To change the profile you can use the :ref:`profile option<topics:cli:profile>`.

To undo the configuration of a particular option and reset it so the default value is used, you can use the ``--unset`` option:

.. code:: bash

    $ verdi config daemon.default_workers --unset
    Success: daemon.default_workers unset for profile-one

If you want to set a particular option that should be applied to all profiles, you can use the ``--global`` flag:

.. code:: bash

    $ verdi config daemon.default_workers 5 --global
    Success: daemon.default_workers set to 5 globally

and just as on a per-profile basis, this can be undone with the ``--unset`` flag:

.. code:: bash

    $ verdi config daemon.default_workers --unset --global
    Success: daemon.default_workers unset globally

.. important::

    Changes that affect the daemon (e.g. ``logging.aiida_loglevel``) will only take affect after restarting the daemon.


.. _how-to:installation:configure:instance-isolation:

Isolating multiple instances
----------------------------
An AiiDA instance is defined as the installed source code plus the configuration folder that stores the configuration files with all the configured profiles.
It is possible to run multiple AiiDA instances on a single machine, simply by isolating the code and configuration in a virtual environment.

To isolate the code, simply create a virtual environment, e.g., with conda or venv, and then follow the instructions for :ref:`installation<intro/install_advanced>` after activation.
Whenever you activate this particular environment, you will be running the particular version of AiiDA (and all the plugins) that you installed specifically for it.

This is separate from the configuration of AiiDA, which is stored in the configuration directory which is always named ``.aiida`` and by default is stored in the home directory.
Therefore, the default path of the configuration directory is ``~/.aiida``.
By default, each AiiDA instance (each installation) will store associated profiles in this folder.
A best practice is to always separate the profiles together with the code to which they belong.
The typical approach is to place the configuration folder in the virtual environment itself and have it automatically selected whenever the environment is activated.

The location of the AiiDA configuration folder, can be controlled with the ``AIIDA_PATH`` environment variable.
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


.. _how-to:installation:plugins:

Installing plugins
==================

`#4122`_


.. _how-to:installation:performance:

Tuning performance
==================

`#4002`_


.. _how-to:installation:update:

Updating your installation
==========================

`#4003`_


.. _how-to:installation:backup:

Backing up your installation
============================

`#4004`_


.. _how-to:installation:multi-user:

Managing multiple users
=======================

`#4005`_



.. _#4002: https://github.com/aiidateam/aiida-core/issues/4002
.. _#4003: https://github.com/aiidateam/aiida-core/issues/4003
.. _#4004: https://github.com/aiidateam/aiida-core/issues/4004
.. _#4005: https://github.com/aiidateam/aiida-core/issues/4005
.. _#4122: https://github.com/aiidateam/aiida-core/issues/4122
