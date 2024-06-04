"""Defaults related to RabbitMQ."""

from __future__ import annotations

import os
import typing as t

from aiida.common.extendeddicts import AttributeDict
from aiida.common.log import AIIDA_LOGGER

__all__ = ('BROKER_DEFAULTS',)

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


def detect_rabbitmq_config() -> dict[str, t.Any] | None:
    """Try to connect to a RabbitMQ server with the default connection parameters.

    :returns: The connection parameters if the RabbitMQ server was successfully connected to, or ``None`` otherwise.
    """
    from kiwipy.rmq.threadcomms import connect

    connection_params = {
        'protocol': os.getenv('AIIDA_BROKER_PROTOCOL', BROKER_DEFAULTS['protocol']),
        'username': os.getenv('AIIDA_BROKER_USERNAME', BROKER_DEFAULTS['username']),
        'password': os.getenv('AIIDA_BROKER_PASSWORD', BROKER_DEFAULTS['password']),
        'host': os.getenv('AIIDA_BROKER_HOST', BROKER_DEFAULTS['host']),
        'port': os.getenv('AIIDA_BROKER_PORT', BROKER_DEFAULTS['port']),
        'virtual_host': os.getenv('AIIDA_BROKER_VIRTUAL_HOST', BROKER_DEFAULTS['virtual_host']),
        'heartbeat': os.getenv('AIIDA_BROKER_HEARTBEAT', BROKER_DEFAULTS['heartbeat']),
    }

    LOGGER.info(f'Attempting to connect to RabbitMQ with parameters: {connection_params}')

    try:
        connect(connection_params=connection_params)
    except ConnectionError:
        return None

    # The profile configuration expects the keys of the broker config to be prefixed with ``broker_``.
    return {f'broker_{key}': value for key, value in connection_params.items()}
