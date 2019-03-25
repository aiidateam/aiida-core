# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi profile` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sys
from enum import IntEnum
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from ..utils.echo import ExitCode


class ServiceStatus(IntEnum):
    """Describe status of services for 'verdi status' command.
    """
    UP = 0  # pylint: disable=invalid-name
    ERROR = 1
    DOWN = 2


STATUS_SYMBOLS = {
    ServiceStatus.UP: {
        'color': 'green',
        'string': u'\u2713',
    },
    ServiceStatus.ERROR: {
        'color': 'red',
        'string': u'\u2717',
    },
    ServiceStatus.DOWN: {
        'color': 'red',
        'string': u'\u2717',
    },
}


@verdi.command('status')
def verdi_status():
    """Print status of AiiDA services."""
    # pylint: disable=broad-except,too-many-statements
    from aiida.manage.external.rmq import get_rmq_url
    from aiida.manage.external.postgres import Postgres
    from aiida.cmdline.utils.daemon import get_daemon_status
    from aiida.common.utils import Capturing, get_repository_folder
    from aiida.manage.manager import get_manager

    exit_code = ExitCode.SUCCESS
    manager = get_manager()

    # getting the profile
    try:
        profile = manager.get_profile()
        print_status(ServiceStatus.UP, 'profile', "On profile {}".format(profile.name))

    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'profile', "Unable to read AiiDA profile")
        exit_code = ExitCode.CRITICAL
        sys.exit(exit_code)  # stop here - without a profile we cannot access anything

    # getting the repository
    try:
        repo_folder = get_repository_folder()
    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'repository', "Error with repo folder", exception=exc)
        exit_code = ExitCode.CRITICAL

    print_status(ServiceStatus.UP, 'repository', repo_folder)

    # getting the postgres status
    try:
        with Capturing(capture_stderr=True):

            postgres = Postgres.from_profile(profile)
            pg_connected = postgres.try_connect()

        dbinfo = postgres.get_dbinfo()
        if pg_connected:
            print_status(ServiceStatus.UP, 'postgres', "Connected to {}@{}:{}".format(
                dbinfo['user'], dbinfo['host'], dbinfo['port']))
        else:
            print_status(ServiceStatus.DOWN, 'postgres', "Unable to connect to {}:{}".format(
                dbinfo['host'], dbinfo['port']))
            exit_code = ExitCode.CRITICAL

    except Exception as exc:
        pd_dict = profile.dictionary
        print_status(
            ServiceStatus.ERROR,
            'postgres',
            "Error connecting to {}:{}".format(pd_dict['AIIDADB_HOST'], pd_dict['AIIDADB_PORT']),
            exception=exc)
        exit_code = ExitCode.CRITICAL

    # getting the rmq status
    try:
        with Capturing(capture_stderr=True):
            comm = manager.create_communicator(with_orm=False)
            comm.stop()

        print_status(ServiceStatus.UP, 'rabbitmq', "Connected to {}".format(get_rmq_url()))

    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'rabbitmq', "Unable to connect to rabbitmq", exception=exc)
        exit_code = ExitCode.CRITICAL

    # getting the daemon status
    try:
        client = manager.get_daemon_client()
        daemon_status = get_daemon_status(client)

        daemon_status = daemon_status.split("\n")[0]  # take only the first line
        if client.is_daemon_running:
            print_status(ServiceStatus.UP, 'daemon', daemon_status)
        else:
            print_status(ServiceStatus.DOWN, 'daemon', daemon_status)
            exit_code = ExitCode.CRITICAL

    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'daemon', "Error getting daemon status", exception=exc)
        exit_code = ExitCode.CRITICAL

    # Note: click does not forward return values to the exit code, see
    # https://github.com/pallets/click/issues/747
    sys.exit(exit_code)


def print_status(status, service, msg="", exception=None):
    """Print status message.

    Includes colored indicator.

    :param status: a ServiceStatus code
    :param service: string for service name
    :param msg:  message string

    """
    symbol = STATUS_SYMBOLS[status]
    click.secho(u' {} '.format(symbol['string']), fg=symbol['color'], nl=False)
    click.secho('{:12s} {}'.format(service + ':', msg))
    if exception is not None:
        click.echo(exception, err=True)
