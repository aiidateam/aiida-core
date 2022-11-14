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
import pytest
import zmq

from aiida.engine.daemon.client import get_daemon_client


@pytest.mark.usefixtures('aiida_profile')
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
