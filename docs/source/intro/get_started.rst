.. _intro:get_started:

****************
Getting Started
****************

A working AiiDA installation consists of three core components, plus any external codes you wish to run:

* aiida-core: The main Python package and the associated command line tool: ``verdi``.
* |PostgreSQL|: A service which manages the database that AiiDA uses to store generated data.
* |RabbitMQ|: A service which manages communication with the processes that AiiDA spawns.

There are multiple routes to setting up a working AiiDA environment.
These are shown below, followed by a recommended "quick-install" route on your local computer.

.. panels::
   :body: bg-light
   :footer: bg-light border-0

   :fa:`desktop,mr-1` **Direct (Bare Metal)**

   *Install software directly into your local root directory.*

   The prerequisite software can be installed using most package managers, including: apt, Homebrew, MacPorts, Gentoo and Windows Subsystem for Linux.

   +++

   :link-badge:`intro:install:prerequisites,Prerequisites install,ref,badge-primary text-white`
   :link-badge:`intro:install:aiida-core,aiida-core install,ref,badge-primary text-white`

   ---------------

   :fa:`folder,mr-1` **Virtual Environment**

   *Install software into an isolated directory on your machine.*

   Environment managers such as `Conda <https://docs.conda.io>`__, `pipenv <https://pipenv.pypa.io>`__  and `venv <https://docs.python.org/3/library/venv.html>`__ create isolated environments, allowing for installation of multiple versions of software on the same machine.
   It is advised that you install ``aiida-core`` into one of these managed environments.

   +++

   :link-badge:`intro:install:virtual_environments,Environments Tutorial,ref,badge-primary text-white`
   :link-badge:`https://anaconda.org/conda-forge/aiida-core,aiida-core on Conda,url,badge-primary text-white`

   ---------------

   :fa:`cube,mr-1` **Containers**

   *Use a pre-made image of all the required software.*

   AiiDA maintains a `Docker <https://www.docker.com/>`__ image, which is particularly useful for learning and testing purposes.
   It is a great way to quickly get started on the tutorials.

   +++

   :link-badge:`intro:install:docker,Docker Tutorial,ref,badge-primary text-white`
   :link-badge:`https://hub.docker.com/r/aiidateam/aiida-core,aiida-core on DockerHub,url,badge-primary text-white`

   ---------------

   :fa:`cloud,mr-1` **Virtual Machines**

   *Use a pre-made machine with all the required software.*

   `Materials Cloud <https://www.materialscloud.org>`__ provides both downloadable and web based VMs,
   also incorporating pre-installed Materials Science codes.

   +++

   :link-badge:`https://materialscloud.org/quantum-mobile,Quantum Mobile,url,badge-primary text-white`
   :link-badge:`https://aiidalab.materialscloud.org,AiiDA lab,url,badge-primary text-white`

.. _intro:quick_start:

Quick Start
===========

Here we first provide a simple approach for installation and setup on your local computer.

Install Software
----------------

.. panels::
    :column: col-lg-6 col-md-6 col-sm-12 col-xs-12 p-2

    :fa:`download,mr-1` **Install from Conda**

    .. code-block:: console

        $ conda create -n aiida -c conda-forge aiida-core aiida-core.services
        $ conda activate aiida
        $ reentry scan

    `Conda <https://docs.conda.io>`__ provides a cross-platform package management system, from which we can install all the basic components of the AiiDA infrastructure in an isolated environment:

    ----------------------------------------------

    :fa:`download,mr-1` **Install with pip**

    .. code-block:: console

        $ pip install aiida-core
        $ reentry scan

    ``aiida-core`` can be installed from `PyPi <https://pypi.org/project/aiida-core>`__.
    You will then need to install |PostgreSQL| and |RabbitMQ| depending on your operating system.

    :link-badge:`intro:install:prerequisites,Install prerequisites,ref,badge-primary text-white`

Initialise Data Storage
------------------------

Before working with AiiDA, you must first initialize a database storage area on disk.

.. code-block:: console

    $ initdb -D mylocal_db


This *database cluster* may contain a collection of databases (one per profile) that is managed by a single running server process.
We start this process with:

.. code-block:: console

    $ pg_ctl -D mylocal_db -l logfile start

.. admonition:: Further Reading
    :class: seealso title-icon-read-more

    - `Creating a Database Cluster <https://www.postgresql.org/docs/12/creating-cluster.html>`__.
    - `Starting the Database Server <https://www.postgresql.org/docs/12/server-start.html>`__.

Next, we set up an AiiDA configuration profile and related data storage, with the `quicksetup` command.

.. code-block:: console

    $ verdi quicksetup
    Info: enter "?" for help
    Info: enter "!" to ignore the default and set no value
    Profile name: me
    Email Address (for sharing data): me@user.com
    First name: my
    Last name: name
    Institution: where-i-work

At this point you now have a working AiiDA environment, from which you can add and retrieve data.

.. admonition:: Tab Completion
    :class: tip title-icon-lightbulb

    Enable tab completion of ``verdi`` commands in the terminal with:

    .. code-block:: console

        $ eval "$(_VERDI_COMPLETE=source verdi)"

    :link-badge:`how-to:installation:configure:tab-completion,Read More,ref,badge-primary text-white`

Start Computation Services
--------------------------

In order to run computations, some additional steps are required to start the services that manage these background processes.
The |RabbitMQ| service is used, to manage communication between processes and retain process states, even after restarting your computer:

.. code-block:: console

    $ rabbitmq-server -detached

We then start one or more "daemon" processes, which handle the execution and monitoring of all submitted computations.

.. code-block:: console

    $ verdi daemon start 2

Finally, to check that all services are running as expected use:

.. code-block:: console

    $ verdi status
    ✓ config dir:  /home/ubuntu/.aiida
    ✓ profile:     On profile me
    ✓ repository:  /home/ubuntu/.aiida/repository/me
    ✓ postgres:    Connected as aiida_qs_ubuntu_c6a4f69d255fbe9cdb7385dcdcf3c050@localhost:5432
    ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
    ✓ daemon:      Daemon is running as PID 16430 since 2020-04-29 12:17:31

Awesome! You now have a fully operational installation from which to take the next steps!

Stopping Services
-----------------

After finishing with your aiida session, particularly if switching between profiles, you may wish to power down the services:

.. code-block:: console

    $ verdi daemon stop
    $ pg_ctl stop

Any computations that are still running at this point, will be picked up next time the services are started.


.. admonition:: Having problems?
    :class: attention title-icon-troubleshoot

    :ref:`See the troubleshooting section <intro:troubleshooting>`.

.. admonition:: In-depth instructions
    :class: seealso title-icon-read-more

    For more ways to install AiiDA, :ref:`check the detailed installation section <intro:install>`.

    For more detailed instructions on configuring AiiDA, :ref:`see the configuration how-to <how-to:installation:configure>`.

Next Steps
==========

If you are new to AiiDA, go through the :ref:`Basic Tutorial <tutorial:basic>`.
We also compiled some useful how-to guides that are especially relevant for the following use cases:

.. div:: dropdown-group

    .. dropdown:: Run pure Python lightweight computations
        :container:

        - **Designing a workflow**: After reading the :ref:`Basic Tutorial <tutorial:basic>`, you may want to learn about how to encode the logic of a typical scientific workflow in the :ref:`multi-step workflows how-to <how-to:workflows>`.
        - **Reusable data types**: If you have a certain input or output data type, which you use often, then you may wish to turn it into its own :ref:`data plugin <how-to:data:plugin>`.
        - **Exploring your data** Once you have run multiple computations, the :ref:`find and query data how-to <how-to:data:find>` can show you how to efficiently explore your data. The data lineage can also be visualised as a :ref:`provenance graph <VisualizingGraphs>`.
        - **Sharing your data**: You can export all or part of your data to file with the :ref:`export/import functionality<how-to:data:share>` or you can even serve your data over HTTP(S) using the :ref:`AiiDA REST API <how-to:data:serve>`.
        - **Sharing your workflows**: Once you have a working computation workflow, you may also wish to :ref:`package it into a python module <how-to:plugins>` for others to use.

    .. dropdown:: Run compute-intensive codes
        :container:

        :ref:`Using caching to save computational resources <how-to:codes:caching >`

        :ref:`Tuning performance <how-to:installation:performance>`

    .. dropdown:: Run computations on High Performance Computers

        :ref:`How to run external codes <how-to:codes>`

        :ref:`Tuning performance <how-to:installation:performance>`

        :ref:`Running on supercomputers <how-to:installation:running-on-supercomputers>`


.. |PostgreSQL| replace:: `PostgreSQL <https://www.postgresql.org>`__
.. |RabbitMQ| replace:: `RabbitMQ <https://www.rabbitmq.com>`__
