import unittest 

from aiida.transport.plugins.local import *
from aiida.transport.plugin_test import *

aiida.transport.plugin_test.custom_transport = LocalTransport()
    
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
