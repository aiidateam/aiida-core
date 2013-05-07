import unittest
import logging
import aida
from aida.transport.plugins.local import *
from aida.common.pluginloader import load_plugin
from aida.transport.plugin_test import *

from aida.transport import Transport
PluginTransport = load_plugin(
    Transport,'aida.transport.plugins', 'local')
aida.transport.plugin_test.custom_transport = PluginTransport()
    
class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """
    def test_closed_connection(self):
        with self.assertRaises(aida.transport.TransportInternalError):
            t = LocalTransport()
            t.listdir()
            
    def test_invalid_param(self):
        with self.assertRaises(ValueError):
            LocalTransport(unrequired_var='something')
            
    def test_basic(self):
        with LocalTransport() as t:
            pass

if __name__ == '__main__':
    unittest.main()
