.. _how-to:tune-performance:

*******************************
How to Tune AiiDA performance
*******************************

AiiDA supports running hundreds of thousands of calculations and graphs with millions of nodes.
However, optimal performance at that scale can require tweaking the AiiDA configuration to balance the CPU and disk load.

Below, we share a few practical tips for assessing and tuning AiiDA performance.
Further in-depth information is available in the dedicated :ref:`topic on performance<topics:performance>`.

.. dropdown:: Benchmark workflow engine performance

    Download the :download:`benchmark script <include/scripts/performance_benchmark_base.py>` :fa:`download`, and run it in your AiiDA environment.

    .. code:: console

        sph@citadel:~/$ python performance_benchmark_base.py -n 100
            Success: Created and configured temporary `Computer` benchmark-e73b8647 for localhost.
            Success: Created temporary `Code` bash for localhost.
            Running 100 calculations.  [####################################]  100%
            Success: All calculations finished successfully.
            Elapsed time: 24.90 seconds.
            Cleaning up...
            12/19/2022 10:57:43 AM <12625> aiida.delete: [REPORT] 400 Node(s) marked for deletion
            12/19/2022 10:57:43 AM <12625> aiida.delete: [REPORT] Starting node deletion...
            12/19/2022 10:57:43 AM <12625> aiida.delete: [REPORT] Deletion of nodes completed.
            Success: Deleted all calculations.
            Success: Deleted the created code bash@benchmark-e73b8647.
            Success: Deleted the created computer benchmark-e73b8647.
            Performance: 0.25 s / process

    The output above was generated on an AMD Ryzen 5 3600 6-Core processor (3.6 GHz, 4.2 GHz turbo boost) using AiiDA v2.2.0, and RabbitMQ and PostgreSQL running on the same machine.
    Here, 100 ``ArithmeticAddCalculation`` processes completed in ~25s, corresponding to 0.25 seconds per process.

    If you observe a significantly higher runtime, you may want to check whether any relevant component (CPU, disk, postgresql, rabbitmq) is congested.

.. dropdown:: Increase the number of daemon workers

    By default, the AiiDA daemon only uses a single worker, i.e. a single operating system process.
    If ``verdi daemon status`` shows the daemon worker constantly at high CPU usage, you can use ``verdi daemon incr X`` to add ``X`` parallel daemon workers.

    Keep in mind that other processes need to run on your computer (e.g. rabbitmq, the PostgreSQL database, ...), i.e. it's a good idea to stop increasing the number of workers before you reach the number of cores of your CPU.

    To make the change permanent, set
    ::

        verdi config set daemon.default_workers 4

.. dropdown:: Increase the number of daemon worker slots

    Each daemon worker accepts only a limited number of tasks at a time.
    If ``verdi daemon status`` constantly warns about a high percentage of the available daemon worker slots being used, you can increase the number of tasks handled by each daemon worker (thus increasing the workload per worker).
    Increasing it to 1000 should typically work.

    Set the corresponding config variable and restart the daemon
    ::

        verdi config set daemon.worker_process_slots 1000

.. dropdown:: Tune SSH connection interval (safe_interval)

    By default, AiiDA enforces a **15s delay** between consecutive SSH connections to the same remote machine to prevent overload.
    This delay is configurable via the CLI and can be adjusted interactively for each Computer.

    If you are running many short tasks on a remote HPC and notice performance bottlenecks,
    you can tune this value via the Computer configuration.

    To view or change the safe interval of an existing Computer:

    .. code:: console

        verdi computer configure core.ssh <COMPUTER_LABEL>

    During the interactive prompt, locate the **SSH safe interval** (sometimes shown as
    *Connection cooldown time*) and enter a new value (in seconds) that matches your workload and
    remote system. Increasing it reduces load on remote servers, while decreasing it allows faster
    connection cycles when safe.

    You can inspect the effective safe interval at any time via:

    .. code:: console

        verdi computer configure show <COMPUTER_LABEL>

    .. note::

        Setting an interval that is too low — especially when many daemon workers are active — can
        overload the remote system and potentially violate usage policies of some HPC centers.

.. dropdown:: Prevent your operating system from indexing the file repository.

    Many Linux distributions include the ``locate`` command to quickly find files and folders, and run a daily cron job ``updatedb.mlocate`` to create the corresponding index.
    A large file repository can take a long time to index, up to the point where the hard drive is constantly indexing.

    In order to exclude the repository folder from indexing, add its path to the ``PRUNEPATH`` variable in the ``/etc/updatedb.conf`` configuration file (use ``sudo``).

.. dropdown:: Move the Postgresql database to a fast disk (SSD), ideally on a large partition.

    1. Stop the AiiDA daemon and :ref:`back up your database <how-to:installation:backup>`.

    2. Find the data directory of your postgres installation (something like ``/var/lib/postgresql/9.6/main``, ``/scratch/postgres/9.6/main``, ...).

        The best way is to become the postgres UNIX user and enter the postgres shell::

            psql
            SHOW data_directory;
            \q

        If you are unable to enter the postgres shell, try looking for the ``data_directory`` variable in a file ``/etc/postgresql/9.6/main/postgresql.conf`` or similar.

    3. Stop the postgres database service::

        service postgresql stop

    4. Copy all files and folders from the postgres ``data_directory`` to the new location::

        cp -a SOURCE_DIRECTORY DESTINATION_DIRECTORY

        .. note:: Flag ``-a`` will create a directory within ``DESTINATION_DIRECTORY``, e.g.::

        cp -a OLD_DIR/main/ NEW_DIR/

        creates ``NEW_DIR/main``.
        It will also keep the file permissions (necessary).

        The file permissions of the new and old directory need to be identical (including subdirectories).
        In particular, the owner and group should be both ``postgres`` (except for symbolic links in ``server.crt`` and ``server.key`` that may or may not be present).

        .. note::

            If the permissions of these links need to be changed, use the ``-h`` option of ``chown`` to avoid changing the permissions of the destination of the links.
            In case you have changed the permission of the links destination by mistake, they should typically be (beware that this might depend on your actual distribution!)::

            -rw-r--r-- 1 root root 989 Mar  1  2012 /etc/ssl/certs/ssl-cert-snakeoil.pem
            -rw-r----- 1 root ssl-cert 1704 Mar  1  2012 /etc/ssl/private/ssl-cert-snakeoil.key

    5. Point the ``data_directory`` variable in your postgres configuration file (e.g. ``/etc/postgresql/9.6/main/postgresql.conf``) to the new directory.

    6. Restart the database daemon::

        service postgresql start

    Finally, check that the data directory has indeed changed::

        psql
        SHOW data_directory;
        \q

    and try a simple AiiDA query with the new database.
    If everything went fine, you can delete the old database location.

If you're still encountering performance issues, the following tips can help with pinpointing performance bottlenecks.

.. dropdown:: Analyze the RabbitMQ message rate

    If you're observing slow performance of the AiiDA engine, the `RabbitMQ management plugin <https://www.rabbitmq.com/management.html>`_ provides an intuitive dashboard that lets you monitor the message rate and check on what the AiiDA engine is up to.

    Enable the management plugin via something like::

        sudo rabbitmq-plugins enable rabbitmq_management

    Then, navigate to http://localhost:15672/ and log in with ``guest``/``guest``.
