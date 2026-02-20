"""ZeroMQ Communicator - client implementing kiwipy Communicator interface."""

from __future__ import annotations

import logging
import threading
import uuid
from concurrent.futures import Future
from typing import Any, Callable

import zmq

from aiida.brokers.utils import YAML_DECODER, YAML_ENCODER

from .defaults import RPC_TIMEOUT
from .protocol import (
    MessageType,
    decode_message,
    encode_message,
    make_broadcast_message,
    make_rpc_message,
    make_rpc_response,
    make_subscribe_message,
    make_task_ack,
    make_task_message,
    make_task_nack,
    make_task_response,
)

_LOGGER = logging.getLogger(__name__)


class ZmqCommunicator:
    """ZMQ client implementing kiwipy Communicator interface.

    Connects to a ZmqBrokerService to send/receive messages.

    Socket architecture:
        DEALER - Connects to broker ROUTER for request-reply
        SUB    - Connects to broker PUB for broadcasts
    """

    def __init__(
        self,
        router_endpoint: str,
        pub_endpoint: str,
        encoder: Callable[[Any], str] | None = None,
        decoder: Callable[[str], Any] | None = None,
        client_id: str | None = None,
    ):
        """Initialize the communicator.

        :param router_endpoint: ZMQ endpoint for ROUTER socket (broker)
        :param pub_endpoint: ZMQ endpoint for PUB socket (broker)
        :param encoder: Function to encode messages
        :param decoder: Function to decode messages
        :param client_id: Optional client identifier
        """
        self._router_endpoint = router_endpoint
        self._pub_endpoint = pub_endpoint
        self._encoder = encoder if encoder is not None else YAML_ENCODER
        self._decoder = decoder if decoder is not None else YAML_DECODER
        self._client_id = client_id or f'client-{uuid.uuid4().hex[:8]}'

        # ZMQ sockets
        self._context: zmq.Context | None = None
        self._dealer: zmq.Socket | None = None
        self._sub: zmq.Socket | None = None
        self._poller: zmq.Poller | None = None

        # Pending futures for responses
        self._pending_futures: dict[str, Future] = {}
        self._futures_lock = threading.Lock()

        # Subscribers
        self._task_subscribers: dict[str, Callable] = {}
        self._rpc_subscribers: dict[str, Callable] = {}
        self._broadcast_subscribers: dict[str, Callable] = {}

        # State
        self._closed = True
        self._poll_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    @property
    def client_id(self) -> str:
        """Return the client identifier."""
        return self._client_id

    def is_closed(self) -> bool:
        """Check if communicator is closed."""
        return self._closed

    def start(self) -> None:
        """Start the communicator.

        Connects to broker and starts background polling thread.
        """
        if not self._closed:
            return

        _LOGGER.info('Starting ZMQ Communicator: %s', self._client_id)

        # Create ZMQ context
        self._context = zmq.Context()

        # DEALER socket for request-reply with broker
        self._dealer = self._context.socket(zmq.DEALER)
        self._dealer.setsockopt_string(zmq.IDENTITY, self._client_id)
        self._dealer.connect(self._router_endpoint)

        # SUB socket for broadcasts
        self._sub = self._context.socket(zmq.SUB)
        self._sub.connect(self._pub_endpoint)
        self._sub.setsockopt_string(zmq.SUBSCRIBE, '')  # Subscribe to all

        # Set up poller
        self._poller = zmq.Poller()
        self._poller.register(self._dealer, zmq.POLLIN)
        self._poller.register(self._sub, zmq.POLLIN)

        self._closed = False
        self._stop_event.clear()

        # Start background polling thread
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

        _LOGGER.info('ZMQ Communicator started')

    def close(self) -> None:
        """Close the communicator.

        Stops polling thread and closes sockets.
        """
        if self._closed:
            return

        _LOGGER.info('Closing ZMQ Communicator: %s', self._client_id)

        self._closed = True
        self._stop_event.set()

        # Wait for poll thread to stop
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2.0)

        # Clean up sockets
        if self._poller:
            if self._dealer:
                self._poller.unregister(self._dealer)
            if self._sub:
                self._poller.unregister(self._sub)
            self._poller = None

        if self._dealer:
            self._dealer.close()
            self._dealer = None

        if self._sub:
            self._sub.close()
            self._sub = None

        if self._context:
            self._context.term()
            self._context = None

        # Cancel pending futures
        with self._futures_lock:
            for future in self._pending_futures.values():
                if not future.done():
                    future.cancel()
            self._pending_futures.clear()

        _LOGGER.info('ZMQ Communicator closed')

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # === Task operations (kiwipy interface) ===

    def task_send(self, task: Any, no_reply: bool = False) -> Future | None:
        """Send a task to the broker for processing.

        :param task: Task payload
        :param no_reply: If True, don't wait for response
        :return: Future for the task result, or None if no_reply=True
        """
        self._ensure_open()

        msg = make_task_message(task, self._client_id, no_reply)
        task_id = msg['id']

        future: Future[Any] | None = None
        if not no_reply:
            future = Future()
            with self._futures_lock:
                self._pending_futures[task_id] = future

        self._send(msg)
        _LOGGER.debug('Sent task: %s', task_id)

        return future

    def add_task_subscriber(self, subscriber: Callable, identifier: str | None = None) -> str:
        """Register as a task subscriber.

        :param subscriber: Callback function(communicator, task) -> result
        :param identifier: Optional subscriber identifier
        :return: The subscriber identifier
        """
        self._ensure_open()

        identifier = identifier or f'task-{uuid.uuid4().hex[:8]}'
        self._task_subscribers[identifier] = subscriber

        # Register with broker
        msg = make_subscribe_message(MessageType.SUBSCRIBE_TASK, self._client_id, identifier)
        self._send(msg)

        _LOGGER.info('Added task subscriber: %s', identifier)
        return identifier

    def remove_task_subscriber(self, identifier: str) -> None:
        """Remove a task subscriber.

        :param identifier: Subscriber identifier
        """
        if identifier in self._task_subscribers:
            del self._task_subscribers[identifier]

            if not self._closed:
                msg = make_subscribe_message(MessageType.UNSUBSCRIBE_TASK, self._client_id, identifier)
                self._send(msg)

            _LOGGER.info('Removed task subscriber: %s', identifier)

    # === RPC operations (kiwipy interface) ===

    def rpc_send(self, recipient_id: str, msg: Any) -> Future:
        """Send an RPC message to a specific recipient.

        :param recipient_id: Target recipient identifier
        :param msg: Message payload
        :return: Future for the RPC result
        """
        self._ensure_open()

        rpc_msg = make_rpc_message(recipient_id, msg, self._client_id)
        rpc_id = rpc_msg['id']

        future: Future[Any] = Future()
        with self._futures_lock:
            self._pending_futures[rpc_id] = future

        self._send(rpc_msg)
        _LOGGER.debug('Sent RPC to %s: %s', recipient_id, rpc_id)

        return future

    def add_rpc_subscriber(self, subscriber: Callable, identifier: str | None = None) -> str:
        """Register as an RPC subscriber.

        :param subscriber: Callback function(communicator, msg) -> result
        :param identifier: Optional subscriber identifier
        :return: The subscriber identifier
        """
        self._ensure_open()

        identifier = identifier or f'rpc-{uuid.uuid4().hex[:8]}'
        self._rpc_subscribers[identifier] = subscriber

        # Register with broker
        msg = make_subscribe_message(MessageType.SUBSCRIBE_RPC, self._client_id, identifier)
        self._send(msg)

        _LOGGER.info('Added RPC subscriber: %s', identifier)
        return identifier

    def remove_rpc_subscriber(self, identifier: str) -> None:
        """Remove an RPC subscriber.

        :param identifier: Subscriber identifier
        """
        if identifier in self._rpc_subscribers:
            del self._rpc_subscribers[identifier]

            if not self._closed:
                msg = make_subscribe_message(MessageType.UNSUBSCRIBE_RPC, self._client_id, identifier)
                self._send(msg)

            _LOGGER.info('Removed RPC subscriber: %s', identifier)

    # === Broadcast operations (kiwipy interface) ===

    def broadcast_send(
        self,
        body: Any,
        sender: str | None = None,
        subject: str | None = None,
        correlation_id: str | None = None,
    ) -> bool:
        """Send a broadcast message.

        :param body: Message body
        :param sender: Optional sender identifier
        :param subject: Optional message subject
        :param correlation_id: Optional correlation ID
        :return: True if sent successfully
        """
        self._ensure_open()

        msg = make_broadcast_message(
            body,
            sender or self._client_id,
            subject,
            correlation_id,
        )
        self._send(msg)
        _LOGGER.debug('Sent broadcast: %s', subject)
        return True

    def add_broadcast_subscriber(
        self,
        subscriber: Callable,
        identifier: str | None = None,
    ) -> str:
        """Register as a broadcast subscriber.

        :param subscriber: Callback function(communicator, body, sender, subject, correlation_id)
        :param identifier: Optional subscriber identifier
        :return: The subscriber identifier
        """
        identifier = identifier or f'broadcast-{uuid.uuid4().hex[:8]}'
        self._broadcast_subscribers[identifier] = subscriber
        _LOGGER.info('Added broadcast subscriber: %s', identifier)
        return identifier

    def remove_broadcast_subscriber(self, identifier: str) -> None:
        """Remove a broadcast subscriber.

        :param identifier: Subscriber identifier
        """
        if identifier in self._broadcast_subscribers:
            del self._broadcast_subscribers[identifier]
            _LOGGER.info('Removed broadcast subscriber: %s', identifier)

    # === Internal methods ===

    def _ensure_open(self) -> None:
        """Ensure communicator is open."""
        if self._closed:
            raise RuntimeError('Communicator is closed')

    def _send(self, msg: dict) -> None:
        """Send a message to the broker."""
        if not self._dealer:
            raise RuntimeError('Communicator not connected')

        encoded = encode_message(msg, self._encoder)
        self._dealer.send_multipart([b'', encoded])

    def _poll_loop(self) -> None:
        """Background thread polling for messages."""
        _LOGGER.debug('Poll loop started')

        while not self._stop_event.is_set() and not self._closed:
            try:
                if not self._poller:
                    break

                socks = dict(self._poller.poll(100))  # 100ms timeout

                if self._dealer in socks:
                    self._handle_dealer_message()

                if self._sub in socks:
                    self._handle_sub_message()

            except zmq.ZMQError as exc:
                if not self._closed:
                    _LOGGER.error('ZMQ error in poll loop: %s', exc)
                break
            except Exception as exc:
                _LOGGER.exception('Error in poll loop: %s', exc)

        _LOGGER.debug('Poll loop stopped')

    def _handle_dealer_message(self) -> None:
        """Handle message from DEALER socket."""
        if not self._dealer:
            return

        frames = self._dealer.recv_multipart()
        # Skip empty delimiter
        msg_frame = frames[1] if len(frames) > 1 and frames[0] == b'' else frames[0]

        msg = decode_message(msg_frame, self._decoder)
        msg_type = msg.get('type')

        _LOGGER.debug('Received from broker: %s', msg_type)

        if msg_type == MessageType.TASK.value:
            self._handle_task(msg)
        elif msg_type == MessageType.TASK_RESPONSE.value:
            self._handle_task_response(msg)
        elif msg_type == MessageType.RPC.value:
            self._handle_rpc(msg)
        elif msg_type == MessageType.RPC_RESPONSE.value:
            self._handle_rpc_response(msg)
        else:
            _LOGGER.warning('Unknown message type from broker: %s', msg_type)

    def _handle_sub_message(self) -> None:
        """Handle message from SUB socket (broadcasts)."""
        if not self._sub:
            return

        data = self._sub.recv()
        msg = decode_message(data, self._decoder)

        if msg.get('type') == MessageType.BROADCAST.value:
            self._handle_broadcast(msg)

    def _handle_task(self, msg: dict) -> None:
        """Handle incoming task from broker."""
        task_id = msg['id']
        body = msg.get('body')
        no_reply = msg.get('no_reply', False)

        _LOGGER.debug('Handling task: %s', task_id)

        # Find a subscriber to handle the task
        for identifier, subscriber in self._task_subscribers.items():
            try:
                result = subscriber(self, body)

                # Send acknowledgment
                ack_msg = make_task_ack(task_id, self._client_id)
                self._send(ack_msg)

                # Send response if expected
                if not no_reply:
                    response = make_task_response(task_id, self._client_id, result=result)
                    self._send(response)

                _LOGGER.debug('Task completed: %s', task_id)
                return

            except Exception as exc:
                _LOGGER.exception('Task subscriber %s failed: %s', identifier, exc)
                # Try next subscriber

        # No subscriber handled the task, nack it
        _LOGGER.warning('No subscriber handled task: %s', task_id)
        nack_msg = make_task_nack(task_id, self._client_id)
        self._send(nack_msg)

    def _handle_task_response(self, msg: dict) -> None:
        """Handle task response from broker."""
        task_id = msg.get('task_id')
        if not task_id:
            return

        with self._futures_lock:
            future = self._pending_futures.pop(task_id, None)

        if future and not future.done():
            error = msg.get('error')
            if error:
                future.set_exception(Exception(error))
            else:
                future.set_result(msg.get('result'))

    def _handle_rpc(self, msg: dict) -> None:
        """Handle incoming RPC from broker."""
        rpc_id = msg['id']
        body = msg.get('body')

        _LOGGER.debug('Handling RPC: %s', rpc_id)

        # Find a subscriber to handle the RPC
        for identifier, subscriber in self._rpc_subscribers.items():
            try:
                result = subscriber(self, body)

                # Resolve Future before serializing: plumpy subscribers
                # return a kiwipy.Future (concurrent.futures.Future) whose
                # result is computed on the runner's event loop thread.
                if isinstance(result, Future):
                    result = result.result(timeout=RPC_TIMEOUT)

                # Send response
                response = make_rpc_response(rpc_id, self._client_id, result=result)
                self._send(response)

                _LOGGER.debug('RPC completed: %s', rpc_id)
                return

            except Exception as exc:
                _LOGGER.exception('RPC subscriber %s failed: %s', identifier, exc)
                response = make_rpc_response(rpc_id, self._client_id, error=str(exc))
                self._send(response)
                return

        # No subscriber handled the RPC
        _LOGGER.warning('No subscriber handled RPC: %s', rpc_id)
        response = make_rpc_response(rpc_id, self._client_id, error='No handler registered')
        self._send(response)

    def _handle_rpc_response(self, msg: dict) -> None:
        """Handle RPC response from broker."""
        rpc_id = msg.get('rpc_id')
        if not rpc_id:
            return

        with self._futures_lock:
            future = self._pending_futures.pop(rpc_id, None)

        if future and not future.done():
            error = msg.get('error')
            if error:
                future.set_exception(Exception(error))
            else:
                future.set_result(msg.get('result'))

    def _handle_broadcast(self, msg: dict) -> None:
        """Handle broadcast message."""
        body = msg.get('body')
        sender = msg.get('sender')
        subject = msg.get('subject')
        correlation_id = msg.get('correlation_id')

        for identifier, subscriber in self._broadcast_subscribers.items():
            try:
                subscriber(self, body, sender, subject, correlation_id)
            except Exception as exc:
                _LOGGER.exception('Broadcast subscriber %s failed: %s', identifier, exc)
