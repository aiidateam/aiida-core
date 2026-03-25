"""ZeroMQ Broker Server.

Can be started as a standalone message broker process. It handles:
- Task queue management with persistence
- Request/reply routing for RPC
- Broadcast distribution
"""

from __future__ import annotations

import json
import logging
import time
from collections import deque
from pathlib import Path
from typing import Any, Callable

import zmq

from .protocol import MessageType, decode_message, encode_message
from .queue import PersistentQueue

_LOGGER = logging.getLogger(__name__)


class ZmqBrokerServer:
    """Standalone ZMQ message broker server.

    Uses a single ROUTER socket for all communication (tasks, RPC, broadcasts).

    The server maintains:
    - A persistent task queue for reliable task delivery
    - RPC subscriber registry for routing RPC calls
    - Task subscriber registry for distributing tasks

    Socket architecture:
        ROUTER - Receives all client messages, routes replies and broadcasts
    """

    def __init__(
        self,
        storage_path: Path | str,
        sockets_path: Path | str,
        encoder: Callable[[Any], str] | None = None,
        decoder: Callable[[str], Any] | None = None,
    ):
        """Initialize the broker server.

        :param storage_path: Path for task queue persistence
        :param sockets_path: Path for IPC socket files
        :param encoder: Function to encode messages (default: yaml.dump)
        :param decoder: Function to decode messages (default: yaml.load)
        """
        encoder = encoder if encoder is not None else json.dumps
        decoder = decoder if decoder is not None else json.loads
        self._storage_path = Path(storage_path)
        self._sockets_path = Path(sockets_path)

        # Ensure directories exist
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._sockets_path.mkdir(parents=True, exist_ok=True)

        # Derive endpoint from sockets_path
        self._router_endpoint = f'ipc://{self._sockets_path}/router.sock'

        self._encoder = encoder
        self._decoder = decoder

        # ZMQ context and sockets
        self._context: zmq.Context | None = None
        self._router: zmq.Socket | None = None
        self._poller: zmq.Poller | None = None
        self._monitor: zmq.Socket | None = None

        # Task queue with persistence
        self._task_queue = PersistentQueue(self._storage_path / 'tasks')

        # Subscriber registries
        # task_subscribers: identifier -> client_identity (bytes)
        self._task_subscribers: dict[str, bytes] = {}
        # Available task workers (ready to receive tasks)
        self._available_workers: deque[bytes] = deque()
        # rpc_subscribers: identifier -> client_identity (bytes)
        self._rpc_subscribers: dict[str, bytes] = {}

        # Pending responses: correlation_id -> (client_identity, timestamp)
        self._pending_task_responses: dict[str, tuple[bytes, float]] = {}
        self._pending_rpc_responses: dict[str, tuple[bytes, float]] = {}

        # Task-worker assignments: task_id -> worker_identity
        # Used to requeue tasks when a worker dies
        self._task_worker_assignments: dict[str, bytes] = {}

        # Server state
        self._running = False

        # Message type -> handler mapping (built once, not per message)
        self._handlers: dict[str, Callable] = {
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

        _LOGGER.info('Starting ZMQ Broker Server')
        _LOGGER.info('Storage path: %s', self._storage_path)
        _LOGGER.info('ROUTER endpoint: %s', self._router_endpoint)

        # Create ZMQ context
        self._context = zmq.Context()

        # ROUTER socket for request-reply
        self._router = self._context.socket(zmq.ROUTER)
        self._router.setsockopt(zmq.ROUTER_MANDATORY, 1)
        # ZMTP heartbeats for dead peer detection
        self._router.setsockopt(zmq.HEARTBEAT_IVL, 2000)      # ping every 2s
        self._router.setsockopt(zmq.HEARTBEAT_TIMEOUT, 6000)   # dead after 6s no response
        self._router.bind(self._router_endpoint)

        # Set up poller
        self._poller = zmq.Poller()
        self._poller.register(self._router, zmq.POLLIN)

        # Monitor for disconnect events (dead peer detection)
        self._monitor = self._router.get_monitor_socket(zmq.EVENT_DISCONNECTED)
        self._poller.register(self._monitor, zmq.POLLIN)

        self._running = True
        _LOGGER.info('ZMQ Broker Server started')

    def stop(self) -> None:
        """Stop the broker server.

        Closes sockets and cleans up resources.
        """
        if not self._running:
            return

        _LOGGER.info('Stopping ZMQ Broker Server')
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

        _LOGGER.info('ZMQ Broker Server stopped')

    def run_forever(self, poll_timeout: int = 1000) -> None:
        """Run the broker event loop.

        Blocks until stop() is called or interrupted.

        :param poll_timeout: Polling timeout in milliseconds
        """
        self.start()

        try:
            while self._running:
                self._poll_once(poll_timeout)
        finally:
            self.stop()

    def run_once(self, timeout: int = 0) -> bool:
        """Process a single message if available.

        :param timeout: Timeout in milliseconds (0 = non-blocking)
        :return: True if a message was processed
        """
        if not self._running:
            return False
        return self._poll_once(timeout)

    def _poll_once(self, timeout: int) -> bool:
        """Poll for messages and handle one if available."""
        if not self._poller:
            return False

        try:
            socks = dict(self._poller.poll(timeout))
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

            msg = decode_message(msg_frame, self._decoder)
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

    def _handle_task(self, identity: bytes, msg: dict) -> None:
        """Handle incoming task message.

        Queue the task and try to dispatch to an available worker.
        """
        task_id = msg['id']
        sender = msg.get('sender', '')
        no_reply = msg.get('no_reply', False)

        # Store task in persistent queue
        task_data = {
            'id': task_id,
            'sender': sender,
            'sender_identity': identity.hex(),
            'body': msg.get('body'),
            'no_reply': no_reply,
            'timestamp': time.time(),
        }
        self._task_queue.push(task_id, task_data)

        # Track pending response if reply expected
        if not no_reply:
            self._pending_task_responses[task_id] = (identity, time.time())

        # Try to dispatch immediately
        self._dispatch_pending_tasks()

    def _handle_task_response(self, identity: bytes, msg: dict) -> None:
        """Handle task response from worker.

        Route the response back to the original task sender.
        """
        task_id = msg.get('task_id')
        if not task_id:
            _LOGGER.warning('Task response missing task_id')
            return

        # Find original sender
        pending = self._pending_task_responses.pop(task_id, None)
        if not pending:
            _LOGGER.warning('No pending response for task: %s', task_id)
            return

        original_sender, _ = pending

        # Forward response to original sender
        self._send_to_client(original_sender, msg)

    def _handle_task_ack(self, identity: bytes, msg: dict) -> None:
        """Handle task acknowledgment from worker."""
        task_id = msg.get('task_id')
        if task_id:
            self._task_queue.ack(task_id)
            self._task_worker_assignments.pop(task_id, None)
            _LOGGER.debug('Task acknowledged: %s', task_id)

        # Worker is available for more tasks
        self._mark_worker_available(identity)

    def _handle_task_nack(self, identity: bytes, msg: dict) -> None:
        """Handle task negative acknowledgment from worker."""
        task_id = msg.get('task_id')
        if task_id:
            self._task_queue.nack(task_id, requeue=True)
            _LOGGER.debug('Task nacked and requeued: %s', task_id)

        # Worker is available for more tasks
        self._mark_worker_available(identity)

    def _handle_rpc(self, identity: bytes, msg: dict) -> None:
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

    def _handle_rpc_response(self, identity: bytes, msg: dict) -> None:
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

    def _handle_broadcast(self, identity: bytes, msg: dict) -> None:
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

    def _handle_subscribe_task(self, identity: bytes, msg: dict) -> None:
        """Handle task subscriber registration."""
        identifier = msg.get('identifier') or msg.get('sender')
        if not identifier:
            _LOGGER.warning('Task subscription missing identifier')
            return

        self._task_subscribers[identifier] = identity
        self._mark_worker_available(identity)
        _LOGGER.info('Task subscriber registered: %s', identifier)

        # Try to dispatch any pending tasks
        self._dispatch_pending_tasks()

    def _handle_subscribe_rpc(self, identity: bytes, msg: dict) -> None:
        """Handle RPC subscriber registration."""
        identifier = msg.get('identifier') or msg.get('sender')
        if not identifier:
            _LOGGER.warning('RPC subscription missing identifier')
            return

        self._rpc_subscribers[identifier] = identity
        _LOGGER.info('RPC subscriber registered: %s', identifier)

    def _handle_unsubscribe_task(self, identity: bytes, msg: dict) -> None:
        """Handle task subscriber removal."""
        identifier = msg.get('identifier') or msg.get('sender')
        if identifier and identifier in self._task_subscribers:
            del self._task_subscribers[identifier]
            _LOGGER.info('Task subscriber removed: %s', identifier)

    def _handle_unsubscribe_rpc(self, identity: bytes, msg: dict) -> None:
        """Handle RPC subscriber removal."""
        identifier = msg.get('identifier') or msg.get('sender')
        if identifier and identifier in self._rpc_subscribers:
            del self._rpc_subscribers[identifier]
            _LOGGER.info('RPC subscriber removed: %s', identifier)

    def _dispatch_pending_tasks(self) -> None:
        """Dispatch pending tasks to available workers."""
        while self._available_workers and not self._task_queue.is_empty():
            worker_identity = self._available_workers.popleft()

            # Verify worker is still subscribed
            if worker_identity not in self._task_subscribers.values():
                continue

            # Get next task
            result = self._task_queue.pop()
            if not result:
                self._available_workers.appendleft(worker_identity)
                break

            task_id, task_data = result

            # Send task to worker
            task_msg = {
                'type': MessageType.TASK.value,
                'id': task_id,
                'body': task_data.get('body'),
                'no_reply': task_data.get('no_reply', False),
            }
            try:
                self._send_to_client(worker_identity, task_msg)
            except zmq.ZMQError:
                # Worker disconnected — requeue the task and remove the
                # dead worker so we don't keep trying to reach it.
                _LOGGER.warning('Worker %s disconnected, requeuing task %s', worker_identity.hex()[:8], task_id)
                self._task_queue.nack(task_id, requeue=True)
                self._remove_dead_worker(worker_identity)
                continue
            self._task_worker_assignments[task_id] = worker_identity
            # Re-add worker so it can receive more tasks concurrently
            # (matching RMQ's multi-prefetch behaviour).  The ACK only
            # affects the PersistentQueue, not worker availability.
            self._mark_worker_available(worker_identity)
            _LOGGER.debug('Dispatched task %s to worker', task_id)

    def _remove_dead_worker(self, identity: bytes) -> None:
        """Remove a disconnected worker from all registries and requeue its tasks."""
        # Requeue all tasks assigned to this worker
        dead_tasks = [tid for tid, wid in self._task_worker_assignments.items() if wid == identity]
        for task_id in dead_tasks:
            self._task_worker_assignments.pop(task_id, None)
            self._task_queue.nack(task_id, requeue=True)
            _LOGGER.warning('Requeued task %s from dead worker %s', task_id, identity.hex()[:8])

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
        ZMQError(EHOSTUNREACH), identifying the dead worker.
        """
        if not self._task_worker_assignments:
            return

        from .protocol import make_ping

        # Get unique worker identities with assigned tasks
        worker_identities = set(self._task_worker_assignments.values())

        for identity in worker_identities:
            try:
                ping_msg = make_ping('broker')
                self._send_to_client(identity, ping_msg)
            except zmq.ZMQError:
                _LOGGER.warning('Worker %s is dead, removing', identity.hex()[:8])
                self._remove_dead_worker(identity)

    def _mark_worker_available(self, identity: bytes) -> None:
        """Mark a worker as available for tasks."""
        if identity not in self._available_workers:
            self._available_workers.append(identity)

    def _send_to_client(self, identity: bytes, msg: dict) -> None:
        """Send a message to a specific client.

        :raises zmq.ZMQError: If the client is disconnected (ROUTER_MANDATORY).
        """
        if not self._router:
            return

        encoded = encode_message(msg, self._encoder)
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

    def get_status(self) -> dict:
        """Get current broker status."""
        return {
            'running': self._running,
            'pending_tasks': self._task_queue.size(),
            'processing_tasks': self._task_queue.processing_count(),
            'task_subscribers': len(self._task_subscribers),
            'rpc_subscribers': len(self._rpc_subscribers),
            'available_workers': len(self._available_workers),
            'pending_task_responses': len(self._pending_task_responses),
            'pending_rpc_responses': len(self._pending_rpc_responses),
        }

    def get_pending_tasks(self) -> list[tuple[str, dict]]:
        """Get all pending tasks."""
        return self._task_queue.get_all_pending()

    def get_processing_tasks(self) -> list[tuple[str, dict]]:
        """Get all tasks currently being processed."""
        return self._task_queue.get_all_processing()
