.. _intro:get_started:conda-install:

***********************************
Installation into Conda environment
***********************************

This installation route installs all necessary software -- including the prerequisite services PostgreSQL and RabbitMQ -- into a Conda environment.
This is the recommended method for users on shared systems and systems where the user has no administrative privileges.
If you want to install AiiDA onto you own personal workstation/laptop, it is recommanded to use the :ref:`system-wide installation <intro:get_started:system-wide-install>`.

.. important::

   This installation method installs **all** software into a conda environment, including PostgreSQL and RabbitMQ.
   See the :ref:`system-wide installation <intro:get_started:system-wide-install>` to use Conda only to install the AiiDA (core) Python package.

.. grid:: 1
    :gutter: 3

    .. grid-item-card:: Install prerequisite services + AiiDA (core)

        *Install the aiida-core package and all required services in a Conda environment.*

        #. We strongly recommend using ``mamba`` instead of the default ``conda`` (or environment resolution may time out).
           Consider using `Mambaforge <https://github.com/conda-forge/miniforge#mambaforge>`_ when starting from scratch, or ``conda install -c conda-forge mamba``.

        #. Open a terminal and execute:

        .. code-block:: console

            $ mamba create -n aiida -c conda-forge aiida-core aiida-core.services
            $ mamba activate aiida

    .. grid-item-card:: Start-up services and initialize data storage

        Before working with AiiDA, you must first initialize a database storage area on disk.

        .. code-block:: console

            (aiida) $ initdb -D mylocal_db

        This *database cluster* (located inside a folder named ``mylocal_db``) may contain a collection of databases (one per profile) that is managed by a single running server process.
        We start this process with:

        .. code-block:: console

            (aiida) $ pg_ctl -D mylocal_db -l logfile start

        .. tip::

            You may encounter issue that ``5432`` port is already in use. In this case, you can pass the ``-o "-F -p <port-num>"`` option to the ``pg_ctl`` command, ``<port-num>`` being the desired port number.
            Then for the ``psql`` command, you can pass the ``-p <port-num>`` option.

        .. admonition:: Further Reading
            :class: seealso title-icon-read-more

            - `Creating a Database Cluster <https://www.postgresql.org/docs/12/creating-cluster.html>`__.
            - `Starting the Database Server <https://www.postgresql.org/docs/12/server-start.html>`__.



        Then, start the RabbitMQ server:

        .. code-block:: console

            (aiida) $ rabbitmq-server -detached

        .. important::

                The services started this way will use the default ports on the machine.
                Conflicts may happen if there are more than one user running AiiDA this way on the same machine, or you already have the server running in a system-wide installation.
                To get around this issue, you can explicitly define the ports to be used.

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

        .. tip::

                In case of non-default ports are used for the *database cluster* and the RabbitMQ server, you can pass them using ``--db-port`` and ``--broker-port`` options respectively.


        .. admonition:: Is AiiDA unable to auto-detect the PostgreSQL setup?
            :class: attention title-icon-troubleshoot

            If you get an error saying that AiiDA has trouble autodetecting the PostgreSQL setup, you will need to do the manual setup explained in the :ref:`troubleshooting section<intro:troubleshooting:installation:postgresql-autodetect-issues>`.

        Once the profile is up and running, you can start the AiiDA daemon(s):

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

        .. admonition:: Missing a checkmark or ecountered some other issue?
            :class: attention title-icon-troubleshoot

            :ref:`See the troubleshooting section <intro:troubleshooting>`.

        .. button-ref:: intro:get_started:next
            :ref-type: ref
            :expand:
            :color: primary
            :outline:
            :class: sd-font-weight-bold

            What's next?

    .. grid-item-card:: Shut-down services

        After finishing with your aiida session, particularly if switching between profiles, you may wish to power down the daemon and the services:

        .. code-block:: console

            (aiida) $ verdi daemon stop
            (aiida) $ pg_ctl -D mylocal_db stop
            (aiida) $ rabbitmqctl stop

    .. grid-item-card:: Restart the services

        If you want to restart the services and the daemon:

        .. code-block:: console

            (aiida) $ pg_ctl -D mylocal_db start
            (aiida) $ rabbitmq-server -detached
            (aiida) $ verdi daemon start

        .. tip::

            If different ports are used, you have to pass them here as well.
