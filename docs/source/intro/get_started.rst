****************
Getting Started
****************

Installation
============

There are numerous routes to setting up the full AiiDA environment,
depending on your use case.
Here we first provide the simplest approach for installation on your local computer.

`Conda <https://docs.conda.io>`_  provides a cross-platform package management system,
from which we can install the basic components of the AiiDA infrastructure in an
isolated environment:

.. code-block:: console

    $ conda create -n aiida -c conda-forge aiida-core aiida-core.services
    $ conda activate aiida
    $ reentry scan

.. note::

    You can also install ``aiida-core`` from `PyPi <https://pypi.org/project/aiida-core>`_

This installs the three core components of AiiDA:

* ``aiida-core``: The main python package and associated CLI ``verdi``.
* `PostgreSQL <https://www.postgresql.org>`_: A service which manages the database where we store generated data.
* `RabbitMQ <https://www.rabbitmq.com>`_: A service which manages communication with the processes that we run. 

To initialise a database cluster with PostgreSQL and start the service:

.. code-block:: console

    $ initdb -D mylocal_db
    $ pg_ctl -D mylocal_db -l logfile start

We can then use the `quicksetup` command, to set up an AiiDA configuration profile and related data storage.

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

.. tip::

    Enable tab completion of ``verdi`` commands in the terminal with:

    .. code-block:: console
    
        $ eval "$(_VERDI_COMPLETE=source verdi)"

In order to run computations, one additional step is required to start the services
which manage these background processes:

.. code-block:: console

    $ rabbitmq-server -detached
    $ verdi daemon start

We can check that all services are running as expected using:

.. code-block:: console

    $ verdi status
    ✓ config dir:  /home/ubuntu/.aiida
    ✓ profile:     On profile me
    ✓ repository:  /home/ubuntu/.aiida/repository/me
    ✓ postgres:    Connected as aiida_qs_ubuntu_c6a4f69d255fbe9cdb7385dcdcf3c050@localhost:5432
    ✓ rabbitmq:    Connected to amqp://127.0.0.1?heartbeat=600
    ✓ daemon:      Daemon is running as PID 16430 since 2020-04-29 12:17:31

You now have a fully operational installation from which to take the next steps!

Finally, to power down the services, you can run:

.. code-block:: console

    $ verdi daemon stop
    $ pg_ctl stop

.. admonition:: Having problems?

    See the :ref:`troubleshooting section <troubleshooting>`.

.. admonition:: In-depth instructions

    Installing from source? Install into a VM?
    Check the :ref:`advanced installation section <install_advanced>`.

Next Steps
==========


.. toggle:: Run pure Python lightweight computations

    blah blah blah

    links to tutorials

.. toggle:: Run compute-intensive codes

    blah blah blah

    links to tutorials

.. toggle:: Run computations on High Performance Computers

    blah blah blah

    links to tutorials
    
