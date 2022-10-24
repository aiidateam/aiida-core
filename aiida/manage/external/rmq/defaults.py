# -*- coding: utf-8 -*-
"""Defaults related to RabbitMQ."""
from aiida.common.extendeddicts import AttributeDict

__all__ = ('BROKER_DEFAULTS',)

LAUNCH_QUEUE = 'process.queue'
MESSAGE_EXCHANGE = 'messages'
TASK_EXCHANGE = 'tasks'

BROKER_DEFAULTS = AttributeDict({
    'protocol': 'amqp',
    'username': 'guest',
    'password': 'guest',
    'host': '127.0.0.1',
    'port': 5672,
    'virtual_host': '',
    'heartbeat': 600,
})
