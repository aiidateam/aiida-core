.. _topics:daemon:

******
Daemon
******

AiiDA provides a daemon process that runs in the background which handles any new processes (i.e., calculations and workflows, see :ref:`process concepts <topics:processes:concepts>`) that are submitted.
Unlike when running a process, which blocks the current Python interpreter (see the :ref:`launching <topics:processes:usage:launching>` section for details on the difference between *run* and *submit*), the daemon can handle multiple processes asynchronously.

The daemon concept in AiiDA consists of multiple *system processes*.

.. note::

    System processes, here, refers to processes that are run by the operating system, not to the AiiDA specific collective term for all calculations and workflows.

When the daemon is started, a single system process is launched in the background that runs indefinitely until it is stopped.
This daemonized process is responsible for launching and then monitoring one or multiple daemon *workers*.
Each daemon worker is another system process that connects to RabbitMQ to retrieve calculations and workflows that have been submitted and run them to completion.
If a daemon worker dies, the daemon will automatically revive it.
When the daemon is requested to stop, it will send a signal to all workers to shut them down before shutting down itself.

In summary: AiiDA's daemon consists of a single system process running in the background (the daemon) that manages one or more system processes that handle all submitted calculations and workflows (the daemon workers).


.. _topics:daemon:client:

======
Client
======

The Python API provides the :class:`~aiida.engine.daemon.client.DaemonClient` class to interact with the daemon.
It can either be constructed directly for a given profile, or the :func:`aiida.engine.get_daemon_client` utility function can be used to construct it.
In order to control the daemon for the current default profile:

.. code-block:: python

    from aiida.engine import get_daemon_client
    client = get_daemon_client()

It is also possible to explicitly specify a profile:

.. code-block:: python

    client = get_daemon_client(profile='some-profile')

The daemon can be started and stopped through the client:

.. code-block:: python

    client.start_daemon()
    assert client.is_daemon_running
    client.stop_daemon(wait=True)

The main methods of interest for interacting with the daemon are:

* :meth:`~aiida.engine.daemon.client.DaemonClient.start_daemon`
* :meth:`~aiida.engine.daemon.client.DaemonClient.restart_daemon`
* :meth:`~aiida.engine.daemon.client.DaemonClient.stop_daemon`
* :meth:`~aiida.engine.daemon.client.DaemonClient.get_status`

These methods will raise a :class:`~aiida.engine.daemon.client.DaemonException` if the daemon fails to start or calls to it fail.
All methods accept a ``timeout`` argument, which is the number of seconds the client should wait for the daemon process to respond, before raising a :class:`~aiida.engine.daemon.client.DaemonTimeoutException`.
The default for the ``timeout`` is taken from the ``daemon.timeout`` configuration option and is set when constructing the :class:`~aiida.engine.daemon.client.DaemonClient`.

.. note::

    The ``DaemonClient`` only directly interacts with the main daemon process, not with any of the daemon workers that it manages.
