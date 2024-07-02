###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Transport plugin for SSH connection using ``fabric``.

This subclasses the ``SshTransport`` plugin to replace the connection configuration using the ``fabric`` package. This
makes the configuration significantly easier for the user since ``fabric`` automatically guesses connection parameters
by parsing available SSH configuration files on the system. Since ``fabric`` uses ``paramiko`` under the hood, which is
the library used by the ``SshTransport``, most of the implementation can be reused. The ``paramiko.SshClient`` is
exposed on the ``fabric.Connection`` instance and is proxied to the ``_client`` attribute of the class where the
``SshTransport`` base class expects to find it.
"""
import fabric

from aiida.common.exceptions import InvalidOperation

from ..transport import Transport
from .ssh import SshTransport

__all__ = ('SshFabricTransport',)


class SshFabricTransport(SshTransport):
    """Transport plugin for SSH connections with highly-automated connection configuration.

    The connection is made using the ``fabric`` package which will try to use available SSH configuration files on the
    system to guess the correct configuration for the connection to the relevant hostname.
    """

    _valid_auth_options = []

    def __init__(self, *args, **kwargs):
        """Construct a new instance."""
        Transport.__init__(self, *args, **kwargs)  # Skip the ``SshTransport`` constructor
        self._connection = fabric.Connection(self.hostname)
        self._client = self._connection.client
        self._sftp = None

    def open(self):
        """Open the connection."""
        if not self._connection.is_connected:
            self._sftp = self._connection.sftp()  # This opens the fabric connection ``self._connection`` as well
            self._sftp.chdir('.')  # Needed to make sure sftp.getcwd() returns a valid path
            self._is_open = True

    def close(self):
        """Close the connection.

        This will close the SFTP channel and the ``fabric`` connection.

        :raise aiida.common.InvalidOperation: If the channel is already open.
        """
        if not self._is_open:
            raise InvalidOperation('Cannot close the transport: it is already closed')

        if self._sftp:
            self._sftp.close()
        self._connection.close()
        self._is_open = False

    def __str__(self):
        """Return a string representation of the transport instance."""
        status = 'OPEN' if self._is_open else 'CLOSED'
        return f'{self._connection.user}@{self.hostname}:{self._connection.port} [{status}]'

    def gotocomputer_command(self, remotedir):
        """Return the command string to connect to the remote and change directory to ``remotedir``."""
        return f'ssh -t {self.hostname} {self._gotocomputer_string(remotedir)}'
