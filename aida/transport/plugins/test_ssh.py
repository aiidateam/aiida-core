"""
Test ssh plugin on localhost
"""
from aida.transport.plugins.ssh import *
import unittest
import logging

import aida.transport.plugin_test
from aida.transport.plugin_test import *

FORMAT = '[%(name)s@%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)

import paramiko
from aida.transport import Transport
global custom_transport

aida.transport.plugin_test.custom_transport = SshTransport(
    machine='localhost', timeout=30, 
    load_system_host_keys=True,
    key_policy = paramiko.AutoAddPolicy())

class TestBasicConnection(unittest.TestCase):
    """
    Test basic connections.
    """
    
    def test_closed_connection_ssh(self):
        with self.assertRaises(aida.transport.TransportInternalError):
            t = SshTransport(machine='localhost')
            t._exec_command_internal('ls')
            
    def test_closed_connection_sftp(self):
        with self.assertRaises(aida.transport.TransportInternalError):
            t = SshTransport(machine='localhost')
            t.listdir()
            
    def test_invalid_param(self):
        with self.assertRaises(ValueError):
            SshTransport(machine='localhost', invalid_param=True)
                             

    def test_auto_add_policy(self):
        with SshTransport(machine='localhost', timeout=30, 
                          load_system_host_keys=True,
                          key_policy=paramiko.AutoAddPolicy()) as t:
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
