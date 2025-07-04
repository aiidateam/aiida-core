"""Tests for the :mod:`aiida.manage.tests.pytest_fixtures` module."""

import uuid
from pathlib import Path

import pytest

from aiida.manage.configuration import get_config, load_config
from aiida.manage.configuration.settings import DEFAULT_CONFIG_FILE_NAME
from aiida.orm import Computer
from aiida.transports import BlockingTransport

pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


def test_aiida_config(tmp_path_factory):
    """Test that ``aiida_config`` fixture is loaded by default and creates a config instance in temp directory."""
    from aiida.manage.configuration import CONFIG

    config = get_config(create=False)
    assert config is CONFIG
    assert config.dirpath.startswith(str(tmp_path_factory.getbasetemp()))
    assert Path(config.dirpath, DEFAULT_CONFIG_FILE_NAME).is_file()
    assert config._default_profile


def test_aiida_config_file(tmp_path_factory):
    """Test that ``aiida_config`` fixture stores the configuration in a config file in a temp directory."""
    # Unlike get_config, load_config always loads the configuration from a file
    config = load_config(create=False)
    assert config.dirpath.startswith(str(tmp_path_factory.getbasetemp()))
    assert Path(config.dirpath, DEFAULT_CONFIG_FILE_NAME).is_file()
    assert config._default_profile


def test_aiida_profile():
    """Test that ``aiida_profile`` fixture is loaded by default and loads a temporary test profile."""
    from aiida.manage.configuration import get_profile
    from aiida.manage.configuration.profile import Profile

    profile = get_profile()
    assert isinstance(profile, Profile)
    assert profile.is_test_profile


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


def test_deamon_client(daemon_client):
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
    daemon_client.start_daemon()
    daemon_client.stop_daemon(wait=True)


def test_started_daemon_client(started_daemon_client):
    assert started_daemon_client.is_daemon_running


def test_stopped_daemon_client(stopped_daemon_client):
    assert not stopped_daemon_client.is_daemon_running
