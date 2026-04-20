###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.brokers.rabbitmq.defaults`."""

from __future__ import annotations

import pytest

from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config


class FakeConnection:
    """Fake RabbitMQ connection."""

    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        """Close the connection."""
        self.closed = True


def test_detect_rabbitmq_config_closes_connection(monkeypatch):
    """Test ``detect_rabbitmq_config`` closes the temporary connection."""
    connection = FakeConnection()

    async def connect_robust(*args, **kwargs):
        return connection

    import aio_pika

    monkeypatch.setattr(aio_pika, 'connect_robust', connect_robust)

    result = detect_rabbitmq_config(protocol='amqp', username='guest', password='guest', host='127.0.0.1', port=5672)

    assert result == {
        'broker_protocol': 'amqp',
        'broker_username': 'guest',
        'broker_password': 'guest',
        'broker_host': '127.0.0.1',
        'broker_port': 5672,
        'broker_virtual_host': '',
    }
    assert connection.closed is True


def test_detect_rabbitmq_config_wraps_connection_error(monkeypatch):
    """Test ``detect_rabbitmq_config`` wraps connection errors consistently."""

    async def connect_robust(*args, **kwargs):
        raise ConnectionError('failed to connect')

    import aio_pika

    monkeypatch.setattr(aio_pika, 'connect_robust', connect_robust)

    with pytest.raises(ConnectionError, match='Failed to connect with following connection parameters'):
        detect_rabbitmq_config(host='127.0.0.1', port=5672)
