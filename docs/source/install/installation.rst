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

    pip install --user --upgrade virtualenv   # install virtualenv tool
    virtualenv ~/aiidapy                      # create "aiidapy" environment
    source ~/aiidapy/bin/activate             # activate "aiidapy" environment

This will create a directory in your home directory named ``aiidapy`` where all the packages will be installed.
After activation, your prompt should have ``(aiidapy)`` in front of it, indicating that you are working inside the virtual environment.
The activation script ensures that the python executable of the virtualenv is the first in ``PATH``, and that python programs have access only to packages installed inside the virtualenv.

To leave or deactivate the environment, simply run::

    (aiidapy) $ deactivate

.. note:: You may need to install ``pip`` and ``setuptools`` in your virtual environment in case the system or user version of these tools is old::

    (aiidapy) $ pip install -U setuptools pip


.. _aiida_path_in_virtualenv:

Isolating the configuration folder in your virtual environment
--------------------------------------------------------------

When you run AiiDA in multiple virtual environments, it can be convenient to use a separate ``.aiida`` configuration folder for each environment.
To do this, you can use the :ref:```AIIDA_PATH`` mechanism <directory_location>` as follows:

1. Create your virtual environment, as described above
2. At the end of ``~/.virtualenvs/my_env/bin/activate``, add the following line, which will set the ``AIIDA_PATH`` environment variable::

    export AIIDA_PATH='~/.virtualenvs/my_env'

3. Deactivate and re-activate the virtual environment
4. You can test that everything is set up correctly if you can reproduce the following::

    (my_env)$ echo $AIIDA_PATH
    >>> ~/.virtualenvs/my_env

    (my_env)$ verdi profile list
    >>> Info: configuration folder: /home/my_username/.virtualenvs/my_env/.aiida
    >>> Critical: configuration file /home/my_username/.virtualenvs/my_env/.aiida/config.json does not exist

   Note: if you get the 'Critical' message, it simply means that you have not yet run `verdi setup` to configure at least one AiiDA profile.
5. Continue setting up AiiDA with ``verdi setup`` or ``verdi quicksetup``.

Aiida python package
====================

.. _PyPI: https://pypi.python.org/pypi/aiida
.. _github repository: https://github.com/aiidateam/aiida_core

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
    git clone https://github.com/aiidateam/aiida_core
    pip install -e aiida_core


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

    (aiidapy) $ pip install -e aiida_core[atomic_tools,docs,advanced_plotting]

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

    source ~/aiidapy/bin/activate

At this point, you can choose to read on for additional installation details and configuration options, or you can choose to start using
AiiDA and go straight to the section :ref:`get started<get_started>`.


.. _configure_aiida:

Configure AiiDA
===============

.. _tab-completion:

Verdi tab-completion
--------------------
The ``verdi`` command line interface has many commands and options,
which can be tab-completed to simplify your life.
Enable tab-completion with the following shell command::

    eval "$(_VERDI_COMPLETE=source verdi)"

Place this command in your startup file, i.e. one of

* the startup file of your shell (``.bashrc``, ``.zsh``, ...), if aiida is installed system-wide
* the `activate script <https://virtualenv.pypa.io/en/latest/userguide/#activate-script>`_ of your virtual environment
* a `startup file <https://conda.io/docs/user-guide/tasks/manage-environments.html#saving-environment-variables>`_ for your conda environment

In order to enable tab completion in your current shell,
make sure to source the startup file once.

.. note::
    This line replaces the ``eval "$(verdi completioncommand)"`` line that was used in ``aiida-core<1.0.0``. While this continues to work, support for the old line may be dropped in the future.


Adding AiiDA to the PATH
------------------------
If you used a virtual environment for the installation of AiiDA, the required commands such as ``verdi`` should have been added automatically to your ``PATH``.
Otherwise, you may have to add the install directory of AiiDA manually to your ``PATH`` so that the binaries are found.

For Linux systems, the path to add is usually ``~/.local/bin``::

    export PATH=~/.local/bin:${PATH}

For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::

    export PATH=~/Library/Python/2.7/bin:${PATH}

After updating your ``PATH`` you can check if it worked in the following way:

* type ``verdi`` on your terminal, and check if the program starts (it should
  provide a list of valid commands). If it doesn't, check if you correctly set
  up the ``PATH`` environment variable above.
* go into your home folder or in another folder different from the AiiDA folder,
  run ``python`` or ``ipython`` and try to import a module, e.g. by typing::

    import aiida

  If the setup is ok, you shouldn't get any error. If you do get an ``ImportError`` instead, check
  that you are in the correct virtual environment. If you did not install AiiDA
  within a virtual environment, you will have to set up the ``PYTHONPATH``
  environment variable in your ``.bashrc``::

    export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"

.. _directory_location:


Customizing the configuration directory location
------------------------------------------------

By default, the AiiDA configuration is stored in the directory ``~/.aiida``.
This can be changed by setting the ``AIIDA_PATH`` environment variable.
The value of ``AIIDA_PATH`` can be a colon-separated list of paths.
For each of the paths in the list, AiiDA will look for a ``.aiida`` directory in the given path.
The first configuration folder that is encountered will be used
If no ``.aiida`` directory is found in any of the paths found in the environment variable, one will be created automatically in the last path that was considered.

For example, the directory structure in your home might look like this ::

    .
    ├── .aiida
    └── project_a
        ├── .aiida
        └── subfolder


If you leave the ``AIIDA_PATH`` variable unset, the default location in your home will be used.
However, if you set ::

    export AIIDA_PATH='~/project_a:'

The configuration directory used will be ``~/project_a/.aiida``.

.. warning::
    Note that even if the sub directory ``.aiida`` would not yet have existed in ``~/project_a``, AiiDA will automatically create it for you.
    Be careful therefore to check that the path you set for ``AIIDA_PATH`` is correct.

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
Alternatively, if you have a ``aiida_core`` repository checked out locally,
you can just copy the file ``<aiida_core>/aiida/tools/ipython/aiida_magic_register.py`` to the same folder.
The current ipython profile folder can be located using::

  ipython locate profile

After this, if you open a Jupyter notebook as explained above and type in a cell::

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."
This line magic should also be enabled in standard ipython shells.
