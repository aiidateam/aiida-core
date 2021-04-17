# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `LocalTransport`."""
import unittest

from aiida.transports.plugins.local import LocalTransport
from aiida.transports.transport import TransportInternalError

# This will be used by test_all_plugins

plugin_transport = LocalTransport()


class TestGeneric(unittest.TestCase):
    """
    Test whoami on localhost.
    """

    def test_whoami(self):
        """Test the `whoami` command."""
        import getpass

        with LocalTransport() as transport:
            self.assertEqual(transport.whoami(), getpass.getuser())


class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """

    def test_closed_connection(self):
        """Test running a command on a closed connection."""

        with self.assertRaises(TransportInternalError):
            transport = LocalTransport()
            transport.listdir()

    @staticmethod
    def test_basic():
        """Test constructor."""
        with LocalTransport():
            pass


def test_gotocomputer():
    """Test gotocomputer"""
    with LocalTransport() as transport:
        cmd_str = transport.gotocomputer_command('/remote_dir/')

        expected_str = (
            """bash -c  "if [ -d '/remote_dir/' ] ;"""
            """ then cd '/remote_dir/' ; bash -l  ; else echo '  ** The directory' ; """
            """echo '  ** /remote_dir/' ; echo '  ** seems to have been deleted, I logout...' ; fi" """
        )
        assert cmd_str == expected_str

        cmd_str = transport.gotocomputer_command('/remote_dir/', "-c 'echo Hello World'")

        expected_str = (
            """bash -c  "if [ -d '/remote_dir/' ] ;"""
            """ then cd '/remote_dir/' ; bash -l  -c 'echo Hello World'; else echo '  ** The directory' ; """
            """echo '  ** /remote_dir/' ; echo '  ** seems to have been deleted, I logout...' ; fi" """
        )
        assert cmd_str == expected_str
