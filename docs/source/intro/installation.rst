.. _intro:install:

*********************
Detailed Installation
*********************

.. _intro:install:prerequisites:

Installing Prerequisites
========================

AiiDA is designed to run on `Unix <https://en.wikipedia.org/wiki/Unix>`_ operating systems and requires the following software:

* `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_ or
  `zsh <https://en.wikipedia.org/wiki/Z_shell>`_ (The shell)
* `python`_ >= 3.6 (The programming language used by AiiDA)
* `python3-pip`_ (Python 3 package manager)
* `postgresql`_ (Database software, version 9.4 or higher)
* `RabbitMQ`_ (A message broker necessary for AiiDA to communicate between processes)

Depending on your set up, there are a few optional dependencies:

* `git`_ (Version control system used for AiiDA development)
* `graphviz`_ (For plotting AiiDA provenance graphs)

.. _graphviz: https://www.graphviz.org/download
.. _git: https://git-scm.com/downloads
.. _python: https://www.python.org/downloads
.. _python3-pip: https://packaging.python.org/installing/#requirements-for-installing-packages
.. _virtualenv: https://packages.ubuntu.com/bionic/virtualenv
.. _virtualenvwrapper: https://packages.ubuntu.com/bionic/virtualenvwrapper
.. _postgresql: https://www.postgresql.org/downloads
.. _RabbitMQ: https://www.rabbitmq.com/

AiiDA has been tested on the following platforms:

* Ubuntu 14.04, 16.04, 18.04
* Mac OS X

We expect AiiDA to also run on:

* Older and newer Ubuntu versions
* Other Linux distributions
* Windows Subsystem for Linux (WSL)

Below, we provide installation instructions for a number of operating systems.

.. div:: dropdown-group

   .. dropdown:: Ubuntu

      .. code-block:: console

         $ sudo apt-get install \
            postgresql postgresql-server-dev-all postgresql-client rabbitmq-server \
            git python3-dev python3-pip
         $ pip install aiida-core

      See :ref:`Ubuntu instructions<intro:install:prerequisites:ubuntu>` for details.

   .. dropdown:: MacOS X (Homebrew)

      .. code-block:: console

         $ brew install postgresql rabbitmq git python
         $ brew services start postgresql
         $ brew services start rabbitmq
         $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
         $ python get-pip.py
         $ pip install aiida-core

      See :ref:`MacOS X (Homebrew) instructions<intro:install:prerequisites:brew>` for details.

   .. dropdown:: MacOS X (MacPorts)

      .. code-block:: console

         $ sudo port install postgresql postgresql-server rabbitmq-server
         $ pg_ctl -D /usr/local/var/postgres start
         $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
         $ python get-pip.py
         $ pip install aiida-core

      See :ref:`MacOS X (MacPorts) instructions<intro:install:prerequisites:macports>` for details.

   .. dropdown:: Gentoo Linux

      .. code-block:: console

         $ emerge -av git postgresql rabbitmq-server
         $ rc-update add rabbitmq
         $ emerge --ask dev-lang/python:3.7
         $ emerge --ask dev-python/pip
         $ pip install aiida-core

      See :ref:`Gentoo Linux instructions<intro:install:prerequisites:gentoo>` for details.

   .. dropdown:: Windows Subsystem for Linux

      .. code-block:: console

         $ sudo apt-get install \
            postgresql postgresql-server-dev-all postgresql-client \
            git python3-dev python-pip
         $ sudo service postgresql start
         # install rabbitmq on windows
         $ pip install aiida-core

      See :ref:`WSL instructions<intro:install:prerequisites:wsl>` for details.

.. _intro:install:prerequisites:ubuntu:

Ubuntu
------

To install the prerequisites on Ubuntu and any other Debian derived distribution, you can use the ``apt`` package manager.
The following will install the basic ``python`` requirements and the ``git`` source control manager:

.. code-block:: console

   $ sudo apt-get install git python3-dev python3-pip

To install the requirements for the ``postgres`` database run the following:

.. code-block:: console

   $ sudo apt-get install postgresql postgresql-server-dev-all postgresql-client

Install the RabbitMQ message broker:

.. code-block:: console

   $ sudo apt-get install rabbitmq-server

This installs and adds RabbitMQ as a system service. To check whether it is running:

.. code-block:: console

   $ sudo rabbitmqctl status

If it is not running already, it should after a reboot.

Finally install the aiida-core python environment:

.. code-block:: console

   $ sudo git python3-dev python3-pip
   $ pip install aiida-core

.. admonition:: Further Reading
   :class: seealso title-icon-read-more

   - For a more detailed description of database requirements and usage see the :ref:`database topic<topics:database>`.
   - For problems with installing RabbitMQ, refer to the detailed instructions provided on the `RabbitMQ website for Debian based distributions <https://www.rabbitmq.com/install-debian.html>`_.

.. _intro:install:prerequisites:brew:

Mac OS X (homebrew)
-------------------

For Mac OS we recommend using the `Homebrew`_ package manager.
If you have not installed Homebrew yet, you can do so with the following command:

.. code-block:: console

   $ /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

.. _Homebrew: http://brew.sh/index_de.html

After you have installed Homebrew, you can install the basic requirements as follows:

.. code-block:: console

   $ brew install postgresql rabbitmq git python

To start the ``postgres`` database server and ``rabbitmq`` service, execute:

.. code-block:: console

   $ brew services start postgresql
   $ brew services start rabbitmq

You can check whether it is running by checking the status through the command:

.. code-block:: console

   $ /usr/local/sbin/rabbitmqctl status

Finally install the aiida-core python environment:

.. code-block:: console

   $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   $ python get-pip.py
   $ pip install aiida-core

.. admonition:: Further Reading
   :class: seealso title-icon-read-more

   - For a more detailed description of database requirements and usage see the :ref:`database topic<topics:database>`.
   - For problems with installing RabbitMQ, refer to the detailed instructions provided on the `RabbitMQ website for Homebrew based distributions <https://www.rabbitmq.com/install-homebrew.html>`_.
   - For details on the installation of the ``pip`` package manager, refer to `their documentation <https://pip.pypa.io/en/stable/installing/#installation>`_

.. _intro:install:prerequisites:macports:

Mac OS X (MacPorts)
-------------------

.. _macports: https://www.macports.org/

Another package manager for MacOS is `macports`_.

.. code-block:: console

   $ sudo port install postgresql postgresql-server rabbitmq-server git python

To start the ``postgres`` database server, run:

.. code-block:: console

   $ sudo su postgres
   $ pg_ctl -D /opt/local/var/db/postgresql96/defaultdb start

To start the ``rabbitmq`` server, run:

.. code-block:: console

   $ sudo launchctl load -w /Library/LaunchDaemons/org.macports.rabbitmq-server.plist

You can check whether it is running as follows:

.. code-block:: console

   $ sudo rabbitmqctl status
     # this starts ``rabbitmq`` at system startup:
   $ sudo port load rabbitmq-server

Finally install the aiida-core python environment:

.. code-block:: console

   $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
   $ python get-pip.py
   $ pip install aiida-core

.. admonition:: Trouble Installing RabbitMQ?
   :class: attention title-icon-troubleshoot

   Be sure to install ``rabbitmq-server 3.7.9`` or later.
   If ``rabbitmqctl status`` returns an error "Hostname mismatch", the easiest solution can be to simply ``sudo port uninstall`` the package and install it again.

.. admonition:: Further Reading
   :class: seealso title-icon-read-more

   - For a more detailed description of database requirements and usage see the :ref:`database topic<topics:database>`.
   - For details on the installation of the ``pip`` package manager, refer to `their documentation <https://pip.pypa.io/en/stable/installing/#installation>`_

.. _intro:install:prerequisites:gentoo:

Gentoo Linux
------------

To install RabbitMQ on a Gentoo distribution through the ``portage`` package manager run the following command:

.. code-block:: console

   $ emerge -av rabbitmq-server

To make sure that RabbitMQ is started at system boot, execute:

.. code-block:: console

    rc-update add rabbitmq

If you want to manually start the RabbitMQ server you can use:

.. code-block:: console

    /etc/init.d/rabbitmq start

Make sure that RabbitMQ is running with:

.. code-block:: console

    rabbitmqctl status

.. admonition:: Trouble Installing RabbitMQ?
   :class: attention title-icon-troubleshoot

    If you have encounter the following error

    .. code-block:: console

        Argument '-smp enable' not supported."

    Remove the mentioned option from the file ``/usr/libexec/rabbitmq/rabbitmq-env`` and restart the server.
    If you still have trouble getting RabbitMQ to run, please refer to the detailed instructions provided on the `website of RabbitMQ itself for generic Unix systems <https://www.rabbitmq.com/install-generic-unix.html>`_.


.. _intro:install:prerequisites:wsl:

Windows Subsystem for Linux (Ubuntu)
------------------------------------

The guide for Ubuntu above can generally be followed, but there are a few things to note:

.. admonition:: Tip
   :class: tip title-icon-tip

   Installing `Ubuntu <https://www.microsoft.com/en-gb/p/ubuntu/9nblggh4msv6?source=lp&activetab=pivot:overviewtab>`_ instead of the version specific applications, will let you have the latest LTS version.

#. The `Windows native RabbitMQ <https://www.rabbitmq.com/install-windows.html>`_ should be installed and started.
   (For WSL 2, this should not be necessary.)

#. Linux services under WSL are not started automatically.
   To start the PostgreSQL and RabbitMQ-server services, type the commands below in the terminal::

     sudo service postgresql start
     sudo service rabbitmq-server start

   .. admonition:: Tip
      :class: tip title-icon-tip

      These services may be run at startup *without* passing a password in the following way:

      Create a ``.sh`` file with the lines above, but *without* ``sudo``.
      Make the file executeable, i.e., type:

      .. code-block:: console

         $ chmod +x /path/to/file.sh
         $ sudo visudo

      And add the line:

      .. code-block:: sh

         <username> ALL=(root) NOPASSWD: /path/to/file.sh

      Replacing ``<username>`` with your Ubuntu username.
      This will allow you to run *only* this specific ``.sh`` file with ``root`` access (without password), without lowering security on the rest of your system.

#. There is a `known issue <https://github.com/Microsoft/WSL/issues/856>`_ in WSL Ubuntu 18.04 where the timezone is not configured correctly out-of-the-box, which may cause problem for the database.
   The following command can be used to re-configure the time zone:

   .. code-block:: console

      $ sudo dpkg-reconfigure tzdata

#. The file open limit may need to be raised using ``ulimit -n 2048`` (default is 1024), when running tests.
   You can check the limit by using ``ulimit -n``.

   .. hint:: This may need to be run every time the system starts up.

It may be worth considering adding some of these commands to your ``~/.bashrc`` file, since some of these settings may reset upon reboot.

.. admonition:: Further Reading
   :class: seealso title-icon-read-more

   For using WSL as a developer, please see the considerations made in our `wiki-page for developers <https://github.com/aiidateam/aiida-core/wiki/Development-environment#using-windows-subsystem-for-linux-wsl>`_.

.. _intro:install:virtual_environments:

Using virtual environments
==========================

AiiDA depends on a number of third party python packages, and usually on specific versions of those packages.
In order not to interfere with third party packages needed by other software on your system, we **strongly** recommend isolating AiiDA in a virtual python environment.

.. admonition:: Additional Information
   :class: seealso title-icon-read-more

   A very good tutorial on python environments is provided by `realpython.com <https://realpython.com/effective-python-environment>`__.

`venv <https://docs.python.org/3/library/venv.html>`__ is module included directly with python for creating virtual environments.
To create a virtual environment, in a given directory, run:

.. code-block:: console

   $ python3 -m venv /path/to/new/virtual/environment/aiida

The command to activate the environment is shell specific (see `the documentation <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`__.
With bash the following command is used:

.. code-block:: console

   $ source /path/to/new/virtual/environment/aiida/bin/activate

To leave or deactivate the environment, simply run:

.. code-block:: console

    (aiida) $ deactivate

.. admonition:: Update install tools
   :class: tip title-icon-tip

   You may need to install ``pip`` and ``setuptools`` in your virtual environment in case the system or user version of these tools is old

   .. code-block:: console

      (aiida) $ pip install -U setuptools pip

If you have `Conda`_ installed then you can directly create a new environment with ``aiida-core`` and (optionally) Postgres and RabbitMQ installed.

.. code-block:: console

   $ conda create -n aiida -c conda-forge python=3.7 aiida-core aiida-core.services pip
   $ conda activate
   $ conda deactivate aiida


.. _intro:install:aiida-core:

Installing the aiida-core package
=================================

.. _Conda: https://anaconda.org/conda-forge/aiida-core
.. _PyPI: https://pypi.python.org/pypi/aiida-core
.. _github repository: https://github.com/aiidateam/aiida-core

AiiDA can be installed either from the python package index `PyPI`_, `Conda`_ (both good for general use) or directly from the aiida-core `github repository`_ (good for developers).

With your virtual environment active (see above), install the ``aiida-core`` python package from `PyPI`_ using:

.. code-block:: console

    $ pip install aiida-core

.. admonition:: Installing AiiDA in your system environment
   :class: tip title-icon-tip

   Consider adding the ``--user`` flag to avoid the need for administrator privileges.

Alternatively, you can create a directory where to clone the AiiDA source code and install AiiDA from source:

.. code-block:: console

    $ mkdir <your_directory>
    $ cd <your_directory>
    $ git clone https://github.com/aiidateam/aiida-core
    $ pip install -e aiida-core

There are additional optional packages that you may want to install, which are grouped in the following categories:

    * ``atomic_tools``: packages that allow importing and manipulating crystal structure from various formats
    * ``ssh_kerberos``: adds support for ssh transport authentication through Kerberos
    * ``REST``: allows a REST server to be ran locally to serve AiiDA data
    * ``docs``: tools to build the documentation
    * ``notebook``: jupyter notebook - to allow it to import AiiDA modules
    * ``testing``: python modules required to run the automatic unit tests

In order to install any of these package groups, simply append them as a comma separated list in the ``pip`` install command

.. code-block:: console

    $ pip install -e aiida-core[atomic_tools,docs]

.. admonition:: Keberos on Ubuntu
   :class: note title-icon-troubleshoot

   If you are installing the optional ``ssh_kerberos`` and you are on Ubuntu you might encounter an error related to the ``gss`` package.
   To fix this you need to install the ``libffi-dev`` and ``libkrb5-dev`` packages:

.. code-block:: console

   $ sudo apt-get install libffi-dev libkrb5-dev

AiiDA uses the `reentry <https://pypi.org/project/reentry/>`_ package to keep a fast cache of entry points for a snappy ``verdi`` cli.
After installing AiiDA packages, always remember to update the reentry cache using:

.. code-block:: console

   $ reentry scan

.. _intro:setup:

Setting up the installation
===========================

.. _intro:setup:profile:

AiiDA profile setup
-------------------

After successful installation, you need to create an AiiDA profile via AiiDA's command line interface ``verdi``.

Most users should use the interactive quicksetup:

.. code-block:: console

    $ verdi quicksetup

which leads through the installation process and takes care of creating the corresponding AiiDA database.

For maximum control and customizability, one can use ``verdi setup`` and set up the database manually as explained below.

.. admonition:: Want to manage multiple profiles?
   :class: seealso title-icon-read-more

   See the :ref:`managing profiles how-to <how-to:installation:profile>`.


.. _intro:setup:start_daemon:

Starting the daemon
-------------------

The AiiDA daemon process runs in the background and takes care of processing your submitted calculations and workflows, checking their status, retrieving their results once they are finished and storing them in the AiiDA database.

The AiiDA daemon is controlled using three simple commands:

 * ``verdi daemon start``: start the daemon
 * ``verdi daemon status``: check the status of the daemon
 * ``verdi daemon stop``: stop the daemon

.. note::

    While operational, the daemon logs its activity to a file in ``~/.aiida/daemon/log/`` (or, more generally, ``$AIIDA_PATH/.aiida/daemon/log``).
    Get the latest log messages via ``verdi daemon logshow``.

.. _intro:setup:final_checks:

Final checks
------------

Use the ``verdi status`` command to check that all services are up and running:

.. code-block:: console

   $ verdi status

   ✓ profile:     On profile quicksetup
   ✓ repository:  /repo/aiida_dev/quicksetup
   ✓ postgres:    Connected to aiida@localhost:5432
   ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
   ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

In the example output, all service have a green check mark and so should be running as expected.

.. admonition:: Want to know more about managing your install?
   :class: seealso title-icon-read-more

   See the :ref:`Installation how-to <how-to:installation>`

   :link-badge:`how-to:installation:configure,Configuring,ref,badge-primary text-white`
   :link-badge:`how-to:installation:update,Updating,ref,badge-primary text-white`
   :link-badge:`how-to:installation:backup:software,Backing-up,ref,badge-primary text-white`


.. _intro:install:docker:

Using the Docker image
======================

AiiDA maintains a `Docker <https://www.docker.com/>`__ image on `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core>`__.
This image contains a pre-configured AiiDA environment, and so is particularly useful for learning and testing purposes.
It is a great way to quickly get started on the tutorials!

Follow Docker's `install guide <https://docs.docker.com/get-docker/>`__ to download Docker and start its daemon.
Now you can pull the aiida-core image straight from Docker Hub, for a specific version.

.. code-block:: console

   $ docker pull aiidateam/aiida-core:1.2.1

We can start a container running by:

.. code-block:: console

   $ docker run -d --name aiida-container aiidateam/aiida-core:1.2.1

The container comes installed with all required services and, on start-up, will automatically start them and create an AiiDA profile (plus a localhost computer).
To (optionally) wait for the services to start and inspect the start-up process, we can run:

.. code-block:: console

   $ docker exec -t aiida-container wait-for-services
   $ docker logs aiida-container

The profile is created under the ``aiida`` username, so to execute commands use:

.. code-block:: console

   $ docker exec -t --user aiida aiida-container /bin/bash -l -c 'verdi status'
   ✓ config dir:  /home/aiida/.aiida
   ✓ profile:     On profile default
   ✓ repository:  /home/aiida/.aiida/repository/default
   ✓ postgres:    Connected as aiida_qs_aiida_477d3dfc78a2042156110cb00ae3618f@localhost:5432
   ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
   ✓ daemon:      Daemon is running as PID 1795 since 2020-05-20 02:54:00

Or to enter into the container interactively:

.. code-block:: console

   $ docker exec -it --user aiida aiida-container /bin/bash

If you stop the container and start it again, any data you created will persist.

.. code-block:: console

   $ docker stop aiida-container
   $ docker start aiida-container

But if you remove the container all data will be removed.

.. code-block:: console

   $ docker stop aiida-container
   $ docker rm aiida-container

To store data and even share it between containers, you may wish to `add a volume <https://docs.docker.com/storage/volumes/>`__:

.. code-block:: console

   $ docker run -d --name aiida-container --mount source=my_data,target=/tmp/my_data aiidateam/aiida-core:1.2.1

Now anything that you save to the ``/tmp/my_data`` folder will be saved to the volume persistently.
You can even add files directly to the folder outside of the container, by finding its mounting point:

.. code-block:: console

   $ docker volume inspect my_data
   $ echo "hallo" | sudo tee -a /var/lib/docker/volumes/my_data/_data/hallo.txt  > /dev/null
