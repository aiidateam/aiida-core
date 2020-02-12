# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi status` command."""
import sys

import enum
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.common.log import override_log_level
from ..utils.echo import ExitCode


class ServiceStatus(enum.IntEnum):
    """Describe status of services for 'verdi status' command."""
    UP = 0  # pylint: disable=invalid-name
    ERROR = 1
    DOWN = 2


STATUS_SYMBOLS = {
    ServiceStatus.UP: {
        'color': 'green',
        'string': '\u2713',
    },
    ServiceStatus.ERROR: {
        'color': 'red',
        'string': '\u2717',
    },
    ServiceStatus.DOWN: {
        'color': 'red',
        'string': '\u2717',
    },
}


@verdi.command('status')
def verdi_status():
    """Print status of AiiDA services."""
    # pylint: disable=broad-except,too-many-statements
    from aiida.cmdline.utils.daemon import get_daemon_status, delete_stale_pid_file
    from aiida.common.utils import Capturing
    from aiida.manage.external.rmq import get_rmq_url
    from aiida.manage.manager import get_manager

    exit_code = ExitCode.SUCCESS
    manager = get_manager()
    profile = manager.get_profile()

    # getting the profile
    try:
        profile = manager.get_profile()
        print_status(ServiceStatus.UP, 'profile', 'On profile {}'.format(profile.name))

    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'profile', 'Unable to read AiiDA profile')
        sys.exit(ExitCode.CRITICAL)  # stop here - without a profile we cannot access anything

    # getting the repository
    repo_folder = 'undefined'
    try:
        repo_folder = profile.repository_path
    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'repository', 'Error with repo folder', exception=exc)
        exit_code = ExitCode.CRITICAL
    else:
        print_status(ServiceStatus.UP, 'repository', repo_folder)

    # Getting the postgres status by trying to get a database cursor
    database_data = [profile.database_username, profile.database_hostname, profile.database_port]
    try:
        with override_log_level():  # temporarily suppress noisy logging
            backend = manager.get_backend()
            backend.cursor()
    except Exception:
        print_status(ServiceStatus.DOWN, 'postgres', 'Unable to connect as {}@{}:{}'.format(*database_data))
        exit_code = ExitCode.CRITICAL
    else:
        print_status(ServiceStatus.UP, 'postgres', 'Connected as {}@{}:{}'.format(*database_data))

    # getting the rmq status
    try:
        with Capturing(capture_stderr=True):
            with override_log_level():  # temporarily suppress noisy logging
                comm = manager.create_communicator(with_orm=False)
                comm.stop()
    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'rabbitmq', 'Unable to connect to rabbitmq', exception=exc)
        exit_code = ExitCode.CRITICAL
    else:
        print_status(ServiceStatus.UP, 'rabbitmq', 'Connected to {}'.format(get_rmq_url()))

    # getting the daemon status
    try:
        client = manager.get_daemon_client()
        delete_stale_pid_file(client)
        daemon_status = get_daemon_status(client)

        daemon_status = daemon_status.split('\n')[0]  # take only the first line
        if client.is_daemon_running:
            print_status(ServiceStatus.UP, 'daemon', daemon_status)
        else:
            print_status(ServiceStatus.DOWN, 'daemon', daemon_status)
            exit_code = ExitCode.CRITICAL

    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'daemon', 'Error getting daemon status', exception=exc)
        exit_code = ExitCode.CRITICAL

    # Note: click does not forward return values to the exit code, see https://github.com/pallets/click/issues/747
    sys.exit(exit_code)


def print_status(status, service, msg='', exception=None):
    """Print status message.

    Includes colored indicator.

    :param status: a ServiceStatus code
    :param service: string for service name
    :param msg:  message string
    """
    symbol = STATUS_SYMBOLS[status]
    click.secho(' {} '.format(symbol['string']), fg=symbol['color'], nl=False)
    click.secho('{:12s} {}'.format(service + ':', msg))
    if exception is not None:
        click.echo(exception, err=True)
