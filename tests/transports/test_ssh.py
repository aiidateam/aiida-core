# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the `SshTransport` plugin on localhost."""
import logging
import unittest

import paramiko

from aiida.transports.plugins.ssh import SshTransport
from aiida.transports.transport import TransportInternalError

# This will be used by test_all_plugins

plugin_transport = SshTransport(machine='localhost', timeout=30, load_system_host_keys=True, key_policy='AutoAddPolicy')


class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """

    def test_closed_connection_ssh(self):
        """Test calling command on a closed connection."""
        with self.assertRaises(TransportInternalError):
            transport = SshTransport(machine='localhost')
            transport._exec_command_internal('ls')  # pylint: disable=protected-access

    def test_closed_connection_sftp(self):
        """Test calling sftp command on a closed connection."""
        with self.assertRaises(TransportInternalError):
            transport = SshTransport(machine='localhost')
            transport.listdir()

    @staticmethod
    def test_auto_add_policy():
        """Test the auto add policy."""
        with SshTransport(machine='localhost', timeout=30, load_system_host_keys=True, key_policy='AutoAddPolicy'):
            pass

    def test_no_host_key(self):
        """Test if there is no host key."""
        # Disable logging to avoid output during test
        logging.disable(logging.ERROR)

        with self.assertRaises(paramiko.SSHException):
            with SshTransport(machine='localhost', timeout=30, load_system_host_keys=False):
                pass

        # Reset logging level
        logging.disable(logging.NOTSET)
