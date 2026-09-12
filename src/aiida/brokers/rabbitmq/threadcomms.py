###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
#                                                                         #
# Portions of this file are derived from kiwipy.                          #
# Copyright (c), 2022, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE          #
# (Theory and Simulation of Materials (THEOS) and National Centre for    #
# Computational Design and Discovery of Novel Materials (NCCR MARVEL)), #
# Switzerland and ROBERT BOSCH LLC, USA. All rights reserved.            #
#                                                                         #
# The kiwipy license is reproduced in open_source_licenses.txt.          #
###########################################################################
"""Synchronous RabbitMQ communicator running an event loop on a separate thread."""

from __future__ import annotations

import asyncio
import concurrent.futures
import functools
import logging
from collections.abc import Callable, Iterator
from concurrent.futures import Future as ThreadFuture
from contextlib import contextmanager
from types import TracebackType
from typing import Any

import aio_pika
import aio_pika.abc
import pamqp.commands
from pytray import aiothreads  # type: ignore[import-untyped]

from aiida.brokers import communicator as broker_communicator
from aiida.brokers import exceptions, futures
from aiida.brokers.rabbitmq import communicator, defaults, tasks

__all__ = ('RmqThreadCommunicator', 'RmqThreadIncomingTask', 'RmqThreadTaskQueue')

_LOGGER = logging.getLogger(__name__)


class RmqThreadCommunicator(broker_communicator.Communicator):
    """RabbitMQ communicator that runs an event loop on a separate thread to do communication.

    This also means that heartbeats are not missed and the main program is free to block for
    as long as it wants.
    """

    TASK_TIMEOUT = 5.0

    @classmethod
    def connect(
        cls,
        connection_params: str | dict[str, Any] | None = None,
        connection_factory: Callable[..., Any] = aio_pika.connect_robust,
        message_exchange: str = defaults.MESSAGE_EXCHANGE,
        task_exchange: str = defaults.TASK_EXCHANGE,
        task_queue: str = defaults.TASK_QUEUE,
        task_prefetch_size: int = defaults.TASK_PREFETCH_SIZE,
        task_prefetch_count: int = defaults.TASK_PREFETCH_COUNT,
        encoder: Callable[..., Any] = defaults.ENCODER,
        decoder: Callable[..., Any] = defaults.DECODER,
        testing_mode: bool = False,
        async_task_timeout: float = TASK_TIMEOUT,
    ) -> RmqThreadCommunicator:
        # pylint: disable=too-many-arguments
        comm = cls(
            connection_params,
            connection_factory,
            message_exchange=message_exchange,
            task_exchange=task_exchange,
            task_queue=task_queue,
            task_prefetch_size=task_prefetch_size,
            task_prefetch_count=task_prefetch_count,
            encoder=encoder,
            decoder=decoder,
            testing_mode=testing_mode,
            async_task_timeout=async_task_timeout,
        )

        # Start the communicator
        return comm

    def __init__(
        self,
        connection_params: str | dict[str, Any] | None = None,
        connection_factory: Callable[..., Any] = aio_pika.connect_robust,
        message_exchange: str = defaults.MESSAGE_EXCHANGE,
        queue_expires: int = defaults.QUEUE_EXPIRES,
        task_exchange: str = defaults.TASK_EXCHANGE,
        task_queue: str = defaults.TASK_QUEUE,
        task_prefetch_size: int = defaults.TASK_PREFETCH_SIZE,
        task_prefetch_count: int = defaults.TASK_PREFETCH_COUNT,
        encoder: Callable[..., Any] = defaults.ENCODER,
        decoder: Callable[..., Any] = defaults.DECODER,
        testing_mode: bool = False,
        async_task_timeout: float = TASK_TIMEOUT,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Initialise the communicator.

        :param connection_params: Parameters passed to the connection factory to create the connection.
        :param connection_factory: The factory method to open the aio-pika connection with.
        :param message_exchange: The name of the RMQ message exchange to use.
        :param queue_expires: Expiry time for standard queues in milliseconds.
        :param task_exchange: The name of the RMQ task exchange to use.
        :param task_queue: The name of the task queue to use.
        :param task_prefetch_count: The number of tasks this communicator can fetch simultaneously.
        :param task_prefetch_size: The total size of the messages that the default queue can fetch simultaneously.
        :param encoder: The encoder to call for encoding a message.
        :param decoder: The decoder to call for decoding a message.
        :param testing_mode: Run in testing mode: all queues and exchanges will be temporary.
        """
        # Always use a separate loop
        self._loop = asyncio.new_event_loop()
        self._loop.set_debug(testing_mode)
        self._loop_scheduler: Any = aiothreads.LoopScheduler(self._loop, 'RMQ communicator', async_task_timeout)
        self._stop_signal: Any = None
        self._closed = False

        self._loop_scheduler.start()  # Start the loop scheduler (i.e. the event loop thread)

        # Establish the connection and get a communicator running on our thread
        try:
            self._communicator: communicator.RmqCommunicator = self._loop_scheduler.await_(
                communicator.async_connect(
                    connection_params=connection_params,
                    connection_factory=connection_factory,
                    # Messages
                    message_exchange=message_exchange,
                    queue_expires=queue_expires,
                    # Tasks
                    task_exchange=task_exchange,
                    task_queue=task_queue,
                    task_prefetch_size=task_prefetch_size,
                    task_prefetch_count=task_prefetch_count,
                    encoder=encoder,
                    decoder=decoder,
                    testing_mode=testing_mode,
                )
            )
        except Exception:
            self._closed = True
            self._loop_scheduler.close()
            self._loop.close()
            raise

    @property
    def server_properties(self) -> dict[str, Any]:
        """A dictionary containing server properties as returned by the RMQ server at connection time.

        :return: The server properties dictionary.
        """
        return self._communicator.server_properties

    def __enter__(self) -> RmqThreadCommunicator:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def loop(self) -> Any:
        return self._loop_scheduler.loop()

    def is_closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        """Close down the communicator and clean up all resources. After this call it cannot be used again."""
        if self.is_closed():
            return

        try:
            self._loop_scheduler.await_(self._communicator.disconnect())
        finally:
            self._loop_scheduler.close()
            self._loop.close()

            # Clean up
            del self._communicator
            del self._loop_scheduler
            del self._loop
            self._closed = True

    def add_close_callback(self, callback: aio_pika.abc.ConnectionCloseCallback, weak: bool = False) -> None:
        """Add a callable to be called each time (after) the connection is closed.

        :param weak: If True, the callback will be added to a ``WeakSet``.
        """
        self._ensure_open()
        self._communicator.add_close_callback(callback, weak)

    def add_rpc_subscriber(self, subscriber: Callable[..., Any], identifier: Any = None) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(
            self._communicator.add_rpc_subscriber(self._wrap_subscriber(subscriber), identifier)
        )

    def remove_rpc_subscriber(self, identifier: Any) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(self._communicator.remove_rpc_subscriber(identifier))

    def add_task_subscriber(self, subscriber: Callable[..., Any], identifier: Any = None) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(
            self._communicator.add_task_subscriber(self._wrap_subscriber(subscriber), identifier)
        )

    def remove_task_subscriber(self, identifier: Any) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(self._communicator.remove_task_subscriber(identifier))

    def add_broadcast_subscriber(self, subscriber: Callable[..., Any], identifier: Any = None) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(self._communicator.add_broadcast_subscriber(subscriber, identifier))

    def remove_broadcast_subscriber(self, identifier: Any) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(self._communicator.remove_broadcast_subscriber(identifier))

    def task_send(self, task: Any, no_reply: bool = False) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(self._communicator.task_send(task, no_reply))

    def task_queue(
        self,
        queue_name: str,
        prefetch_size: int = defaults.TASK_PREFETCH_SIZE,
        prefetch_count: int = defaults.TASK_PREFETCH_COUNT,
    ) -> RmqThreadTaskQueue:
        self._ensure_open()
        aioqueue = self._loop_scheduler.await_(self._communicator.task_queue(queue_name, prefetch_size, prefetch_count))
        return RmqThreadTaskQueue(aioqueue, self._loop_scheduler, self._wrap_subscriber)

    def rpc_send(self, recipient_id: Any, msg: Any) -> Any:
        self._ensure_open()
        return self._loop_scheduler.await_(self._communicator.rpc_send(recipient_id, msg))

    def broadcast_send(self, body: Any, sender: Any = None, subject: Any = None, correlation_id: Any = None) -> bool:
        self._ensure_open()
        result = self._loop_scheduler.await_(
            self._communicator.broadcast_send(body=body, sender=sender, subject=subject, correlation_id=correlation_id)
        )
        return isinstance(result, pamqp.commands.Basic.Ack)

    def _wrap_subscriber(self, subscriber: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a subscriber converting any thread futures into asyncio ones for the event loop communicator."""

        @functools.wraps(subscriber)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = subscriber(*args, **kwargs)
            if isinstance(result, ThreadFuture):
                result = self._wrap_future(result)
            return result

        return wrapper

    def _wrap_future(self, kiwi_future: futures.Future[Any]) -> asyncio.Future[Any]:
        aio_future: asyncio.Future[Any] = self._loop.create_future()

        def done(_: futures.Future[Any]) -> None:
            try:
                result = kiwi_future.result()
            except concurrent.futures.CancelledError:
                self._loop.call_soon_threadsafe(aio_future.cancel)
            except Exception as exc:  # pylint: disable=broad-except
                self._loop.call_soon_threadsafe(aio_future.set_exception, exc)
            else:
                if isinstance(result, futures.Future):
                    result = self._wrap_future(result)
                self._loop.call_soon_threadsafe(aio_future.set_result, result)

        kiwi_future.add_done_callback(done)
        return aio_future

    def _ensure_open(self) -> None:
        if self.is_closed():
            raise exceptions.CommunicatorClosed


class RmqThreadTaskQueue:
    """Thread task queue."""

    def __init__(
        self,
        task_queue: tasks.RmqTaskQueue,
        loop_scheduler: Any,
        wrap_subscriber: Callable[..., Any],
    ) -> None:
        self._task_queue = task_queue
        self._loop_scheduler = loop_scheduler
        self._wrap_subscriber = wrap_subscriber

    def __iter__(self) -> Iterator[RmqThreadIncomingTask]:
        for task in self._loop_scheduler.async_iter(self._task_queue):
            yield RmqThreadIncomingTask(task, self._loop_scheduler)

    def task_send(self, task: Any, no_reply: bool = False) -> Any:
        return self._loop_scheduler.await_(self._task_queue.task_send(task, no_reply))

    def add_task_subscriber(self, subscriber: Callable[..., Any]) -> Any:
        return self._loop_scheduler.await_(self._task_queue.add_task_subscriber(self._wrap_subscriber(subscriber)))

    def remove_task_subscriber(self, subscriber: Any) -> Any:
        # Note: This probably doesn't work as in add_task_subscriber we wrap it and so
        # it will be a different function here
        return self._loop_scheduler.await_(self._task_queue.remove_task_subscriber(subscriber))

    @contextmanager
    def next_task(self, timeout: float = 5.0, fail: bool = True) -> Iterator[RmqThreadIncomingTask]:
        with self._loop_scheduler.async_ctx(self._task_queue.next_task(timeout=timeout, fail=fail)) as task:
            yield RmqThreadIncomingTask(task, self._loop_scheduler)


class RmqThreadIncomingTask:
    """A task received from the thread task queue."""

    def __init__(self, task: tasks.RmqIncomingTask, loop_scheduler: Any) -> None:
        self._task = task
        self._loop_scheduler = loop_scheduler

    @property
    def body(self) -> Any:
        return self._task.body

    @property
    def no_reply(self) -> bool:
        return self._task.no_reply

    @property
    def state(self) -> str:
        return self._task.state

    def process(self) -> Any:
        return aiothreads.aio_future_to_thread(self._task.process())

    def requeue(self) -> None:
        """Requeue the task. This call is blocking; the task is back in the queue when it returns."""
        self._loop_scheduler.await_(self._task.requeue())

    @contextmanager
    def processing(self) -> Iterator[Any]:
        with self._loop_scheduler.async_ctx(self._task.processing()) as outcome:
            yield outcome
