====================================
Installation and Deployment of AiiDA
====================================

FAQ
+++

What happened to ``verdi install``?
-----------------------------------

``verdi install`` has been renamed to ``verdi setup``, a name we feel better reflects what the command does.

.. _install.faq.virtualenv:

What is a virtual environment (virtualenv)?
-------------------------------------------

A python virtual environment is essentially a folder, containing everything needed to run python programs, including

* python executable
* python standard packages
* (often) ``pip`` and related packages (for package management)
* a script (often ``activate``) that sets the PYTHONPATH and PATH variables

The ``python`` executable might be a link to an executable elswhere, depending on the way the environment is created.

The activation process ensures that the python executable of the virtualenv is the first in PATH, and that python programs have access only to packages installed inside the virtualenv (unless specified otherwise during creation). This allows to have an isolated environment for programs that rely on running with a specific version of python or specific versions of third party python packages.

Packages can be installed into an environment by activating it and then using the ``pip`` or ``easy_install`` executables created with the environment.

The creator of a virtualenv can install packages into it without using ``sudo``, therefore this technique can be used on machines where one has restricted access.

To create a virtual environment named aiidapy in your home folder, assuming you have a working installation of Python 2.7.x::
   
      $ pip install --user -U setuptools pip wheel virtualenv
      $ virtualenv ~/aiidapy # or equivalent
      $ source ~/aiidapy/bin/activate

After the last line, the environment is activated, ``python`` will point to ``~/aiidapy/bin/python`` and packages will by default be installed into ``~/aiidapy/lib/python2.7/site-packages`` (or similar).

To leave the virtual environment and reset your PATH and PYTHONPATH variables to what they were before activating it, type::

   $ deactivate

Why install AiiDA into a virtualenv?
------------------------------------

AiiDA depends on third party python packages. Because AiiDA is not compatible with all versions and specifically not always with the newest version of each of these dependencies, installing AiiDA might up- or downgrade third party packages you are already using. Similarly a package you install at a later point might request an incompatible version of one of AiiDA's dependencies.

In Summary, installing AiiDA might interfere with installed python packages, installing other packages might interfere with AiiDA.
Since your scientific data is important to you and to us, we *strongly* recommend isolating AiiDA in a virtual environment.

For a single purpose machine, only meant to run AiiDA and nothing else, you may at your own risk simply leaving away the steps to setup and activate the virtual environment. You may want to install AiiDA and it's dependencies with the --user flag to avoid having to use sudo in that case.

How to use verdi tab-completion with a virtualenv?
--------------------------------------------------

Verdi tab-completion is enabled by evaluating the output of ``verdi completioncommand`` (either with ``eval`` or by pasting it into a bash script and sourcing it).
You can automatically run ``eval "$(verdi completioncommand)"`` when you activate the environment (especially useful when you use multiple environments for development). To achieve this, simply append the line to the end of your ``aiidapy/bin/activate`` (which is a bash script). You can use this trick to do things like automatically start the daemon, etc.

There are many projects that aim to make managing many virtual environments easier and some of them even have pre- and postactivate scripts, which you may edit specifically for such intialization tasks. One such manager is `virtualenvwrapper`_.

Tab-completion is only supported for bash.

Quickstart (new users)
++++++++++++++++++++++

Get started immediately with just a few commands! Look at :ref:`quicksetup` for more details

.. _quickstart-ubuntu:

Quickstart - Linux (Ubuntu)
---------------------------

.. highlight:: bash

If you use another debian derivate, chances are this still works for you.
If your distribution uses a different package manager, simply replace the commandline in the first step (the package names might be slightly different). The links in :ref:`install_dependencies` contain additional information on how to get the required programs for your system.

1. Install dependencies::

   $ sudo apt-get install git python-pip python2.7-dev postgresql postgresql-server-dev-all postgresql-client

2. Setup a virtualenv:

   .. code-block:: bash

      $ pip install --user -U setuptools pip wheel virtualenv
      $ virtualenv ~/aiidapy # or equivalent
      $ source ~/aiidapy/bin/activate
      (aiidapy) $ # the name of the active environment is indicated in front of the prompt

3. Install AiiDA into the environment::
   
   (aiidapy) $ cd <where_you_want_the_aiida_sourcecode>
   (aiidapy) $ git clone https://github.com/aiidateam/aiida_core
   (aiidapy) $ pip install -e aiida_core[verdi_shell,ssh,REST] --process-dependency-links


The ``[verdi_shell,...]`` part of the last line above is to specify optional features. To install additonal optional features, simply run the line again with a changed list of optional features.

For the next step to work, postgres must be running on port ``5432``. This should automatically be the case once it is installed (on Ubuntu).
If you have changed the default configuration of postgres, you will be asked for the details. Refer to the `PostgresQL`_ documentation for details on how to ensure your postgres is running. Read ``(aiidapy) $ verdi quicksetup --help`` to see how to supply information about your postgres configuration beforehand.

4. Setup AiiDA::

   (aiidapy) $ verdi quicksetup

You will be asked for your user information. Be aware that this information will be associated with your experiments and results for sharing.
Alternatively you can give your information as commandline options (use the ``--help`` option for a list of options).

5. (optional) Add the verdi command to your PATH::

   $ # for bash:
   $ echo "export PATH="${PATH}:~/aiidapy/bin" >> ~/.bashrc

Instead you might create a shell alias or explicitly activate (``source ~/aiidapy/bin/activate``) the virtualenvironment before working with aiida.
If you are using a virtualenv manager like `virtualenvwrapper`_, or `conda`_, it is possible to set up the environment so that activating it launches the AiiDA daemon and possibly initializes other things for you. How this is done is described in your virtualenv manager's documentation.


.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/index.html
.. _conda: https://conda.io/docs/

Quickstart - OS X (Homebrew)
----------------------------

`Homebrew`_ is an actively maintained package manager for OS X.
If you use another package manager just replace the first step accordingly.

1. Install dependencies::

      $ brew install git python postgresql

2. Start Postgres Server::

      $ pg_ctl -D /usr/local/var/postgres start

3. Follow steps 3-5 of :ref:`quickstart-ubuntu`

If you prefer not to use a package manager, follow the links in :ref:`install_dependencies` for instructions on how to install the required programs and start the postgres server before continuing with the third step.

.. _Homebrew: http://brew.sh/index_de.html

Other systems and custom setups
+++++++++++++++++++++++++++++++
 
For new and inexperienced users we strongly recommend to start with the Quickstart procedure detailed above. It is possible to customize your configuration afterwards if necessary.

If you are updating from a previous version and you don't want to
reinstall everything from scratch, read the instructions in
:ref:`updating_aiida`.

If you are trying to install AiiDA on another system than Ubunto or OS X, please take a look at :ref:`install_dependencies` before proceeding with one of the following.

* Install AiiDA on another system :ref:`install.other.install`
* Setup AiiDA using quicksetup :ref:`quicksetup`
* Using setup for more options or to customize your user profile :ref:`setup`
* Using setup to programatically install AiiDA :ref:`setup-noninteractive`

.. Four types of installations are described in the following:
.. 
.. * For new users:
.. 
..   * :ref:`quicksetup`
.. 
.. * For experienced users:
.. 
..   * :ref:`Custom user configuration`
..   * :ref:`Server setup`
..   * :ref:`Developer`

Installation requirements
-------------------------
Read on for more information about the kind of operating system AiiDA can run on and what software needs to be installed before AiiDA can work.

Supported architecture
^^^^^^^^^^^^^^^^^^^^^^
AiiDA is tested to run on:

* Mac OS X (tested)
* Ubuntu 14.04 & 16.04

AiiDA should run on:

* Older / newer Ubuntu versions
* Other Linux distributions

.. OLD:
.. AiiDA has a few strict requirements, in its current version:
.. first, it will run only on Unix-like systems - it
.. is tested (and developed) in Mac OS X and Linux (Ubuntu), but other Unix
.. flavours *should* work as well.

.. OLD:
.. Moreover, on the clusters (computational resources) side, it expects to find
.. a Unix system, and the default shell is **required** to be ``bash``.

.. _install_dependencies:

Required software
^^^^^^^^^^^^^^^^^
The following are required to be installed on your computer:

* `git`_ (To download the ``aiida`` package)
* `python 2.7.x`_ (The programming language used for AiiDA)
* `python-pip`_ (To install python packages)
* `python-virtualenv`_ (Or equivalent, to install AiiDA safely)
* `PostgreSQL`_ (For the database)
* PostgreSQL development files (required by some of the python packages AiiDA relies on)

.. _git: https://git-scm.com/downloads
.. _python 2.7.x: https://www.python.org/downloads
.. _python-pip: https://packaging.python.org/installing/#requirements-for-installing-packages
.. _python-virtualenv: https://virtualenv.pypa.io/en/stable/
.. _PostgreSQL: https://www.postgresql.org/downloads


.. _install.other.install:

Installing AiiDA (other systems)
--------------------------------

1. Create a virtual python environment, this is done so installing AiiDA can not accidentally up- or downgrade any of your system's python packages.::

   $ virtualenv ~/aiidapy
   $ # or conda create -n aiidapy python2.7 # if you use conda to manage python environments
   $ # or mkvirtualenv aiidapy # if you use virtualenvwrapper
      
2. Activate the environment::

   $ source ~/aiidapy/bin/activate
   $ or source activate aiidapy # (conda)
   $ or workon aiidapy # (virtualenvwrapper)

3. Install AiiDA into the environment::

   (aiidapy) $ cd <where_you_want_the_aiida_sourcecode>
   (aiidapy) $ git clone https://github.com/aiidateam/aiida_core
   (aiidapy) $ pip install -e aiida_core[verdi_shell,ssh,REST] --process-dependency-links

This installs the verdi command into your python environment and puts the source into <folder/containing/aiida>/aiida.
You can either activate the environment every time before using AiiDA (that way you could have multiple AiiDA versions installed in parallel), or you can add the verdi command to your path.

The ``[verdi_shell,...]`` part of the last line above is to specify optional features. To install additonal optional features, simply run the line again with a changed list of optional features.

4. (optional) add AiiDA's executables to your path or create aliases: 
   
   Add this to your .bashrc or .bash_profile or equivalent, assuming you installed with virtualenv::

      export PATH="${PATH}:~/aiidapy/bin

   or::

      alias verdi=~/aiidapy/bin/verdi
      alias runaiida=~/aiidapy/bin/runaiida

If you use conda, verdi will be installed to (envs directory)/aiidapy/bin/verdi, where envs directory depends on which version of Anaconda or Miniconda you use, for miniconda2 the default is ~/miniconda2/envs/.
The following command line will print the correct path::

   conda info | grep "envs directories"

If you use `virtualenvwrapper`_, you can find out in its online documentation where environments install their binaries.

If everything went smoothly, congratulations! Now the code is installed!

Next steps:

* set up AiiDA using :ref:`verdi quicksetup (New Users)<quicksetup>` or :ref:`verdi setup (Experienced Users)<setup>`

.. _create_db:

Create a database
-----------------

Run the following to create a database for use with an AiiDA profile. Replace

``<username>``
   with a name containing your system username and the name of the profile

``<password>``
   with the password for this database user. Make sure to remember it, AiiDA will require it to setup your profile

.. code-block:: bash

   $ psql -d template1
   > create role <username> with password "<password>";
   > create db <username>_aiida owner <username>;
   > grant all privileges on <username>_aiida to <username>;
   > \q

.. * :ref:`Try out AiiDA for the first time`
.. * :ref:`Custom configuration` for more advanced configurations.

.. OLD:
.. Installing Required Dependencies
.. ++++++++++++++++++++++++++++++++
.. 
.. Installing python
.. -----------------
.. 
.. AiiDA requires python 2.7.x (only CPython has been tested).
.. It is probable that you already have a version of
.. python installed on your computer. To check, open a terminal and type::
.. 
..     python -V
.. 
.. that will print something like this::
.. 
..     Python 2.7.3
.. 
.. If you don't have python installed, or your version is outdated, please install
.. a suitable version of python (either refer to the manual of your Linux
.. distribution, or for instance you can download the ActiveState Python from
.. ActiveState_. Choose the appropriate distribution corresponding to your
.. architecture, and with version 2.7.x.x).
.. 
.. .. _ActiveState: http://www.activestate.com/activepython/downloads

.. Installation of the core dependencies
.. +++++++++++++++++++++++++++++++++++++

.. OLD:
.. Database
.. --------
.. 
.. As a first thing, :doc:`choose and setup the database that you want to
.. use<database/index>`.
.. 
.. .. _other_core_dependencies:

.. OLD:
.. Some of them are mandatory, while others are optional (but often strongly suggested), also depending for instance on the :doc:`type of database <database/index>` that you plan to use.

.. OLD:
.. Here is a list of packages/programs that you need to install (for each of them,
.. there may be a specific/easier way to install them in your distribution, as
.. for instance ``apt-get`` in Debian/Ubuntu -see below for the specific names
.. of packages to install- or ``yum`` in RedHat/Fedora).

.. OLD:
.. * `git`_ (required to download the code)
.. * `python-pip`_ (required to automatically download and install further
..   python packages required by AiiDA)
.. * `ipython`_ (optional, but strongly recommended for interactive usage)
.. * python 2.7 development files (these may be needed; refer to your distribution
..   to know how to locate and install them)
.. * To support  SQLite:
.. 
..   * `SQLite3 development files`_ (required later to compile the library,
..     when configuring the python sqlite module; see below for the Ubuntu
..     module required to install these files)
.. 
.. * To support  PostgreSQL:
.. 
..   * `PostgreSQL development files`_ (required later to compile the library,
..     when configuring the python psycopg2 module; see below for the Ubuntu
..     module required to install these files)
.. 
.. .. _git: http://git-scm.com/
.. .. _python-pip: https://pypi.python.org/pypi/pip
.. .. _ipython: http://ipython.org/
.. .. _SQLite3 development files: http://www.sqlite.org/
.. .. _PostgreSQL development files: http://www.postgresql.org/

.. Todo: confirm outdated due to dropping support for other dbs
.. .. note:: For the latter line, please use the same version (in the
..   example above is 9.1) of the
..   postgresql server that you installed (in this case, to install the server of
..   the same version, use the ``sudo apt-get install postgresql-9.1`` command).
.. 
..   If you want to use postgreSQL, use a version greater than 9.1
..   (the greatest that your distribution supports).

Additional bash configuration for AiiDA
---------------------------------------

PATH settings
^^^^^^^^^^^^^

.. OLD:
.. Path configuration
.. ------------------
.. 
.. The main interface to AiiDA is through its command-line tool, called ``verdi``.
.. For it to work, it must be on the system path, and moreover the AiiDA python
.. code must be found on the python path.
.. 
.. To do this, add the following to your ``~/.bashrc`` file (create it if not already present)::
.. 
..       export PYTHONPATH=~/git/aiida:${PYTHONPATH}
..       export PATH=~/git/aiida/bin:${PATH}
.. 
.. and then source the .bashrc file with the command ``source ~/.bashrc``, or login
.. in a new window.
.. 
.. .. note:: replace ``~/git/aiida`` with the path where you installed AiiDA. Note
..   also that in the ``PYTHONPATH`` you simply have to specify the AiiDA path, while
..   in ``PATH`` you also have to append the ``/bin`` subfolder!
.. 
.. .. note:: if you installed the modules with the ``--user`` parameter during the
..   ``pip install`` step, you will need to add one more directory to your ``PATH``
..   variable in the ``~/.bashrc`` file.
..   For Linux systems, the path to add is usually ``~/.local/bin``::
.. 
..   	export PATH=~/git/aiida/bin:~/.local/bin:${PATH}
.. 
..   For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::
.. 
..   	export PATH=~/git/aiida/bin:~/Library/Python/2.7/bin:${PATH}
.. 
..   To verify if this is the correct path to add, navigate to this location and
..   you should find the executable ``supervisord`` in the directory.
.. 
.. To verify if the path setup is OK:
.. 
.. * type ``verdi`` on your terminal, and check if the program starts (it should
..   provide a list of valid commands). If it doesn't, check if you correctly set
..   up the ``PATH`` environmente variable above.
.. * go in your home folder or in another folder different from the AiiDA folder,
..   run ``python`` or ``ipython`` and try to import a module, e.g. typing::
.. 
..     import aiida
.. 
..   If the setup is ok, you shouldn't get any error. If you do get an
..   ``ImportError`` instead, check if you correctly set up the ``PYTHONPATH``
..   environment variable in the steps above.

The main interface to AiiDA is through its command-line tool, called ``verdi``.

.. note:: if you installed the modules with the ``--user`` parameter during the
  ``pip install`` step, you will need to add one more directory to your ``PATH``
  variable in the ``~/.bashrc`` file.
  For Linux systems, the path to add is usually ``~/.local/bin``::

  	export PATH=~/.local/bin:${PATH}

  For Mac OS X systems, the path to add is usually ``~/Library/Python/2.7/bin``::

  	export PATH=~/Library/Python/2.7/bin:${PATH}

  To verify if this is the correct path to add, navigate to this location and
  you should find the executable ``supervisord``, or ``celeryd``, in the directory.

To verify if the path setup is OK:

* type ``verdi`` on your terminal, and check if the program starts (it should
  provide a list of valid commands). If it doesn't, check if you correctly set
  up the ``PATH`` environmente variable above.
* go in your home folder or in another folder different from the AiiDA folder,
  run ``python`` or ``ipython`` and try to import a module, e.g. typing::

    import aiida

  If the setup is ok, you shouldn't get any error. If you do get an
  ``ImportError`` instead, check if you correctly set up the ``PYTHONPATH``
  environment variable in the steps above.


Bash completion
^^^^^^^^^^^^^^^

``verdi`` fully supports bash completion (i.e., the possibility to press the
``TAB`` of your keyboard to get a list of sensible commands to type.
We strongly suggest to enable bash completion by adding also the following
line to your ``.bashrc``, **after** the previous lines::

   eval "$(verdi completioncommand)"

If you feel that the bash loading time is becoming too slow, you can instead
run the::

    verdi completioncommand

on a shell, and copy-paste the output directly inside your ``.bashrc`` file,
**instead** of the ``eval "$(verdi completioncommand)"`` line.

Remember, after any modification to the ``.bashrc`` file, to source it,
or to open a new shell window.

.. note:: remember to check that your ``.bashrc`` is sourced also from your
  ``.profile`` or ``.bash_profile`` script. E.g., if not already present,
  you can add to your ``~/.bash_profile`` the following lines::

    if [ -f ~/.bashrc ]
    then
        . ~/.bashrc
    fi

If you chose to work with multiple AiiDA versions or just prefer explicitly working inside the virtual invironment in which you installed aiida, it might be a good idea to put the completion command into a postactivation hook of your python environment manager (look up in the documentation of your manager how to do this).

Optional dependencies
---------------------

.. _CIF_manipulation_dependencies:

CIF manipulation
^^^^^^^^^^^^^^^^

For the manipulation of `Crystallographic Information Framework (CIF) files`_,
following dependencies are required to be installed:

* `PyCifRW`_
* `pymatgen`_
* `pyspglib`_
* `jmol`_
* `Atomic Simulation Environment (ASE)`_
* :doc:`cod-tools<plugins/codtools/index>`

First four can be installed from the default repositories::

    sudo pip install pycifrw==3.6.2.1
    sudo pip install pymatgen==3.0.13
    sudo pip install pyspglib
    sudo apt-get install jmol

ASE has to be installed from source::

    curl https://wiki.fysik.dtu.dk/ase-files/python-ase-3.8.1.3440.tar.gz > python-ase-3.8.1.3440.tar.gz
    tar -zxvf python-ase-3.8.1.3440.tar.gz
    cd python-ase-3.8.1.3440
    setup.py build
    setup.py install
    export PYTHONPATH=$(pwd):$PYTHONPATH

For the setting up of cod-tools please refer to
`the software homepage<https://github.com/sauliusg/cod-tools>`.

.. _Crystallographic Information Framework (CIF) files: http://www.iucr.org/resources/cif
.. _pymatgen: http://pymatgen.org
.. _Atomic Simulation Environment (ASE): https://wiki.fysik.dtu.dk/ase/
.. _PyCifRW: https://pypi.python.org/pypi/PyCifRW/3.6.2
.. _jmol: http://jmol.sourceforge.net
.. _pyspglib: http://spglib.sourceforge.net/pyspglibForASE/

Setting up AiiDA for use
++++++++++++++++++++++++

Adding and editing profiles
---------------------------

If you wish AiiDA to try to automatically create a database for your new profile and to guess sensible defaults for all the values you leave out you can add a profile using::

   verdi quicksetup --profile=<profile>
   # verdi quicksetup -h for possible commandline options

If you prefer to setup a database by hand first or are only going to edit the profile run the following command::

   verdi setup <profile> # synonym to verdi -p <profile> setup

to add or edit a profile in AiiDA. The command will guide you through a process to configure
the database, the repository location, and it will finally (automatically) run
a django ``migrate`` command, if needed, that creates the required tables
in the database and installs the database triggers.

The first thing that will be asked to you is the timezone, extremely important
to get correct dates and times for your calculations.

AiiDA will do its best to try and understand the local timezone (if properly
configured on your machine), and will suggest a set of sensible values.
Choose the timezone that fits best to you (that is, the nearest city in your
timezone - for Lausanne, for instance, we choose ``Europe/Zurich``) and type
it at the prompt.

If the automatic zone detection did not work for you,  type instead another
valid string.
A list of valid strings can be found at
http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
but for the definitive list of timezones supported by your system, open
a python shell and type::

  import pytz
  print pytz.all_timezones

as AiiDA will not accept a timezone string that is not in the above list.

As a second parameter to input during the ``verdi setup`` phase,
the "Default user email" is asked.

We suggest here to use your institution email, that will be used to associate
the calculations to you.

.. note:: In AiiDA, the user email is used as
  username, and also as unique identifier when importing/exporting data from
  AiiDA.

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
	Database engine: sqlite3
	AiiDA Database location: /home/wagner/.aiida/aiida.db
	AiiDA repository directory: /home/wagner/.aiida/repository/
	[...]
	Configuring a new user with email 'richard.wagner@leipzig.de'
	First name: Richard
	Last name: Wagner
	Institution: BRUHL, LEIPZIG
	The user has no password, do you want to set one? [y/N] y
	Insert the new password:
	Insert the new password (again):

.. OLD:
.. .. note:: When the "Database engine" is asked, use 'sqlite3' **only if** you want
..   to try out AiiDA without setting up a database.
.. 
..   **However, keep in mind that for serious use, SQLite has serious
..   limitations!!** For instance, when many calculations are managed at the same
..   time, the database file is locked by SQLite to avoid corruption, but this
..   can lead to timeouts that do not allow to AiiDA to properly store the
..   calculations in the DB.
.. 
..   **Therefore, for production use of AiiDA, we strongly suggest to setup a
..   "real" database** as PostgreSQL or MySQL. Then, in the "Database engine"
..   field, type either 'postgres' or 'mysql' according to the database you
..   chose to use. See :doc:`here<database/index>` for the documentation
..   to setup such databases (including info on how to proceed with ``verdi install``
..   in this case).

At the end, AiiDA will also ask to configure your user, if you set up a user
different from ``aiida@localhost``.

If something fails, there is a high chance that you may have misconfigured
the database. Double-check your settings before reporting an error.

.. note:: The repository will contain the same number of folders
  as the number of nodes plus the number of workflows. For very large databases,
  some operations on the repository folder, such as rsync or scanning its content,
  might be very slow, and if they are performed reguarly this will slow down
  the computer due to an intensive use of the hard drive.
  Check out our :ref:`tips<repo_troubleshooting>` in the
  troubeshooting section in case this happens.

.. _setup-noninteractive:

Programmatically setup AiiDA profiles:
--------------------------------------

.. code-block:: bash
   
   $ verdi setup <profile> --non-interactive --email=<..> ...

Can be used to create profiles from scripts. If not all values are given on the commandline, setup will fail. Type::

   $ verdi setup -h

For a list of options that have to be passed.

Command reference
+++++++++++++++++

.. _quicksetup:

Verdi quicksetup
----------------

Usage::

	$ verdi quicksetup --help
   $ verdi quicksetup [options]

This command will try to create everything that is needed to start working with aiida. This includes a postgres database with user and an AiiDA configuration with a profile. This command can not be used to edit existing profiles. The database creation is equivalent to the process documented in :ref:`setup`

Make sure your postgresql daemon is running and you are either a postgres super user or have sudo rights to your system to switch to a postgres super user.

Setup and configure AiiDA using::
      
   $ verdi quicksetup

This will prompt you for an email address, first and last name and institution.
Remember that it is important for this information to be accurate if you wish to share your results with other AiiDA users.

Optionally you cann pass the same information as commandline options::

   $ verdi quicksetup --email=<email> --first-name=<First> --last-name=<Last> --institution=<Inst>

More commandline options are available in case you custom configured your postgresql installation, or if you would like to store your setup under a different profile name than "quicksetup". For an overview use::

   $ verdi quicksetup --help

.. _setup:

Verdi setup
-----------

This command was previously called ``verdi install``

``verdi setup`` will not create a database for your profile, instead before setting up a new profile, follow the instructions in :ref:`create_db`.
Use this command to reconfigure a previously setup profile.

On Mac OS X it is important to remember to start the postgres daemon first using ``pg_ctl start -D <database dir>``, where <database dir> depends on how you installed postgres.

Usage::

   $ verdi setup --help
   $ verdi -p profile setup [options]
   $ verdi setup [options] profile
   $ verdi setup --non-interactive OPTIONS profile

.. OLD:
.. Downloading the code
.. ++++++++++++++++++++
.. 
.. Download the code using git in a directory of your choice (``~/git/aiida`` in
.. this tutorial), using the
.. following command::
.. 
..     git clone https://USERNAME@github.com/aiidateam/aiida_core.git
.. 
.. (or use ``git@github.com:aiidateam/aiida_core.git`` if you are downloading
.. through SSH; note that this requires your ssh key to be added on the
.. GitHub account.)
.. 
.. Python dependencies
.. +++++++++++++++++++
.. Python dependencies are managed using ``pip``, that you have installed in the
.. previous steps.
.. 
.. As a first step, check that ``pip`` is at its most recent version.
.. 
.. One possible way of doing this is to update ``pip`` with itself, with
.. a command similar to the following::
.. 
..   sudo pip install -U pip
.. 
.. Then, install the python dependencies is as simple as this::
.. 
..       cd ~/git/aiida # or the folder where you downloaded AiiDA
..       pip install --user -U -r requirements.txt
.. 
.. (this will download and install requirements that are listed in the
.. ``requirements.txt`` file; the ``--user`` option allows to install
.. the packages as a normal user, without the need of using ``sudo`` or
.. becoming root). Check that every package is installed correctly.
.. 
.. There are some additional dependencies need to be installed if you are
.. using PostgreSQL or MySql as backend database. No additional dependency
.. is required for SQLite.
.. 
.. For PostgreSQL::
.. 
..   pip install --user psycopg2==2.6
.. 
.. For MySQL::
.. 
..   pip install --user MySQL-python==1.2.5
.. 
.. 
.. .. note:: This step should work seamlessly, but there are a number of reasons
..   for which problems may occur. Often googling for the error message helps in
..   finding a solution. Some common pitfalls are described in the notes below.
.. 
.. .. note:: if the ``pip install`` command gives you this kind of error message::
.. 
..     OSError: [Errno 13] Permission denied: '/usr/local/bin/easy_install'
.. 
..   then try again as root::
.. 
..     sudo pip install -U -r requirements.txt

Using AiiDA
+++++++++++

Start the daemon
-----------------
If you configured your user account with your personal email (or if in
general there are more than just one user) you will not be able to
start the daemon with the command ``verdi daemon start`` before its configuration.

  *If you are working in a single-user mode, and you are sure that nobody else
  is going to run the daemon*, you can configure your user as the (only)
  one who can run the daemon.

To configure the deamon, run::

    verdi daemon configureuser

and (after having read and understood the warning text that appears) insert
the email that you used above during the ``verdi setup`` phase.


To try AiiDA and start the daemon, run::

    verdi daemon start

If everything was done correctly, the daemon should start.
You can inquire the daemon status using::

    verdi daemon status

and, if the daemon is running, you should see something like::

  * aiida-daemon[0]        RUNNING    pid 12076, uptime 0:39:05
  * aiida-daemon-beat[0]   RUNNING    pid 12075, uptime 0:39:05


To stop the daemon, use::

    verdi daemon stop

A log of the warning/error messages of the daemon
can be found in ``in ~/.aiida/daemon/log/``, and can also be seen using
the ``verdi daemon logshow`` command. The daemon is
a fundamental component of AiiDA, and it is in charge of submitting new
calculations, checking their status on the cluster, retrieving and parsing
the results of finished calculations, and managing the workflow steps.

The next step will be to add computational resources (computers, codes) to work with 
The documentation for these steps can be found :doc:`here<setup/computerandcodes>`.
.. OLD:
.. (i.e.,
.. on computational resource as a cluster or a supercomputer, on which you want
.. to run your calculations) *and one code*. 

Further comments and troubleshooting
++++++++++++++++++++++++++++++++++++

* if the ``pip install`` command gives you an error that
  resembles the one
  shown below, you might need to downgrade to an older version of pip::

	Cannot fetch index base URL https://pypi.python.org/simple/

  To downgrade pip, use the following command::

	sudo easy_install pip==1.2.1

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
  time it fails (see also `this issue`_ of django).  To solve the problem, first
  remove the sqlite database that was created.

  Then, run in your terminal (or maybe even better, add to your ``.bashrc``, but
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

Updating AiiDA from a previous version
++++++++++++++++++++++++++++++++++++++

.. note::
  A few important points regarding the updates:

  * If you encounter any problems and/or inconsistencies, delete any .pyc
    files that may have remained from the previous version. E.g. If you are
    in your AiiDA folder you can type ``find . -name "*.pyc" -type f -delete``.
  * The requirements file may have changed. Please be sure that you have
    installed all the needed requirements. This can be done by executing:
    ``pip install --user -U -r requirements.txt``.
  * If you installed AiiDA using pip you should be simply able to pip install --upgrade aiida (from the python environment into which AiiDA is installed).

Updating from 0.7.0 Django to 0.8.0 Django
------------------------------------------

1. Stop the AiiDA daemon using ``verdi daemon stop``

2. Undo all PATH and PYTHONPATH changes in your ``.bashrc`` and similar files you did to add ``verdi`` and ``runaiida``. The link in step 3 documents how to set them for the new version.

3. Install AiiDA into a :ref:`virtual python environment (virtualenv) <install.faq.virtualenv>`, following :ref:`install.other.install`.
   Optionally set bash aliases for the ``verdi`` and ``runaiida`` installed into the ``bin/`` folder of the virtual environment

4. Rerun ``verdi setup`` (formerly ``verdi install``), no manual changes to your profile should be necessary. This step is necessary as it updates some internal configuration files and run a database migration.

.. TODO: Add "Execute the migration script" if necessary

Updating from 0.6.0 Django to 0.7.0 Django
------------------------------------------
In version 0.7 we have changed the Django database schema and we also have
updated the AiiDA configuration files.

* Stop your daemon (using ``verdi daemon stop``).
* Store your AiiDA source folder somewhere in case you did some
  modifications to some files.
* Replace the AiiDA folder with the new one (either from the tar.gz or,
  if you are using git, by doing a ``git pull``). If you use the same
  folder name, you will not need to update the ``PATH`` and ``PYTHONPATH``
  variables.
* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (v.0.7.0
  is using a newer version of the schema).
  The command will look like
  ``python manage.py --aiida-profile=default migrate``, but please read the
  message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.
* To update the AiiDA configuration files, you should execute the migration
  script (``python _your_aiida_folder_/aiida/common/additions/migration_06dj_to_07dj.py``).
* You can now restart your daemon and work as usual.

Updating from 0.6.0 Django to 0.7.0 SQLAlchemy
----------------------------------------------
The SQLAlchemy backend is in beta mode for version 0.7.0. Therefore some of
the verdi commands may not work as expected or at all (these are very few).
If you would like to test the new backend with your existing AiiDA database,
you should convert it to the new JSON format. We provide a transition script
that will update your config files and change your database to the new schema.


.. note::
  Please note that the transition script expects that you are already at
  version 0.6.0. Therefore if you use a previous version of AiiDA please
  update first to 0.6.0.

* Stop your daemon (using ``verdi daemon stop``).
* Store your AiiDA source folder somewhere in case you did some
  modifications to some files.
* Replace the AiiDA folder with the new one (either from the tar.gz or,
  if you are using git, by doing a ``git pull``). If you use the same
  folder name, you will not need to update the ``PATH`` and ``PYTHONPATH``
  variables.
* Go to you AiiDA folder and run ``ipython``. Then execute
  ``from aiida.backends.sqlalchemy.transition_06dj_to_07sqla import transition``
  and ``transition(profile="your_profile",group_size=10000)`` by replacing
  ``your_profile`` with the name of the profile that you would like to
  transition.
* You can now exit ipython, restart your daemon and work as usual.


Updating from 0.5.0 to 0.6.0
----------------------------
This migration will update your AiiDA configuration files making them
compatible with AiiDA version 0.6.0.

.. note::
  We performed a lot of changes to introduce in one of our following
  releases a second object-relational mapper (we will refer to it as
  back-end) for the management of the used DBMSs and more specifically
  of PostgreSQL.

  Even if most of the needed restructuring & code addition has been finished,
  a bit of more work is needed before we make the new back-end available.

.. note::
  A few important points regarding the upgrade:

  * Please try to checkout the latest version from the corresponding
    development branch. Problems encountered are resolved and fixes are
    pushed to the branch.
  * You can not directly import data (``verdi import``) that you have exported
    (``verdi export``) with a previous version of AiiDA. Please use
    :download:`this script <examples/convert_exportfile_version.py>`
    to convert it to the new schema. (Usage: ``python
    convert_exportfile_version.py input_file output_file``).


To perform the update:

* Stop your daemon (using ``verdi daemon stop``).
* Backup your configuration files that are in .aiida directory.
* Replace the AiiDA folder with the new one (e.g. by doing a ``git pull``).
  If you use the same folder name, you will not need to update the
  ``PATH`` and ``PYTHONPATH`` variables.
* Execute the migration script (``python _your_aiida_folder_/aiida/common/additions/migration.py``).
* Start again you daemon (using ``verdi daemon start``).


Updating from 0.4.1 to 0.5.0
----------------------------
* Stop your daemon (using ``verdi daemon stop``)
* Store your AiiDA source folder somewhere in case you did some
  modifications to some files
* Replace the AiiDA folder with the new one (either from the tar.gz or,
  if you are using git, by doing a ``git pull``). If you use the same
  folder name, you will not need to update the ``PATH`` and ``PYTHONPATH``
  variables
* Run a ``verdi`` command, e.g., ``verdi calculation list``. This should
  raise an exception, and in the exception message you will see the
  command to run to update the schema version of the DB (v.0.5.0
  is using a newer version of the schema).
  The command will look like
  ``python manage.py --aiida-profile=default migrate``, but please read the
  message for the correct command to run.
* If you run ``verdi calculation list`` again now, it should work without
  error messages.
* You can now restart your daemon and work as usual.

.. note:: If you modified or added files, you need to put them back in place.
  Note that if you were working on a plugin, the plugin interface changed:
  you need to change the CalcInfo returning also a CodeInfo, as specified
  :ref:`here<qeplugin-prepare-input>` and also accept a ``Code`` object
  among the inputs (also described in the same page).



