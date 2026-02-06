"""ZeroMQ Broker Server - standalone message broker.

This module is completely independent of AiiDA and can be used as a standalone
message broker server. It handles:
- Task queue management with persistence
- Request/reply routing for RPC
- Broadcast distribution
"""

from __future__ import annotations

import json
import logging
import threading
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

    Uses ROUTER socket for request-reply routing and PUB socket for broadcasts.

    The server maintains:
    - A persistent task queue for reliable task delivery
    - RPC subscriber registry for routing RPC calls
    - Task subscriber registry for distributing tasks

    Socket architecture:
        ROUTER (frontend) - Receives all client messages, routes replies
        PUB (broadcast)   - Publishes broadcast messages to all subscribers
    """

    def __init__(
        self,
        storage_path: Path | str,
        sockets_path: Path | str,
        encoder: Callable[[Any], str] = json.dumps,
        decoder: Callable[[str], Any] = json.loads,
    ):
        """Initialize the broker server.

        :param storage_path: Path for task queue persistence
        :param sockets_path: Path for IPC socket files
        :param encoder: Function to encode messages to JSON string
        :param decoder: Function to decode JSON string to messages
        """
        self._storage_path = Path(storage_path)
        self._sockets_path = Path(sockets_path)

        # Ensure directories exist
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._sockets_path.mkdir(parents=True, exist_ok=True)

        # Derive endpoints from sockets_path
        self._router_endpoint = f'ipc://{self._sockets_path}/router.sock'
        self._pub_endpoint = f'ipc://{self._sockets_path}/pub.sock'

        self._encoder = encoder
        self._decoder = decoder

        # ZMQ context and sockets
        self._context: zmq.Context | None = None
        self._router: zmq.Socket | None = None
        self._pub: zmq.Socket | None = None
        self._poller: zmq.Poller | None = None

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

        # Server state
        self._running = False
        self._lock = threading.Lock()

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
    def pub_endpoint(self) -> str:
        """Return the PUB socket endpoint."""
        return self._pub_endpoint

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
        _LOGGER.info('PUB endpoint: %s', self._pub_endpoint)

        # Create ZMQ context
        self._context = zmq.Context()

        # ROUTER socket for request-reply
        self._router = self._context.socket(zmq.ROUTER)
        self._router.bind(self._router_endpoint)

        # PUB socket for broadcasts
        self._pub = self._context.socket(zmq.PUB)
        self._pub.bind(self._pub_endpoint)

        # Set up poller
        self._poller = zmq.Poller()
        self._poller.register(self._router, zmq.POLLIN)

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
            self._poller.unregister(self._router)
            self._poller = None

        if self._router:
            self._router.close()
            self._router = None

        if self._pub:
            self._pub.close()
            self._pub = None

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

        if self._router in socks:
            self._handle_router_message()
            return True

        # Try to dispatch pending tasks to available workers
        self._dispatch_pending_tasks()
        return False

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

            # Route by message type
            handlers: dict[str, Any] = {
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

            handler = handlers.get(msg_type)
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

        # Find recipient identity
        recipient_identity = self._rpc_subscribers.get(recipient)
        if not recipient_identity:
            _LOGGER.warning('RPC recipient not found: %s', recipient)
            self._send_rpc_error(identity, rpc_id, f'Recipient not found: {recipient}')
            return

        # Track pending response
        self._pending_rpc_responses[rpc_id] = (identity, time.time())

        # Forward to recipient
        self._send_to_client(recipient_identity, msg)

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

        Publish to all subscribers via PUB socket.
        """
        if not self._pub:
            return

        # Publish on PUB socket
        encoded = encode_message(msg, self._encoder)
        self._pub.send(encoded)
        _LOGGER.debug('Broadcast sent: %s', msg.get('subject', 'no subject'))

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
            self._send_to_client(worker_identity, task_msg)
            _LOGGER.debug('Dispatched task %s to worker', task_id)

    def _mark_worker_available(self, identity: bytes) -> None:
        """Mark a worker as available for tasks."""
        if identity not in self._available_workers:
            self._available_workers.append(identity)

    def _send_to_client(self, identity: bytes, msg: dict) -> None:
        """Send a message to a specific client."""
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
