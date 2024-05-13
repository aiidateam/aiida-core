"""Defaults related to RabbitMQ."""

from __future__ import annotations

import typing as t

from aiida.common.extendeddicts import AttributeDict

__all__ = ('BROKER_DEFAULTS',)

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

    connection_params = dict(BROKER_DEFAULTS)

    try:
        connect(connection_params=connection_params)
    except ConnectionError:
        return None

    return connection_params
