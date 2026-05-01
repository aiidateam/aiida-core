"""Tests for the :mod:`aiida.tools.pytest_fixtures.orm` module."""

import uuid

import pytest

from aiida.orm import Computer
from aiida.transports import AsyncTransport, BlockingTransport
from aiida.transports.plugins.async_backend import _AsyncSSH, _OpenSSH

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.tools.pytest_fixtures']


def test_aiida_localhost(aiida_localhost):
    """Test the ``aiida_localhost`` fixture."""
    assert aiida_localhost.label == 'localhost'


@pytest.mark.parametrize(
    'fixture_name, transport_cls, transport_type',
    [
        ('aiida_computer_ssh', BlockingTransport, 'core.ssh'),
        ('aiida_computer_local', BlockingTransport, 'core.local'),
    ],
)
@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_fixtures(fixture_name, transport_cls, transport_type, request):
    """Test the computer fixtures."""
    aiida_computer = request.getfixturevalue(fixture_name)
    computer = aiida_computer()

    assert isinstance(computer, Computer)
    assert computer.is_configured
    assert computer.hostname == 'localhost'
    assert computer.transport_type == transport_type

    with computer.get_transport() as transport:
        assert isinstance(transport, transport_cls)

    # Calling it again with the same label should simply return the existing computer
    computer_alt = aiida_computer(label=computer.label)
    assert computer_alt.uuid == computer.uuid

    computer_new = aiida_computer(label=str(uuid.uuid4()))
    assert computer_new.uuid != computer.uuid

    computer_unconfigured = aiida_computer(label=str(uuid.uuid4()), configure=False)
    assert not computer_unconfigured.is_configured


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_integrity_error_fallback(aiida_computer):
    """Test that ``aiida_computer`` falls back to ``get()`` on ``IntegrityError``.

    Simulates the TOCTOU race under xdist where ``get()`` raises ``NotExistent``
    but ``store()`` fails because another worker already created the computer.
    """
    from unittest.mock import patch

    from aiida.common.exceptions import IntegrityError, NotExistent

    # First, create and store the computer normally.
    label = f'test-integrity-{uuid.uuid4().hex}'
    computer = aiida_computer(label=label)

    # Simulate the race: the first get() misses (as if DB was just wiped by
    # another worker's aiida_profile_clean), store() fails with IntegrityError
    # (another worker re-created the computer first), and the fallback get()
    # inside the except block finds the computer.
    original_get = Computer.collection.get

    collection = Computer.collection
    with (
        patch.object(
            type(collection),
            'get',
            side_effect=[NotExistent('Simulated race: DB was just cleaned'), original_get(label=label)],
        ),
        patch.object(Computer, 'store', side_effect=IntegrityError('UNIQUE constraint failed')),
    ):
        fallback_computer = aiida_computer(label=label)

    assert fallback_computer.pk == computer.pk
    assert fallback_computer.uuid == computer.uuid


@pytest.mark.parametrize(
    'backend, backend_class',
    [
        ('openssh', _OpenSSH),
        ('asyncssh', _AsyncSSH),
    ],
)
@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_fixtures_async(backend, backend_class, request):
    """Test the computer fixtures."""

    aiida_computer = request.getfixturevalue('aiida_computer_ssh_async')

    # check if the fixture works for configuration parameters, if any
    computer = aiida_computer(label=str(uuid.uuid4()), configure=True, backend=backend)

    assert isinstance(computer, Computer)
    assert computer.is_configured
    assert computer.hostname == 'localhost'
    assert computer.transport_type == 'core.ssh_async'

    with computer.get_transport() as transport:
        assert isinstance(transport, AsyncTransport)
        assert isinstance(transport.async_backend, backend_class)

    # Calling it again with the same label should simply return the existing computer
    computer_alt = aiida_computer(label=computer.label)
    assert computer_alt.uuid == computer.uuid

    computer_new = aiida_computer(label=str(uuid.uuid4()), configure=True, backend=backend)
    assert computer_new.uuid != computer.uuid

    computer_unconfigured = aiida_computer(label=str(uuid.uuid4()), configure=False)
    assert not computer_unconfigured.is_configured
