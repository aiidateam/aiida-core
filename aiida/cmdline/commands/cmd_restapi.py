# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This allows to hook-up the AiiDA built-in RESTful API.
Main advantage of doing this by means of a verdi command is that different
profiles can be selected at hook-up (-p flag).
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import os

import click

import aiida.restapi
from aiida.cmdline.commands.cmd_verdi import verdi

DEFAULT_CONFIG_DIR = os.path.join(os.path.split(os.path.abspath(aiida.restapi.__file__))[0], 'common')


@verdi.command('restapi')
@click.option('-H', '--host', type=click.STRING, default='127.0.0.1', help='the hostname to use')
@click.option('-p', '--port', type=click.INT, default=5000, help='the port to use')
@click.option(
    '-c',
    '--config-dir',
    type=click.Path(exists=True),
    default=DEFAULT_CONFIG_DIR,
    help='the path of the configuration directory')
def restapi(host, port, config_dir):
    """
    Run the AiiDA REST API server

    Example Usage:

        \b
        verdi -p <profile_name> restapi --host 127.0.0.5 --port 6789 --config-dir <location of the config.py file>
    """
    from aiida.restapi.api import App, AiidaApi
    from aiida.restapi.run_api import run_api

    # Construct parameter dictionary
    kwargs = dict(
        hookup=True,
        prog_name='verdi-restapi',
        default_host=host,
        default_port=port,
        default_config=config_dir,
        parse_aiida_profile=False,
        catch_internal_server=True)

    # Invoke the runner
    run_api(App, AiidaApi, **kwargs)
