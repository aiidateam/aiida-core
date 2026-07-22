.. _internal_architecture:broker:

*************
ZeroMQ broker
*************

.. versionadded:: 2.9

The ZeroMQ broker is AiiDA's built-in message broker.
It implements the subset of AMQP semantics that AiiDA actually uses (tasks, RPC, broadcasts) on top of ZeroMQ, so a profile can run without an external RabbitMQ service.

This page documents the internal architecture for developers working on the broker itself.
For user-facing documentation, see the :ref:`installation guide <installation:guide-complete:broker:zeromq>`.


Process and thread architecture
===============================

When ``verdi daemon start`` is run with a ZeroMQ-configured profile, circus launches two types of processes:

.. code-block:: text

    verdi daemon start
    └── circus (daemon supervisor)
        ├── verdi daemon broker         ← broker process (1 instance, hidden command)
        │   └── ZeromqBrokerService
        │       └── ZeromqBrokerServer     (single-threaded poller event loop)
        │           └── PersistentQueue (file-based task durability)
        │
        └── verdi daemon worker         ← worker process(es) (1..N instances)
            └── Runner
                └── ZeromqBroker
                    └── ZeromqCommunicator
                        ├── main thread     (public API: task_send, rpc_send, ...)
                        └── loop thread     (private asyncio loop with ZeroMQ DEALER socket)

The broker process is single-threaded.
``ZeromqBrokerServer`` runs a plain poller loop (epoll/kqueue under the hood); there is no asyncio and there are no threads on this side.

Worker processes talk to the broker through a ``ZeromqCommunicator``.
The communicator runs a private asyncio loop on a dedicated background thread, and all ZeroMQ socket I/O happens on that thread.
Public methods hand work to the loop via ``call_soon_threadsafe``, which is why the communicator needs no locks.

Circus adds the broker watcher before the worker watcher, so in practice the broker's IPC socket exists by the time workers connect.
When it does not, ``get_communicator()`` polls for the socket file for up to ``BROKER_READY_TIMEOUT``.
If a broker is already running for the profile (for example one started by a test fixture), the broker watcher is skipped entirely.


Module overview
===============

``ZeromqCommunicator`` implements ``kiwipy.Communicator``, the same interface that ``RmqThreadCommunicator`` implements for RabbitMQ.
plumpy and the AiiDA engine only ever see this interface; they do not know which broker backend they are talking to.

.. code-block:: text

    src/aiida/brokers/zeromq/
    ├── broker.py         ZeromqBroker — the Broker interface for workers
    ├── communicator.py   ZeromqCommunicator — kiwipy.Communicator over ZeroMQ
    ├── server.py         ZeromqBrokerServer — the broker's message router
    ├── service.py        ZeromqBrokerService — process wrapper (PID, signals, status files)
    ├── queue.py          PersistentQueue — file-based durable task queue
    ├── protocol.py       Message types, encoding/decoding, factory functions
    └── defaults.py       Developer-tunable constants (not user-facing)


Endpoint discovery
==================

Unlike RabbitMQ, the ZeroMQ broker needs no connection configuration: no host, no port, no credentials.
Discovery is file-based.
Both sides derive the broker directory from the profile UUID as ``{config_dir}/broker/{profile-uuid}-{profile-name}``.

1. On startup, the broker process creates a temporary socket directory (e.g. ``/tmp/aiida_zeromq_xyz``) and writes its path to ``{config_dir}/broker/{profile-uuid}/broker.sockets``.
2. When a worker calls ``get_communicator()``, it reads that file and derives the endpoint as ``ipc://{sockets_dir}/router.sock``.
3. The worker connects its DEALER socket to that endpoint.

The flip side is that the broker is local-only, since IPC sockets do not cross machine boundaries.
If you need workers on other hosts, use RabbitMQ.


Socket architecture
===================

All traffic converges on a single ROUTER socket in the broker; every client connects to it with a DEALER socket over IPC.
Daemon workers are the main clients, but any user process that loads the profile and talks to the broker connects the same way: a submission script calling ``submit()`` sends a task, and ``verdi`` commands such as ``verdi process kill`` or ``verdi process play`` send RPCs.
The broker does not care which kind of client it is; each connection is just another identity on the ROUTER socket.

.. code-block:: text

                     ┌───────────────────────┐
                     │  User client process  │
                     │  (submission script,  │
                     │   verdi commands)     │
                     │  ┌─────────────────┐  │
                     │  │ DEALER socket   │  │
                     │  └───────┬─────────┘  │
                     └──────────┼────────────┘
                                │ ipc://
                                ▼
                   ┌──────────────────────────┐
                   │      Broker process      │
                   │  ┌────────────────────┐  │
                   │  │   ROUTER socket    │  │
                   │  │  (sync, poller)    │  │
                   │  └────────────────────┘  │
                   │  ┌────────────────────┐  │
                   │  │  PersistentQueue   │  │
                   │  │  (disk storage)    │  │
                   │  └────────────────────┘  │
                   └──────────────────────────┘
                            ▲       ▲
            ┌───────────────┘       └───────────────┐
            │ ipc://                                │ ipc://
 ┌──────────┼────────────┐               ┌──────────┼────────────┐
 │  ┌───────┴─────────┐  │               │  ┌───────┴─────────┐  │
 │  │ DEALER socket   │  │               │  │ DEALER socket   │  │
 │  │ (async, loop    │  │               │  │ (async, loop    │  │
 │  │  thread)        │  │               │  │  thread)        │  │
 │  └─────────────────┘  │               │  └─────────────────┘  │
 │   Worker process 1    │               │   Worker process 2    │
 └───────────────────────┘               └───────────────────────┘

The ROUTER socket prepends the sender's identity to every incoming message, which is what lets the broker route replies back to the right client.
We set ``ROUTER_MANDATORY`` so that sending to a disconnected identity raises a socket error immediately instead of silently dropping the message.


Message protocol
================

The protocol is defined in ``protocol.py``.
All messages are JSON-encoded dicts sent as single ZeroMQ frames.
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
     - broker → client |br| worker → broker
     - From broker to client: immediate acknowledgment that the task was persisted to the queue
       (matches RabbitMQ publisher-confirm semantics).
       Workers also send a ``TASK_RESPONSE`` with the task result when it completes,
       but the broker logs and discards it — the result is not forwarded back to the sender.
   * - ``RPC``
     - client → broker → recipient
     - Remote procedure call to a named recipient. Broker routes by subscriber ID.
   * - ``RPC_RESPONSE``
     - recipient → broker → client
     - Return RPC result. Broker forwards to original caller.
   * - ``BROADCAST``
     - client → broker → all
     - Fan-out to all connected clients.
       The broker derives the recipient set from its task and RPC subscriber registries;
       broadcast subscriptions themselves are client-local and never sent to the broker
       (see :ref:`broadcast semantics <internal_architecture:broker:broadcast>`).
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

The protocol maps AMQP concepts to ZeroMQ message types:

.. code-block:: text

    AMQP concept              ZeroMQ broker equivalent
    ────────────────────────  ──────────────────────────────────
    publisher confirm         TASK_RESPONSE (immediate broker ack)
    basic.ack                 TASK_ACK
    basic.nack                TASK_NACK
    consumer with prefetch    TASK dispatch to available workers
    fanout exchange           BROADCAST via ROUTER fan-out
    direct exchange           RPC routed to named recipient
    durable queue             PersistentQueue (file-based)
    basic.consume             SUBSCRIBE_TASK / SUBSCRIBE_RPC

Wire format
-----------

Messages travel as ZeroMQ multipart frames:

.. code-block:: text

    Client (DEALER) sends:        [ empty-delimiter | json-payload ]
    Broker (ROUTER) receives:     [ client-identity | empty-delimiter | json-payload ]
    Broker (ROUTER) sends:        [ target-identity | empty-delimiter | json-payload ]

The empty delimiter frame is the standard ZeroMQ convention for ROUTER/DEALER interop.
The ROUTER socket prepends the sender's identity on receive and uses the first frame as the routing target on send.

Payload fields like ``body`` and ``result`` are opaque to the broker.
They are pre-encoded by the sender (typically as YAML strings by plumpy/kiwipy) and passed through without inspection.


Message flow: task submission
=============================

.. code-block:: text

    verdi run / submit()          Worker (daemon)            Broker
    ────────────────────          ───────────────            ──────
          │                             │                      │
          │  task_send(task)            │                      │
          │──── TASK ──────────────────────────────────────────▶│
          │                             │          push to PersistentQueue
          │◀──── TASK_RESPONSE (ack) ──────────────────────────│  immediate
          │                             │                      │
          │                             │◀─── TASK ────────────│  dispatch
          │                             │                      │
          │                             │  (process runs...)   │
          │                             │                      │
          │                             │──── TASK_ACK ───────▶│  ack: remove from queue
          │                             │                      │

The broker replies with ``TASK_RESPONSE`` as soon as the task is persisted to the queue on disk, before any worker has seen it.
This mirrors RabbitMQ's publisher confirms: the caller's ``Future`` resolves right away.
Without it, ``task_send`` would block until ``broker.task_timeout`` whenever no workers are connected — which is exactly the situation ``verdi process repair`` runs in.

Persisting before dispatching means a broker crash cannot lose a task; whatever was in the queue is recovered from disk on restart.

Workers hold back the ACK until the task's ``Future`` resolves (see :ref:`deferred ACK <internal_architecture:broker:deferred_ack>` below).
If a worker dies mid-task, the ACK never arrives; the broker notices the disconnect (ZMTP heartbeats plus PING probing) and requeues the task.

With ``no_reply=True`` the task stays fully fire-and-forget: the broker sends no immediate persistence confirmation, and the worker sends no completion ``TASK_RESPONSE`` later either.
``submit()`` always uses this mode while RPC messages do send a completion response.


Task dispatch strategy
======================

The broker keeps a deque of available workers, ``_available_workers``.
A worker joins the pool when it sends ``SUBSCRIBE_TASK``.
Since the ROUTER socket routes by identity, dispatching a task is just picking the next worker from the deque and sending to its identity.

After dispatching, the worker goes straight back into the pool; the broker does not wait for the ACK.
A single worker can therefore have several tasks in flight at once, which matches RabbitMQ's multi-prefetch behavior.
The ACK only affects the ``PersistentQueue`` (removing the task from disk), never worker availability.

.. code-block:: text

    Dispatch loop (runs after every poll):

    while available_workers AND pending_tasks:
        worker = available_workers.popleft()
        if worker no longer subscribed:      # stale entry
            continue
        task   = task_queue.pop()           # pending → processing
        send task to worker                  # on failure: requeue + remove dead worker
        available_workers.append(worker)     # immediately re-available


.. _internal_architecture:broker:deferred_ack:

Deferred ACK pattern
====================

kiwipy allows a task subscriber to return a ``Future`` instead of a result, and plumpy's process runner relies on this because AiiDA processes are long-running and asynchronous.
Any compatible ``kiwipy.Communicator`` has to support it, so ours does too.

When a task subscriber returns, there are two cases:

- The subscriber returned a direct result: the communicator sends ``TASK_ACK`` immediately and sends a completion ``TASK_RESPONSE`` only if ``no_reply=False``.
- The subscriber returned a ``Future``: the communicator stores the task in ``_in_progress_tasks`` and attaches a done-callback that sends the ACK once the ``Future`` resolves and sends a completion ``TASK_RESPONSE`` only if ``no_reply=False``.

The deferral is what makes delivery reliable.
If the worker process dies before the ``Future`` completes, no ACK was ever sent, and the broker requeues the task.

.. code-block:: text

    Worker receives TASK
    │
    ├── subscriber returns result directly
    │   └── send TASK_ACK immediately
    │       └── if no_reply=False: send completion TASK_RESPONSE
    │
    └── subscriber returns Future
        └── store in _in_progress_tasks
            └── Future resolves → _finalize_task()
                ├── send TASK_ACK
                └── if no_reply=False: send completion TASK_RESPONSE

For ``no_reply=False``, that completion ``TASK_RESPONSE`` goes from worker to broker and is currently discarded there, because the original sender already received the broker's immediate persistence confirmation.
RPC works the same way: if the subscriber returns a ``Future``, the response is deferred until it resolves.


.. _internal_architecture:broker:broadcast:

Broadcast semantics
===================

Broadcasts are asymmetric between sending and receiving.

Sending goes through the broker: ``broadcast_send()`` sends a single ``BROADCAST`` message, and the broker fans it out to every client identity found in its task and RPC subscriber registries.

Receiving is purely client-local: ``add_broadcast_subscriber()`` sends nothing to the broker.
The communicator just registers the callback and invokes it for any ``BROADCAST`` message that arrives on its DEALER socket.

The catch is that a client only receives broadcasts if the broker knows about it, i.e. if it is registered as a task or RPC subscriber.
That is enough for AiiDA: daemon workers always hold task and RPC subscriptions, and any client running a process holds an RPC subscription for it (registered by plumpy).


Dead worker detection
=====================

Detecting a dead worker takes two steps, because ZeroMQ tells us *that* someone disconnected but not *who*.

The detection itself is built into ZeroMQ.
The ROUTER socket is configured with ``HEARTBEAT_IVL`` and ``HEARTBEAT_TIMEOUT``, so ZeroMQ pings connected peers at the transport level.
When a worker stops responding, ZeroMQ disconnects it internally and emits an ``EVENT_DISCONNECTED`` on the monitor socket we attached to the ROUTER.
That event only carries a file descriptor, though — it does not say which client identity is gone.

Identifying the dead worker is our job.
On each ``EVENT_DISCONNECTED``, ``_handle_disconnect_event`` calls ``_probe_workers``, which sends a ``PING`` to every worker identity that has in-flight tasks.
Because the socket has ``ROUTER_MANDATORY`` set, sending to a dead identity fails immediately with ``EHOSTUNREACH``.
Every worker that fails the probe is removed via ``_remove_dead_worker``, which requeues all its assigned tasks and cleans up the subscriber registries.


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

``ZeromqBrokerService`` manages the broker process lifecycle and writes files that ``ZeromqBroker`` (in worker processes) reads to discover the broker:

.. code-block:: text

    {config_dir}/broker/{profile-uuid}-{profile-name}/      (config_dir is typically ~/.aiida)
    ├── broker.pid         "aiida-zeromq-broker {pid}" — sentinel + PID for ownership check
    ├── broker.status      JSON with task counts, updated every STATUS_INTERVAL seconds
    ├── broker.sockets     path to the temp socket directory
    └── storage/           PersistentQueue data

    /tmp/aiida_zeromq_{random}/
    └── router.sock        IPC socket (temp dir avoids 107-byte Unix path limit)


Known limitations
=================

- The broker is a single process and therefore a single point of failure.
  If it crashes, no tasks are dispatched until circus restarts it; tasks in the persistent queue survive the crash.
- IPC sockets do not work across machines, so the broker only serves workers on the same host.
  For distributed setups, use RabbitMQ.
- There is no message TTL: tasks stay in the queue indefinitely until consumed or manually cleared.
- There is no dead letter queue: NACKed tasks are requeued to the front of the queue, and a task that keeps failing keeps coming back.
- A client only receives broadcasts if it holds at least one task or RPC subscription (see :ref:`broadcast semantics <internal_architecture:broker:broadcast>`).
- All traffic — tasks, RPC, broadcasts — shares one ROUTER socket.
  Fine for AiiDA's workload, but it could become a throughput bottleneck under extreme fan-out.


Timeouts
========

.. list-table::
   :header-rows: 1
   :widths: 30 10 60

   * - Constant / option
     - Default
     - Purpose
   * - ``broker.task_timeout`` |br| (``verdi config``)
     - 10s
     - How long a caller waits for a task or RPC response from the broker.
       Fires a ``TimeoutError`` on the pending Future. Replaces the deprecated ``rmq.task_timeout``.
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
     - Server-side poll timeout per iteration. Controls how quickly the broker responds to shutdown signals.
   * - ``STATUS_INTERVAL``
     - 5s
     - How often the broker service writes its status JSON to disk.

Only ``broker.task_timeout`` is user-configurable.
All other values are developer-tunable constants in ``defaults.py``.


.. |br| raw:: html

   <br/>
