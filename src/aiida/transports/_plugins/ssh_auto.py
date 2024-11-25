###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for transport over SSH (and SFTP for file transfer)."""

import pathlib

import paramiko

from .ssh import SshTransport

__all__ = ('SshAutoTransport',)


class SshAutoTransport(SshTransport):
    """Support connection, command execution and data transfer to remote computers via SSH+SFTP."""

    _valid_connect_params = []
    _valid_auth_options = []

    FILEPATH_CONFIG: pathlib.Path = pathlib.Path('~').expanduser() / '.ssh' / 'config'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, key_policy='AutoAddPolicy')

        config_ssh = paramiko.SSHConfig()

        try:
            with self.FILEPATH_CONFIG.open() as handle:
                config_ssh.parse(handle)
        except FileNotFoundError as exception:
            raise RuntimeError(
                f'Could not determine connection configuration as the `{self.FILEPATH_CONFIG}` does not exist.'
            ) from exception
        except PermissionError as exception:
            raise RuntimeError(
                f'Could not determine connection configuration as the `{self.FILEPATH_CONFIG}` is not readable.'
            ) from exception

        if self._machine not in config_ssh.get_hostnames():
            self.logger.warning(
                f'The host `{self._machine}` is not defined in SSH config, connection will most likely fail to open.'
            )

        config_host = config_ssh.lookup(self._machine)

        self._connect_args = {
            'port': config_host.get('port', 22),
            'username': config_host.get('user'),
            'key_filename': config_host.get('identityfile', []),
            'timeout': config_host.get('connecttimeout', 60),
            'proxy_command': config_host.get('proxycommand', None),
            'proxy_jump': config_host.get('proxyjump', None),
        }

        self._machine = config_host['hostname']
