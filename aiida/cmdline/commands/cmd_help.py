# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Command for `verdi help`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sys
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.utils import echo


@verdi.command('help')
@click.pass_context
@click.argument('command', type=click.STRING, required=False)
def verdi_help(ctx, command):
    """Show help for given command."""

    cmdctx = ctx.parent

    if command:
        cmd = verdi.get_command(ctx.parent, command)

        if not cmd:
            echo.echo_error("command '{}' not found".format(command))
            sys.exit(1)

        cmdctx = click.Context(cmd, info_name=cmd.name, parent=ctx.parent)

    echo.echo(cmdctx.get_help())
