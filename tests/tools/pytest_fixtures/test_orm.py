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


@pytest.mark.parametrize(
    'fallback_get_misses',
    [False, True],
    ids=['fallback_get_succeeds', 'fallback_get_misses_rebuilds'],
)
@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_integrity_error_recovery(aiida_computer, fallback_get_misses):
    """Cover both branches of the ``IntegrityError`` recovery path under xdist races.

    In both cases, the first ``get()`` misses (as if ``aiida_profile_clean`` wiped
    the DB) and ``store()`` fails with ``IntegrityError`` (another worker re-created
    the computer). The two branches differ in what the fallback ``get()`` sees:

    - ``fallback_get_succeeds``: it finds the racing worker's row and returns it.
    - ``fallback_get_misses_rebuilds``: it raises ``NotExistent`` again (rare),
      so the fixture rebuilds and stores fresh.
    """
    from unittest.mock import patch

    from aiida.common.exceptions import IntegrityError, NotExistent

    label = f'test-recovery-{uuid.uuid4().hex}'

    pre_existing = aiida_computer(label=label) if not fallback_get_misses else None

    if fallback_get_misses:
        get_side_effect = [
            NotExistent('First get: DB was just cleaned'),
            NotExistent('Second get: racing worker row vanished'),
        ]
    else:
        get_side_effect = [NotExistent('First get: DB was just cleaned'), pre_existing]

    original_store = Computer.store
    store_calls = {'n': 0}

    def store_side_effect(self):
        store_calls['n'] += 1
        if store_calls['n'] == 1:
            raise IntegrityError('UNIQUE constraint failed')
        return original_store(self)

    with (
        patch.object(type(Computer.collection), 'get', side_effect=get_side_effect),
        patch.object(Computer, 'store', autospec=True, side_effect=store_side_effect),
    ):
        recovered = aiida_computer(label=label)

    assert recovered.is_stored
    assert recovered.label == label
    if fallback_get_misses:
        assert store_calls['n'] == 2  # rebuild path: first store failed, second persisted
    else:
        assert pre_existing is not None
        assert recovered.pk == pre_existing.pk
        assert store_calls['n'] == 1  # fallback path: only the failing store ran


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
