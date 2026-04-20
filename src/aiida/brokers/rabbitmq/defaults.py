"""Defaults related to RabbitMQ."""

from __future__ import annotations

import asyncio
import os
import typing as t

from aiida.common.extendeddicts import AttributeDict
from aiida.common.log import AIIDA_LOGGER

LOGGER = AIIDA_LOGGER.getChild('brokers.rabbitmq.defaults')

LAUNCH_QUEUE = 'process.queue'
MESSAGE_EXCHANGE = 'messages'
TASK_EXCHANGE = 'tasks'

BROKER_DEFAULTS = AttributeDict(
    {
        'protocol': 'amqp',
        'username': 'guest',
        'password': 'guest',
        'host': '127.0.0.1',
        'port': 5672,
        'virtual_host': '',
        'heartbeat': 600,
    }
)


def detect_rabbitmq_config(
    protocol: str | None = None,
    username: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: int | None = None,
    virtual_host: str | None = None,
) -> dict[str, t.Any]:
    """Try to connect to a RabbitMQ server with the default connection parameters.

    :raises ConnectionError: If the connection failed with the provided connection parameters
    :returns: The connection parameters if the RabbitMQ server was successfully connected to, or ``None`` otherwise.
    """
    import aio_pika

    from .utils import get_rmq_url

    async def probe_rabbitmq_connection(url: str) -> None:
        """Open and close a temporary RabbitMQ connection."""
        connection = await aio_pika.connect_robust(url=url)
        await connection.close()

    protocol = protocol or os.getenv('AIIDA_BROKER_PROTOCOL', BROKER_DEFAULTS['protocol'])
    username = username or os.getenv('AIIDA_BROKER_USERNAME', BROKER_DEFAULTS['username'])
    password = password or os.getenv('AIIDA_BROKER_PASSWORD', BROKER_DEFAULTS['password'])
    host = host or os.getenv('AIIDA_BROKER_HOST', BROKER_DEFAULTS['host'])
    port = port or int(os.getenv('AIIDA_BROKER_PORT', BROKER_DEFAULTS['port']))
    virtual_host = virtual_host or os.getenv('AIIDA_BROKER_VIRTUAL_HOST', BROKER_DEFAULTS['virtual_host'])

    connection_params = {
        'protocol': protocol,
        'username': username,
        'password': password,
        'host': host,
        'port': port,
        'virtual_host': virtual_host,
    }
    url = get_rmq_url(
        protocol=protocol,
        username=username,
        password=password,
        host=host,
        port=str(port),
        virtual_host=virtual_host,
    )

    LOGGER.info(f'Attempting to connect to RabbitMQ with parameters: {connection_params}')

    try:
        # Use a direct temporary connection instead of a ``kiwipy`` communicator.
        # The communicator stack can leave ``aio_pika`` connection objects to be garbage-collected after the event
        # loop has already been closed, which then surfaces as an unraisable ``Connection.__del__`` exception in the
        # test suite.
        asyncio.run(probe_rabbitmq_connection(url))
    except ConnectionError:
        msg = f'Failed to connect with following connection parameters: {connection_params}'
        raise ConnectionError(msg)

    # The profile configuration expects the keys of the broker config to be prefixed with ``broker_``.
    return {f'broker_{key}': value for key, value in connection_params.items()}
