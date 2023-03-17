# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for command line commands related to the daemon."""
from aiida.cmdline.utils import echo


def print_client_response_status(response):
    """
    Print the response status of a call to the CircusClient through the DaemonClient

    :param response: the response object
    :return: an integer error code; non-zero means there was an error (FAILED, TIMEOUT), zero means OK (OK, RUNNING)
    """
    from aiida.engine.daemon.client import DaemonClient

    if 'status' not in response:
        return 1

    if response['status'] == 'active':
        echo.echo('RUNNING', fg=echo.COLORS['success'], bold=True)
        return 0
    if response['status'] == 'ok':
        echo.echo('OK', fg=echo.COLORS['success'], bold=True)
        return 0
    if response['status'] == DaemonClient.DAEMON_ERROR_NOT_RUNNING:
        echo.echo('FAILED', fg=echo.COLORS['error'], bold=True)
        echo.echo('Try to run `verdi daemon start-circus --foreground` to potentially see the exception')
        return 2
    if response['status'] == DaemonClient.DAEMON_ERROR_TIMEOUT:
        echo.echo('TIMEOUT', fg=echo.COLORS['error'], bold=True)
        return 3
    # Unknown status, I will consider it as failed
    echo.echo_critical(response['status'])
    return -1
