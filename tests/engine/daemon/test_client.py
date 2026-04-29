###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the `DaemonClient` class."""

from unittest.mock import patch

import pytest
import zmq

from aiida.engine.daemon.client import (
    DaemonClient,
    DaemonNotRunningException,
    DaemonTimeoutException,
    get_daemon_client,
)

pytestmark = pytest.mark.requires_broker


def test_ipc_socket_file_length_limit():
    """The maximum length of socket filepaths is often limited by the operating system.
    For MacOS it is limited to 103 bytes, versus 107 bytes on Unix. This limit is
    exposed by the Zmq library which is used by Circus library that is used to
    daemonize the daemon runners. This test verifies that the three endpoints used
    for the Circus client have a filepath that does not exceed that path limit.

    See issue #1317 and pull request #1403 for the discussion
    """
    daemon_client = get_daemon_client()

    controller_endpoint = daemon_client.get_controller_endpoint()
    pubsub_endpoint = daemon_client.get_pubsub_endpoint()
    stats_endpoint = daemon_client.get_stats_endpoint()

    assert len(controller_endpoint) <= zmq.IPC_PATH_MAX_LEN
    assert len(pubsub_endpoint) <= zmq.IPC_PATH_MAX_LEN
    assert len(stats_endpoint) <= zmq.IPC_PATH_MAX_LEN


def test_get_daemon_client_non_default_profile(profile_factory, empty_config):
    """Test that ``get_daemon_client`` returns a client for the requested profile, not the default."""
    profile_default = profile_factory('default-profile')
    profile_other = profile_factory('other-profile')
    empty_config.add_profile(profile_default)
    empty_config.add_profile(profile_other)
    empty_config.set_default_profile('default-profile', overwrite=True).store()

    client = get_daemon_client('other-profile')
    assert client.profile.name == 'other-profile'


def test_get_daemon_client_does_not_switch_profile(empty_config, profile_factory):
    """Test that ``get_daemon_client`` does not switch the loaded profile."""
    from aiida.manage import get_manager

    profile_default = profile_factory(
        'default',
        storage_backend='core.sqlite_dos',
        process_control_backend='rabbitmq',
        repository_dirpath=empty_config.dirpath,
    )
    profile_other = profile_factory(
        'other',
        storage_backend='core.sqlite_dos',
        process_control_backend='rabbitmq',
        repository_dirpath=empty_config.dirpath,
    )

    empty_config.add_profile(profile_default)
    empty_config.add_profile(profile_other)
    empty_config.set_default_profile(profile_default.name, overwrite=True)
    empty_config.store()

    manager = get_manager()
    manager.load_profile(profile_other.name, allow_switch=True)

    assert manager.get_profile().name == profile_other.name
    assert get_daemon_client(profile_default.name).profile.name == profile_default.name
    assert manager.get_profile().name == profile_other.name


def test_get_status_daemon_not_running(stopped_daemon_client):
    """Test ``DaemonClient.get_status`` output when the daemon is not running."""
    with pytest.raises(DaemonNotRunningException, match='The daemon is not running.'):
        stopped_daemon_client.get_status()


def raise_daemon_timeout():
    """Raise a ``DaemonTimeoutException``."""
    raise DaemonTimeoutException('Connection to the daemon timed out.')


@patch.object(DaemonClient, 'get_status', lambda _: raise_daemon_timeout())
def test_get_status_timeout(stopped_daemon_client):
    """Test ``DaemonClient.get_status`` output when the circus daemon process cannot be reached."""
    with pytest.raises(DaemonTimeoutException, match='Connection to the daemon timed out.'):
        stopped_daemon_client.get_status()
