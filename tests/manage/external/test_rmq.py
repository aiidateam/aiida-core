# -*- coding: utf-8 -*-
"""Tests for the `aiida.manage.external.rmq` module."""
import pytest

from aiida.manage.external import rmq


@pytest.mark.parametrize(('args', 'kwargs', 'expected'), (
    ((), {}, 'amqp://guest:guest@127.0.0.1:5672?'),
    ((), {'heartbeat': 1}, 'amqp://guest:guest@127.0.0.1:5672?'),
    ((), {'invalid_parameters': 1}, ValueError),
    ((), {'cafile': 'file', 'cadata': 'ab'}, 'amqp://guest:guest@127.0.0.1:5672?'),
    (('amqps', 'jojo', 'rabbit', '192.168.0.1', 6783), {}, 'amqps://jojo:rabbit@192.168.0.1:6783?'),
))  # yapf: disable
def test_get_rmq_url(args, kwargs, expected):
    """Test the `get_rmq_url` method.

    It is not possible to use a complete hardcoded URL to compare to the return value of `get_rmq_url` because the order
    of the query parameters are arbitrary. Therefore, we just compare the rest of the URL and make sure that all query
    parameters are present in the expected form separately.
    """
    if isinstance(expected, str):
        url = rmq.get_rmq_url(*args, **kwargs)
        assert url.startswith(expected)
        for key, value in kwargs.items():
            assert '{}={}'.format(key, value) in url
    else:
        with pytest.raises(expected):
            rmq.get_rmq_url(*args, **kwargs)
