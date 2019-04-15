# -*- coding: utf-8 -*-
import unittest

from aiida.transport.plugins.local import *

# This will be used by test_all_plugins

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."

plugin_transport = LocalTransport()


class TestGeneric(unittest.TestCase):
    """
    Test whoami on localhost.
    """

    def test_whoami(self):
        import getpass

        with LocalTransport() as t:
            self.assertEquals(t.whoami(), getpass.getuser())


class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """

    def test_closed_connection(self):
        from aiida.transport import TransportInternalError

        with self.assertRaises(TransportInternalError):
            t = LocalTransport()
            t.listdir()

    def test_invalid_param(self):
        with self.assertRaises(ValueError):
            LocalTransport(unrequired_var='something')

    def test_basic(self):
        with LocalTransport():
            pass


if __name__ == '__main__':
    unittest.main()
