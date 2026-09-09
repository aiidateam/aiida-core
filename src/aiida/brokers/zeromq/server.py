###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""ZeroMQ Broker Server.

Can be started as a standalone message broker process. It handles:
- Task queue management with persistence
- Request/reply routing for RPC
- Broadcast distribution
"""

from __future__ import annotations

import logging
import time
from collections import deque
from collections.abc import Callable
from pathlib import Path
from typing import Any

import zmq

from aiida.brokers.zeromq.defaults import HEARTBEAT_IVL, HEARTBEAT_TIMEOUT, POLL_TIMEOUT
from aiida.brokers.zeromq.protocol import DEFAULT_TASK_QUEUE, MessageType, decode_message, encode_message
from aiida.brokers.zeromq.queue import PersistentQueue

_LOGGER = logging.getLogger(__name__)


class ZeromqBrokerServer:
    """Standalone ZeroMQ message broker server.

    Uses a single ROUTER socket for all communication (tasks, RPC, broadcasts).

    The server maintains:
    - Named persistent task queues for reliable task delivery
    - RPC subscriber registry for routing RPC calls
    - Task subscriber registry for distributing tasks
    - Per-worker prefetch limits and in flight task counts, which throttle dispatch

    Socket architecture:
        ROUTER - Receives all client messages, routes replies and broadcasts
    """

    def __init__(
        self,
        storage_path: Path | str,
        sockets_path: Path | str,
    ):
        """Initialize the broker server.

        :param storage_path: Path for task queue persistence
        :param sockets_path: Path for IPC socket files

        Note: The server uses JSON for the message envelope. Payload fields (body, result)
        are pre-encoded as YAML strings by the sender and remain opaque to the server.
        """
        self._storage_path = Path(storage_path)
        self._sockets_path = Path(sockets_path)

        # Ensure directories exist
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._sockets_path.mkdir(parents=True, exist_ok=True)

        # Derive endpoint from sockets_path
        self._router_endpoint = f'ipc://{self._sockets_path}/router.sock'

        # ZeroMQ context and sockets
        self._context: zmq.Context | None = None  # type: ignore[type-arg]
        self._router: zmq.Socket | None = None  # type: ignore[type-arg]
        self._poller: zmq.Poller | None = None
        self._monitor: zmq.Socket | None = None  # type: ignore[type-arg]

        # Named persistent task queues. The default queue keeps the legacy
        # ``tasks`` storage directory; additional queues (e.g. a scheduler
        # submission queue) get ``tasks-<name>`` directories on first use.
        self._task_queues: dict[str, PersistentQueue] = {}
        self._task_queue = self._get_queue(DEFAULT_TASK_QUEUE)
        # task_id -> queue name, for routing ACKs/NACKs to the owning queue
        self._task_queue_names: dict[str, str] = {}

        # Subscriber registries
        # task_subscribers: identifier -> client_identity (bytes)
        self._task_subscribers: dict[str, bytes] = {}
        # task_subscription_queues: identifier -> queue name
        self._task_subscription_queues: dict[str, str] = {}
        # worker_queues: client_identity -> subscribed queue names
        self._worker_queues: dict[bytes, set[str]] = {}
        # Available task workers (ready to receive tasks)
        self._available_workers: deque[bytes] = deque()
        # rpc_subscribers: identifier -> client_identity (bytes)
        self._rpc_subscribers: dict[str, bytes] = {}

        # Pending RPC responses: correlation_id -> (client_identity, timestamp)
        self._pending_rpc_responses: dict[str, tuple[bytes, float]] = {}

        # Task-worker assignments: task_id -> worker_identity
        # Used to requeue tasks when a worker dies
        self._task_worker_assignments: dict[str, bytes] = {}

        # Prefetch limit declared by each worker on SUBSCRIBE_TASK (None = unlimited)
        self._worker_prefetch: dict[bytes, int | None] = {}
        # Number of dispatched but not yet acknowledged tasks per worker identity
        self._worker_load: dict[bytes, int] = {}

        # Server state
        self._running = False

        # Message type -> handler mapping (built once, not per message)
        self._handlers: dict[str, Callable[[bytes, dict[str, Any]], None]] = {
            MessageType.TASK.value: self._handle_task,
            MessageType.TASK_RESPONSE.value: self._handle_task_response,
            MessageType.TASK_ACK.value: self._handle_task_ack,
            MessageType.TASK_NACK.value: self._handle_task_nack,
            MessageType.RPC.value: self._handle_rpc,
            MessageType.RPC_RESPONSE.value: self._handle_rpc_response,
            MessageType.BROADCAST.value: self._handle_broadcast,
            MessageType.SUBSCRIBE_TASK.value: self._handle_subscribe_task,
            MessageType.SUBSCRIBE_RPC.value: self._handle_subscribe_rpc,
            MessageType.UNSUBSCRIBE_TASK.value: self._handle_unsubscribe_task,
            MessageType.UNSUBSCRIBE_RPC.value: self._handle_unsubscribe_rpc,
        }

    @property
    def storage_path(self) -> Path:
        """Return the path for task queue storage."""
        return self._storage_path

    @property
    def sockets_path(self) -> Path:
        """Return the path for socket files."""
        return self._sockets_path

    @property
    def router_endpoint(self) -> str:
        """Return the ROUTER socket endpoint."""
        return self._router_endpoint

    @property
    def is_running(self) -> bool:
        """Return whether the server is running."""
        return self._running

    def start(self) -> None:
        """Start the broker server.

        Binds sockets and prepares for message handling.
        """
        if self._running:
            return

        _LOGGER.info('Starting ZeroMQ Broker Server')
        _LOGGER.info('Storage path: %s', self._storage_path)
        _LOGGER.info('ROUTER endpoint: %s', self._router_endpoint)

        # Create ZeroMQ context
        self._context = zmq.Context()

        # ROUTER socket for request-reply
        self._router = self._context.socket(zmq.ROUTER)
        self._router.setsockopt(zmq.ROUTER_MANDATORY, 1)
        # ZMTP heartbeats for dead peer detection
        self._router.setsockopt(zmq.HEARTBEAT_IVL, int(HEARTBEAT_IVL * 1000))
        self._router.setsockopt(zmq.HEARTBEAT_TIMEOUT, int(HEARTBEAT_TIMEOUT * 1000))
        self._router.bind(self._router_endpoint)

        # Set up poller
        self._poller = zmq.Poller()
        self._poller.register(self._router, zmq.POLLIN)

        # Monitor for disconnect events (dead peer detection)
        self._monitor = self._router.get_monitor_socket(zmq.EVENT_DISCONNECTED)
        self._poller.register(self._monitor, zmq.POLLIN)

        self._running = True
        _LOGGER.info('ZeroMQ Broker Server started')

    def stop(self) -> None:
        """Stop the broker server.

        Closes sockets and cleans up resources.
        """
        if not self._running:
            return

        _LOGGER.info('Stopping ZeroMQ Broker Server')
        self._running = False

        if self._poller:
            if self._monitor:
                self._poller.unregister(self._monitor)
            self._poller.unregister(self._router)
            self._poller = None

        if self._monitor:
            self._monitor.close()
            self._monitor = None

        if self._router:
            self._router.setsockopt(zmq.LINGER, 0)
            self._router.close()
            self._router = None

        if self._context:
            self._context.term()
            self._context = None

        _LOGGER.info('ZeroMQ Broker Server stopped')

    def run_forever(self, poll_timeout: float = POLL_TIMEOUT) -> None:
        """Run the broker event loop.

        Blocks until stop() is called or interrupted.

        :param poll_timeout: Polling timeout in seconds.
        """
        self.start()

        try:
            while self._running:
                self._poll_once(poll_timeout)
        finally:
            self.stop()

    def run_once(self, timeout: float = 0) -> bool:
        """Process a single message if available.

        :param timeout: Timeout in seconds (0 = non-blocking).
        :return: True if a message was processed.
        """
        if not self._running:
            return False
        return self._poll_once(timeout)

    def _poll_once(self, timeout: float) -> bool:
        """Poll for messages and handle one if available."""
        if not self._poller:
            return False

        try:
            socks = dict(self._poller.poll(int(timeout * 1000)))
        except zmq.ZMQError:
            return False

        handled = False

        if self._router in socks:
            self._handle_router_message()
            handled = True

        if self._monitor in socks:
            self._handle_disconnect_event()

        # Try to dispatch pending tasks to available workers
        self._dispatch_pending_tasks()
        return handled

    def _handle_router_message(self) -> None:
        """Handle a message from the ROUTER socket."""
        if not self._router:
            return

        try:
            # ROUTER socket prepends identity frame
            frames = self._router.recv_multipart()
            if len(frames) < 2:
                _LOGGER.warning('Invalid message: insufficient frames')
                return

            identity = frames[0]
            # Skip empty delimiter frame if present
            msg_frame = frames[2] if len(frames) > 2 and frames[1] == b'' else frames[1]

            msg = decode_message(msg_frame)
            msg_type: str | None = msg.get('type')

            _LOGGER.debug('Received %s from %s', msg_type, identity.hex()[:8])

            if msg_type is None:
                _LOGGER.warning('Message missing type field')
                return

            handler = self._handlers.get(msg_type)
            if handler:
                handler(identity, msg)
            else:
                _LOGGER.warning('Unknown message type: %s', msg_type)

        except Exception as exc:
            _LOGGER.exception('Error handling router message: %s', exc)

    def _get_queue(self, queue_name: str | None) -> PersistentQueue:
        """Return the persistent queue for a name, creating it on first use.

        :raises ValueError: If the queue name is not a safe directory fragment.
        """
        name = queue_name or DEFAULT_TASK_QUEUE
        if name not in self._task_queues:
            if name != DEFAULT_TASK_QUEUE and (
                not name.replace('-', '').replace('_', '').isalnum() or name.startswith(('-', '_'))
            ):
                msg = f'Invalid task queue name: {name!r}'
                raise ValueError(msg)
            dirname = 'tasks' if name == DEFAULT_TASK_QUEUE else f'tasks-{name}'
            self._task_queues[name] = PersistentQueue(self._storage_path / dirname)
        return self._task_queues[name]

    def _handle_task(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle incoming task message.

        Queue the task on its named queue and try to dispatch to an available
        worker subscribed to that queue.

        When the sender expects a reply (``no_reply=False``), an immediate
        acknowledgment response is sent back as soon as the task is persisted
        to disk.  This mirrors RabbitMQ's publisher-confirm behaviour: the
        caller learns that the broker accepted the task without having to wait
        for a worker to process it.  The worker's eventual result (if any) is
        *not* forwarded back to the original sender — callers like
        ``continue_process`` only need the confirmation, not the outcome.
        """
        task_id = msg['id']
        sender = msg.get('sender', '')
        no_reply = msg.get('no_reply', False)
        queue_name = msg.get('queue') or DEFAULT_TASK_QUEUE

        # Store task in persistent queue
        task_data = {
            'id': task_id,
            'sender': sender,
            'sender_identity': identity.hex(),
            'body': msg.get('body'),
            'no_reply': no_reply,
            'queue': queue_name,
            'timestamp': time.time(),
        }
        try:
            queue = self._get_queue(queue_name)
        except ValueError:
            _LOGGER.warning('Dropping task %s with invalid queue name: %r', task_id, queue_name)
            return
        queue.push(task_id, task_data)
        self._task_queue_names[task_id] = queue_name

        # Send an immediate acknowledgment to the sender so its Future
        # resolves without waiting for a worker (matches RabbitMQ semantics).
        if not no_reply:
            response = {
                'type': MessageType.TASK_RESPONSE.value,
                'task_id': task_id,
                'result': True,
            }
            self._send_to_client(identity, response)

        # Try to dispatch immediately
        self._dispatch_pending_tasks()

    def _handle_task_response(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle task response from worker.

        Since the broker already sends an immediate acknowledgment when a task
        is queued, the worker's result response is simply logged and discarded.
        """
        task_id = msg.get('task_id', '?')
        _LOGGER.debug('Received task response for %s (discarded — sender already acknowledged)', task_id)

    def _handle_task_ack(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle task acknowledgment from worker."""
        task_id = msg.get('task_id')
        if task_id:
            # Verify this worker owns the task
            owner = self._task_worker_assignments.get(task_id)
            if owner != identity:
                _LOGGER.warning(
                    'Worker %s tried to ack task %s owned by another worker',
                    identity.hex()[:8],
                    task_id,
                )
                return
            if not self._settle_task(task_id, requeue=False):
                _LOGGER.warning('Cannot ack task %s: not found on any queue', task_id)
                return
            self._release_task(task_id)
            _LOGGER.debug('Task acknowledged: %s', task_id)

        # Worker has freed a slot and is available for more tasks
        self._mark_worker_available(identity)

    def _handle_task_nack(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle task negative acknowledgment from worker."""
        task_id = msg.get('task_id')
        if task_id:
            # Verify this worker owns the task
            owner = self._task_worker_assignments.get(task_id)
            if owner != identity:
                _LOGGER.warning(
                    'Worker %s tried to nack task %s owned by another worker',
                    identity.hex()[:8],
                    task_id,
                )
                return
            if not self._settle_task(task_id, requeue=True):
                _LOGGER.warning('Cannot nack task %s: not found on any queue', task_id)
                return
            self._release_task(task_id)
            _LOGGER.debug('Task nacked and requeued: %s', task_id)

        # Worker has freed a slot and is available for more tasks
        self._mark_worker_available(identity)

    def _handle_rpc(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle RPC message.

        Route to the specified recipient.
        """
        rpc_id = msg['id']
        recipient = msg.get('recipient')

        if not recipient:
            _LOGGER.warning('RPC message missing recipient')
            self._send_rpc_error(identity, rpc_id, 'Missing recipient')
            return

        # Find recipient identity (convert to string for consistent lookup,
        # since subscribers register with string identifiers)
        recipient_identity = self._rpc_subscribers.get(str(recipient))
        if not recipient_identity:
            _LOGGER.warning('RPC recipient not found: %s', recipient)
            self._send_rpc_error(identity, rpc_id, f'Recipient not found: {recipient}')
            return

        # Track pending response
        self._pending_rpc_responses[rpc_id] = (identity, time.time())

        # Forward to recipient
        try:
            self._send_to_client(recipient_identity, msg)
        except zmq.ZMQError:
            _LOGGER.warning('RPC recipient %s disconnected', recipient)
            self._pending_rpc_responses.pop(rpc_id, None)
            self._remove_dead_worker(recipient_identity)
            self._send_rpc_error(identity, rpc_id, f'Recipient not found: {recipient}')
            return

    def _handle_rpc_response(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle RPC response.

        Route back to original caller.
        """
        rpc_id = msg.get('rpc_id')
        if not rpc_id:
            _LOGGER.warning('RPC response missing rpc_id')
            return

        # Find original sender
        pending = self._pending_rpc_responses.pop(rpc_id, None)
        if not pending:
            _LOGGER.warning('No pending response for RPC: %s', rpc_id)
            return

        original_sender, _ = pending

        # Forward response to original sender
        self._send_to_client(original_sender, msg)

    def _handle_broadcast(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle broadcast message.

        Forward to all connected clients via ROUTER socket.
        Connected clients are derived from the task and RPC subscriber registries.
        """
        # Collect unique client identities from all subscriber registries
        client_identities = set(self._task_subscribers.values()) | set(self._rpc_subscribers.values())

        for client_identity in client_identities:
            try:
                self._send_to_client(client_identity, msg)
            except zmq.ZMQError:
                _LOGGER.warning('Failed to send broadcast to %s', client_identity.hex()[:8])

        _LOGGER.debug('Broadcast sent to %d clients: %s', len(client_identities), msg.get('subject', 'no subject'))

    def _handle_subscribe_task(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle task subscriber registration."""
        identifier = msg.get('identifier') or msg.get('sender')
        if not identifier:
            _LOGGER.warning('Task subscription missing identifier')
            return

        self._task_subscribers[identifier] = identity
        queue_name = msg.get('queue') or DEFAULT_TASK_QUEUE
        self._task_subscription_queues[identifier] = queue_name
        self._worker_queues.setdefault(identity, set()).add(queue_name)
        # The prefetch limit applies to the connection, like AMQP's channel-level
        # ``basic.qos``, so the most recent declaration for this identity wins.
        prefetch = msg.get('prefetch_count')
        self._worker_prefetch[identity] = prefetch if prefetch and prefetch > 0 else None
        self._mark_worker_available(identity)
        _LOGGER.info(
            'Task subscriber registered: %s (queue: %s, prefetch: %s)',
            identifier,
            queue_name,
            self._worker_prefetch[identity],
        )

        # Try to dispatch any pending tasks
        self._dispatch_pending_tasks()

    def _handle_subscribe_rpc(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle RPC subscriber registration."""
        identifier = msg.get('identifier') or msg.get('sender')
        if not identifier:
            _LOGGER.warning('RPC subscription missing identifier')
            return

        self._rpc_subscribers[identifier] = identity
        _LOGGER.info('RPC subscriber registered: %s', identifier)

    def _handle_unsubscribe_task(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle task subscriber removal."""
        identifier = msg.get('identifier') or msg.get('sender')
        if identifier and identifier in self._task_subscribers:
            worker_identity = self._task_subscribers.pop(identifier)
            self._task_subscription_queues.pop(identifier, None)
            # Recompute the connection's queues from its remaining subscriptions
            remaining = {
                self._task_subscription_queues[ident]
                for ident, wid in self._task_subscribers.items()
                if wid == worker_identity
            }
            if remaining:
                self._worker_queues[worker_identity] = remaining
            else:
                self._worker_queues.pop(worker_identity, None)
            # Forget the prefetch limit once the connection has no task subscriptions left
            if worker_identity not in self._task_subscribers.values():
                self._worker_prefetch.pop(worker_identity, None)
            _LOGGER.info('Task subscriber removed: %s', identifier)

    def _handle_unsubscribe_rpc(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Handle RPC subscriber removal."""
        identifier = msg.get('identifier') or msg.get('sender')
        if identifier and identifier in self._rpc_subscribers:
            del self._rpc_subscribers[identifier]
            _LOGGER.info('RPC subscriber removed: %s', identifier)

    def _settle_task(self, task_id: str, *, requeue: bool) -> bool:
        """Ack a task (or requeueing-nack it) on its owning queue.

        The recorded owner is tried first; remaining queues are probed as a
        fallback. The fallback matters after a broker restart (in-flight
        tasks are recovered from disk with an empty owner map) and keeps
        direct queue manipulation working. ``ack``/``nack`` are side-effect
        free on queues that do not hold the task, so probing is safe.

        :return: True if a queue held (and settled) the task.
        """
        names = []
        if (recorded := self._task_queue_names.get(task_id)) is not None:
            names.append(recorded)
        names.extend(name for name in self._task_queues if name not in names)
        for name in names:
            queue = self._task_queues[name]
            settled = queue.nack(task_id, requeue=True) if requeue else queue.ack(task_id)
            if settled:
                if requeue:
                    self._task_queue_names[task_id] = name
                else:
                    self._task_queue_names.pop(task_id, None)
                return True
        return False

    def _find_worker(self, queue_name: str) -> bytes | None:
        """Return an available worker subscribed to a queue, or ``None``.

        Scans the availability deque once, preserving the order of workers
        that cannot take work from this queue.
        """
        for _ in range(len(self._available_workers)):
            worker_identity = self._available_workers.popleft()
            # Verify worker is still subscribed (to anything at all)
            if worker_identity not in self._task_subscribers.values():
                continue
            queues = self._worker_queues.get(worker_identity)
            if queues is None:
                # Subscription predates queue tracking (e.g. registries poked
                # directly in tests): assume the default queue.
                queues = {DEFAULT_TASK_QUEUE}
            if queue_name not in queues:
                self._available_workers.append(worker_identity)
                continue
            # Guard against stale entries for a worker that has since filled up
            if not self._has_capacity(worker_identity):
                self._available_workers.append(worker_identity)
                continue
            return worker_identity
        return None

    def _dispatch_pending_tasks(self) -> None:
        """Dispatch pending tasks to workers subscribed to each queue."""
        # One pass per call is enough: ``_poll_once`` invokes dispatch on
        # every loop iteration, so no queue can starve.
        for queue_name, task_queue in self._task_queues.items():
            while not task_queue.is_empty():
                worker_identity = self._find_worker(queue_name)
                if worker_identity is None:
                    break

                # Get next task
                result = task_queue.pop()
                if not result:
                    self._mark_worker_available(worker_identity)
                    break

                task_id, task_data = result
                self._task_queue_names[task_id] = queue_name

                # Send task to worker
                task_msg = {
                    'type': MessageType.TASK.value,
                    'id': task_id,
                    'body': task_data.get('body'),
                    'no_reply': task_data.get('no_reply', False),
                    'queue': queue_name,
                }
                try:
                    self._send_to_client(worker_identity, task_msg)
                except zmq.ZMQError:
                    # Worker disconnected — requeue the task and remove the
                    # dead worker so we don't keep trying to reach it.
                    _LOGGER.warning('Worker %s disconnected, requeuing task %s', worker_identity.hex()[:8], task_id)
                    task_queue.nack(task_id, requeue=True)
                    self._remove_dead_worker(worker_identity)
                    continue
                self._assign_task(task_id, worker_identity)
                # Re-add the worker so it can receive more tasks concurrently, but
                # only while it stays below its declared prefetch limit (matching
                # RMQ's multi-prefetch behaviour).  The ACK frees the slot again.
                self._mark_worker_available(worker_identity)
                _LOGGER.debug('Dispatched task %s to worker on queue %s', task_id, queue_name)

    def _remove_dead_worker(self, identity: bytes) -> None:
        """Remove a disconnected worker from all registries and requeue its tasks."""
        # Requeue all tasks assigned to this worker
        dead_tasks = [tid for tid, wid in self._task_worker_assignments.items() if wid == identity]
        for task_id in dead_tasks:
            self._release_task(task_id)
            self._settle_task(task_id, requeue=True)
            _LOGGER.warning('Requeued task %s from dead worker %s', task_id, identity.hex()[:8])

        self._worker_prefetch.pop(identity, None)
        self._worker_load.pop(identity, None)
        self._worker_queues.pop(identity, None)

        # Remove from task subscribers
        dead_keys = [k for k, v in self._task_subscribers.items() if v == identity]
        for key in dead_keys:
            del self._task_subscribers[key]
            _LOGGER.info('Removed dead task subscriber: %s', key)

        # Remove from RPC subscribers
        dead_keys = [k for k, v in self._rpc_subscribers.items() if v == identity]
        for key in dead_keys:
            del self._rpc_subscribers[key]
            _LOGGER.info('Removed dead RPC subscriber: %s', key)

        # Remove from available workers
        self._available_workers = deque(w for w in self._available_workers if w != identity)

    def _handle_disconnect_event(self) -> None:
        """Handle a disconnect event from the socket monitor.

        ZMTP heartbeat detected a dead peer. We don't know which identity
        disconnected (monitor only provides endpoint/fd), so we probe all
        workers with in-progress tasks to find the dead one.
        """
        if not self._monitor:
            return

        # Read and discard the monitor event
        try:
            from zmq.utils.monitor import recv_monitor_message

            recv_monitor_message(self._monitor)
        except Exception:
            return

        _LOGGER.info('Disconnect event detected, probing workers')
        self._probe_workers()

    def _probe_workers(self) -> None:
        """Probe workers with in-progress tasks to find dead ones.

        Sends a PING to each worker identity that has tasks assigned.
        With ROUTER_MANDATORY, sending to a dead identity raises
        a socket error with ``EHOSTUNREACH``, identifying the dead worker.
        """
        if not self._task_worker_assignments:
            return

        from aiida.brokers.zeromq.protocol import make_ping

        # Get unique worker identities with assigned tasks
        worker_identities = set(self._task_worker_assignments.values())

        for identity in worker_identities:
            try:
                ping_msg = make_ping('broker')
                self._send_to_client(identity, ping_msg)
            except zmq.ZMQError:
                _LOGGER.warning('Worker %s is dead, removing', identity.hex()[:8])
                self._remove_dead_worker(identity)

    def _assign_task(self, task_id: str, identity: bytes) -> None:
        """Record a task as in flight on a worker, occupying one of its slots."""
        if task_id in self._task_worker_assignments:
            _LOGGER.warning('Task %s already assigned to worker, skipping', task_id)
            return
        self._task_worker_assignments[task_id] = identity
        self._worker_load[identity] = self._worker_load.get(identity, 0) + 1

    def _release_task(self, task_id: str) -> None:
        """Drop a task's worker assignment, freeing the slot it occupied."""
        identity = self._task_worker_assignments.pop(task_id, None)
        if identity is None:
            _LOGGER.debug('Tried to release task %s but it was not assigned', task_id)
            return

        remaining = self._worker_load.get(identity, 0) - 1
        if remaining > 0:
            self._worker_load[identity] = remaining
        else:
            self._worker_load.pop(identity, None)

    def _has_capacity(self, identity: bytes) -> bool:
        """Return whether a worker has a free slot for another task.

        This is the equivalent of AMQP's ``basic.qos``: a worker declares a
        prefetch count when it subscribes and is only handed further tasks while
        its dispatched-but-unacknowledged count stays below it. A
        worker that declared no limit is always considered to have capacity.
        """
        prefetch = self._worker_prefetch.get(identity)
        if prefetch is None:
            return True
        return self._worker_load.get(identity, 0) < prefetch

    def _mark_worker_available(self, identity: bytes) -> None:
        """Mark a worker as available for tasks, unless it is at its prefetch limit."""
        if not self._has_capacity(identity):
            return
        if identity not in self._available_workers:
            self._available_workers.append(identity)

    def _send_to_client(self, identity: bytes, msg: dict[str, Any]) -> None:
        """Send a message to a specific client.

        :raises zmq.ZMQError: If the client is disconnected (ROUTER_MANDATORY).
        """
        if not self._router:
            return

        encoded = encode_message(msg)
        self._router.send_multipart([identity, b'', encoded])

    def _send_rpc_error(self, identity: bytes, rpc_id: str, error: str) -> None:
        """Send an RPC error response."""
        error_msg = {
            'type': MessageType.RPC_RESPONSE.value,
            'rpc_id': rpc_id,
            'error': error,
        }
        self._send_to_client(identity, error_msg)

    # === Status and monitoring ===

    def get_status(self) -> dict[str, Any]:
        """Get current broker status."""
        return {
            'running': self._running,
            'pending_tasks': sum(queue.size() for queue in self._task_queues.values()),
            'processing_tasks': sum(queue.processing_count() for queue in self._task_queues.values()),
            'task_subscribers': len(self._task_subscribers),
            'rpc_subscribers': len(self._rpc_subscribers),
            'available_workers': len(self._available_workers),
            'in_flight_tasks': len(self._task_worker_assignments),
            'pending_rpc_responses': len(self._pending_rpc_responses),
            'task_queues': sorted(self._task_queues),
        }

    def get_pending_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all pending tasks across all queues."""
        return [task for queue in self._task_queues.values() for task in queue.get_all_pending()]

    def get_processing_tasks(self) -> list[tuple[str, dict[str, Any]]]:
        """Get all tasks currently being processed across all queues."""
        return [task for queue in self._task_queues.values() for task in queue.get_all_processing()]
