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
"""Asyncio RabbitMQ communicator built on aio-pika."""

from __future__ import annotations

import asyncio
import copy
import logging
from collections.abc import Callable
from functools import partial
from typing import Any

import aio_pika
import aio_pika.abc
import shortuuid

from aiida.brokers import exceptions, futures
from aiida.brokers.rabbitmq import defaults, messages, tasks, utils

__all__ = ('RmqCommunicator', 'RmqPublisher', 'RmqSubscriber', 'async_connect')

_LOGGER = logging.getLogger(__name__)

# The exchange properties used by the publisher and subscriber. These have to match
# which is why they're declared here.
EXCHANGE_PROPERTIES: dict[str, Any] = {'type': aio_pika.ExchangeType.TOPIC}


class RmqPublisher(messages.BasePublisherWithReplyQueue):
    """Publisher for sending a range of message types over RMQ."""

    DEFAULT_EXCHANGE_PARAMS: dict[str, Any] = EXCHANGE_PROPERTIES

    async def rpc_send(self, recipient_id: str, msg: Any) -> asyncio.Future[Any]:
        routing_key = f'{defaults.RPC_TOPIC}.{recipient_id}'
        assert self._reply_queue is not None
        _LOGGER.debug(
            'Sending RPC with routing key %r to RMQ queue %r: %r',
            routing_key,
            self._reply_queue.name,
            msg,
        )
        message = aio_pika.Message(body=self._encode(msg), reply_to=self._reply_queue.name)
        published, response_future = await self.publish_expect_response(
            message, routing_key=routing_key, mandatory=True
        )
        assert published, 'The message was not published to the exchanges'
        return response_future

    async def broadcast_send(
        self, msg: Any, sender: Any = None, subject: Any = None, correlation_id: Any = None
    ) -> Any:
        message_dict = messages.BroadcastMessage.create(
            body=msg,
            sender=sender,
            subject=subject,
            correlation_id=correlation_id,
        )
        _LOGGER.debug(
            'Sending broadcast with routing key %r to RMQ via exchange %r: %r',
            defaults.BROADCAST_TOPIC,
            self._exchange_name,
            message_dict,
        )
        message = aio_pika.Message(
            body=self._encode(message_dict),
            delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT,
        )
        # Send as mandatory=False because we don't expect the message to be routable to anyone
        return await self.publish(message, routing_key=defaults.BROADCAST_TOPIC, mandatory=False)


class RmqSubscriber:
    """Subscriber for receiving a range of messages over RMQ."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        connection: aio_pika.Connection,
        message_exchange: str = defaults.MESSAGE_EXCHANGE,
        queue_expires: int = defaults.QUEUE_EXPIRES,
        decoder: Callable[..., Any] = defaults.DECODER,
        encoder: Callable[..., Any] = defaults.ENCODER,
        testing_mode: bool = False,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Initialise the subscriber.

        :param connection: The aio-pika connection.
        :param message_exchange: The name of the exchange to use.
        :param queue_expires: Expiry time for standard queues in milliseconds.
        :param encoder: The encoder to call for encoding a message.
        :param decoder: The decoder to call for decoding a message.
        :param testing_mode: Run in testing mode: all queues and exchanges will be temporary.
        """
        super().__init__()

        self._connection = connection
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None
        self._exchange_name = message_exchange
        self._decode = decoder
        self._testing_mode = testing_mode
        self._response_encode = encoder

        self._broadcast_queue_arguments: dict[str, Any] = {'x-message-ttl': defaults.MESSAGE_TTL}

        self._rmq_queue_arguments: dict[str, Any] = {'x-message-ttl': defaults.MESSAGE_TTL}
        if queue_expires:
            self._rmq_queue_arguments['x-expires'] = queue_expires

        self._rpc_subscribers: dict[str, aio_pika.abc.AbstractQueue] = {}
        self._broadcast_subscribers: dict[str, Callable[..., Any]] = {}
        self._broadcast_queue: aio_pika.abc.AbstractQueue | None = None
        self._broadcast_consumer_tag: str | None = None

    async def add_rpc_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        assert self._channel is not None
        # Create an RPC queue
        rpc_queue = await self._channel.declare_queue(exclusive=True, arguments=self._rmq_queue_arguments)
        try:
            identifier = await rpc_queue.consume(partial(self._on_rpc, subscriber), consumer_tag=identifier)
        except aio_pika.exceptions.DuplicateConsumerTag as exception:
            raise exceptions.DuplicateSubscriberIdentifier(f"RPC identifier '{identifier}'") from exception
        else:
            assert self._exchange is not None
            assert identifier is not None
            await rpc_queue.bind(self._exchange, routing_key=f'{defaults.RPC_TOPIC}.{identifier}')
            # Save the queue so we can cancel and unbind later
            self._rpc_subscribers[identifier] = rpc_queue
            return identifier

    async def remove_rpc_subscriber(self, identifier: str) -> None:
        try:
            rpc_queue = self._rpc_subscribers.pop(identifier)
        except KeyError as exception:
            raise ValueError(f"Unknown subscriber '{identifier}'") from exception
        else:
            await rpc_queue.cancel(identifier)
            assert self._exchange is not None
            await rpc_queue.unbind(self._exchange, routing_key=f'{defaults.RPC_TOPIC}.{identifier}')

    async def add_broadcast_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        identifier = identifier or shortuuid.uuid()
        if identifier in self._broadcast_subscribers:
            raise exceptions.DuplicateSubscriberIdentifier(f"Broadcast identifier '{identifier}'")

        self._broadcast_subscribers[identifier] = subscriber
        if self._broadcast_consumer_tag is None:
            # Consume on the broadcast queue
            assert self._broadcast_queue is not None
            self._broadcast_consumer_tag = await self._broadcast_queue.consume(self._on_broadcast)
        return identifier

    async def remove_broadcast_subscriber(self, identifier: str) -> None:
        try:
            del self._broadcast_subscribers[identifier]
        except KeyError as exception:
            raise ValueError(f"Broadcast subscriber '{identifier}' unknown") from exception
        if not self._broadcast_subscribers:
            assert self._broadcast_queue is not None
            assert self._broadcast_consumer_tag is not None
            await self._broadcast_queue.cancel(self._broadcast_consumer_tag)
            self._broadcast_consumer_tag = None

    def channel(self) -> aio_pika.abc.AbstractChannel | None:
        return self._channel

    async def connect(self) -> None:
        """Get a channel and set up all the exchanges/queues we need."""
        if self._channel:
            # Already connected
            return

        exchange_params: dict[str, Any] = copy.copy(EXCHANGE_PROPERTIES)

        if self._testing_mode:
            exchange_params.setdefault('auto_delete', self._testing_mode)

        self._channel = await self._connection.channel()
        self._exchange = await self._channel.declare_exchange(name=self._exchange_name, **exchange_params)

        await self._create_broadcast_queue()

    async def _create_broadcast_queue(self) -> None:
        """Create and bind the broadcast queue. One is used for all broadcasts on this exchange."""
        # Create a new such that we can see this is the broadcast queue
        name = f'broadcast-{shortuuid.uuid()}'
        assert self._channel is not None
        self._broadcast_queue = await self._channel.declare_queue(
            name=name, exclusive=True, arguments=self._broadcast_queue_arguments
        )
        assert self._exchange is not None
        assert self._broadcast_queue is not None
        await self._broadcast_queue.bind(self._exchange, routing_key=defaults.BROADCAST_TOPIC)

    async def disconnect(self) -> None:
        assert self._channel is not None
        await self._channel.close()
        self._exchange = None
        self._channel = None

    async def _on_rpc(self, subscriber: Callable[..., Any], message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """:param subscriber: The subscriber function or coroutine that will get the RPC message."""
        async with message.process(ignore_processed=True):
            # Tell the sender that we've dealt with it
            await message.ack()
            msg = self._decode(message.body)

            try:
                receiver = utils.ensure_coroutine(subscriber)
                result = await receiver(self, msg)
            except Exception as exc:  # pylint: disable=broad-except
                # We had an exception in calling the receiver
                await self._send_response(message.reply_to, message.correlation_id, utils.exception_response(exc))
            else:
                if asyncio.isfuture(result):
                    await self._send_future_response(result, message.reply_to, message.correlation_id)
                else:
                    # All good, send the response out
                    await self._send_response(message.reply_to, message.correlation_id, utils.result_response(result))

    async def _on_broadcast(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        async with message.process():
            msg = self._decode(message.body)
            for receiver in self._broadcast_subscribers.values():
                try:
                    wrapped_receiver = utils.ensure_coroutine(receiver)
                    await wrapped_receiver(
                        self,
                        msg[messages.BroadcastMessage.BODY],
                        msg[messages.BroadcastMessage.SENDER],
                        msg[messages.BroadcastMessage.SUBJECT],
                        msg[messages.BroadcastMessage.CORRELATION_ID],
                    )
                except Exception:  # pylint: disable=broad-except
                    _LOGGER.exception('Exception in broadcast receiver')

    async def _send_future_response(
        self, future: asyncio.Future[Any], reply_to: str | None, correlation_id: str | None
    ) -> None:
        """Send pending responses while an RPC future resolves, then the final result.

        :param future: The future from the RPC call.
        :param reply_to: The recipient.
        :param correlation_id: The correlation id.
        """
        # Keep looping in case we're in a situation where a future resolves to a future etc.
        pending: Any = future
        try:
            while asyncio.isfuture(pending):
                # Send out a message saying that we're waiting for a future to complete
                await self._send_response(reply_to, correlation_id, utils.pending_response())
                pending = await pending
        except (futures.CancelledError, asyncio.CancelledError) as exc:
            # Send out a cancelled response
            await self._send_response(reply_to, correlation_id, utils.cancelled_response(str(exc)))
            return
        except Exception as exc:  # pylint: disable=broad-except
            # Send out an exception response
            await self._send_response(reply_to, correlation_id, utils.exception_response(exc))
            return
        # We have a final result so send that as the response
        await self._send_response(reply_to, correlation_id, utils.result_response(pending))

    async def _send_response(self, reply_to: str | None, correlation_id: str | None, response: dict[str, Any]) -> Any:
        assert reply_to, 'Must provide an identifier for the recipient'

        message = aio_pika.Message(body=self._response_encode(response), correlation_id=correlation_id)
        assert self._exchange is not None
        result = await self._exchange.publish(message, routing_key=reply_to)
        return result


class RmqCommunicator:
    """An asynchronous communicator over a RabbitMQ server using aio-pika and an asyncio event loop."""

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        connection: aio_pika.Connection,
        # Messages
        message_exchange: str = defaults.MESSAGE_EXCHANGE,
        queue_expires: int = defaults.QUEUE_EXPIRES,
        # Tasks
        task_exchange: str = defaults.TASK_EXCHANGE,
        task_queue: str = defaults.TASK_QUEUE,
        task_prefetch_size: int = defaults.TASK_PREFETCH_SIZE,
        task_prefetch_count: int = defaults.TASK_PREFETCH_COUNT,
        encoder: Callable[..., Any] = defaults.ENCODER,
        decoder: Callable[..., Any] = defaults.DECODER,
        testing_mode: bool = False,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Create a new asynchronous communicator.

        .. note:: This communicator takes ownership of the connection and, therefore, it should not be shared as when
            this communicator disconnects it will also hang up the connection.

        :param connection: An aio-pika connection, doesn't need to be connected.
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
        super().__init__()

        self._connection = connection
        self._loop: asyncio.AbstractEventLoop = connection.loop

        # Save some of these settings for later
        self._message_exchange = message_exchange
        self._queue_expires = queue_expires

        # Default tasks queue
        self._task_exchange = task_exchange
        self._task_queue = task_queue
        self._task_prefetch_size = task_prefetch_size
        self._task_prefetch_count = task_prefetch_count
        self._task_queues: list[tasks.RmqTaskQueue] = []

        self._decoder = decoder
        self._encoder = encoder
        self._testing_mode = testing_mode

        self._message_subscriber: RmqSubscriber | None = None
        self._message_publisher: RmqPublisher | None = None
        self._default_task_queue: tasks.RmqTaskQueue | None = None

    async def __aenter__(self) -> RmqCommunicator:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect()

    def __str__(self) -> str:
        return f'RMQCommunicator({self._connection})'

    @property
    def server_properties(self) -> dict[str, Any]:
        """A dictionary containing server properties as returned by the RMQ server at connection time.

        :return: The server properties dictionary.
        """
        transport = self._connection.transport
        assert transport is not None
        properties: dict[str, Any] = transport.connection.server_properties
        return properties

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get the event loop instance driving this communicator connection."""
        return self._connection.loop

    def add_close_callback(self, callback: aio_pika.abc.ConnectionCloseCallback, weak: bool = False) -> None:
        """Add a callable to be called each time (after) the connection is closed.

        :param weak: If True, the callback will be added to a ``WeakSet``.
        """
        self._connection.close_callbacks.add(callback, weak)

    async def get_default_task_queue(self) -> tasks.RmqTaskQueue:
        """Get a default task queue, creating it if it doesn't exist yet."""
        self._ensure_connected()

        if self._default_task_queue is None:
            task_queue = tasks.RmqTaskQueue(
                self._connection,
                exchange_name=self._task_exchange,
                queue_name=self._task_queue,
                decoder=self._decoder,
                encoder=self._encoder,
                prefetch_size=self._task_prefetch_size,
                prefetch_count=self._task_prefetch_count,
                testing_mode=self._testing_mode,
            )

            await task_queue.connect()
            self._default_task_queue = task_queue

        assert self._default_task_queue is not None
        return self._default_task_queue

    async def get_message_subscriber(self) -> RmqSubscriber:
        """Get the message subscriber, creating it if it doesn't exist yet."""
        self._ensure_connected()

        if self._message_subscriber is None:
            subscriber = RmqSubscriber(
                self._connection,
                message_exchange=self._message_exchange,
                queue_expires=self._queue_expires,
                encoder=self._encoder,
                decoder=self._decoder,
                testing_mode=self._testing_mode,
            )
            await subscriber.connect()
            self._message_subscriber = subscriber

        assert self._message_subscriber is not None
        return self._message_subscriber

    async def get_message_publisher(self) -> RmqPublisher:
        """Get a message publisher, creating it if it doesn't exist yet."""
        self._ensure_connected()

        if self._message_publisher is None:
            publisher = RmqPublisher(
                self._connection,
                exchange_name=self._message_exchange,
                encoder=self._encoder,
                decoder=self._decoder,
                testing_mode=self._testing_mode,
            )

            await publisher.connect()
            self._message_publisher = publisher

        assert self._message_publisher is not None
        return self._message_publisher

    def connected(self) -> bool:
        return not self._connection.is_closed

    async def connect(self) -> None:
        """Establish a connection if not already connected."""
        if not self.connected():
            await self._connection.connect()

    async def disconnect(self) -> None:
        """Disconnect from the connection if connected."""
        if not self.connected():
            return

        if self._message_publisher is not None:
            await self._message_publisher.disconnect()
            self._message_publisher = None

        if self._message_subscriber is not None:
            await self._message_subscriber.disconnect()
            self._message_subscriber = None

        if self._default_task_queue is not None:
            await self._default_task_queue.disconnect()
            self._default_task_queue = None

        await self._connection.close()

    async def add_rpc_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        msg_subscriber = await self.get_message_subscriber()
        identifier = await msg_subscriber.add_rpc_subscriber(subscriber, identifier)
        return identifier

    async def remove_rpc_subscriber(self, identifier: str) -> None:
        msg_subscriber = await self.get_message_subscriber()
        await msg_subscriber.remove_rpc_subscriber(identifier)

    async def add_task_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        default_task_queue = await self.get_default_task_queue()
        return await default_task_queue.add_task_subscriber(subscriber, identifier)

    async def remove_task_subscriber(self, identifier: str) -> None:
        default_task_queue = await self.get_default_task_queue()
        await default_task_queue.remove_task_subscriber(identifier)

    async def add_broadcast_subscriber(self, subscriber: Callable[..., Any], identifier: str | None = None) -> str:
        msg_subscriber = await self.get_message_subscriber()
        identifier = await msg_subscriber.add_broadcast_subscriber(subscriber, identifier)
        return identifier

    async def remove_broadcast_subscriber(self, identifier: str) -> None:
        msg_subscriber = await self.get_message_subscriber()
        await msg_subscriber.remove_broadcast_subscriber(identifier)

    async def rpc_send(self, recipient_id: str, msg: Any) -> asyncio.Future[Any]:
        """Initiate a remote procedure call on a recipient.

        :param recipient_id: The recipient identifier.
        :param msg: The body of the message.
        :return: A future corresponding to the outcome of the call.
        """
        try:
            publisher = await self.get_message_publisher()
            response_future = await publisher.rpc_send(recipient_id, msg)
            return response_future
        except aio_pika.exceptions.DeliveryError as exception:
            raise exceptions.UnroutableError(str(exception))

    async def broadcast_send(
        self, body: Any, sender: Any = None, subject: Any = None, correlation_id: Any = None
    ) -> Any:
        publisher = await self.get_message_publisher()
        result = await publisher.broadcast_send(body, sender, subject, correlation_id)
        return result

    async def task_send(self, task: Any, no_reply: bool = False) -> asyncio.Future[Any] | None:
        try:
            task_queue = await self.get_default_task_queue()
            result = await task_queue.task_send(task, no_reply)
            return result
        except aio_pika.exceptions.DeliveryError as exception:
            raise exceptions.UnroutableError(str(exception))
        except aio_pika.exceptions.AMQPError as exception:
            # Find out what the exception is when a nack is generated!
            raise exceptions.TaskRejected(str(exception))

    async def task_queue(
        self,
        queue_name: str,
        prefetch_size: int = defaults.TASK_PREFETCH_SIZE,
        prefetch_count: int = defaults.TASK_PREFETCH_COUNT,
    ) -> tasks.RmqTaskQueue:
        """Create a new task queue."""
        queue = tasks.RmqTaskQueue(
            self._connection,
            exchange_name=self._task_exchange,
            queue_name=queue_name,
            decoder=self._decoder,
            encoder=self._encoder,
            prefetch_size=prefetch_size,
            prefetch_count=prefetch_count,
            testing_mode=self._testing_mode,
        )
        await queue.connect()
        self._task_queues.append(queue)
        return queue

    def _ensure_connected(self) -> None:
        if not self.connected():
            raise RuntimeError(
                'The communicator is not connected, call connect() or use in a context to establish a connection.'
            )


async def async_connect(
    # Connection parameters
    connection_params: str | dict[str, Any] | None = None,
    connection_factory: Callable[..., Any] = aio_pika.connect_robust,
    # Messages
    message_exchange: str = defaults.MESSAGE_EXCHANGE,
    queue_expires: int = defaults.QUEUE_EXPIRES,
    # Tasks
    task_exchange: str = defaults.TASK_EXCHANGE,
    task_queue: str = defaults.TASK_QUEUE,
    task_prefetch_size: int = defaults.TASK_PREFETCH_SIZE,
    task_prefetch_count: int = defaults.TASK_PREFETCH_COUNT,
    encoder: Callable[..., Any] = defaults.ENCODER,
    decoder: Callable[..., Any] = defaults.DECODER,
    testing_mode: bool = False,
) -> RmqCommunicator:
    # pylint: disable=too-many-arguments
    """Return a connected communicator.

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
    connection_params = connection_params or {}
    if isinstance(connection_params, dict):
        connection = await connection_factory(**connection_params)
    else:
        connection = await connection_factory(connection_params)

    communicator = RmqCommunicator(
        connection=connection,
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

    await communicator.connect()
    return communicator
