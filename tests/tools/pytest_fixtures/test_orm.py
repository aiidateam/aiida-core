"""Tests for the :mod:`aiida.tools.pytest_fixtures.orm` module."""

import uuid

import pytest

from aiida.orm import Computer
from aiida.transports import AsyncTransport, BlockingTransport
from aiida.transports.plugins import _AsyncSSH, _OpenSSH

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
