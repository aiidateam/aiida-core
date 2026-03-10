###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the ``AiidaDaemon`` class."""

import pytest

pytestmark = pytest.mark.requires_rmq


def test_get_status_daemon_not_running(stopped_daemon_client):
    """Test ``AiidaDaemon.get_status`` output when the daemon is not running."""
    status = stopped_daemon_client.get_status()
    assert status['status'] == 'stopped'
