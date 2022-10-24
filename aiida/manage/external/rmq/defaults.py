# -*- coding: utf-8 -*-
"""Defaults related to RabbitMQ."""
import pamqp.encode

from aiida.common.extendeddicts import AttributeDict

# The following statement enables support for RabbitMQ 3.5 because without it, connections established by `aiormq` will
# fail because the interpretation of the types of integers passed in connection parameters has changed after that
# version. Once RabbitMQ 3.5 is no longer supported (it has been EOL since October 2016) this can be removed. This
# should also allow to remove the direct dependency on `pamqp` entirely.
pamqp.encode.support_deprecated_rabbitmq()

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
