.. _internal_architecture:broker:

**********
ZMQ Broker
**********

.. versionadded:: 2.9

The ZMQ broker is AiiDA's built-in message broker, replacing the need for an external RabbitMQ service.
It implements the subset of AMQP semantics that AiiDA requires (tasks, RPC, broadcasts) using ZeroMQ as the transport layer.

This page documents the internal architecture for developers working on the broker itself.
For user-facing documentation, see the :ref:`installation guide <installation:guide-complete:broker:zmq>`.


Process and thread architecture
===============================

When ``verdi daemon start`` is run with a ZMQ-configured profile, circus launches two types of processes:

.. code-block:: text

    verdi daemon start
    └── circus (daemon supervisor)
        ├── verdi devel zmq-broker      ← broker process (1 instance)
        │   └── ZmqBrokerService
        │       └── ZmqBrokerServer     (single-threaded, zmq.Poller event loop)
        │           └── PersistentQueue (file-based task durability)
        │
        └── verdi daemon worker         ← worker process(es) (1..N instances)
            └── Runner
                └── ZmqBroker
                    └── ZmqCommunicator
                        ├── main thread     (public API: task_send, rpc_send, ...)
                        └── loop thread     (private asyncio loop with ZMQ DEALER socket)

Key points:

- The **broker process** is single-threaded.
  ``ZmqBrokerServer`` uses a ``zmq.Poller`` event loop (non-blocking I/O via epoll/kqueue underneath) — no asyncio, no threads.
- Each **worker process** creates a ``ZmqCommunicator`` that runs a private asyncio event loop on a dedicated **background thread**.
  All ZMQ socket I/O happens on that thread; public methods schedule work via ``call_soon_threadsafe``, so no locks are needed.
- The broker process is started **before** workers by circus, so its IPC socket is ready when workers connect.
  If it isn't ready yet, ``get_communicator()`` polls until the socket file appears.


Module overview
===============

``ZmqCommunicator`` implements ``kiwipy.Communicator`` — the same interface that ``RmqThreadCommunicator`` implements for RabbitMQ.
plumpy and the AiiDA engine are unaware of which broker backend is in use; they only interact through this interface.

.. code-block:: text

    src/aiida/brokers/zmq/
    ├── broker.py         ZmqBroker — the Broker interface for workers
    ├── communicator.py   ZmqCommunicator — kiwipy.Communicator over ZMQ
    ├── server.py         ZmqBrokerServer — the broker's message router
    ├── service.py        ZmqBrokerService — process wrapper (PID, signals, status files)
    ├── queue.py          PersistentQueue — file-based durable task queue
    ├── protocol.py       Message types, encoding/decoding, factory functions
    └── defaults.py       Developer-tunable constants (not user-facing)


Endpoint discovery
==================

Unlike RabbitMQ, the ZMQ broker requires no connection configuration (no host, port, or credentials).
Discovery is file-based: both sides derive the broker directory from the profile UUID.

1. On startup, the broker process writes the IPC socket path to ``~/.aiida/broker/{profile-uuid}/broker.sockets``.
2. When a worker calls ``get_communicator()``, it reads that file to obtain the endpoint (e.g. ``ipc:///tmp/aiida_zmq_xyz/router.sock``).
3. The worker connects its DEALER socket to that endpoint.

This means the ZMQ broker is **local-only** — IPC sockets do not work across machines.
For distributed setups (workers on different hosts), use RabbitMQ.


Socket architecture
===================

All traffic flows through a single ZMQ ROUTER/DEALER socket pair over IPC:

.. code-block:: text

    ┌──────────────────────┐          ┌──────────────────────┐
    │   Worker process 1   │          │   Worker process 2   │
    │  ┌────────────────┐  │          │  ┌────────────────┐  │
    │  │ DEALER socket   │  │          │  │ DEALER socket   │  │
    │  │ (async, loop    │  │          │  │ (async, loop    │  │
    │  │  thread)        │  │          │  │  thread)        │  │
    │  └───────┬─────────┘  │          │  └───────┬─────────┘  │
    └──────────┼────────────┘          └──────────┼────────────┘
               │ ipc://                           │ ipc://
               └────────────┐         ┌───────────┘
                            ▼         ▼
                 ┌──────────────────────────┐
                 │     Broker process       │
                 │  ┌────────────────────┐  │
                 │  │   ROUTER socket    │  │
                 │  │  (sync, zmq.Poller)│  │
                 │  └────────────────────┘  │
                 │  ┌────────────────────┐  │
                 │  │  PersistentQueue   │  │
                 │  │  (disk storage)    │  │
                 │  └────────────────────┘  │
                 └──────────────────────────┘

The ROUTER socket auto-prepends the sender's identity to incoming frames, enabling the broker to route replies back to specific clients.
``ROUTER_MANDATORY`` is set so that sending to a disconnected identity raises ``ZMQError`` immediately rather than silently dropping the message.


Message protocol
================

The protocol is defined in ``protocol.py``.
All messages are JSON-encoded dicts sent as single ZMQ frames.
Every message has a ``type`` field (a ``MessageType`` enum value) and an ``id`` (UUID hex).

Message types
-------------

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Message type
     - Direction
     - Purpose
   * - ``TASK``
     - client → broker → worker
     - Submit a task for processing. Contains ``body``, ``sender``, ``no_reply``.
   * - ``TASK_ACK``
     - worker → broker
     - Acknowledge successful receipt/completion. Broker removes task from persistent queue.
   * - ``TASK_NACK``
     - worker → broker
     - Negative acknowledgment. Broker requeues the task for redelivery.
   * - ``TASK_RESPONSE``
     - worker → broker → client
     - Return the result of a completed task. Broker forwards to original sender.
   * - ``RPC``
     - client → broker → recipient
     - Remote procedure call to a named recipient. Broker routes by subscriber ID.
   * - ``RPC_RESPONSE``
     - recipient → broker → client
     - Return RPC result. Broker forwards to original caller.
   * - ``BROADCAST``
     - client → broker → all
     - Fan-out to all connected clients (derived from subscriber registries).
   * - ``SUBSCRIBE_TASK``
     - worker → broker
     - Register as a task consumer. Broker adds worker to dispatch pool.
   * - ``UNSUBSCRIBE_TASK``
     - worker → broker
     - Deregister as a task consumer.
   * - ``SUBSCRIBE_RPC``
     - worker → broker
     - Register as an RPC handler under a given identifier.
   * - ``UNSUBSCRIBE_RPC``
     - worker → broker
     - Deregister as an RPC handler.
   * - ``PING``
     - broker → worker
     - Liveness probe. Worker ignores it; failure to deliver (``EHOSTUNREACH``) tells the broker the worker is dead.

AMQP mapping
------------

The protocol maps AMQP concepts to ZMQ message types:

.. code-block:: text

    AMQP concept              ZMQ broker equivalent
    ────────────────────────  ──────────────────────────────────
    basic.ack                 TASK_ACK
    basic.nack                TASK_NACK
    consumer with prefetch    TASK dispatch to available workers
    fanout exchange           BROADCAST via ROUTER fan-out
    direct exchange           RPC routed to named recipient
    durable queue             PersistentQueue (file-based)
    basic.consume             SUBSCRIBE_TASK / SUBSCRIBE_RPC

Wire format
-----------

Messages travel as ZMQ multipart frames:

.. code-block:: text

    Client (DEALER) sends:        [ empty-delimiter | json-payload ]
    Broker (ROUTER) receives:     [ client-identity | empty-delimiter | json-payload ]
    Broker (ROUTER) sends:        [ target-identity | empty-delimiter | json-payload ]

The empty delimiter frame is a ZMQ convention for ROUTER/DEALER interop.
The ROUTER socket automatically prepends the sender's identity on receive and uses the first frame as the routing target on send.

Payload fields like ``body`` and ``result`` are opaque to the broker — they are pre-encoded by the sender (typically as YAML strings by plumpy/kiwipy) and passed through without inspection.


Message flow: task submission
=============================

.. code-block:: text

    verdi run / submit()          Worker (daemon)            Broker
    ────────────────────          ───────────────            ──────
          │                             │                      │
          │  task_send(task)            │                      │
          │──── TASK ──────────────────────────────────────────▶│
          │                             │          push to PersistentQueue
          │                             │                      │
          │                             │◀─── TASK ────────────│  dispatch
          │                             │                      │
          │                             │  (process runs...)   │
          │                             │                      │
          │                             │──── TASK_ACK ───────▶│  ack: remove from queue
          │                             │──── TASK_RESPONSE ──▶│
          │                             │                      │
          │◀────────────── TASK_RESPONSE (forwarded) ──────────│
          │                             │                      │

Key details:

- The broker persists the task to disk **before** dispatching it.
  If the broker crashes, tasks are recovered from disk on restart.
- Workers delay the ACK until the task Future resolves (see :ref:`deferred ACK <internal_architecture:broker:deferred_ack>` below).
  If a worker dies before ACK'ing, the broker detects the disconnect (via ZMTP heartbeats + PING probing) and requeues the task.
- If ``no_reply=True``, no TASK_RESPONSE is sent.


Task dispatch strategy
======================

The broker maintains a ``_available_workers`` deque.
When a worker sends ``SUBSCRIBE_TASK``, it is added to this pool.
The ROUTER socket provides identity-based routing — the broker picks the next available worker from the deque and sends directly to it.

After dispatching a task, the worker is **immediately re-added** to the available pool — it does not wait for the ACK.
This means a single worker can have multiple tasks in flight concurrently, matching RabbitMQ's multi-prefetch behavior.
The ACK only affects the ``PersistentQueue`` (removing the task from disk), not worker availability.

.. code-block:: text

    Dispatch loop (runs after every poll):

    while available_workers AND pending_tasks:
        worker = available_workers.popleft()
        task   = task_queue.pop()           # pending → processing
        send task to worker
        available_workers.append(worker)     # immediately re-available


.. _internal_architecture:broker:deferred_ack:

Deferred ACK pattern
====================

The kiwipy/plumpy stack requires that task subscribers can return ``Future`` objects — plumpy's process runner does this because AiiDA processes are long-running and asynchronous.
The ZMQ communicator must support this to be a compatible ``kiwipy.Communicator``.

When a task subscriber returns a result, two paths are possible:

- **Direct result**: the communicator sends ``TASK_ACK`` and ``TASK_RESPONSE`` immediately.
- **Future**: the communicator stores the task in ``_in_progress_tasks`` and registers a done-callback on the Future.
  The ACK is deferred until the Future resolves. This is critical for reliability — if the worker process dies before the Future completes, no ACK is sent, and the broker requeues the task.

.. code-block:: text

    Worker receives TASK
    │
    ├── subscriber returns result directly
    │   └── send TASK_ACK + TASK_RESPONSE immediately
    │
    └── subscriber returns Future
        └── store in _in_progress_tasks
            └── Future resolves → _finalize_task()
                └── send TASK_ACK + TASK_RESPONSE

The same pattern applies to RPC: if the subscriber returns a ``Future``, the response is deferred until it resolves.


Dead worker detection
=====================

Dead worker detection combines ZMQ transport features with application-level logic.

**Detection** (ZMQ built-in):
the ROUTER socket is configured with ``HEARTBEAT_IVL`` and ``HEARTBEAT_TIMEOUT``.
ZMQ sends periodic ping frames at the transport level; if a worker stops responding within the timeout, ZMQ disconnects it internally and emits an ``EVENT_DISCONNECTED`` on the monitor socket we attached to the ROUTER.

The problem is that this event only reports the file descriptor, not which client identity disconnected.
So the event is just a **trigger** — it tells us *someone* died, but not *who*.

**Identification** (our logic):
on each ``EVENT_DISCONNECTED``, ``_handle_disconnect_event`` calls ``_probe_workers``, which sends a ``PING`` message to every worker identity that has in-flight tasks.
With ``ROUTER_MANDATORY`` set on the socket, sending to a dead identity immediately raises ``ZMQError(EHOSTUNREACH)``.
Any worker that fails the probe is removed via ``_remove_dead_worker``, which requeues all its assigned tasks and cleans up the subscriber registries.


Persistent queue (crash recovery)
=================================

``PersistentQueue`` stores tasks as individual JSON files:

.. code-block:: text

    {storage_path}/tasks/
    ├── pending/                      ← waiting to be dispatched
    │   └── {timestamp}_{id}.json
    └── processing/                   ← dispatched, awaiting ACK
        └── {timestamp}_{id}.json

- **push**: writes to ``pending/`` (atomic: write ``.tmp`` then ``rename``)
- **pop**: moves from ``pending/`` to ``processing/``
- **ack**: deletes from ``processing/``
- **nack**: moves back from ``processing/`` to ``pending/`` (front of queue for retry)
- **crash recovery**: on startup, all files in ``processing/`` are moved back to ``pending/``


Service files
=============

``ZmqBrokerService`` manages the broker process lifecycle and writes files that ``ZmqBroker`` (in worker processes) reads to discover the broker:

.. code-block:: text

    ~/.aiida/broker/{profile-uuid}/
    ├── broker.pid         "aiida-zmq-broker {pid}" — sentinel + PID for ownership check
    ├── broker.status      JSON with task counts, updated every STATUS_INTERVAL seconds
    ├── broker.sockets     path to the temp socket directory
    └── storage/           PersistentQueue data

    /tmp/aiida_zmq_{random}/
    └── router.sock        IPC socket (temp dir avoids 107-byte Unix path limit)


Known limitations
=================

- **Single point of failure**: the broker is a single process. If it crashes, no tasks are dispatched until it restarts (circus auto-restarts it). Tasks in the persistent queue survive the crash.
- **Local-only**: IPC sockets do not work across machines. For distributed setups with workers on different hosts, use RabbitMQ.
- **No message TTL**: tasks remain in the queue indefinitely until consumed or manually cleared.
- **No dead letter queue**: NACKed tasks are requeued to the front of the queue. There is no mechanism to route repeatedly-failing tasks to a separate queue.
- **Single ROUTER socket**: all traffic (tasks, RPC, broadcasts) shares one socket. This is sufficient for AiiDA's workload but could become a throughput bottleneck under extreme fan-out.


Timeouts
========

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Constant / option
     - Default
     - Purpose
   * - ``zmq.task_timeout`` |br| (``verdi config``)
     - 10s
     - How long a caller waits for a task or RPC response from the broker.
       Fires a ``TimeoutError`` on the pending Future. Analogous to ``rmq.task_timeout``.
   * - ``BROKER_READY_TIMEOUT``
     - 10s
     - How long ``get_communicator()`` polls for the broker to write its socket files at startup.
       A warning is logged after 5s.
   * - ``LOOP_TIMEOUT``
     - 5s
     - How long the main thread waits when scheduling work onto the communicator's background event loop.
       Fires if the loop thread is blocked or dead.
   * - ``LOOP_JOIN_TIMEOUT``
     - 3s
     - How long ``close()`` waits for the loop thread to shut down.
   * - ``HEARTBEAT_IVL``
     - 2s
     - ZMTP heartbeat interval — how often the broker pings connected workers.
   * - ``HEARTBEAT_TIMEOUT``
     - 6s
     - Peer considered dead after no heartbeat response for this duration.
   * - ``POLL_TIMEOUT``
     - 1s
     - Server-side ``zmq.Poller`` timeout per iteration. Controls how quickly the broker responds to shutdown signals.
   * - ``STATUS_INTERVAL``
     - 5s
     - How often the broker service writes its status JSON to disk.

Only ``zmq.task_timeout`` is user-configurable.
All other values are developer-tunable constants in ``defaults.py``.


.. |br| raw:: html

   <br/>
