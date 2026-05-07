"""Tests for the :mod:`aiida.tools.pytest_fixtures.orm` module."""

import uuid
from unittest.mock import patch

import pytest

from aiida.common.exceptions import IntegrityError, NotExistent
from aiida.orm import Computer
from aiida.transports import AsyncTransport, BlockingTransport
from aiida.transports.plugins.async_backend import _AsyncSSH, _OpenSSH

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.tools.pytest_fixtures']


def test_aiida_localhost(aiida_localhost):
    """Test the ``aiida_localhost`` fixture.

    The label is suffixed with the pytest-xdist worker id to avoid collisions with literal
    ``'localhost'`` Computers created by other tests or commands (e.g. ``verdi presto``).
    """
    # Assert at the contract level (the suffix exists) rather than coupling to the specific
    # worker-id value, which depends on ``PYTEST_XDIST_WORKER`` at runtime.
    assert aiida_localhost.label.startswith('localhost-')
    assert aiida_localhost.hostname == 'localhost'
    assert aiida_localhost.transport_type == 'core.local'
    assert aiida_localhost.scheduler_type == 'core.direct'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_localhost_no_literal_collision(request):
    """The fixture's Computer must coexist with a pre-existing literal ``'localhost'`` Computer.

    ``verdi presto`` and other code paths create a Computer with the literal ``'localhost'``
    label in the same profile. This is the actual #7347 failure
    order: the literal row is inserted first, then ``aiida_localhost`` is requested. Worker-
    suffixing the fixture's label makes its row distinct from any literal-label row already in
    the database, so no UNIQUE-constraint collision can fire.
    """
    Computer(
        label='localhost',
        hostname='localhost',
        transport_type='core.ssh',
        scheduler_type='core.direct',
        workdir='/tmp',
    ).store()

    # Defer the fixture's creation until *after* the literal-``'localhost'`` row exists, mirroring
    # the actual #7347 failure order. If we depended on ``aiida_localhost`` via the test signature,
    # pytest would evaluate it before the test body runs and the literal row would not yet be
    # present — we'd be testing the wrong direction of the race.
    aiida_localhost = request.getfixturevalue('aiida_localhost')

    assert aiida_localhost.label != 'localhost'
    assert aiida_localhost.transport_type == 'core.local'


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
    """The fallback ``get()`` returns the racing worker's row.

    Simulates the xdist race where a row exists in the shared DB but our session
    can't see it on the first ``get()`` (as if ``aiida_profile_clean`` just wiped
    things from this worker's POV); ``store()`` then fails with ``IntegrityError``
    on the UNIQUE label constraint, and the fallback ``get()`` finds the row.
    """
    label = f'test-fallback-{uuid.uuid4().hex}'
    existing = aiida_computer(label=label)

    with (
        patch.object(
            type(Computer.collection),
            'get',
            side_effect=[NotExistent('First get: DB was just cleaned'), existing],
        ),
        patch.object(Computer, 'store', side_effect=IntegrityError('UNIQUE constraint failed')),
    ):
        recovered = aiida_computer(label=label)

    assert recovered.pk == existing.pk
    assert recovered.uuid == existing.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_integrity_error_rebuild(aiida_computer):
    """The fallback ``get()`` also misses, so the fixture rebuilds and stores fresh.

    Rare follow-up to the fallback case: ``store()`` raised ``IntegrityError`` (so
    the racing worker's row should be there), but by the time we re-query it has
    already vanished. The fixture must then build a new ``Computer`` and store it.
    """
    label = f'test-rebuild-{uuid.uuid4().hex}'

    # store() fails the first time (simulating the race) and persists for real on
    # the second call (the rebuild). ``autospec=True`` is required so the mock
    # passes ``self`` to ``store_side_effect``, which we need to call through.
    original_store = Computer.store
    store_calls = {'n': 0}

    def store_side_effect(self):
        store_calls['n'] += 1
        if store_calls['n'] == 1:
            raise IntegrityError('UNIQUE constraint failed')
        return original_store(self)

    with (
        patch.object(
            type(Computer.collection),
            'get',
            side_effect=[
                NotExistent('First get: DB was just cleaned'),
                NotExistent('Second get: racing worker row vanished'),
            ],
        ),
        patch.object(Computer, 'store', autospec=True, side_effect=store_side_effect),
    ):
        recovered = aiida_computer(label=label)

    assert recovered.is_stored
    assert recovered.label == label
    assert store_calls['n'] == 2


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
