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
import os

import click

import aiida.restapi
from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params.options import HOSTNAME, PORT

CONFIG_DIR = os.path.join(os.path.split(os.path.abspath(aiida.restapi.__file__))[0], 'common')


@verdi.command('restapi')
@HOSTNAME(default='127.0.0.1')
@PORT(default=5000)
@click.option(
    '-c',
    '--config-dir',
    type=click.Path(exists=True),
    default=CONFIG_DIR,
    help='the path of the configuration directory'
)
@click.option('--debug', 'debug', is_flag=True, default=False, help='run app in debug mode')
@click.option(
    '--wsgi-profile',
    'wsgi_profile',
    is_flag=True,
    default=False,
    help='to use WSGI profiler middleware for finding bottlenecks in web application'
)
@click.option('--hookup/--no-hookup', 'hookup', is_flag=True, default=True, help='to hookup app')
def restapi(hostname, port, config_dir, debug, wsgi_profile, hookup):
    """
    Run the AiiDA REST API server.

    Example Usage:

        \b
        verdi -p <profile_name> restapi --hostname 127.0.0.5 --port 6789 --config-dir <location of the config.py file>
        --debug --wsgi-profile --hookup
    """
    from aiida.restapi.api import App, AiidaApi
    from aiida.restapi.run_api import run_api

    # Construct parameter dictionary
    kwargs = dict(
        prog_name='verdi-restapi',
        hostname=hostname,
        port=port,
        config=config_dir,
        debug=debug,
        wsgi_profile=wsgi_profile,
        hookup=hookup,
        catch_internal_server=True
    )

    # Invoke the runner
    run_api(App, AiidaApi, **kwargs)
