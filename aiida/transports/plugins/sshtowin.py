# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for transport over SSH to a Windows computer (and SFTP for file transfer).
Uses powershell instead of bash
"""

from aiida.common.escaping import escape_for_bash

from .ssh import SshTransport

__all__ = ('SshToWindowsTransport',)


class SshToWindowsTransport(SshTransport):  # pylint: disable=too-many-public-methods
    """
    Support connection, command execution and data transfer to remote computers running Windows Powershell via SSH+SFTP.
    """

    def __init__(self, *args, **kwargs):  # pylint: disable=unused-argument

        super().__init__(*args, **kwargs)

        if self._use_login_shell:
            self._bash_command_str = 'powershell '
        else:
            self._bash_command_str = 'powershell '

    def _exec_command_internal(self, command, combine_stderr=False, bufsize=-1):  # pylint: disable=arguments-differ
        """
        Executes the specified command in bash login shell.

        Before the command is executed, changes directory to the current
        working directory as returned by self.getcwd().

        For executing commands and waiting for them to finish, use
        exec_command_wait.

        :param  command: the command to execute. The command is assumed to be
            already escaped using :py:func:`aiida.common.escaping.escape_for_bash`.
        :param combine_stderr: (default False) if True, combine stdout and
                stderr on the same buffer (i.e., stdout).
                Note: If combine_stderr is True, stderr will always be empty.
        :param bufsize: same meaning of the one used by paramiko.

        :return: a tuple with (stdin, stdout, stderr, channel),
            where stdin, stdout and stderr behave as file-like objects,
            plus the methods provided by paramiko, and channel is a
            paramiko.Channel object.
        """
        channel = self.sshclient.get_transport().open_session()
        channel.set_combine_stderr(combine_stderr)

        if self.getcwd() is not None:
            escaped_folder = escape_for_bash(self.getcwd()[1:])
            command_to_execute = (f'cd {escaped_folder}; {command}')
        else:
            command_to_execute = command

        self.logger.debug(f'Command to be executed: {command_to_execute[:self._MAX_EXEC_COMMAND_LOG_SIZE]}')

        channel.exec_command(self._bash_command_str + f' "{command_to_execute}"')

        stdin = channel.makefile('wb', bufsize)
        stdout = channel.makefile('rb', bufsize)
        stderr = channel.makefile_stderr('rb', bufsize)

        return stdin, stdout, stderr, channel
