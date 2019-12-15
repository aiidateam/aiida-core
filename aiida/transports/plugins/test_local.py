# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import unittest

from aiida.transports.plugins.local import *

# This will be used by test_all_plugins

plugin_transport = LocalTransport()


class TestGeneric(unittest.TestCase):
    """
    Test whoami on localhost.
    """

    def test_whoami(self):
        import getpass

        with LocalTransport() as t:
            self.assertEqual(t.whoami(), getpass.getuser())


class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """

    def test_closed_connection(self):
        from aiida.transports.transport import TransportInternalError

        with self.assertRaises(TransportInternalError):
            t = LocalTransport()
            t.listdir()

    def test_basic(self):
        with LocalTransport():
            pass


if __name__ == '__main__':
    unittest.main()
