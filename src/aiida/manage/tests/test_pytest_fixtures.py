"""Tests for the :mod:`aiida.manage.tests.pytest_fixtures` module."""

import uuid

import pytest

from aiida.manage.configuration import get_config
from aiida.manage.configuration.config import Config
from aiida.orm import Computer
from aiida.transports import BlockingTransport

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


def test_profile_config():
    """Check that the config file created with the test profile passes validation."""
    Config.from_file(get_config().filepath)


def test_aiida_localhost(aiida_localhost):
    """Test the ``aiida_localhost`` fixture."""
    assert aiida_localhost.label == 'localhost'


@pytest.mark.parametrize(
    'fixture_name, transport_cls, transport_type',
    [
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


def test_deamon_client(daemon_client):
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
    daemon_client.start_daemon()
    daemon_client.stop_daemon(wait=True)


def test_started_daemon_client(started_daemon_client):
    assert started_daemon_client.is_daemon_running


def test_stopped_daemon_client(stopped_daemon_client):
    assert not stopped_daemon_client.is_daemon_running
