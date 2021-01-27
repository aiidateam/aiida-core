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
This allows to hook-up the AiiDA built-in RESTful API.
Main advantage of doing this by means of a verdi command is that different
profiles can be selected at hook-up (-p flag).
"""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.options import HOSTNAME, PORT, DEBUG
from aiida.restapi.common import config


@verdi.command('restapi')
@HOSTNAME(default=config.CLI_DEFAULTS['HOST_NAME'])
@PORT(default=config.CLI_DEFAULTS['PORT'])
@click.option(
    '-c',
    '--config-dir',
    type=click.Path(exists=True),
    default=config.CLI_DEFAULTS['CONFIG_DIR'],
    help='Path to the configuration directory'
)
@DEBUG(default=config.APP_CONFIG['DEBUG'])
@click.option(
    '--wsgi-profile',
    is_flag=True,
    default=config.CLI_DEFAULTS['WSGI_PROFILE'],
    help='Whether to enable WSGI profiler middleware for finding bottlenecks'
)
@click.option('--hookup/--no-hookup', 'hookup', is_flag=True, default=None, help='Hookup app to flask server')
@click.option(
    '--posting/--no-posting',
    'posting',
    is_flag=True,
    default=config.CLI_DEFAULTS['POSTING'],
    help='Enable POST endpoints (currently only /querybuilder).',
    hidden=True,
)
def restapi(hostname, port, config_dir, debug, wsgi_profile, hookup, posting):
    """
    Run the AiiDA REST API server.

    Example Usage:

        verdi -p <profile_name> restapi --hostname 127.0.0.5 --port 6789
    """
    from aiida.restapi.run_api import run_api
    # Invoke the runner
    run_api(
        hostname=hostname,
        port=port,
        config=config_dir,
        debug=debug,
        wsgi_profile=wsgi_profile,
        hookup=hookup,
        posting=posting,
    )
