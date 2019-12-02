# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi config` command."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import echo


@verdi.command('config')
@arguments.CONFIG_OPTION(metavar='OPTION_NAME')
@click.argument('value', metavar='OPTION_VALUE', required=False)
@click.option('--global', 'globally', is_flag=True, help='Apply the option configuration wide.')
@click.option('--unset', is_flag=True, help='Remove the line matching the option name from the config file.')
@click.pass_context
def verdi_config(ctx, option, value, globally, unset):
    """Configure profile-specific or global AiiDA options."""
    config = ctx.obj.config
    profile = ctx.obj.profile

    if option.global_only:
        globally = True

    # Define the string that determines the scope: for specific profile or globally
    scope = profile.name if (not globally and profile) else None
    scope_text = 'for {}'.format(profile.name) if (not globally and profile) else 'globally'

    # Unset the specified option
    if unset:
        config.unset_option(option.name, scope=scope)
        config.store()
        echo.echo_success('{} unset {}'.format(option.name, scope_text))

    # Get the specified option
    elif value is None:
        option_value = config.get_option(option.name, scope=scope, default=False)
        if option_value:
            echo.echo('{}'.format(option_value))

    # Set the specified option
    else:
        config.set_option(option.name, value, scope=scope)
        config.store()
        echo.echo_success('{} set to {} {}'.format(option.name, value, scope_text))
