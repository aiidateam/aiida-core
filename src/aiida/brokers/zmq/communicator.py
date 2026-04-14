"""ZeroMQ Communicator - client implementing kiwipy Communicator interface.

Uses an internal asyncio event loop on a background thread for all ZMQ I/O.
Public methods schedule work onto the loop via ``call_soon_threadsafe``,
eliminating the need for locks around shared state.  This follows the same
pattern as kiwipy's ``RmqThreadCommunicator``.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from concurrent.futures import Future
from types import TracebackType
from typing import Any, Callable, TypeVar

import kiwipy
import zmq
import zmq.asyncio

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
_T = TypeVar('_T')

# Timeout (seconds) for scheduling work onto the event loop from the main
# thread.  If the loop is blocked or dead for longer than this, callers get
# a TimeoutError.
_LOOP_TIMEOUT = 5.0


class ZmqCommunicator(kiwipy.Communicator):  # type: ignore[misc]
    """ZMQ client implementing kiwipy Communicator interface.

    Connects to a ZmqBrokerService to send/receive messages.

    Socket architecture:
        DEALER - Connects to broker ROUTER for all communication
                 (tasks, RPC, broadcasts)

    Threading model:
        A private asyncio event loop runs on a dedicated background thread.
        All ZMQ socket I/O and mutable-state access happen exclusively on
        that loop, so no locks are needed.  Public methods schedule work
        onto the loop and block until the result is ready.
    """

    def __init__(
        self,
        router_endpoint: str,
        client_id: str | None = None,
    ):
        self._router_endpoint = router_endpoint
        self._client_id = client_id or f'client-{uuid.uuid4().hex[:8]}'

        # ZMQ sockets (created on the event loop thread)
        self._context: zmq.asyncio.Context | None = None
        self._dealer: zmq.asyncio.Socket | None = None

        # Pending futures for responses (only accessed from the loop thread)
        self._pending_futures: dict[str, Future[Any]] = {}

        # Subscribers (only accessed from the loop thread)
        self._task_subscribers: dict[str, Callable[..., Any]] = {}
        self._rpc_subscribers: dict[str, Callable[..., Any]] = {}
        self._broadcast_subscribers: dict[str, Callable[..., Any]] = {}

        # Tasks in progress: task_id -> (Future, no_reply).  We delay the
        # ACK until the Future resolves so the broker can redeliver if we die.
        self._in_progress_tasks: dict[str, tuple[Future[Any], bool]] = {}

        # RPCs in progress: rpc_id -> (recipient, Future).
        self._in_progress_rpcs: dict[str, tuple[str, Future[Any]]] = {}

        # Event loop thread
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._dealer_poll_task: asyncio.Task[None] | None = None

        self._closed = True

    @property
    def client_id(self) -> str:
        return self._client_id

    def is_closed(self) -> bool:
        return self._closed

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the communicator.

        Creates a background thread running an asyncio event loop, connects
        ZMQ sockets, and starts polling coroutines.
        """
        if not self._closed:
            return

        _LOGGER.info('Starting ZMQ Communicator: %s', self._client_id)

        self._loop = asyncio.new_event_loop()
        ready: Future[bool] = Future()

        self._loop_thread = threading.Thread(target=self._run_loop, args=(ready,), daemon=True)
        self._loop_thread.start()

        # Block until the loop thread has set up sockets and is polling.
        ready.result(timeout=_LOOP_TIMEOUT)
        _LOGGER.info('ZMQ Communicator started')

    def _run_loop(self, ready: Future[bool]) -> None:
        """Entry point for the background thread."""
        assert self._loop is not None
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_start(ready))
            self._loop.run_forever()
        except Exception:
            _LOGGER.exception('Event loop crashed')
            if not ready.done():
                ready.set_exception(RuntimeError('Event loop failed to start'))
        finally:
            self._loop.run_until_complete(self._async_cleanup())
            self._loop.close()
            asyncio.set_event_loop(None)

    async def _async_start(self, ready: Future[bool]) -> None:
        """Set up sockets and start polling (runs on the loop thread)."""
        self._context = zmq.asyncio.Context()

        self._dealer = self._context.socket(zmq.DEALER)
        self._dealer.setsockopt_string(zmq.IDENTITY, self._client_id)
        self._dealer.connect(self._router_endpoint)

        self._closed = False

        self._dealer_poll_task = asyncio.ensure_future(self._poll_dealer())

        ready.set_result(True)

    async def _async_cleanup(self) -> None:
        """Close sockets and context (runs on the loop thread)."""
        if self._dealer:
            self._dealer.setsockopt(zmq.LINGER, 0)
            self._dealer.close()
            self._dealer = None
        if self._context:
            self._context.term()
            self._context = None

    def close(self) -> None:
        if self._closed:
            return

        _LOGGER.info('Closing ZMQ Communicator: %s', self._client_id)
        self._closed = True

        if self._loop is not None and self._loop.is_running():
            if threading.current_thread() is self._loop_thread:
                # Called from a subscriber callback on the loop thread.
                self._do_close_on_loop()
                self._loop.call_soon(self._loop.stop)
            else:
                gate: Future[bool] = Future()

                def _on_loop() -> None:
                    try:
                        self._do_close_on_loop()
                    finally:
                        gate.set_result(True)

                self._loop.call_soon_threadsafe(_on_loop)
                gate.result(timeout=_LOOP_TIMEOUT)
                self._loop.call_soon_threadsafe(self._loop.stop)

        if self._loop_thread and self._loop_thread.is_alive():
            if threading.current_thread() is not self._loop_thread:
                self._loop_thread.join(timeout=3.0)

        self._loop = None
        self._loop_thread = None

        _LOGGER.info('ZMQ Communicator closed')

    def _do_close_on_loop(self) -> None:
        """Cleanup that must run on the event loop thread."""
        # Cancel poll task
        if self._dealer_poll_task and not self._dealer_poll_task.done():
            self._dealer_poll_task.cancel()
        self._dealer_poll_task = None

        # Send unsubscribe messages
        for identifier in list(self._task_subscribers):
            try:
                msg = make_subscribe_message(MessageType.UNSUBSCRIBE_TASK, self._client_id, identifier)
                self._send(msg)
            except Exception:
                pass
        self._task_subscribers.clear()

        for identifier in list(self._rpc_subscribers):
            try:
                msg = make_subscribe_message(MessageType.UNSUBSCRIBE_RPC, self._client_id, identifier)
                self._send(msg)
            except Exception:
                pass
        self._rpc_subscribers.clear()

        # Cancel pending futures
        for future in self._pending_futures.values():
            if not future.done():
                future.cancel()
        self._pending_futures.clear()

    def __enter__(self) -> 'ZmqCommunicator':
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Thread-safe scheduling helper
    # ------------------------------------------------------------------

    def _run_on_loop(self, fn: Callable[[], _T]) -> _T:
        """Schedule *fn* on the event loop thread and block for the result.

        If already on the loop thread (e.g. inside a subscriber callback),
        execute directly to avoid deadlock.
        """
        if threading.current_thread() is self._loop_thread:
            return fn()

        gate: Future[_T] = Future()

        def _callback() -> None:
            try:
                result = fn()
                gate.set_result(result)
            except Exception as exc:
                if not gate.done():
                    gate.set_exception(exc)

        assert self._loop is not None
        self._loop.call_soon_threadsafe(_callback)
        return gate.result(timeout=_LOOP_TIMEOUT)

    # ------------------------------------------------------------------
    # Task operations (kiwipy interface)
    # ------------------------------------------------------------------

    def task_send(self, task: Any, no_reply: bool = False) -> Future[Any] | None:
        self._ensure_open()

        def _do() -> Future[Any] | None:
            msg = make_task_message(task, self._client_id, no_reply)
            task_id = msg['id']
            pending: Future[Any] | None = None
            if not no_reply:
                pending = Future()
                self._pending_futures[task_id] = pending
            self._send(msg)
            _LOGGER.debug('Sent task: %s', task_id)
            return pending

        return self._run_on_loop(_do)

    def add_task_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        self._ensure_open()

        def _do() -> str:
            ident = identifier or f'task-{uuid.uuid4().hex[:8]}'
            self._task_subscribers[ident] = subscriber
            msg = make_subscribe_message(MessageType.SUBSCRIBE_TASK, self._client_id, ident)
            self._send(msg)
            _LOGGER.info('Added task subscriber: %s', ident)
            return ident

        return self._run_on_loop(_do)

    def remove_task_subscriber(self, identifier: str) -> None:
        def _do() -> None:
            if identifier in self._task_subscribers:
                del self._task_subscribers[identifier]
                if not self._closed:
                    msg = make_subscribe_message(MessageType.UNSUBSCRIBE_TASK, self._client_id, identifier)
                    self._send(msg)
                _LOGGER.info('Removed task subscriber: %s', identifier)

        self._run_on_loop(_do)

    # ------------------------------------------------------------------
    # RPC operations (kiwipy interface)
    # ------------------------------------------------------------------

    def rpc_send(self, recipient_id: str, msg: Any) -> Future[Any]:
        self._ensure_open()

        def _do() -> Future[Any]:
            rpc_msg = make_rpc_message(recipient_id, msg, self._client_id)
            rpc_id = rpc_msg['id']
            future: Future[Any] = Future()
            self._pending_futures[rpc_id] = future
            self._send(rpc_msg)
            _LOGGER.debug('Sent RPC to %s: %s', recipient_id, rpc_id)
            return future

        return self._run_on_loop(_do)

    def add_rpc_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        self._ensure_open()

        def _do() -> str:
            ident = identifier or f'rpc-{uuid.uuid4().hex[:8]}'
            if ident in self._rpc_subscribers:
                raise kiwipy.DuplicateSubscriberIdentifier(f"RPC identifier '{ident}'")
            self._rpc_subscribers[ident] = subscriber
            msg = make_subscribe_message(MessageType.SUBSCRIBE_RPC, self._client_id, ident)
            self._send(msg)
            _LOGGER.info('Added RPC subscriber: %s', ident)
            return ident

        return self._run_on_loop(_do)

    def remove_rpc_subscriber(self, identifier: str) -> None:
        def _do() -> None:
            if identifier in self._rpc_subscribers:
                del self._rpc_subscribers[identifier]
                if not self._closed:
                    msg = make_subscribe_message(MessageType.UNSUBSCRIBE_RPC, self._client_id, identifier)
                    self._send(msg)
                _LOGGER.info('Removed RPC subscriber: %s', identifier)

        self._run_on_loop(_do)

    # ------------------------------------------------------------------
    # Broadcast operations (kiwipy interface)
    # ------------------------------------------------------------------

    def broadcast_send(
        self,
        body: Any,
        sender: str | None = None,
        subject: str | None = None,
        correlation_id: str | None = None,
    ) -> bool:
        self._ensure_open()

        def _do() -> bool:
            msg = make_broadcast_message(body, sender or self._client_id, subject, correlation_id)
            self._send(msg)
            _LOGGER.debug('Sent broadcast: %s', subject)
            return True

        return self._run_on_loop(_do)

    def add_broadcast_subscriber(
        self,
        subscriber: Callable[..., Any],
        identifier: str | None = None,
    ) -> str:
        def _do() -> str:
            ident = identifier or f'broadcast-{uuid.uuid4().hex[:8]}'
            self._broadcast_subscribers[ident] = subscriber
            _LOGGER.info('Added broadcast subscriber: %s', ident)
            return ident

        return self._run_on_loop(_do)

    def remove_broadcast_subscriber(self, identifier: str) -> None:
        def _do() -> None:
            if identifier in self._broadcast_subscribers:
                del self._broadcast_subscribers[identifier]
                _LOGGER.info('Removed broadcast subscriber: %s', identifier)

        self._run_on_loop(_do)

    # ------------------------------------------------------------------
    # Internal — sending
    # ------------------------------------------------------------------

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError('Communicator is closed')

    def _send(self, msg: dict[str, Any]) -> None:
        """Send a message to the broker.  MUST be called from the loop thread."""
        if not self._dealer:
            raise RuntimeError('Communicator not connected')

        encoded = encode_message(msg)
        self._dealer.send_multipart([b'', encoded], zmq.NOBLOCK)

    # ------------------------------------------------------------------
    # Internal — polling coroutines
    # ------------------------------------------------------------------

    async def _poll_dealer(self) -> None:
        """Receive messages from the DEALER socket."""
        assert self._dealer is not None
        while not self._closed:
            try:
                frames = await self._dealer.recv_multipart()
                msg_frame = frames[1] if len(frames) > 1 and frames[0] == b'' else frames[0]
                msg = decode_message(msg_frame)
                self._dispatch_dealer_message(msg)
            except zmq.ZMQError:
                if not self._closed:
                    _LOGGER.error('ZMQ error in dealer poll')
                break
            except asyncio.CancelledError:
                break
            except Exception:
                _LOGGER.exception('Error in dealer poll')

    # ------------------------------------------------------------------
    # Internal — message dispatch
    # ------------------------------------------------------------------

    def _dispatch_dealer_message(self, msg: dict[str, Any]) -> None:
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
        elif msg_type == MessageType.BROADCAST.value:
            self._handle_broadcast(msg)
        elif msg_type == MessageType.PING.value:
            pass  # Liveness probe from broker — no action needed
        else:
            _LOGGER.warning('Unknown message type from broker: %s', msg_type)

    # --- Tasks ---

    def _handle_task(self, msg: dict[str, Any]) -> None:
        task_id = msg['id']
        body = msg.get('body')
        no_reply = msg.get('no_reply', False)

        _LOGGER.debug('Handling task: %s', task_id)

        for identifier, subscriber in self._task_subscribers.items():
            try:
                result = subscriber(self, body)

                if isinstance(result, Future):
                    self._in_progress_tasks[task_id] = (result, no_reply)
                    loop = self._loop
                    assert loop is not None

                    def _on_task_done(fut: Future[Any], _tid: str = task_id, _nr: bool = no_reply) -> None:
                        loop.call_soon_threadsafe(self._finalize_task, _tid, fut, _nr)

                    result.add_done_callback(_on_task_done)
                    _LOGGER.debug('Task in progress (deferred ACK): %s', task_id)
                else:
                    ack_msg = make_task_ack(task_id, self._client_id)
                    self._send(ack_msg)
                    if not no_reply:
                        response = make_task_response(task_id, self._client_id, result=result)
                        self._send(response)
                    _LOGGER.debug('Task completed: %s', task_id)
                return

            except Exception as exc:
                _LOGGER.exception('Task subscriber %s failed: %s', identifier, exc)

        _LOGGER.warning('No subscriber handled task: %s', task_id)
        nack_msg = make_task_nack(task_id, self._client_id)
        self._send(nack_msg)

    def _finalize_task(self, task_id: str, future: Future[Any], no_reply: bool) -> None:
        """Called on the loop thread when a deferred task completes."""
        if task_id not in self._in_progress_tasks:
            return
        del self._in_progress_tasks[task_id]

        if future.cancelled():
            _LOGGER.debug('Cancelled in-progress task dropped: %s', task_id)
            return

        try:
            ack_msg = make_task_ack(task_id, self._client_id)
            self._send(ack_msg)
            if not no_reply:
                self._send_task_result(task_id, future)
            _LOGGER.debug('Deferred task completed, ACK sent: %s', task_id)
        except Exception:
            _LOGGER.exception('Failed to finalise task %s', task_id)

    def _send_task_result(self, task_id: str, result: Any) -> None:
        """Send a task response, resolving chained Futures if needed."""
        if isinstance(result, Future):
            if result.done():
                try:
                    self._send_task_result(task_id, result.result())
                except Exception as exc:
                    response = make_task_response(task_id, self._client_id, error=str(exc))
                    self._send(response)
            else:
                loop = self._loop
                assert loop is not None

                def _on_result_done(fut: Future[Any], _tid: str = task_id) -> None:
                    loop.call_soon_threadsafe(self._send_task_result, _tid, fut)

                result.add_done_callback(_on_result_done)
        else:
            response = make_task_response(task_id, self._client_id, result=result)
            self._send(response)

    def _handle_task_response(self, msg: dict[str, Any]) -> None:
        task_id = msg.get('task_id')
        if not task_id:
            return

        future = self._pending_futures.pop(task_id, None)

        if future and not future.done():
            error = msg.get('error')
            if error:
                future.set_exception(Exception(error))
            else:
                result_future = kiwipy.Future()
                result_future.set_result(msg.get('result'))
                future.set_result(result_future)

    # --- RPCs ---

    def _handle_rpc(self, msg: dict[str, Any]) -> None:
        rpc_id = msg['id']
        body = msg.get('body')
        recipient = str(msg['recipient']) if 'recipient' in msg else None

        _LOGGER.debug('Handling RPC: %s (recipient=%s)', rpc_id, recipient)

        subscriber = self._rpc_subscribers.get(recipient) if recipient else None

        if subscriber is None:
            _LOGGER.warning('No subscriber for RPC recipient %s: %s', recipient, rpc_id)
            response = make_rpc_response(rpc_id, self._client_id, error=f'No handler for {recipient}')
            self._send(response)
            return

        assert recipient is not None  # guaranteed by subscriber lookup above
        rpc_recipient: str = recipient
        try:
            result = subscriber(self, body)
            if isinstance(result, Future):
                self._in_progress_rpcs[rpc_id] = (rpc_recipient, result)
                loop = self._loop
                assert loop is not None

                def _on_rpc_done(fut: Future[Any], _rid: str = rpc_id, _rec: str = rpc_recipient) -> None:
                    loop.call_soon_threadsafe(self._finalize_rpc, _rid, _rec, fut)

                result.add_done_callback(_on_rpc_done)
                _LOGGER.debug('RPC in progress (deferred response): %s', rpc_id)
                return
            response = make_rpc_response(rpc_id, self._client_id, result=result)
            self._send(response)
            _LOGGER.debug('RPC handled: %s', rpc_id)

        except Exception as exc:
            _LOGGER.exception('RPC subscriber %s failed: %s', recipient, exc)
            response = make_rpc_response(rpc_id, self._client_id, error=str(exc))
            self._send(response)

    def _finalize_rpc(self, rpc_id: str, recipient: str, future: Future[Any]) -> None:
        """Called on the loop thread when a deferred RPC completes."""
        if rpc_id not in self._in_progress_rpcs:
            return
        del self._in_progress_rpcs[rpc_id]

        if future.cancelled():
            return

        try:
            result = future.result()
            # Unwrap nested done Futures
            while isinstance(result, Future) and result.done():
                result = result.result()
            if isinstance(result, Future):
                # Still pending — re-register
                self._in_progress_rpcs[rpc_id] = (recipient, result)
                loop = self._loop
                assert loop is not None

                def _on_rpc_retry(fut: Future[Any], _rid: str = rpc_id, _rec: str = recipient) -> None:
                    loop.call_soon_threadsafe(self._finalize_rpc, _rid, _rec, fut)

                result.add_done_callback(_on_rpc_retry)
                return
            response = make_rpc_response(rpc_id, self._client_id, result=result)
            self._send(response)
        except Exception as exc:
            response = make_rpc_response(rpc_id, self._client_id, error=str(exc))
            self._send(response)

    def _handle_rpc_response(self, msg: dict[str, Any]) -> None:
        rpc_id = msg.get('rpc_id')
        if not rpc_id:
            return

        future = self._pending_futures.pop(rpc_id, None)

        if future and not future.done():
            error = msg.get('error')
            if error:
                future.set_exception(Exception(error))
            else:
                future.set_result(msg.get('result'))

    # --- Broadcasts ---

    def _handle_broadcast(self, msg: dict[str, Any]) -> None:
        body = msg.get('body')
        sender = msg.get('sender')
        subject = msg.get('subject')
        correlation_id = msg.get('correlation_id')

        for identifier, subscriber in self._broadcast_subscribers.items():
            try:
                subscriber(self, body, sender, subject, correlation_id)
            except Exception as exc:
                _LOGGER.exception('Broadcast subscriber %s failed: %s', identifier, exc)
