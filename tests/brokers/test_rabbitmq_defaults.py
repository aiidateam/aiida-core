###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.brokers.rabbitmq.defaults`."""

import subprocess
import sys
import textwrap

import pytest

from aiida.brokers.rabbitmq import defaults


@pytest.fixture
def connection_params():
    """Return RabbitMQ connection parameters for tests."""
    return {
        'protocol': 'amqps',
        'username': 'user',
        'password': 'password',
        'host': 'host',
        'port': 1234,
        'virtual_host': 'virtual-host',
    }


def test_detect_rabbitmq_config(monkeypatch, connection_params):
    """Test ``detect_rabbitmq_config`` returns the broker configuration on success."""
    captured = {}
    monkeypatch.setattr(defaults, '_probe_rabbitmq_connection', lambda params: captured.setdefault('params', params))

    result = defaults.detect_rabbitmq_config(**connection_params)

    assert captured['params'] == connection_params
    assert result == {f'broker_{key}': value for key, value in connection_params.items()}


def test_detect_rabbitmq_config_raises_connection_error(monkeypatch):
    """Test ``detect_rabbitmq_config`` raises ``ConnectionError`` on failure."""

    def probe(_):
        raise RuntimeError('failed to connect')

    monkeypatch.setattr(defaults, '_probe_rabbitmq_connection', probe)

    with pytest.raises(ConnectionError, match='Failed to connect with following connection parameters'):
        defaults.detect_rabbitmq_config()


def test_detect_rabbitmq_config_failed_probe_does_not_emit_cleanup_warning():
    """Test failed probes do not emit asyncio cleanup warnings on interpreter shutdown."""
    code = textwrap.dedent("""
        from aiida.brokers.rabbitmq.defaults import detect_rabbitmq_config

        try:
            detect_rabbitmq_config(host='127.0.0.1', port=1)
        except ConnectionError:
            pass
        """)

    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert 'error when creating transport' not in result.stderr
    assert 'Exception ignored while calling deallocator' not in result.stderr
    assert "coroutine 'RobustConnection.close' was never awaited" not in result.stderr


def test_probe_rabbitmq_connection_closes_connection_on_failure(monkeypatch):
    """Test ``_probe_rabbitmq_connection`` closes the connection if connecting fails."""
    connection = None

    class DummyConnection:
        def __init__(self, url, loop):
            nonlocal connection
            self.url = url
            self.loop = loop
            self.closed = False
            connection = self

        async def connect(self):
            raise RuntimeError('failed to connect')

        async def close(self):
            self.closed = True

    monkeypatch.setattr(defaults, 'make_url', lambda **kwargs: kwargs)
    monkeypatch.setattr(defaults, 'RobustConnection', DummyConnection)

    with pytest.raises(RuntimeError, match='failed to connect'):
        defaults._probe_rabbitmq_connection(
            {
                'protocol': 'amqp',
                'username': 'guest',
                'password': 'guest',
                'host': '127.0.0.1',
                'port': 5672,
                'virtual_host': '',
            }
        )

    assert connection is not None
    assert connection.closed is True
