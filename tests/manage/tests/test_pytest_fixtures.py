"""Tests for the :mod:`aiida.manage.tests.pytest_fixtures` module."""

import uuid

import pytest

from aiida.manage.configuration import get_config
from aiida.manage.configuration.config import Config
from aiida.orm import Computer
from aiida.transports import Transport


def test_profile_config():
    """Check that the config file created with the test profile passes validation."""
    Config.from_file(get_config().filepath)


def test_aiida_localhost(aiida_localhost):
    """Test the ``aiida_localhost`` fixture."""
    assert aiida_localhost.label == 'localhost'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_local(aiida_computer_local):
    """Test the ``aiida_computer_local`` fixture."""
    computer = aiida_computer_local()
    assert isinstance(computer, Computer)
    assert computer.is_configured
    assert computer.hostname == 'localhost'
    assert computer.transport_type == 'core.local'

    with computer.get_transport() as transport:
        assert isinstance(transport, Transport)

    # Calling it again with the same label should simply return the existing computer
    computer_alt = aiida_computer_local(label=computer.label)
    assert computer_alt.uuid == computer.uuid

    computer_new = aiida_computer_local(label=str(uuid.uuid4()))
    assert computer_new.uuid != computer.uuid

    computer_unconfigured = aiida_computer_local(label=str(uuid.uuid4()), configure=False)
    assert not computer_unconfigured.is_configured


@pytest.mark.usefixtures('aiida_profile_clean')
def test_aiida_computer_ssh(aiida_computer_ssh):
    """Test the ``aiida_computer_ssh`` fixture."""
    computer = aiida_computer_ssh()
    assert isinstance(computer, Computer)
    assert computer.is_configured
    assert computer.hostname == 'localhost'
    assert computer.transport_type == 'core.ssh'

    with computer.get_transport() as transport:
        assert isinstance(transport, Transport)

    # Calling it again with the same label should simply return the existing computer
    computer_alt = aiida_computer_ssh(label=computer.label)
    assert computer_alt.uuid == computer.uuid

    computer_new = aiida_computer_ssh(label=str(uuid.uuid4()))
    assert computer_new.uuid != computer.uuid

    computer_unconfigured = aiida_computer_ssh(label=str(uuid.uuid4()), configure=False)
    assert not computer_unconfigured.is_configured
