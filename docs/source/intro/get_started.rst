.. _intro:get_started:

****************
Getting started
****************

An AiiDA installation consists of three core components (plus any external codes you wish to run):

* aiida-core: The main Python package and the associated ``verdi`` command line interface
* |PostgreSQL|: The service that manages the database that AiiDA uses to store data.
* |RabbitMQ|: The message broker used for communication within AiiDA.

.. _intro:install:setup:
.. _intro:get_started:setup:

Setup
=====

There are multiple routes to setting up a working AiiDA environment.
Which of those is optimal depends on your environment and use case.
If you are unsure, use the :ref:`system-wide installation <intro:get_started:system-wide-install>` method.

.. panels::
   :body: bg-light
   :footer: bg-light border-0

   :fa:`desktop,mr-1` **System-wide installation**

   .. link-button:: intro:get_started:system-wide-install
      :type: ref
      :text: Install all software directly on your workstation or laptop.
      :classes: stretched-link btn-link

   Install the prerequisite services using standard package managers (apt, homebrew, etc.) with administrative privileges.

   ---------------

   :fa:`folder,mr-1` **Installation into Conda environment**

   .. link-button:: intro:get_started:conda-install
      :type: ref
      :text: Install all software into an isolated conda environment.
      :classes: stretched-link btn-link

   This method does not require administrative privileges, but involves manual management of start-up and shut-down of services.

   ---------------

   :fa:`cube,mr-1` **Run via docker container**

   .. link-button:: intro:get_started:docker
      :type: ref
      :text: Run AiiDA and prerequisite services as a single docker container.
      :classes: stretched-link btn-link

   Does not require the separate installation of prerequisite services.
   Especially well-suited to get directly started on the **tutorials**.

   ---------------

   :fa:`cloud,mr-1` **Run via virtual machine**

   .. link-button:: https://quantum-mobile.readthedocs.io/
      :text: Use a virtual machine with all the required software pre-installed.
      :classes: stretched-link btn-link

   `Materials Cloud <https://www.materialscloud.org>`__ provides both downloadable and web based VMs,
   also incorporating pre-installed Materials Science codes.


.. _intro:get_started:system-wide-install:

System-wide installation
------------------------

The system-wide installation will install the prerequisite services (PostgreSQL and RabbitMQ) via standard package managers such that their startup and shut-down is largely managed by the operating system.
The AiiDA (core) Python package is then installed either with Conda or pip.

This is the *recommended* installation method to setup AiiDA on a personal laptop or workstation for the majority of users.

.. panels::
   :container: container-lg pb-3
   :column: col-lg-12 p-2

   **Install prerequisite services**

      AiiDA is designed to run on `Unix <https://en.wikipedia.org/wiki/Unix>`_ operating systems and requires a `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_ or `zsh <https://en.wikipedia.org/wiki/Z_shell>`_ shell, and Python >= 3.6.

   .. tabbed:: Ubuntu

      *AiiDA is tested on Ubuntu versions 16.04, 18.04, and 20.04.*

      Open a terminal and execute:

       .. code-block:: console

           $ sudo apt install \
              git python3-dev python3-pip \
              postgresql postgresql-server-dev-all postgresql-client rabbitmq-server

   .. tabbed:: MacOS X (Homebrew)

       The recommended installation method for Mac OS X is to use `Homebrew <https://brew.sh>`__.

       #. Follow `this guide <https://docs.brew.sh/Installation>`__ to install Homebrew on your system if not installed yet.

       #. Open a terminal and execute:

          .. code-block:: console

              $ brew install postgresql rabbitmq git python
              $ brew services start postgresql
              $ brew services start rabbitmq

   .. tabbed:: Windows Subsystem for Linux

      *The following instructions are for setting up AiiDA on WSL 2 in combination with Ubuntu.*

      #. The `Windows native RabbitMQ <https://www.rabbitmq.com/install-windows.html>`_ should be installed and started.

      #. Install Python and PostgreSQL:

         .. code-block:: console

             $ sudo apt-get install \
                postgresql postgresql-server-dev-all postgresql-client \
                git python3-dev python-pip
             $ sudo service postgresql start

      .. dropdown:: How to setup WSL to automatically start services after system boot.

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

      .. dropdown:: :fa:`wrench` How to resolve a timezone issue on Ubuntu 18.04.

          There is a `known issue <https://github.com/Microsoft/WSL/issues/856>`_ in WSL Ubuntu 18.04 where the timezone is not configured correctly out-of-the-box, which may cause a problem for the database.
          The following command can be used to re-configure the time zone:

          .. code-block:: console

              $ sudo dpkg-reconfigure tzdata

   .. tabbed:: Other

      #. Install RabbitMQ following the `instructions applicable to your system <https://www.rabbitmq.com/download.html>`__.
      #. Install PostgreSQL following the `instructions applicable to your system <https://www.postgresql.org/download/>`__.

      .. hint::

          Alternatively use the :ref:`pure conda installation method <intro:get_started:conda-install>`.

   ---

   **Install AiiDA (core)**

   .. tabbed:: Conda

      *Install the aiida-core package in a Conda environment.*

      #. Make sure that conda is installed, e.g., by following `the instructions on installing Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__.

      #. Open a terminal and execute:

         .. code-block:: console

             $ conda create -n aiida -c conda-forge aiida-core
             $ conda activate aiida
             (aiida) $ reentry scan

   .. tabbed:: pip + venv

      *Install the aiida-core package from PyPI into a virtual environment.*

      Open a terminal and execute:

      .. code-block:: console

          $ python -m pip venv ~/envs/aiida
          $ source ~/envs/aiida/bin/activate
          (aiida) $ pip install aiida-core
          (aiida) $ reentry scan

      .. dropdown:: :fa:`plus-circle` Installation extras

         There are additional optional packages that you may want to install, which are grouped in the following categories:

         * ``atomic_tools``: packages that allow importing and manipulating crystal structure from various formats
         * ``ssh_kerberos``: adds support for ssh transport authentication through Kerberos
         * ``REST``: allows a REST server to be ran locally to serve AiiDA data
         * ``docs``: tools to build the documentation
         * ``notebook``: jupyter notebook - to allow it to import AiiDA modules
         * ``tests``: python modules required to run the automatic unit tests
         * ``pre-commit``: pre-commit tools required for developers to enable automatic code linting and formatting

         In order to install any of these package groups, simply append them as a comma separated list in the ``pip`` install command, for example:

         .. code-block:: console

             (aiida) $ pip install aiida-core[atomic_tools,docs]

         .. dropdown:: :fa:`wrench` Kerberos on Ubuntu

            If you are installing the optional ``ssh_kerberos`` and you are on Ubuntu you might encounter an error related to the ``gss`` package.
            To fix this you need to install the ``libffi-dev`` and ``libkrb5-dev`` packages:

            .. code-block:: console

               $ sudo apt-get install libffi-dev libkrb5-dev



   .. tabbed:: From source

      *Install the aiida-core package directly from the cloned repository.*

      Open a terminal and execute:

      .. code-block:: console

          $ git clone https://github.com/aiidateam/aiida-core.git
          $ cd aiida-core/
          $ python -m pip venv ~/envs/aiida
          $ source ~/envs/aiida/bin/activate
          (aiida) $ pip install .
          (aiida) $ reentry scan

   ---

   **Start verdi daemons**

   Start the verdi daemon(s) that are used to run AiiDA workflows.

   .. code-block:: console

       (aiida) $ verdi daemon start 2

   .. important::

        The verdi daemon(s) must be restarted after a system reboot.

   .. hint::

       Do not start more daemons then there are physical processors on your system.

   ---

   **Setup profile**

   Next, set up an AiiDA configuration profile and related data storage, with the ``verdi quicksetup`` command.

   .. code-block:: console

       (aiida) $ verdi quicksetup
       Info: enter "?" for help
       Info: enter "!" to ignore the default and set no value
       Profile name: me
       Email Address (for sharing data): me@user.com
       First name: my
       Last name: name
       Institution: where-i-work

   ---

   **Check setup**

   To check that everything is set up correctly, execute:

   .. code-block:: console

       (aiida) $ verdi status
       ✓ config dir:  /home/ubuntu/.aiida
       ✓ profile:     On profile me
       ✓ repository:  /home/ubuntu/.aiida/repository/me
       ✓ postgres:    Connected as aiida_qs_ubuntu_c6a4f69d255fbe9cdb7385dcdcf3c050@localhost:5432
       ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
       ✓ daemon:      Daemon is running as PID 16430 since 2020-04-29 12:17:31

   At this point you should now have a working AiiDA environment, from which you can add and retrieve data.

   .. admonition:: Missing a checkmark or ecountered some other issue?
       :class: attention title-icon-troubleshoot

       :ref:`See the troubleshooting section <intro:troubleshooting>`.

   .. link-button:: intro:get_started:next
       :type: ref
       :text: What's next?
       :classes: btn-outline-primary btn-block font-weight-bold

.. _intro:get_started:conda-install:

Installation into Conda environment
-----------------------------------

This installation route installs all necessary software -- including the prerequisite services PostgreSQL and RabbitMQ -- into a Conda environment.
This is the recommended method for users on shared systems and systems where the user has no administrative privileges.

.. important::

   This installation method installs **all** software into a conda environment, including PostgreSQL and RabbitMQ.
   See the :ref:`system-wide installation <intro:get_started:system-wide-install>` to use Conda only to install the AiiDA (core) Python package.

.. panels::
   :container: container-lg pb-3
   :column: col-lg-12 p-2

   **Install prerequisite services + AiiDA (core)**

   .. code-block:: console

       $ conda create -n aiida -c conda-forge aiida-core aiida-core.services
       $ conda activate aiida
       (aiida) $ reentry scan

   ---

   **Start-up services and initialize data storage**

   Before working with AiiDA, you must first initialize a database storage area on disk.

   .. code-block:: console

       (aiida) $ initdb -D mylocal_db

   This *database cluster* may contain a collection of databases (one per profile) that is managed by a single running server process.
   We start this process with:

   .. code-block:: console

       (aiida) $ pg_ctl -D mylocal_db -l logfile start

   .. admonition:: Further Reading
       :class: seealso title-icon-read-more

       - `Creating a Database Cluster <https://www.postgresql.org/docs/12/creating-cluster.html>`__.
       - `Starting the Database Server <https://www.postgresql.org/docs/12/server-start.html>`__.

   Then, start the RabbitMQ server:

   .. code-block:: console

       (aiida) $ rabbitmq-server -detached

   Finally, start the AiiDA daemon(s):

   .. code-block:: console

       (aiida) $ verdi daemon start 2

   .. important::

        The verdi daemon(s) must be restarted after a system reboot.

   .. hint::

       Do not start more daemons then there are physical processors on your system.

   ---

   **Setup profile**

   Next, set up an AiiDA configuration profile and related data storage, with the ``verdi quicksetup`` command.

   .. code-block:: console

       (aiida) $ verdi quicksetup
       Info: enter "?" for help
       Info: enter "!" to ignore the default and set no value
       Profile name: me
       Email Address (for sharing data): me@user.com
       First name: my
       Last name: name
       Institution: where-i-work

   ---

   **Check setup**

   To check that everything is set up correctly, execute:

   .. code-block:: console

       (aiida) $ verdi status
       ✓ config dir:  /home/ubuntu/.aiida
       ✓ profile:     On profile me
       ✓ repository:  /home/ubuntu/.aiida/repository/me
       ✓ postgres:    Connected as aiida_qs_ubuntu_c6a4f69d255fbe9cdb7385dcdcf3c050@localhost:5432
       ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
       ✓ daemon:      Daemon is running as PID 16430 since 2020-04-29 12:17:31

   At this point you now have a working AiiDA environment, from which you can add and retrieve data.

   .. admonition:: Missing a checkmark or ecountered some other issue?
       :class: attention title-icon-troubleshoot

       :ref:`See the troubleshooting section <intro:troubleshooting>`.

   .. link-button:: intro:get_started:next
       :type: ref
       :text: What's next?
       :classes: btn-outline-primary btn-block font-weight-bold

   ---

   **Shut-down services**

   After finishing with your aiida session, particularly if switching between profiles, you may wish to power down the services:

   .. code-block:: console

       (aiida) $ verdi daemon stop
       (aiida) $ pg_ctl stop

.. _intro:get_started:docker:
.. _intro:install:docker:

Run AiiDA via a Docker image
----------------------------

The AiiDA team maintains a `Docker <https://www.docker.com/>`__ image on `Docker Hub <https://hub.docker.com/r/aiidateam/aiida-core>`__.
This image contains a fully pre-configured AiiDA environment which makes it particularly useful for learning and testing purposes.

.. panels::
   :container: container-lg pb-3
   :column: col-lg-12 p-2

   **Start container**

   First, pull the image:

   .. parsed-literal::

      $ docker pull aiidateam/aiida-core:\ |release|\

   Then start the container with:

   .. parsed-literal::

      $ docker run -d --name aiida-container aiidateam/aiida-core:\ |release|\

   You can use the following command to block until all services have started up:

   .. code-block:: console

      $ docker exec -t aiida-container wait-for-services

   ---

   **Check setup**

   The default profile is created under the ``aiida`` user, so to execute commands you must add the ``--user aiida`` option.

   For example, to check the verdi status, execute:

   .. code-block:: console

      $ docker exec -t --user aiida aiida-container /bin/bash -l -c 'verdi status'
      ✓ config dir:  /home/aiida/.aiida
      ✓ profile:     On profile default
      ✓ repository:  /home/aiida/.aiida/repository/default
      ✓ postgres:    Connected as aiida_qs_aiida_477d3dfc78a2042156110cb00ae3618f@localhost:5432
      ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
      ✓ daemon:      Daemon is running as PID 1795 since 2020-05-20 02:54:00

   .. link-button:: intro:get_started:next
       :type: ref
       :text: What's next?
       :classes: btn-outline-primary btn-block font-weight-bold

.. caution::

    All data stored in the container will persist as long as you restart the same container, e.g., with (``docker start aiida-container``), however if you remove the container, all data will be lost.
    Use `volumes <https://docs.docker.com/storage/volumes/>`__ to share data between containers and ensure its persistency on the host machine.


.. _intro:get_started:next:

What's next?
============

If you are new to AiiDA, we recommed you go through the :ref:`Basic Tutorial <tutorial:basic>`,
or see our :ref:`Next steps guide <tutorial:next-steps>`.

If however, you encountered some issues, proceed to the :ref:`troubleshooting section <intro:troubleshooting>`.

.. admonition:: In-depth instructions
    :class: seealso title-icon-read-more

    For more detailed instructions on configuring AiiDA, :ref:`see the configuration how-to <how-to:installation:configure>`.

.. |PostgreSQL| replace:: `PostgreSQL <https://www.postgresql.org>`__
.. |RabbitMQ| replace:: `RabbitMQ <https://www.rabbitmq.com>`__
.. |Homebrew| replace:: `Homebrew <https://brew.sh>`__
