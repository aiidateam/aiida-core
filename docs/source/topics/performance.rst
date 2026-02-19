.. _topics:performance:

***********
Performance
***********

The performance of AiiDA depends on many factors:

* the hardware that AiiDA is running on
* how the services for AiiDA are configured (the database, message broker, filesystem, etc.)
* the codes and their plugins that are being run.

This section gives an overview of how each of these factors influence the overall performance of AiiDA and how it can be optimized.


.. _topics:performance:hardware:

Hardware
========

The bulk of AiiDA's workload is typically carried by the daemon and its workers.
The performance is typically limited by the computing power of the machine on which AiiDA is running.

Each worker is a separate Python process that takes care of executing the AiiDA processes that are submitted.
AiiDA was designed to allow to increase the throughput by adding more daemon workers that can work independently in parallel.
A rule of thumb is to not have more workers than the number of cores of the machine's CPU on which AiiDA is running.
If more workers are added, they will have to start sharing and swapping resources and the performance scaling will degrade.


.. _topics:performance:services:

Services
========

For the default setup, AiiDA essentially has three services that influence its performance:

* PostgreSQL (the database in which the provenance graph is stored)
* RabbitMQ (the message broker that the daemon workers use to communicate)
* Filesystem (files are stored by AiiDA in the file repository on a filesytem)

For the simplest installations, the PostgreSQL and RabbitMQ services are typically running on the same machine as AiiDA itself.
Although this means that a part of the machine's resources is not available for AiiDA itself and its daemon, the latency for AiiDA to communicate with the services is minimal.

It is possible to configure an AiiDA profile to use services that are running on a different machine and can be reached over a network.
However, this will typically affect the performance negatively as now each time a connection needs to be made to a service, the latency of the network is incurred.


.. _topics:performance:benchmarks:

Benchmarks
==========

The :download:`benchmark script <../howto/include/scripts/performance_benchmark_base.py>` :fa:`download` provides a basic way of assessing performance of the workflow engine that involves all components (CPU, file system, postgresql, rabbitmq).

It launches ``ArithmeticAddCalculation``s on the localhost and measures the time until completion.
Since the workload of the ``ArithmeticAddCalculation`` (summing two numbers) completes instantly, the time per process is a reasonable measure of the overhead incurred from the workflow engine.

The numbers reported in the :ref:`howto section<how-to:tune-performance>` were obtained by running the processes in the current shell, which is the default.
The ``--daemon`` option can be used to run the calculations through the AiiDA daemon instead, and to look at parallelizing over multiple daemon workers:

.. table::
    :widths: auto

    ========== ======================= ========================
    # Workers  Total elapsed time (s)  Performance (s/process)
    ========== ======================= ========================
    1          46.55                   0.47
    2          27.83                   0.28
    4          16.43                   0.16
    ========== ======================= ========================

.. note::

    While the process rate increases with the number of daemon workers, the scaling is not quite linear.
    This is because, for simplicity, the benchmark script measures both the time required to submit the processes to the daemon (not parallelized) as well as the time needed to run the processes (parallelized over daemon workers).
    In long-running processes, the time required to submit the process (roughly 0.1 seconds per process) is not relevant and linear scaling is achieved.


.. _topics:performance:plugins:

Plugins
=======

One of AiiDA's strengths is its plugin system, which allows it capabilities to be customized in a variety of ways.
However, this flexibility also means that the performance of AiiDA can be affected significantly by the implementation of the plugins.
For example, a `CalcJob` plugin determines which files are transferred from and to the computing resources.
If the plugin needs to transfer and store large amounts of data, this will affect the process throughput of the daemon workers.
Likewise, if a `Parser` plugin performs heavy numerical computations to parse the retrieved data, this will slow down the workers' throughput.
In order to optimize the process throughput, plugins should try to minize heavy computations and the transfer of lots of unnecessary data.
