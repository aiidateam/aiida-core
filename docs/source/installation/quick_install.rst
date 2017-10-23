.. _quick_install:

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

For a more detailed description of database requirements and usage see section :ref:`database <database>`.

Install AiiDA and its python dependencies
+++++++++++++++++++++++++++++++++++++++++
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

  If you run into issue related to ``version 'GFORTRAN_1.4'`` when installing through Anaconda, see the :ref:`troubleshooting <troubleshooting>` section 


Configure the AiiDA installation
++++++++++++++++++++++++++++++++
After successful installation, AiiDA needs to be configured, such as setting up a profile and creating a database, which can be done through AiiDA's command line interface ``verdi``.
For a fast and default setup use ``verdi quicksetup`` and for greater control use ``verdi setup`` (see :ref:`verdi setup <verdi_setup>`).
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


