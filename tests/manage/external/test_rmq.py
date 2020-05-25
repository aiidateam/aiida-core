"""Tests for the `aiida.manage.external.rmq` module."""
from aiida.manage.external import rmq


def test_get_rmq_url():
    """Test the `get_rmq_url` method."""
    assert rmq.get_rmq_url() == 'amqp://guest:guest@127.0.0.1:5672?heartbeat=600'

    connection_params = {
        'protocol': 'amqps',
        'username': 'jojo',
        'password': 'rabbit',
        'host': '192.168.0.1',
        'port': 6783,
        'heartbeat_timeout': 0
    }

    template = '{protocol}://{username}:{password}@{host}:{port}?heartbeat={heartbeat_timeout}'
    assert rmq.get_rmq_url(**connection_params) == template.format(**connection_params)
