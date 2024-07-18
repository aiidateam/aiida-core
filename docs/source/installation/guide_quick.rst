.. _installation:guide-quick:

========================
Quick installation guide
========================

First, install the ``aiida-core`` Python package:

.. code-block:: console

    pip install aiida-core

Next, set up a profile where all data is stored:

.. code-block:: console

    verdi presto

Verify that the installation was successful:

.. code-block:: console

    verdi status

If none of the lines show a red cross, indicating a problem, the installation was successful and you are good to go.

.. admonition:: What next?
    :class: hint

    If you are a new user, we recommend to start with the :ref:`basic tutorial <tutorial:basic>`.
    Alternatively, check out the :ref:`next steps guide <tutorial:next-steps>`.

.. admonition:: Problems during installation?
    :class: warning

    If you encountered any issues, please refer to the :ref:`troubleshooting section <installation:troubleshooting>`.

.. warning::

    Not all AiiDA functionality is supported by the quick installation.
    Please refer to the :ref:`section below <installation:guide-quick:limitations>` for more information.


.. _installation:guide-quick:limitations:

Quick install limitations
=========================

By default, ``verdi presto`` creates a profile that uses SQLite instead of PostgreSQL and does not use the RabbitMQ message broker.
The table below gives a quick overview of the functionality that is not supported in those cases:

+-----------------------------------------+------------------------------------------------------------------------+
| No RabbitMQ                             | SQLite instead of PostgreSQL                                           |
+=========================================+========================================================================+
| Cannot run the daemon                   | Not suitable for high-throughput workloads                             |
+-----------------------------------------+------------------------------------------------------------------------+
| Cannot submit processes to the daemon\* | No support for ``has_key`` and ``contains`` operators in query builder |
+-----------------------------------------+------------------------------------------------------------------------+
| Cannot play, pause, kill processes      | No support for ``QueryBuilder.get_creation_statistics``                |
+-----------------------------------------+------------------------------------------------------------------------+

\* Calculations can still be run on remote computers

.. note::
    To enable the RabbitMQ broker for an existing profile, :ref:`install RabbitMQ <installation:guide-complete:rabbitmq>` and then run ``verdi profile configure-rabbitmq``.

Functionality
-------------

Part of AiiDA's functionality requires a `message broker <https://en.wikipedia.org/wiki/Message_broker>`_, with the default implementation using `RabbitMQ <https://www.rabbitmq.com/>`_.
The message broker is used to allow communication with the :ref:`daemon <topics:daemon>`.
Since RabbitMQ is a separate service and is not always trivial to install, the quick installation guide sets up a profile that does not require it.
As a result, the daemon cannot be started and processes cannot be submitted to it but can only be run in the current Python interpreter.

.. note::
    The ``verdi presto`` command automatically checks if RabbitMQ is running on the localhost.
    If it can successfully connect, it configures the profile with the message broker and therefore the daemon functionality will be available.

.. tip::
    The connection parameters of RabbitMQ can be (re)configured after the profile is set up with ``verdi profile configure-rabbitmq``.
    This can be useful when the RabbitMQ setup is different from the default that AiiDA checks for and the automatic configuration of ``verdi presto`` failed.


Performance
-----------

The quick installation guide by default creates a profile that uses `SQLite <https://www.sqlite.org/>`_ for the database.
Since SQLite does not require running a service, it is easy to install and use on essentially any system.
However, for certain use cases it is not going to be the most performant solution.
AiiDA also supports `PostgreSQL <https://www.postgresql.org/>`_ which is often going to be more performant compared to SQLite.

.. tip::
    If a PostgreSQL service is available, run ``verdi presto --use-postgres`` to set up a profile that uses PostgreSQL instead of SQLite.
    The command tries to connect to the service and automatically create a user account and database to use for the new profile.
    AiiDA provides defaults that work for most setups where PostgreSQL is installed on the localhost.
    Should this fail, the connection parameters can be customized using the ``--postgres-hostname``, ``--postgres-port``, ``--postgres-username``, ``--postgres-password`` options.

Please refer to the :ref:`complete installation guide <installation:guide-complete>` for instructions to set up a feature-complete and performant installation.
