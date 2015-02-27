# -*- coding: utf-8 -*-
import unittest 

from aiida.transport.plugins.local import *

# This will be used by test_all_plugins

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi"

plugin_transport = LocalTransport()
    
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
