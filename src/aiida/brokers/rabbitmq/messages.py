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
"""RabbitMQ message primitives: broadcast envelope, exchange connections and reply-queue publishers."""

from __future__ import annotations

import asyncio
import copy
import logging
import traceback
import uuid
from collections import deque
from collections.abc import Callable
from typing import Any

import aio_pika
import aio_pika.abc

from aiida.brokers.rabbitmq import defaults, utils

_LOGGER = logging.getLogger(__name__)

__all__ = ('BaseConnectionWithExchange', 'BasePublisherWithReplyQueue', 'BroadcastMessage')


class BroadcastMessage:
    """Envelope keys for broadcast messages."""

    BODY = 'body'
    SENDER = 'sender'
    SUBJECT = 'subject'
    CORRELATION_ID = 'correlation_id'

    @staticmethod
    def create(body: Any, sender: Any = None, subject: Any = None, correlation_id: Any = None) -> dict[str, Any]:
        return {
            BroadcastMessage.BODY: body,
            BroadcastMessage.SENDER: sender,
            BroadcastMessage.SUBJECT: subject,
            BroadcastMessage.CORRELATION_ID: correlation_id,
        }


class BaseConnectionWithExchange:
    """An RMQ connection with a channel and exchange."""

    DEFAULT_EXCHANGE_PARAMS: dict[str, Any] = {'type': aio_pika.ExchangeType.TOPIC}

    def __init__(
        self,
        connection: aio_pika.Connection,
        exchange_name: str = defaults.MESSAGE_EXCHANGE,
        exchange_params: dict[str, Any] | None = None,
        testing_mode: bool = False,
    ) -> None:
        """Initialise the connection wrapper.

        :param connection: The aio-pika connection.
        :param exchange_name: The name of the exchange to use.
        :param exchange_params: Optional exchange parameters.
        :param testing_mode: Run in testing mode: all queues and exchanges will be temporary.
        """
        super().__init__()

        if exchange_params is None:
            exchange_params = copy.copy(self.DEFAULT_EXCHANGE_PARAMS)

        if testing_mode:
            exchange_params.setdefault('auto_delete', testing_mode)

        self._connection = connection
        self._exchange_name = exchange_name
        self._exchange_params = exchange_params
        self._loop: asyncio.AbstractEventLoop = self._connection.loop

        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None
        self._is_closing = False

    @property
    def is_closing(self) -> bool:
        return self._is_closing

    def loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def get_exchange_name(self) -> str:
        return self._exchange_name

    def channel(self) -> aio_pika.abc.AbstractChannel | None:
        return self._channel

    async def connect(self) -> None:
        if self._channel:
            return

        # Create the channel
        self._channel = await self._connection.channel()
        # Create the exchange
        self._exchange = await self._channel.declare_exchange(name=self.get_exchange_name(), **self._exchange_params)

    async def disconnect(self) -> None:
        if not self.is_closing:
            self._is_closing = True
            channel = self._channel
            if channel is not None:
                await channel.close()
                self._channel = None


class BasePublisherWithReplyQueue:
    """A base class for any object that publishes a message and potentially expects a reply."""

    # pylint: disable=too-many-instance-attributes

    DEFAULT_EXCHANGE_PARAMS: dict[str, Any] = {'type': aio_pika.ExchangeType.TOPIC}

    def __init__(
        self,
        connection: aio_pika.Connection,
        exchange_name: str = defaults.MESSAGE_EXCHANGE,
        exchange_params: dict[str, Any] | None = None,
        encoder: Callable[..., Any] = defaults.ENCODER,
        decoder: Callable[..., Any] = defaults.DECODER,
        confirm_deliveries: bool = True,
        testing_mode: bool = False,
    ) -> None:
        # pylint: disable=too-many-arguments
        """Initialise the publisher.

        :param connection: The aio-pika RMQ connection.
        :param exchange_name: The name of the exchange to use.
        :param exchange_params: Optional exchange parameters.
        :param encoder: The encoder to call for encoding a message.
        :param decoder: The decoder to call for decoding a message.
        :param confirm_deliveries: Whether to use publisher confirms.
        :param testing_mode: Run in testing mode: all queues and exchanges will be temporary.
        """
        super().__init__()

        if exchange_params is None:
            exchange_params = copy.copy(self.DEFAULT_EXCHANGE_PARAMS)

        if testing_mode:
            exchange_params.setdefault('auto_delete', testing_mode)

        self._exchange_name = exchange_name
        self._exchange_params = exchange_params
        self._encode = encoder
        self._response_decode = decoder
        self._confirm_deliveries = confirm_deliveries
        if self._confirm_deliveries:
            self._num_published = 0
            self._delivery_info: deque[Any] = deque()
        self._testing_mode = testing_mode

        self._awaiting_response: dict[str, asyncio.Future[Any]] = {}

        self._connection = connection
        self._channel: aio_pika.abc.AbstractChannel | None = None
        self._exchange: aio_pika.abc.AbstractExchange | None = None
        self._reply_queue: aio_pika.abc.AbstractQueue | None = None

        self._is_closing = False

    @property
    def is_closing(self) -> bool:
        return self._is_closing

    @property
    def is_connected(self) -> aio_pika.abc.AbstractChannel | None:
        return self._channel

    async def connect(self) -> None:
        if self.is_connected:
            return

        self._channel = await self._connection.channel(
            publisher_confirms=self._confirm_deliveries, on_return_raises=True
        )
        self._channel.close_callbacks.add(self._on_channel_close)

        self._exchange = await self._channel.declare_exchange(name=self.get_exchange_name(), **self._exchange_params)

        # Declare the reply queue
        reply_queue_name = f'{self._exchange_name}-reply-{uuid.uuid4()}'
        self._reply_queue = await self._channel.declare_queue(
            name=reply_queue_name,
            exclusive=True,
            auto_delete=self._testing_mode,
            arguments={'x-expires': defaults.REPLY_QUEUE_EXPIRES},
        )

        await self._reply_queue.bind(self._exchange, routing_key=reply_queue_name)
        await self._reply_queue.consume(self._on_response, no_ack=True)

    async def disconnect(self) -> None:
        if not self.is_closing:
            self._is_closing = True
            channel = self._channel
            if channel is not None and not channel.is_closed:
                await channel.close()
            self._channel = None

    def action_message(self, message: Any) -> Any:
        """Execute a message that involves communication.

        :param message: The message to execute.
        :return: A future corresponding to the action.
        """
        message.send(self)
        return message.future

    async def publish(self, message: aio_pika.Message, routing_key: str, mandatory: bool = True) -> Any:
        """Send a fire-and-forget message i.e. no response expected.

        :param message: The message to send.
        :param routing_key: The routing key.
        :param mandatory: If the message cannot be routed this will raise an unroutable exception.
        """
        assert self._exchange is not None
        result = await self._exchange.publish(message, routing_key=routing_key, mandatory=mandatory)
        return result

    async def publish_expect_response(
        self, message: aio_pika.Message, routing_key: str, mandatory: bool = True
    ) -> tuple[Any, asyncio.Future[Any]]:
        # If there is no correlation id we have to set one so that we know what the response will be to
        if not message.correlation_id:
            message.correlation_id = str(uuid.uuid4())
        correlation_id: str = message.correlation_id

        response_future: asyncio.Future[Any] = asyncio.Future()
        self._awaiting_response[correlation_id] = response_future
        try:
            result = await self.publish(message, routing_key=routing_key, mandatory=mandatory)
        except BaseException:
            self._awaiting_response.pop(correlation_id, None)
            raise
        return result, response_future

    def get_exchange_name(self) -> str:
        return self._exchange_name

    def channel(self) -> aio_pika.abc.AbstractChannel | None:
        return self._channel

    async def _on_response(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        """Called when we get a message on our response queue.

        :param message: The response message.
        """
        correlation_id = message.correlation_id
        if correlation_id is None:
            _LOGGER.error("Got a response for an unknown id '%s':\n%s", correlation_id, message)
            return
        try:
            response_future = self._awaiting_response.pop(correlation_id)
        except KeyError:
            _LOGGER.error("Got a response for an unknown id '%s':\n%s", correlation_id, message)
        else:
            try:
                response = self._response_decode(message.body)
            except Exception:
                _LOGGER.error('Failed to decode message body:\n%s%s', message.body, traceback.format_exc())
                raise
            else:
                utils.response_to_future(response, response_future)
                try:
                    # If the response was a future it means we should get another message that
                    # resolves that future
                    if asyncio.isfuture(response_future.result()):
                        self._awaiting_response[correlation_id] = response_future.result()
                except Exception:  # pylint: disable=broad-except
                    pass

    def _on_channel_close(self, _closing_future: Any, *args: Any, **kwargs: Any) -> None:
        """Reset all channel specific members."""
        if self._confirm_deliveries:
            self._num_published = 0
            self._delivery_info = deque()
