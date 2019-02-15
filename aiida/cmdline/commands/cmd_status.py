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

from enum import IntEnum
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.common import exceptions
from aiida.cmdline.utils.daemon import get_daemon_status
from aiida.manage import get_manager


class ServiceStatus(IntEnum):
    """Describe status of services for 'verdi status' command.
    """
    UP = 0
    ERROR = 1
    DOWN = 2


STATUS_COLOR_MAP = {
    ServiceStatus.UP: 'green',
    ServiceStatus.ERROR: 'red',
    ServiceStatus.DOWN: 'red',
}


@verdi.command('status')
def verdi_status():
    """Print status of AiiDA services."""

    manager = get_manager()

    # getting the profile
    try:
        profile = manager.get_profile()
        print_status(ServiceStatus.UP, 'profile', "On profile {}".format(profile.name))
    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'profile', "Unable to read AiiDA profile")
        print(exc)

    # getting the daemon status
    try:
        client = manager.get_daemon_client()
        daemon_status = get_daemon_status(client)
        daemon_status = daemon_status.split("\n")[0]  # take only the first line

        if client.is_daemon_running:
            print_status(ServiceStatus.UP, 'daemon', daemon_status)
        else:
            print_status(ServiceStatus.DOWN, 'daemon', daemon_status)
    except Exception as exc:
        print_status(ServiceStatus.ERROR, 'daemon', "Error getting daemon status")
        print(exc)

    # getting the postgres status


def print_status(status, service, msg=""):
    """Print status message.

    Includes colored indicator.

    :param status: a ServiceStatus
    :param service: string for service
    :param msg:  message string

    """
    click.secho(u'  \u2B24  ', fg=STATUS_COLOR_MAP[status], nl=False)
    click.secho('{}: '.format(service), nl=False)
    click.secho(msg)
