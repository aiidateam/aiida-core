###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test :mod:`aiida.transports.plugins.ssh`."""

import logging

import paramiko
import pytest

from aiida.transports.plugins.ssh import SshTransport
from aiida.transports.transport import TransportInternalError


def test_closed_connection_ssh():
    """Test calling command on a closed connection."""
    with pytest.raises(TransportInternalError):
        transport = SshTransport(machine='localhost')
        transport._exec_command_internal('ls')


def test_closed_connection_sftp():
    """Test calling sftp command on a closed connection."""
    with pytest.raises(TransportInternalError):
        transport = SshTransport(machine='localhost')
        transport.listdir('/home')


def test_auto_add_policy():
    """Test the auto add policy."""
    with SshTransport(machine='localhost', timeout=30, load_system_host_keys=True, key_policy='AutoAddPolicy'):
        pass


def test_proxy_jump():
    """Test the connection with a proxy jump or several"""
    with SshTransport(
        machine='localhost', proxy_jump='localhost', timeout=30, load_system_host_keys=True, key_policy='AutoAddPolicy'
    ):
        pass

    # kind of pointless, but should work and to check that proxy chaining works
    with SshTransport(
        machine='localhost',
        proxy_jump='localhost,localhost,localhost',
        timeout=30,
        load_system_host_keys=True,
        key_policy='AutoAddPolicy',
    ):
        pass


def test_proxy_jump_invalid():
    """Test proper error reporting when invalid host as a proxy"""
    # import is also that when Python is running with debug warnings `-Wd`
    # no unclosed files are reported.
    with pytest.raises(paramiko.SSHException):
        with SshTransport(
            machine='localhost',
            proxy_jump='localhost,nohost',
            timeout=30,
            load_system_host_keys=True,
            key_policy='AutoAddPolicy',
        ):
            pass


def test_proxy_command():
    """Test the connection with a proxy command"""
    with SshTransport(
        machine='localhost',
        proxy_command='ssh -W localhost:22 localhost',
        timeout=30,
        load_system_host_keys=True,
        key_policy='AutoAddPolicy',
    ):
        pass


def test_no_host_key():
    """Test if there is no host key."""
    # Disable logging to avoid output during test
    logging.disable(logging.ERROR)

    with pytest.raises(paramiko.SSHException):
        with SshTransport(machine='localhost', timeout=30, load_system_host_keys=False):
            pass

    # Reset logging level
    logging.disable(logging.NOTSET)


def test_gotocomputer():
    """Test gotocomputer"""
    with SshTransport(
        machine='localhost',
        timeout=30,
        use_login_shell=False,
        key_policy='AutoAddPolicy',
        proxy_command='ssh -W localhost:22 localhost',
    ) as transport:
        cmd_str = transport.gotocomputer_command('/remote_dir/')

        expected_str = (
            """ssh -t localhost -o ProxyCommand='ssh -W localhost:22 localhost'  "if [ -d '/remote_dir/' ] ;"""
            """ then cd '/remote_dir/' ; bash  ; else echo '  ** The directory' ; """
            """echo '  ** /remote_dir/' ; echo '  ** seems to have been deleted, I logout...' ; fi" """
        )
        assert cmd_str == expected_str


def test_gotocomputer_proxyjump():
    """Test gotocomputer"""
    with SshTransport(
        machine='localhost',
        timeout=30,
        use_login_shell=False,
        key_policy='AutoAddPolicy',
        proxy_jump='localhost',
    ) as transport:
        cmd_str = transport.gotocomputer_command('/remote_dir/')

        expected_str = (
            """ssh -t localhost -o ProxyJump='localhost'  "if [ -d '/remote_dir/' ] ;"""
            """ then cd '/remote_dir/' ; bash  ; else echo '  ** The directory' ; """
            """echo '  ** /remote_dir/' ; echo '  ** seems to have been deleted, I logout...' ; fi" """
        )
        assert cmd_str == expected_str
