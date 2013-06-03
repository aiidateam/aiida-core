import unittest 

from aiida.transport.plugins.local import *
from aiida.common.pluginloader import load_plugin
from aiida.transport.plugin_test import *

from aiida.transport import Transport
PluginTransport = load_plugin(
    Transport,'aiida.transport.plugins', 'local')
aiida.transport.plugin_test.custom_transport = PluginTransport()
    
class TestGeneric(unittest.TestCase):
    """
    Test whoami on localhost.
    """
    def test_whoami(self):
        import getpass
        with LocalTransport() as t:
            self.assertEquals( t.whoami() , getpass.getuser() )    
    
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
