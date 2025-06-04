"""Tests for the :mod:`aiida.tools.pytest_fixtures.orm` module."""

import uuid

import pytest

from aiida.orm import Computer
from aiida.transports import AsyncTransport, BlockingTransport

# This is needed when we run this file in isolation using
# the `--noconftest` pytest option in the 'test-pytest-fixtures' CI job.
pytest_plugins = ['aiida.manage.tests.pytest_fixtures']


@pytest.mark.parametrize(
    'fixture_name, transport_cls, transport_type',
    [
        ('aiida_computer_ssh', BlockingTransport, 'core.ssh'),
        ('aiida_computer_local', BlockingTransport, 'core.local'),
        ('aiida_computer_ssh_async', AsyncTransport, 'core.ssh_async'),
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
