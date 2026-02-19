.. _how-to:tune-performance:

***************************************
How to tune high-throughput performance
***************************************

AiiDA supports running hundreds of thousands of calculations and graphs with millions of nodes.
However, optimal performance at that scale can require tweaking the AiiDA configuration to balance the CPU and disk load.

Further in-depth information is available in the dedicated :ref:`topic on performance<topics:performance>`.

TL;DR
=====

Quick settings to consider for high-throughput workloads:

- Start the daemon with multiple workers: ``verdi daemon start X`` (e.g., ``X=4``)
- Reduce the SSH connection cooldown time for remote Computers (default 15s)
- Enable caching: ``verdi config set caching.default_enabled True``
- Increase worker slots: ``verdi config set daemon.worker_process_slots X`` (e.g., ``X=1000``)

To see all available configuration options and their current values, run ``verdi config list``.

Daemon configuration
====================

**Increase the number of daemon workers** --
By default, the AiiDA daemon only uses a single worker, i.e. a single operating system process.
If ``verdi daemon status`` shows the daemon worker constantly at high CPU usage, use ``verdi daemon start X`` to run with ``X`` workers, or ``verdi daemon incr X`` to add ``X`` workers to a running daemon.
Keep in mind that other processes need to run on your computer, so it's a good idea to stop increasing the number of workers before you reach the number of cores of your CPU.
To set the default value for your profile:

.. code:: console

    $ verdi config set daemon.default_workers X

**Increase the number of daemon worker slots** --
Each daemon worker accepts only a limited number of concurrent process tasks (event loop tasks) at a time.
If ``verdi daemon status`` constantly warns about a high percentage of the available daemon worker slots being used, increase the number of tasks handled by each daemon worker and restart the daemon:

.. code:: console

    $ verdi config set daemon.worker_process_slots X

Remote connections
==================

**Tune SSH connection interval** --
By default, AiiDA enforces a 15-second delay between consecutive SSH connections to the same remote machine.
This cooldown prevents overloading remote systems with too many connection requests, which could get you blocked by HPC center firewalls or violate their usage policies.

If you are running many short tasks and notice performance bottlenecks, you can adjust this value via the interactive configuration:

.. code:: console

    $ verdi computer configure core.ssh <COMPUTER_LABEL>
    ...
    Connection cooldown time (s) [15.0]: <lower-value>

Or non-interactively with ``--safe-interval``:

.. code:: console

    $ verdi computer configure core.ssh --safe-interval <lower-value> <COMPUTER_LABEL>

Inspect the current value with:

.. code:: console

    $ verdi computer configure show <COMPUTER_LABEL>

.. warning::

    Setting the interval too low -- especially with many daemon workers active -- can trigger
    rate limiting or IP bans from HPC centers. Check your center's policies before reducing this value.

**Consider using aiida-hyperqueue for many short calculations** --
When running many small calculations on HPC systems, you may hit limits on the number of active jobs allowed, or face long total queueing times.
The `aiida-hyperqueue <https://aiida-hyperqueue.readthedocs.io/>`_ plugin allows you to submit many AiiDA calculations to the `HyperQueue <https://github.com/It4innovations/hyperqueue>`_ metascheduler, which runs them within a single job allocation.

Caching
=======

AiiDA can skip redundant calculations entirely by reusing cached results from identical previous runs.
This can dramatically improve throughput when running similar calculations.
Enable it globally:

.. code:: console

    $ verdi config set caching.default_enabled True

See :ref:`how-to:run-codes:caching` for details on how caching works and how to configure it per calculation type.

System and storage
==================

**Move the PostgreSQL database to an SSD** --
If AiiDA's database is on a slow disk, moving it to an SSD can significantly improve query performance.
Consult the `PostgreSQL documentation <https://www.postgresql.org/docs/current/manage-ag-tablespaces.html>`_ for instructions on relocating the data directory.
Remember to :ref:`back up your database <how-to:installation:backup>` before making changes.

Diagnosing bottlenecks
======================

**Analyze the RabbitMQ message rate** --
The `RabbitMQ management plugin <https://www.rabbitmq.com/management.html>`_ provides a dashboard to monitor the message rate.
Enable it with:

.. code:: console

    $ sudo rabbitmq-plugins enable rabbitmq_management

Then navigate to http://localhost:15672/ (login: ``guest``/``guest``).

**Benchmark workflow engine performance** --
Download the :download:`benchmark script <include/scripts/performance_benchmark_base.py>` :fa:`download` and run it in your AiiDA environment:

.. code:: console

    $ python performance_benchmark_base.py -n 100
    ...
    Elapsed time: 24.90 seconds.
    Performance: 0.25 s / process

This runs 100 ``ArithmeticAddCalculation`` processes and reports the time per process.
The example above was obtained on an AMD Ryzen 5 3600 (3.6 GHz) with AiiDA v2.2.0.
If you observe significantly higher runtimes, check whether any relevant component (CPU, disk, PostgreSQL, RabbitMQ) is congested.
Results may vary depending on your hardware and AiiDA version.
