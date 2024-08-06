.. _installation:guide-quick:

========================
Quick installation guide
========================

.. warning::

    Not all AiiDA functionality is supported by the quick installation.
    Please refer to the :ref:`section below <installation:guide-quick:limitations>` for more information and see the :ref:`complete installation guide <installation:guide-complete>` for instructions to set up a feature-complete and performant installation.


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


.. _installation:guide-quick:limitations:

Quick install limitations
=========================

A setup that is ideal for production work requires the PostgreSQL and RabbitMQ services.
By default, ``verdi presto`` creates a profile that allows running AiiDA without these:

* **Database**: The PostgreSQL database that is used to store queryable data, is replaced by SQLite.
* **Broker**: The RabbitMQ message broker that allows communication with and between processes is disabled.

The following matrix shows the possible combinations of the database and broker options and their use cases:

+----------------------+----------------------------------------------------+-------------------------------------------------------------+
|                      | **SQLite database**                                | **PostgreSQL database**                                     |
+======================+====================================================+=============================================================+
| **No broker**        | Quick start with AiiDA                             | [*not really relevant for any usecase*]                     |
+----------------------+----------------------------------------------------+-------------------------------------------------------------+
| **RabbitMQ**         | Production (low-throughput; beta, has limitations) | Production (maximum performance, ideal for high-throughput) |
+----------------------+----------------------------------------------------+-------------------------------------------------------------+

The sections below provide details on the use of the PostgreSQL and RabbitMQ services and the limitations when running AiiDA without them.

.. _installation:guide-quick:limitations:rabbitmq:

RabbitMQ
--------

Part of AiiDA's functionality requires a `message broker <https://en.wikipedia.org/wiki/Message_broker>`_, with the default implementation using `RabbitMQ <https://www.rabbitmq.com/>`_.
The message broker is used to allow communication with processes and the :ref:`daemon <topics:daemon>` as well as between themselves.
Since RabbitMQ is a separate service and is not always trivial to install, the quick installation guide allows setting up a profile that does not require it.
However, as a result the profile:

* is not suitable for high-throughput workloads (a polling-based mechanism is used rather than an event-based one)
* cannot run the daemon (no ``verdi daemon start/stop``) and therefore processes cannot be submitted to the daemon (i.e., one can only use ``run()`` instead of ``submit()`` to launch calculations and workflows)
* cannot play, pause, kill processes

.. note::
    The ``verdi presto`` command automatically checks if RabbitMQ is running on the localhost.
    If it can successfully connect, it configures the profile with the message broker and therefore the limitations listed above do not apply.

.. tip::
    A profile created by ``verdi presto`` can easily start using RabbitMQ as the broker at a later stage.
    Once a RabbitMQ service is available (see :ref:`install RabbitMQ <installation:guide-complete:rabbitmq>` for instruction to install it) and run ``verdi profile configure-rabbitmq`` to configure its use for the profile.

.. _installation:guide-quick:limitations:postgresql:

PostgreSQL
----------

AiiDA stores (part of) the data of the provenance graph in a database and the `PostgreSQL <https://www.postgresql.org/>`_ service provides great performance for use-cases that require high-throughput.
Since PostgreSQL is a separate service and is not always trivial to install, the quick installation guide allows setting up a profile that uses the serverless `SQLite <https://www.sqlite.org/>`_ instead.
However, as a result the profile:

* is not suitable for high-throughput workloads (concurrent writes from multiple processes to the database are serialized)
* does not support the ``has_key`` and ``contains`` operators in the ``QueryBuilder``
* does not support the ``get_creation_statistics`` method of the ``QueryBuilder``

.. tip::
    If a PostgreSQL service is available, run ``verdi presto --use-postgres`` to set up a profile that uses PostgreSQL instead of SQLite.
    The command tries to connect to the service and automatically create a user account and database to use for the new profile.
    AiiDA provides defaults that work for most setups where PostgreSQL is installed on the localhost.
    Should this fail, the connection parameters can be customized using the ``--postgres-hostname``, ``--postgres-port``, ``--postgres-username``, ``--postgres-password`` options.
