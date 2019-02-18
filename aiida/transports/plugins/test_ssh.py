# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Test ssh plugin on localhost
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
import logging

import aiida.transports
import aiida.transports.transport
import paramiko
from aiida.transports.plugins.ssh import SshTransport

# This will be used by test_all_plugins

plugin_transport = SshTransport(machine='localhost', timeout=30, load_system_host_keys=True, key_policy='AutoAddPolicy')


class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """

    def test_closed_connection_ssh(self):
        with self.assertRaises(aiida.transports.transport.TransportInternalError):
            t = SshTransport(machine='localhost')
            t._exec_command_internal('ls')

    def test_closed_connection_sftp(self):
        with self.assertRaises(aiida.transports.transport.TransportInternalError):
            t = SshTransport(machine='localhost')
            t.listdir()

    def test_invalid_param(self):
        with self.assertRaises(ValueError):
            SshTransport(machine='localhost', invalid_param=True)

    def test_auto_add_policy(self):
        with SshTransport(machine='localhost', timeout=30, load_system_host_keys=True, key_policy='AutoAddPolicy'):
            pass

    def test_no_host_key(self):
        # Disable logging to avoid output during test
        logging.disable(logging.ERROR)

        with self.assertRaises(paramiko.SSHException):
            with SshTransport(machine='localhost', timeout=30, load_system_host_keys=False):
                pass

        # Reset logging level
        logging.disable(logging.NOTSET)


if __name__ == '__main__':
    unittest.main()
