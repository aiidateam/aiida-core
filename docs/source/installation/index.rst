.. _installation:

############
Installation
############

=============
Quick install
=============

This section of the manual will guide you through the process of installing AiiDA on your system as quick as possible.
For more detailed instructions and explanations refer to the later sections.
The installation procedure can generally be split into three separate steps:

1. Install prerequisite software
2. Install AiiDA and its python dependencies
3. Configure the AiiDA installation

Install prerequisite software
+++++++++++++++++++++++++++++
The installation procedure itself requires certain software, which therefore will have to be installed first.
The following software is required to continue with the installation:

* `git`_ (To download the ``aiida`` package)
* `python-2.7.x`_ (The programming language used for AiiDA)
* `python-pip`_ (Python package manager)
* `virtualenv`_ (Software to create a virtual python environment to install AiiDA in)
* `postgresql`_ (Database software version 9.4 or higher)

.. _git: https://git-scm.com/downloads
.. _python-2.7.x: https://www.python.org/downloads
.. _python-pip: https://packaging.python.org/installing/#requirements-for-installing-packages
.. _virtualenv: https://packages.ubuntu.com/xenial/virtualenv
.. _postgresql: https://www.postgresql.org/downloads


Installation instructions will depend on your system.
For Ubuntu and any other Debian derived distributions you can use::

    $ sudo apt-get install git python2.7-dev python-pip virtualenv postgresql postgresql-server-dev-all postgresql-client

For MacOS X using `Homebrew`_ as the package manager::

    $ brew install git python postgresql
    $ pg_ctl -D /usr/local/var/postgres start

.. _Homebrew: http://brew.sh/index_de.html

For a more detailed description of database requirements and usage see section `database`_.

Install AiiDA and its python dependencies
+++++++++++++++++++++++++++++++++++++++++
With the prerequisites installed, we can now download AiiDA itself and install it along with all its python dependencies.
Create a directory where you want to install AiiDA and clone the repository::

    $ mkdir <your_directory>
    $ cd <your_directory>
    $ git clone https://github.com/aiidateam/aiida_core

To prevent the python packages that AiiDA depends on, from clashing with the packages you already have installed on your system, we will install them in a virtual environment.
For detailed information about virtual environment refer to the section :ref:`virtual-environment`.
To create a new virtual environment and activate it, run the following commands::

    $ virtualenv ~/aiidapy
    $ source ~/aiidapy/bin/activate

This will create a directory in your home directory named ``aiidapy`` where all the packages will be installed.
After activation, your prompt now should have ``(aiidapy)`` in front of it, indicating that you are working in the virtual environment.

.. note:: You may need to install ``pip`` and ``setuptools`` in your virtual environment in case the system or user version of these tools is old::

    $ pip install -U setuptools pip

Finally, to install AiiDA, run the following command from the directory where you cloned the repository::

   (aiidapy) $ pip install -e aiida_core

(In this example the AiiDA directory is in ``aiida_core``)

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


Configure the AiiDA installation
++++++++++++++++++++++++++++++++
After successful installation, AiiDA needs to be configured, such as setting up a profile and creating a database, which can be done through AiiDA's command line interface ``verdi``.
For a fast and default setup use ``verdi quicksetup`` and for greater control use ``verdi setup`` (see `verdi-setup`_).
Here we will use the quicksetup by executing::

    (aiidapy) $ verdi quicksetup

You will be asked for your user information. Be aware that this information will be associated with your data if you decide later to share it.
Alternatively you can give your information as commandline options (use ``verdi quicksetup --help`` option for a list of options).

.. note:: ``verdi setup`` used to be called ``verdi install``, but the new name better reflects the command's purpose.

Congratulations, you should now have a working installation of AiiDA.
You can verify that the installation was successful by running::

    $ verdi profile list

This should list the profile that was just created by the ``quicksetup``::

    > quicksetup (DEFAULT) (DAEMON PROFILE)

Remember that in order to work with AiiDA through for example the ``verdi`` command, you need to be in your virtual environment.
If you open a new terminal for example, be sure to activate it first with::

    $ source ~/aiidapy/bin/activate

At this point, you can choose to read on for additional installation details and configuration options, or you can choose to start using
AiiDA and go straight to the section :ref:`get-started`.


======================
Optional configuration
======================

.. _tab-completion:

Verdi tab-completion
++++++++++++++++++++
The ``verdi`` command line tool has many commands and options.
To simplify its usage, there is a way to enable tab-completion for it in your bash shell.
To do so, simply run the following command::

    $ verdi completioncommand

and append the result to the activation script of your virtual environment (or to your bash config, e.g. ``.bashrc``).
Alternatively, you can accomplish the same by simply adding the following line to the activation script::

    eval "$(verdi completioncommand)"

For the changes to apply to your current shell, make sure to source the activation script or ``.bashrc`` (depending the approach you chose).

Adding AiiDA to the PATH
++++++++++++++++++++++++
If you used a virtual environment for the installation of AiiDA, the required commands such as ``verdi`` should have been added automatically to your ``PATH``.
Otherwise, you may have to add the install directory of AiiDA manually to your ``PATH`` so that the binaries are found.

For Linux systems, the path to add is usually ``~/.local/bin``::

    export PATH=~/.local/bin:${PATH}

For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::

    export PATH=~/Library/Python/2.7/bin:${PATH}

To verify if this is the correct path to add, navigate to this location and you should find the executable ``supervisord``, or ``celeryd``, in the directory.

After updating your ``PATH`` you can check if it worked in the following way:

* type ``verdi`` on your terminal, and check if the program starts (it should
  provide a list of valid commands). If it doesn't, check if you correctly set
  up the ``PATH`` environment variable above.
* go into your home folder or in another folder different from the AiiDA folder,
  run ``python`` or ``ipython`` and try to import a module, e.g. typing::

    import aiida

  If the setup is ok, you shouldn't get any error. If you do get an ``ImportError`` instead, check
  that you are in the correct virtual environment. If you did not install AiiDA
  within a virtual environment, you will have to set up the ``PYTHONPATH``
  environment variable in your ``.bashrc``::

    export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"

Customizing the configuration directory location
++++++++++++++++++++++++++++++++++++++++++++++++

By default, the AiiDA configuration is stored in the directory ``~/.aiida``. This can be changed by setting the ``AIIDA_PATH`` environment variable. The value of ``AIIDA_PATH`` can be a colon-separated list of paths. For each of the paths in the list, AiiDA will look for a ``.aiida`` directory in the given path and all of its parent folders. If no ``.aiida`` directory is found, ``~/.aiida`` will be used.

For example, the directory structure in your home might look like this ::

    .
    ├── .aiida
    ├── project_a
    │   ├── .aiida
    │   └── subfolder
    └── project_b
        └── .aiida

If you set ::

    export AIIDA_PATH='~/project_a:~/project_b'

the configuration directory used will be ``~/project_a/.aiida``. The same is true if you set ``AIIDA_PATH='~/project_a/subdir'``, because ``subdir`` itself does not contain a ``.aiida`` folder, so AiiDA will first check its parent directories.

If you set ``AIIDA_PATH='.'``, the configuration directory used depends on the current working directory. Inside the ``project_a`` and ``project_b`` directories, their respective ``.aiida`` directory will be used. Outside of these directories, ``~/.aiida`` is used.

An example for when this option might be used is when two different AiiDA versions are used simultaneously. Using two different ``.aiida`` directories also allows running two daemon concurrently.
Note however that this option does **not** change the database cluster that is being used. This means that by default you still need to take care that the database names do not clash.

Using AiiDA in Jupyter
++++++++++++++++++++++

`Jupyter <http://jupyter.org>`_ is an open-source web application that allows you to create in-browser notebooks containing live code, visualizations and formatted text.

Originally born out of the iPython project, it now supports code written in many languages and customized iPython kernels.

If you didn't already install AiiDA with the ``[notebook]`` option (during ``pip install``), run ``pip install jupyter`` **inside** the virtualenv, and then run **from within the virtualenv**::

    $ jupyter notebook

This will open a tab in your browser. Click on ``New -> Python 2`` and type::

    import aiida

followed by ``Shit-Enter``. If no exception is thrown, you can use AiiDA in Jupyter.

If you want to set the same environment as in a ``verdi shell``, add the following code in ``<your.home.folder>/.ipython/profile_default/ipython_config.py``::

  c = get_config()
  c.InteractiveShellApp.extensions = [
          'aiida.common.ipython.ipython_magics'
  ]

then open a Jupyter notebook as explained above and type in a cell:

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."


.. _virtual-environment:

===================
Virtual environment
===================

Why a virtual environment?
++++++++++++++++++++++++++

AiiDA depends on third party python packages and very often on specific versions of those packages.
If AiiDA were to be installed system wide, it may up- or downgrade third party packages used by other parts of the system and leave them potentially broken.
Conversely, if a different version of a package is later installed which is incompatible with AiiDA, it too will become broken.

In short, installing AiiDA might interfere with installed python packages and installing other packages might interfere with AiiDA.
Since your scientific data is important to you and to us, we *strongly* recommend isolating AiiDA in what is called a virtual environment.

For a single purpose machine, only meant to run AiiDA and nothing else, you may at your own risk opt to omit working in a virtual environment.
In this case, you may want to install AiiDA and its dependencies in user space by using a ``--user`` flag, to avoid the need for administrative rights to install them system wide.

What is a virtual environment?
++++++++++++++++++++++++++++++
A python virtual environment is essentially a folder, that contains everything that is needed to run python programs, including

* python executable
* python standard packages
* package managers such as ``pip``
* an activation script that sets the ``PYTHONPATH`` and ``PATH`` variables

The ``python`` executable might be a link to an executable elsewhere, depending on the way the environment is created.
The activation script ensures that the python executable of the virtualenv is the first in ``PATH``, and that python programs have access only to packages installed inside the virtualenv (unless specified otherwise during creation).
This allows to have an isolated environment for programs that rely on running with a specific version of python or specific versions of third party python packages.

A virtual environment as well as the packages that will be installed within it, will often be installed in the home space of the user such that administrative rights are not required, therefore also making this technique very useful on machines where one has restricted access.

Creating a virtual environment
++++++++++++++++++++++++++++++
There are different programs that can create and work with virtual environments.
An example for python virtual environments is called ``virtualenv`` and can be installed with for example ``pip`` by running::

    $ pip install --user -U virtualenv

As explained before, a virtual environment is in essence little more than a directory containing everything it needs.
In principle a virtual environment can thus be created anywhere where you can create a directory.
You could for example opt to create a directory for all your virtual environments in your home folder::

    $ mkdir ~/.virtualenvs

Using ``virtualenv`` you can then create a new virtual environment by running::

    $ virtualenv ~/.virtualenvs/my_env

This will create the environment ``my_env`` and automatically activate it for you.
If you open a new terminal, or you have deactivated the environment, you can reactivate it as follows::

    $ ~/.virtualenvs/my_env/bin/activate

If it is activated successfully, you should see that your prompt is prefixed with the name of the environment::

    (my_env) $

To leave or deactivate the environment and set all the settings back to default, simply run::

    (my_env) $ deactivate


.. _database:

========
Database
========
AiiDA needs a database backend to store the nodes, node attributes and other
information, allowing the end user to perform very fast queries of the results.
Currently, only `postgresql`_ is allowed as a database backend.


Setup instructions
++++++++++++++++++
In order for AiiDA to be able to use postgres it needs to be installed first.
On Ubuntu and other Debian derivative distributions this can be accomplished with::

    $ sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

For Mac OS X, binary packages can be downloaded from the official website of `postgresql`_ or you can use ``brew``::

    $ brew install postgresql
    $ pg_ctl -D /usr/local/var/postgres start

To manually create a database for AiiDA that will later be used in the configuration with ``verdi setup``, you should follow these instructions.
First you will need to run the program ``psql`` to interact with postgres and you have to do so as the ``postgres`` user that was created upon installing the software.
To assume the role of ``postgres`` run as root::

    $ su - postgres

and launch the postgres program::

    $ psql

Create a new database user account for AiiDA by running::

    CREATE USER aiida WITH PASSWORD '<password>';

replacing ``<password>`` with a password of your choice.
Make sure to remember it, as you will need it again when you configure AiiDA to use this database through ``verdi setup``.
If you want to change the password you just created use the command::

    ALTER USER aiida PASSWORD '<password>';

Next we create the database itself::

    CREATE DATABASE aiidadb OWNER aiida;

and grant all privileges on this DB to the previously-created ``aiida`` user::

    GRANT ALL PRIVILEGES ON DATABASE aiidadb to aiida;

You have now created a database for AiiDA and you can close the postgres shell by typing ``\q``.
To test if the database was created successfully, you can run the following command as a regular user in a bash terminal::

    $ psql -h localhost -d aiidadb -U aiida -W

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

.. note:: Due to the presence of a bug, PostgreSQL could refuse to restart after a crash,
  or after a restore from binary backup. The workaround given below is adapted from `here`_.
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


.. _here: https://wiki.postgresql.org/wiki/May_2015_Fsync_Permissions_Bug


.. _verdi-setup:

===========
Verdi setup
===========
The quick install section detailed how ``verdi quicksetup`` can be used to quickly setup AiiDA by creating a profile and a database for you.
If you want more control over this process, for example if you want to use a database that you created yourself, you can use ``verdi setup``::

    $ verdi setup <profile_name>

or equivalently::

    $ verdi -p <profile_name> setup

The same commands can also be used to edit already existing profiles.
The ``verdi setup`` command will guide you through the setup process through a series of prompts.

The first thing that will be asked to you is the timezone, extremely important to get correct dates and times for your calculations.

AiiDA will do its best to try and understand the local timezone (if properly configured on your machine), and will suggest a set of sensible values.
Choose the timezone that fits best to you (that is, the nearest city in your timezone - for Lausanne, for instance, we choose ``Europe/Zurich``) and type it at the prompt.

As a second parameter to input during the ``verdi setup`` phase, the "Default user email" is asked.
We suggest here to use your institution email, that will be used to associate the calculations to you.

.. note:: In AiiDA, the user email is used as username, and also as unique identifier when importing/exporting data from AiiDA.

.. note:: Even if you choose an email different from the default one
  (``aiida@localhost``), a user with email ``aiida@localhost`` will be
  set up,
  with its password set to ``None`` (disabling access via this user
  via API or Web interface).

  The existence of a default user is internally useful for multi-user
  setups, where only one user
  runs the daemon, even if many users can simultaneously access the DB.
  See the page on :ref:`setting up AiiDA in multi-user mode<aiida_multiuser>`
  for more details (only for advanced users).

.. note:: The password, in the current version of AiiDA, is not used (it will
    be used only in the REST API and in the web interface). If you leave the
    field empty, no password will be set and no access will be granted to the
    user via the REST API and the web interface.

Then, the following prompts will help you configure the database. Typical settings are::

    Insert your timezone: Europe/Zurich
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


=========================
Installation requirements
=========================
Read on for more information about the kind of operating system AiiDA can run on and what software needs to be installed before AiiDA can work.

Supported architecture
++++++++++++++++++++++
AiiDA is tested to run on:

* Mac OS X (tested)
* Ubuntu 14.04 & 16.04

AiiDA should run on:

* Older / newer Ubuntu versions
* Other Linux distributions


===============
Troubleshooting
===============

* On a clean Ubuntu 16.04 install the pip install command ``pip install -e aiida_core``
  may fail due to a problem with dependencies on the ``numpy`` package. In this case
  you may be presented with a message like the following:

    from numpy.distutils.misc_util import get_numpy_include_dirs
    ImportError: No module named numpy.distutils.misc_util

  To fix this, simply install ``numpy`` individually through pip in your virtual env, i.e.

    pip install numpy

  followed by executing the original install command once more

    pip install -e .

  This should fix the dependency error.

* If the ``pip install`` command gives you an error that resembles the one
  shown below, you might need to downgrade to an older version of pip::

    Cannot fetch index base URL https://pypi.python.org/simple/

  To downgrade pip, use the following command::

    sudo easy_install pip==1.2.1

* In order to use the AiiDA objects and functions in Jupyter, this latter has to be instructed to use the iPython kernel installed in the AiiDA virtual environment. This happens by default if you install AiiDA with ``pip`` including the ``notebook`` option and run Jupyter from the AiiDA virtual environment.

  If, for any reason, you do not want to install Jupyter in the virtual environment, you might consider to install it out of the virtual environment, if not already done::

      $ pip install jupyter

  Then, activate the AiiDA virtual environment::

      $ source ~/<aiida.virtualenv>/bin/activate

  and setup the AiiDA iPython kernel::

      $ pip install ipykernel
      $ python -m ipykernel install --user --name=<aiida.kernel.name>

  where you have chosen a meaningful name for the new kernel.

  Finally, start a Jupyter server::

      $ jupyter notebook

  and from the newly opened browser tab select ``New -> <aiida.kernel.name>``


* Several users reported the need to install also ``libpq-dev`` (header files for libpq5 - PostgreSQL library)::

    apt-get install libpq-dev

  But under Ubuntu 12.04 this is not needed.

* If the installation fails while installing the packages related
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


* For some reasons, on some machines (notably often on Mac OS X) there is no
  default locale defined, and when you run ``verdi setup`` for the first
  time it fails (see also `this issue`_ of django).
  Run in your terminal (or maybe even better, add to your ``.bashrc``, but
  then remember to open a new shell window!)::

     export LANG="en_US.UTF-8"
     export LC_ALL="en_US.UTF-8"

  and then run ``verdi setup`` again.

.. _this issue: https://code.djangoproject.com/ticket/16017

* [*Only for developers*] The developer tests of the *SSH* transport plugin are
  performed connecting to ``localhost``. The tests will fail if
  a passwordless ssh connection is not set up. Therefore, if you want to run
  the tests:

  + make sure to have a ssh server. On Ubuntu, for instance, you can install
    it using::

       sudo apt-get install openssh-server

  + Configure a ssh key for your user on your machine, and then add
    your public key to the authorized keys of localhsot.
    The easiest way to achieve this is to run::

       ssh-copy-id localhost

    (it will ask your password, because it is connecting via ssh to ``localhost``
    to install your public key inside ~/.ssh/authorized_keys).

.. _updating_aiida:

======================================
Updating AiiDA from a previous version
======================================

AiiDA can be updated from a previously installed version. Before beginning
the procedure, make sure of the following:

  * your daemon is stopped (use ``verdi daemon stop``),
  * you know your current AiiDA version. In case, you can get it from the ``verdi shell``::

      import aiida
      aiida.__version__

    (only the two first digits matter),
  * you have a backup of your database(s) (follow the guidelines in the
    :ref:`backup section<backup>`),
  * you have a backup of the full ``~/.aiida`` folder (where configuration
    files are stored),
  * (optional) ``virtualenv`` is installed, i.e. you once ran the command::

      pip install --user -U setuptools pip wheel virtualenv

.. note::
  A few general remarks:

  * If you want to update the code in the same folder, but modified some files locally,
    you can stash them (``git stash``) before cloning or pulling the new code.
    Then put them back with ``git stash pop`` (note that conflicts might appear).
  * If you encounter any problems and/or inconsistencies, delete any .pyc
    files that may have remained from the previous version. E.g. If you are
    in your AiiDA folder you can type ``find . -name "*.pyc" -type f -delete``.
  * From 0.8.0 onwards there is no ``requirements.txt`` file anymore. It has been replaced by ``setup_requirements.py`` and ``pip`` will install all the requirements automatically. If for some reason you would still like to get such a file, you can create it using the script ``aiida_core/utils/create_requirements.py``

.. note::
  Since AiiDA 0.9.0, we use Alembic for the database migrations of the
  SQLAlchemy backend. In case you were using SQLAlchemy before the introduction
  of Alembic, you may experience problems during your first migration. If it is
  the case, please have a look at the following section :ref:`first_alembic_migration`

Updating between development versions (for Developers)
++++++++++++++++++++++++++++++++++++++++++++++++++++++

After you checkout a development branch or pull a new state from the repository

* run ``pip install -e`` again (or in a different virtualenv)
  This applies changes to the distribution system (setup.py and related)

To use the new version in production:

* run ``verdi setup``
  This updates your daemon profile and related files. It should not be done when another version of aiida is wished to be used productively on the same machine/user.

Updating from 0.9.* to 0.10.0
++++++++++++++++++++++++++++++++++++++++++

In version ``0.10.0`` the Quantum ESPRESSO plugin was removed from the ``aiida_core`` repository and moved to a separate plugin repository.
With the new plugin system introduced in version ``0.9.0``, installing the Quantum ESPRESSO plugin through the repository is very easy.
However, if your current AiiDA installation still has the plugin files in the ``aiida_core`` tree, they have to be removed manually and the old entry points have to be removed from the cache.
The instructions to accomplish this will be detailed below.

* First, make sure that you are in the correct virtual environment, for example (replace the path with the path to your actual virtual environment::

    source ~/aiidapy/bin/activate

* Go to the directory of the ``aiida_core`` source code tree, for example::

    cd ~/code/aiida/core

* Check out the new version, either through the develop branch or a specific tag::

    git checkout -b develop
    git pull origin develop

  or::

    git checkout -b v0.10.0 v0.10.0

* Remove the obsolete Quantum ESPRESSO plugin directory::

    rm -rf aiida/orm/calculation/job/quantumespresso

* Install the new version of AiiDA by typing::

    pip install -e .[<EXTRAS>]

  where <EXTRAS> is a comma separated list of the optional features you wish to install (see the :ref:`optional dependencies<install_optional_dependencies>`).

This should have successfully removed the old plugin entry points from your virtual environment installation.
To verify this, execute the following command and make sure that the ``quantumespresso.*`` plugins are not listed::

  verdi calculation plugins

If this is not the case, run the following command and check the ``verdi`` command again::

  reentry scan
  verdi calculation plugins

If the plugin is no longer listed, we can safely reinstall them from the new plugin repository and the plugin loading system.
First, clone the plugin repository from github in a separate directory::

  mkdir -p ~/code/aiida/plugins
  cd ~/code/aiida/plugins
  git clone https://github.com/aiidateam/aiida-quantumespresso

Now all we have to do to install the plugin and have it registered with AiiDA is execute the following ``pip`` command::

  pip install -e aiida-quantumespresso

To verify that the plugin was installed correctly, list the plugin entry points through ``verdi``::

  verdi calculation plugins

If the Quantum ESPRESSO plugin entry points are not listed, you can try the following::

  reentry scan
  verdi calculation plugins

If the entry points are still not listed, please contact the developers for support.
Finally, make sure to restart the daemon::

  verdi daemon restart

Now everything should be working properly and you can use the plugin as you were used to.
You can use the ``CalculationFactory`` exactly in the same way to load calculation classes.
For example you can still call ``CalculationFactory('quantumespresso.pw')`` to load the ``PwCalculation`` class.
The only thing that will have changed is that you can no longer directly import from the old plugin location.
That means that ``from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation`` will no longer work as those files no longer exist.
Instead you can use the factories or the new import location ``from aiida_quantumespresso.calculation.pw import PwCalculation``.


Updating from 0.8.* Django to 0.9.0 Django
++++++++++++++++++++++++++++++++++++++++++

* Enable your virtual environment::

    virtualenv ~/aiidapy
    source ~/aiidapy/bin/activate

* Go to the directory where you want to place your code and clone the latest
  version from Github::

    cd <where_you_want_the_aiida_sourcecode>
    git clone git@github.com:aiidateam/aiida_core.git

.. note::
    * If you have cloned in the past the code, you can just checkout the latest version

    * In case you have an older version of pip or setuptools, try to upgrade them::

        pip install -U setuptools pip

* Install the new version of AiiDA by typing::

    pip install -e aiida_core[<EXTRAS>]

  where <EXTRAS> is a comma separated list of the optional features
  you wish to install (see the :ref:`optional dependencies<install_optional_dependencies>`).
  The two first steps above can be removed if you do not want to install AiiDA
  into a virtual environment (reminder: this is *not* recommended).


Updating from 0.7.0 Django to 0.8.0 Django
++++++++++++++++++++++++++++++++++++++++++

* In a virtual environment, clone and install the code from github with::

    virtualenv ~/aiidapy
    source ~/aiidapy/bin/activate
    cd <where_you_want_the_aiida_sourcecode>
    git clone git@github.com:aiidateam/aiida_core.git
    pip install -e aiida_core[<EXTRAS>]

  where <EXTRAS> is a comma separated list of the optional features
  you wish to install (see the :ref:`optional dependencies<install_optional_dependencies>`).
  The two first steps above can be removed if you do not want to install AiiDA
  into a virtual environment (reminder: this is *not* recommended).

* Undo all PATH and PYTHONPATH changes you did in your ``.bashrc`` and similar
  files to add ``verdi`` and ``runaiida`` of the previous version.
  When using the virtual environment, you do not need anymore to update
  the PYTHONPATH nor the PATH.
* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (version 0.8
  is using a newer version of the schema). The command will look like
  ``python manage.py --aiida-profile=default migrate`` (to be run from
  <AiiDA_folder>/aiida/backends/djsite) but please read the message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.
* Rerun ``verdi setup`` (formerly ``verdi install``), no manual changes
  to your profile should be necessary. This step is necessary as it
  updates some internal configuration files.
* You might want to create an alias to easily go into the correct virtual
  environment and have all AiiDA commands available: in your `~/.bashrc`
  file you can add an alias like::

    alias aiida_env='source ~/aiidapy/bin/activate'

* Activate the tab-completion of `verdi` commands (see :ref:`here<tab-completion>`).

**Updating the backup script**

In case you used the AiiDA repository backup mechanism in 0.7.0 and you would
like to continue using it in 0.8.0, you should update the backup scripts.

To do so:

* Re-run the backup_setup.py (``verdi -p PROFILENAME run MY_AIIDA_FOLDER/aiida/common/additions/backup_script/backup_setup.py``).
  Keep in mind that you should have activated your virtual environment in case
  you use one.

* Provide the backup folder by providing the full path. This is the folder
  where the backup configuration files and scripts reside.

* Provide the destination folder of the backup (normally in the previously
  provided backup folder)

* Reply *No* when the scripts asks you to print the configuration parameters
  explanation.

* Reply *No* when the scripts asks you to configure backup configuration file.

* The script should have exited now. Ignore its proposals to update the
  ``backup_info.json.tmpl`` and the startup script.

* Your backup mechanism is ready to be used again. You can continue using it
  by executing ``start_backup.py``.

Updating from an older version
++++++++++++++++++++++++++++++

Because the database schema changes typically at every version, and since
the migration script assumes that you are using the previous AiiDA version,
one has to migrate in steps, from the version of AiiDA you were using,
until the current one. For instance, if you are currently using AiiDA 0.5,
you should first update to 0.6, then to 0.7, and finally to 0.8. Do not forget to
**deactivate** the current virtual environment before installing any new version.

For *each intermediate update* (e.g. when you update from 0.5 to 0.6 in the above example),
do the following::

  virtualenv ~/aiidapy_<VERSION>
  source ~/aiidapy_<VERSION>/bin/activate
  cd <where_you_want_the_aiida_sourcecode>

(<VERSION> being the intermediate version you are updating to, in our example 0.6).

Then get the code with the appropriate version and install its dependencies:
AiiDA versions prior or equal to 0.7 can be cloned from bitbucket::

  git clone git@bitbucket.org:aiida_team/aiida_core.git aiida_core_<VERSION>
  cd aiida_core_<VERSION>
  git checkout v<VERSION>
  pip install -U -r requirements.txt

and update the ``PATH`` and ``PYTHONPATH`` environment variables
in your ``~/.bashrc`` file before sourcing it (replace <AiiDA_folder> with the folder in
which you just installed AiiDA)::

    export PATH="${PATH}:<AiiDA_folder>/bin"
    export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"

Then follow the specific instructions below for each intermediate update.

.. note::
  * If you have an issue with ``ultrajson`` during the ``pip install`` step,
    replace ``ultrajson`` with ``ujson`` in the ``requirements.txt`` file
    (the name of this module changed over time).
  * In the ``pip install`` step, you might need to install some dependencies
    located in ``optional_requirements.txt`` (e.g. ``psycopg2`` for postgresql
    database users), as well as ``ipython`` to get a proper shell, e.g.::

      pip install -U -r requirements.txt psycopg2==2.6 ipython

Updating from 0.6.0 Django to 0.7.0 Django
------------------------------------------
In version 0.7 we have changed the Django database schema and we also have
updated the AiiDA configuration files.

* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (version 0.7
  is using a newer version of the schema).
  The command will look like
  ``python manage.py --aiida-profile=default migrate`` (to be run from
  <AiiDA_folder>/aiida/backends/djsite) but please read the
  message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.
* To update the AiiDA configuration files, you should execute the migration
  script::

    python <AiiDA_folder>/aiida/common/additions/migration_06dj_to_07dj.py

Updating from 0.6.0 Django to 0.7.0 SQLAlchemy
----------------------------------------------
The SQLAlchemy backend was in beta mode for version 0.7.0. Therefore some of
the verdi commands may not work as expected or at all (these are very few).
If you would like to test the SQLAlchemy backend with your existing AiiDA database,
you should convert it to the JSON format. We provide a transition script
that will update your config files and change your database to the proper schema.

* Go to you AiiDA folder and run ``ipython``. Then execute::

    from aiida.backends.sqlalchemy.transition_06dj_to_07sqla import transition
    transition(profile="<your_profile>",group_size=10000)

  by replacing ``<your_profile>`` with the name of the appropriate profile
  (typically, ``default`` if you have only one profile).

Updating from 0.5.0 to 0.6.0
----------------------------

* Execute the migration script::

    python <AiiDA_folder>/aiida/common/additions/migration.py

.. note::
  * In this version a lot of changes were introduced in order to allow
    a second object-relational mapper later (we will refer to it as
    backend) for the management of the used DBMSs and more specifically
    of PostgreSQL.
    Even if most of the needed restructuring & code addition was finished,
    a bit of more work was needed to get the new backend available.
  * You can not directly import data (``verdi import``) that you have exported
    (``verdi export``) with a previous version of AiiDA. Please use
    :download:`this script <../examples/convert_exportfile_version.py>`
    to convert it to the new schema. (Usage: ``python
    convert_exportfile_version.py input_file output_file``).


Updating from 0.4.1 to 0.5.0
----------------------------
* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (version 0.5
  is using a newer version of the schema).
  The command will look like
  ``python manage.py --aiida-profile=default migrate``
  (to be run from `<AiiDA_folder>/ai    aiida/djsite`) but please read the
  message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.

.. note:: If you were working on a plugin, the plugin interface changed:
  you need to change the CalcInfo returning also a CodeInfo, as specified
  :ref:`here<qeplugin-prepare-input>` and also accept a ``Code`` object
  among the inputs (also described in the same page).
