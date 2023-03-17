# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
"""Unit tests for the `DaemonClient` class."""
from unittest.mock import patch

import zmq

from aiida.engine.daemon.client import DaemonClient, get_daemon_client


def test_ipc_socket_file_length_limit():
    """
    The maximum length of socket filepaths is often limited by the operating system.
    For MacOS it is limited to 103 bytes, versus 107 bytes on Unix. This limit is
    exposed by the Zmq library which is used by Circus library that is used to
    daemonize the daemon runners. This test verifies that the three endpoints used
    for the Circus client have a filepath that does not exceed that path limit.

    See issue #1317 and pull request #1403 for the discussion
    """
    # pylint: disable=no-member

    daemon_client = get_daemon_client()

    controller_endpoint = daemon_client.get_controller_endpoint()
    pubsub_endpoint = daemon_client.get_pubsub_endpoint()
    stats_endpoint = daemon_client.get_stats_endpoint()

    assert len(controller_endpoint) <= zmq.IPC_PATH_MAX_LEN
    assert len(pubsub_endpoint) <= zmq.IPC_PATH_MAX_LEN
    assert len(stats_endpoint) <= zmq.IPC_PATH_MAX_LEN


def test_get_status_daemon_not_running(stopped_daemon_client):
    """Test ``DaemonClient.get_status`` output when the daemon is not running."""
    status = stopped_daemon_client.get_status()
    assert status.is_running is False
    assert status.error is False
    assert status.message == 'The daemon is not running.'


@patch.object(DaemonClient, 'get_daemon_status', lambda _: {'status': 'timeout'})
def test_get_status_circus_timeout(stopped_daemon_client):
    """Test ``DaemonClient.get_status`` output when the circus daemon process cannot be reached."""
    status = stopped_daemon_client.get_status()
    assert status.is_running is False
    assert status.error is True
    assert status.message == 'The daemon is running but the call to the circus controller timed out.'
