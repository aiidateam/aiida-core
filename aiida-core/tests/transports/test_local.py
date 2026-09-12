###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test :mod:`aiida.transports.plugins.local`."""

import getpass

import pytest

from aiida.transports.plugins.local import LocalTransport
from aiida.transports.transport import TransportInternalError


def test_basic():
    """Test constructor."""
    with LocalTransport():
        pass


def test_whoami():
    """Test the `whoami` command."""
    with LocalTransport() as transport:
        assert transport.whoami() == getpass.getuser()


def test_closed_connection():
    """Test running a command on a closed connection."""
    with pytest.raises(TransportInternalError):
        transport = LocalTransport()
        transport.listdir('/home')


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
