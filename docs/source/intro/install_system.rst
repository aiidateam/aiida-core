.. _intro:get_started:system-wide-install:

************************
System-wide installation
************************

The system-wide installation will install the prerequisite services (PostgreSQL and RabbitMQ) via standard package managers such that their startup and shut-down is largely managed by the operating system.
The AiiDA (core) Python package is then installed either with Conda or pip.

.. warning:: RabbitMQ v3.5 and below are EOL and not supported at all. For versions RabbitMQ v3.8.15 and up, AiiDA is not compatible with default server configurations. For details refer to the :ref:`dedicated troubleshooting section<intro:troubleshooting:installation:rabbitmq>`.

This is the *recommended* installation method to setup AiiDA on a personal laptop or workstation for the majority of users.

.. grid:: 1
   :gutter: 3

   .. grid-item-card:: Install prerequisite services

      AiiDA is designed to run on `Unix <https://en.wikipedia.org/wiki/Unix>`_ operating systems and requires a `bash <https://en.wikipedia.org/wiki/Bash_(Unix_shell)>`_ or `zsh <https://en.wikipedia.org/wiki/Z_shell>`_ shell, and Python >= 3.7.

      .. tab-set::

         .. tab-item:: Ubuntu

            *AiiDA is tested on Ubuntu versions 16.04, 18.04, and 20.04.*

            Open a terminal and execute:

            .. code-block:: console

               $ sudo apt install git python3-dev python3-pip postgresql postgresql-server-dev-all postgresql-client rabbitmq-server

         .. tab-item:: MacOS X (Homebrew)

            The recommended installation method for Mac OS X is to use `Homebrew <https://brew.sh>`__.

            #. Follow `this guide <https://docs.brew.sh/Installation>`__ to install Homebrew on your system if not installed yet.

            #. Open a terminal and execute:

               .. code-block:: console

                  $ brew install postgresql rabbitmq git python
                  $ brew services start postgresql
                  $ brew services start rabbitmq

         .. tab-item:: Windows Subsystem for Linux

            *The following instructions are for setting up AiiDA on WSL 1/2 in combination with Ubuntu.*

            #. Installing RabbitMQ:

               * (WSL 1) Install and start the `Windows native RabbitMQ <https://www.rabbitmq.com/install-windows.html>`_.

               * (WSL 2) Install RabbitMQ inside the the WSL:

                  .. code-block:: console

                     $ sudo apt install rabbitmq-server

                  then start the ``rabbitmq`` server:

                  .. code-block:: console

                     $ sudo service rabbitmq-server start

            #. Install Python and PostgreSQL:

               .. code-block:: console

                  $ sudo apt install postgresql postgresql-server-dev-all postgresql-client git python3-dev python-pip

               then start the PostgreSQL server:

               .. code-block:: console

                  $ sudo service postgresql start

            .. dropdown:: How to setup WSL to automatically start services after system boot.

               Create a file ``start_aiida_services.sh`` containing the following lines:

               .. code-block:: console

                  $ service postgresql start
                  $ service rabbitmq-server start # Only for WSL 2!

               and store it in your preferred location, e.g., the home directory.
               Then make the file executable, and editable only by root users with:

               .. code-block:: console

                  $ chmod a+x,go-w /path/to/start_aiida_services.sh
                  $ sudo chown root:root /path/to/start_aiida_services.sh

               Next, run

               .. code-block:: console

                  $ sudo visudo

               and add the line

               .. code-block:: sh

                  <username> ALL=(root) NOPASSWD: /path/to/start_aiida_services.sh

               replacing ``<username>`` with your Ubuntu username.
               This will allow you to run *only* this specific ``.sh`` file with ``root`` access (without password), without lowering security on the rest of your system.

               Now you can use the Windows Task Scheduler to automatically execute this file on startup:

               #. Open Task Scheduler.

               #. In the "Actions" menu, click "Create Task".

               #. In "General/Security options", select "Run whether user is logged on or not".

               #. In the "Triggers" tab, click "New...".

                  #. In the "Begin the task:" dropdown, select "At startup".

                  #. Click "OK" to confirm.

               #. In the "Actions" tab, click "New...".

                  #. In the "Action" dropdown, select "Start a program".

                  #. In the "Program/script" text field, add ``C:\Windows\System32\bash.exe``.

                  #. In the "Add arguments (optional)" text field, add ``-c "sudo /path/to/start_aiida_services.sh"``.

                  #. Click "OK" to confirm.

               #. Click "OK" to confirm the task.

               You can tweak other details of this task to fit your needs.

         .. tab-item:: Other

            #. Install RabbitMQ following the `instructions applicable to your system <https://www.rabbitmq.com/download.html>`__.
            #. Install PostgreSQL following the `instructions applicable to your system <https://www.postgresql.org/download/>`__.

            .. tip::

               Alternatively use the :ref:`pure conda installation method <intro:get_started:conda-install>`.

   .. grid-item-card:: Install AiiDA (core)

      .. tab-set::

         .. tab-item:: pip + venv

            *Install the aiida-core package from PyPI into a virtual environment.*

            Open a terminal and execute:

            .. code-block:: console

               $ python -m venv ~/envs/aiida
               $ source ~/envs/aiida/bin/activate
               (aiida) $ pip install aiida-core

            .. important::

               Make sure the ``python`` executable is for a Python version that is supported by AiiDA.
               You can see the version using:

               .. code-block:: console

                  $ python --version

               You can find the supported Python versions for the latest version of AiiDA `on the PyPI page <https://pypi.org/project/aiida-core/>`__.

            .. tip::

               See the `venv documentation <https://docs.python.org/3/library/venv.html>`__ if the activation command fails.
               The exact command for activating a virtual environment differs slightly based on the used shell.

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

         .. tab-item:: Conda

            *Install the aiida-core package in a Conda environment.*

            #. Make sure that conda is installed, e.g., by following `the instructions on installing Miniconda <https://docs.conda.io/en/latest/miniconda.html>`__.

            #. Open a terminal and execute:

               .. code-block:: console

                  $ conda create -yn aiida -c conda-forge aiida-core
                  $ conda activate aiida

         .. tab-item:: From source

            *Install the aiida-core package directly from the cloned repository.*

            Open a terminal and execute:

            .. code-block:: console

               $ git clone https://github.com/aiidateam/aiida-core.git
               $ cd aiida-core/
               $ python -m venv ~/envs/aiida
               $ source ~/envs/aiida/bin/activate
               (aiida) $ pip install .

   .. grid-item-card:: Setup profile

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

      .. admonition:: Is AiiDA unable to auto-detect the PostgreSQL setup?
         :class: attention title-icon-troubleshoot

         If you get an error saying that AiiDA has trouble autodetecting the PostgreSQL setup, you will need to do the manual setup explained in the :ref:`troubleshooting section<intro:troubleshooting:installation:postgresql-autodetect-issues>`.

   .. grid-item-card:: Start verdi daemons

      Start the verdi daemon(s) that are used to run AiiDA workflows.

      .. code-block:: console

         (aiida) $ verdi daemon start 2

      .. important::

         The verdi daemon(s) must be restarted after a system reboot.

      .. tip::

         Do not start more daemons then there are physical processors on your system.

   .. grid-item-card:: Check setup

      To check that everything is set up correctly, execute:

      .. code-block:: console

         (aiida) $ verdi status
         ✓ version:     AiiDA v2.0.0
         ✓ config:      /path/to/.aiida
         ✓ profile:     default
         ✓ storage:     Storage for 'default' @ postgresql://username:***@localhost:5432/db_name / file:///path/to/repository
         ✓ rabbitmq:    Connected as amqp://127.0.0.1?heartbeat=600
         ✓ daemon:      Daemon is running as PID 2809 since 2019-03-15 16:27:52

      At this point you should now have a working AiiDA environment, from which you can add and retrieve data.

      .. admonition:: Missing a checkmark or encountered some other issue?
         :class: attention title-icon-troubleshoot

         :ref:`See the troubleshooting section <intro:troubleshooting>`.

      .. button-ref:: intro:get_started:next
         :ref-type: ref
         :expand:
         :color: primary
         :outline:
         :class: sd-font-weight-bold

         What's next?
