# -*- coding: utf-8 -*-
"""Tests for the :mod:`aiida.manage.manager` module."""
import pytest
from packaging.version import parse

from aiida.manage import manager


@pytest.mark.parametrize(
    ('version', 'supported'),
    (
        ('3.5', False),
        ('3.6', True),
        ('3.6.0', True),
        ('3.6.1', True),
        ('3.8', True),
        ('3.8.14', True),
        ('3.8.15', False),
        ('3.9.0', False),
        ('3.9', False),
    ),
)
def test_is_rabbitmq_version_supported(monkeypatch, version, supported, communicator):
    """Test the :func:`aiida.manage.manager.is_rabbitmq_version_supported`."""
    monkeypatch.setattr(manager, 'get_rabbitmq_version', lambda communicator: parse(version))
    assert manager.is_rabbitmq_version_supported(communicator) is supported
