"""
Test ssh plugin on localhost
"""
import unittest
import logging

from aiida.transport.plugins.ssh import *

import aiida.transport.plugin_test
from aiida.transport.plugin_test import *

from aiida.transport import Transport
global custom_transport

aiida.transport.plugin_test.custom_transport = SshTransport(
    machine='localhost', timeout=30, 
    load_system_host_keys=True,
    key_policy = 'AutoAddPolicy')

class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """
    
    def test_closed_connection_ssh(self):
        with self.assertRaises(aiida.transport.TransportInternalError):
            t = SshTransport(machine='localhost')
            t._exec_command_internal('ls')
            
    def test_closed_connection_sftp(self):
        with self.assertRaises(aiida.transport.TransportInternalError):
            t = SshTransport(machine='localhost')
            t.listdir()
            
    def test_invalid_param(self):
        with self.assertRaises(ValueError):
            SshTransport(machine='localhost', invalid_param=True)
                             

    def test_auto_add_policy(self):
        with SshTransport(machine='localhost', timeout=30, 
                          load_system_host_keys=True,
                          key_policy='AutoAddPolicy') as t:
            pass

    def test_no_host_key(self):
        # Disable logging to avoid output during test
        logging.disable(logging.ERROR)

        with self.assertRaises(paramiko.SSHException):
            with SshTransport(machine='localhost', timeout=30, 
                              load_system_host_keys = False) as t:
                pass

        # Reset logging level
        logging.disable(logging.NOTSET)


if __name__ == '__main__': 
    unittest.main()
