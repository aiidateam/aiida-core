.. _installation:

************
Installation
************

This section of the manual will guide you through the process of installing AiiDA on your system.
AiiDA has been tested to run on the following platforms:

* Ubuntu 14.04, 16.04
* Mac OS X

We expect that AiiDA should also run on these other platforms:

* Older and newer Ubuntu versions
* Other Linux distributions

The installation procedure can generally be split into four separate steps:

1. :ref:`Install prerequisite software<install_prerequisites>`
2. :ref:`Install AiiDA<install_aiida>`
3. :ref:`Setup AiiDA<setup_aiida>`
4. :ref:`Configure AiiDA<configure_aiida>`


.. _install_prerequisites:

Install prerequisites
=====================

The installation procedure itself requires certain software, which therefore will have to be installed first.
The following software is required to continue with the installation:

* `git`_ (To download the ``aiida-core`` repository)
* `python-2.7.x`_ (The programming language used for AiiDA)
* `python-pip`_ (Python package manager)
* `virtualenv`_ (Software to create a virtual python environment to install AiiDA in)
* `postgresql`_ (Database software version 9.4 or higher)
* `RabbitMQ`_ (A message broker necessary for AiiDA to communicate between processes)

.. _git: https://git-scm.com/downloads
.. _python-2.7.x: https://www.python.org/downloads
.. _python-pip: https://packaging.python.org/installing/#requirements-for-installing-packages
.. _virtualenv: https://packages.ubuntu.com/xenial/virtualenv
.. _postgresql: https://www.postgresql.org/downloads
.. _RabbitMQ: https://www.rabbitmq.com/


The installation instructions for these prerequisites will depend on the operating system of your machine.
We provide basic instructions for :ref:`several operating systems<installation_os>`.
Make sure you have successfully installed these prerequisites before continuing with the installation guide.


.. _install_aiida:

Install AiiDA
=============

With the prerequisites installed, we can now download AiiDA itself and install it along with all its python dependencies.
Create a directory where you want to install AiiDA and clone the repository::

    $ mkdir <your_directory>
    $ cd <your_directory>
    $ git clone https://github.com/aiidateam/aiida_core

To prevent the python packages that AiiDA depends on, from clashing with the packages you already have installed on your system, we will install them in a virtual environment.
For detailed information, see the section on :ref:`virtual environments <virtual_environment>`.
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

.. note:: If you are installing the optional ``ssh_kerberos`` and you are on Ubuntu you might encounter an error related to the ``gss`` package.
  To fix this you need to install the ``libffi-dev`` and ``libkrb5-dev`` packages::

    sudo apt-get install libffi-dev libkrb5-dev


.. _setup_aiida:

Setup AiiDA
===========

After successful installation AiiDA needs to be setup, which includes setting up a profile.
This can be accomplished through through AiiDA's command line interface ``verdi``.
The setup functionality requires that a database has already been created, for information on how to do this, please refer to the :ref:`database section<database>`.
Once the database has been created, AiiDA can be setup by calling the following command:

.. code-block:: bash

    verdi setup <profile_name>

or equivalently

.. code-block:: bash

    verdi -p <profile_name> setup

where `<profile_name>` is a profile name of your choosing.
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


Remember that in order to work with AiiDA through for example the ``verdi`` command, you need to be in your virtual environment.
If you open a new terminal for example, be sure to activate it first with::

    $ source ~/aiidapy/bin/activate

At this point, you can choose to read on for additional installation details and configuration options, or you can choose to start using
AiiDA and go straight to the section :ref:`get started<get_started>`.


.. _configure_aiida:

Configure AiiDA
===============

.. _tab-completion:

Verdi tab-completion
--------------------
The ``verdi`` command line interface has many commands and options.
To simplify its usage, there is a way to enable tab-completion for it in your shell.
To do so, simply add the following line to the activation script of your virtual environment (or to your shell config, e.g. ``.bashrc``)::

    eval "$(_VERDI_COMPLETE=source verdi)"

For the changes to apply to your current shell, make sure to source the activation script or ``.bashrc`` (depending the approach you chose).

.. note::
    This line replaces the ``eval "$(verdi completioncommand)"`` line that was used in ``aiida-core<1.0.0``.

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
  run ``python`` or ``ipython`` and try to import a module, e.g. typing::

    import aiida

  If the setup is ok, you shouldn't get any error. If you do get an ``ImportError`` instead, check
  that you are in the correct virtual environment. If you did not install AiiDA
  within a virtual environment, you will have to set up the ``PYTHONPATH``
  environment variable in your ``.bashrc``::

    export PYTHONPATH="${PYTHONPATH}:<AiiDA_folder>"

.. _directory_location:

Customizing the configuration directory location
------------------------------------------------

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
----------------------

`Jupyter <http://jupyter.org>`_ is an open-source web application that allows you to create in-browser notebooks containing live code, visualizations and formatted text.

Originally born out of the iPython project, it now supports code written in many languages and customized iPython kernels.

If you didn't already install AiiDA with the ``[notebook]`` option (during ``pip install``), run ``pip install jupyter`` **inside** the virtualenv, and then run **from within the virtualenv**::

    $ jupyter notebook

This will open a tab in your browser. Click on ``New -> Python 2`` and type::

    import aiida

followed by ``Shit-Enter``. If no exception is thrown, you can use AiiDA in Jupyter.

If you want to set the same environment as in a ``verdi shell``, add the following code in ``<your.home.folder>/.ipython/profile_default/ipython_config.py``::

  try:
      import aiida
  except ImportError:
      pass
  else:
      c = get_config()
      c.InteractiveShellApp.extensions = [
            'aiida.common.ipython.ipython_magics'
      ]

then open a Jupyter notebook as explained above and type in a cell:

    %aiida

followed by ``Shift-Enter``. You should receive the message "Loaded AiiDA DB environment."