# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The `verdi data` command line interface."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.commands.cmd_plugin import verdi_plugin
from aiida.cmdline.utils import decorators
from aiida.cmdline.utils.pluginable import Pluginable


@verdi.group('data', entry_point_group='aiida.cmdline.data', cls=Pluginable)
def verdi_data():
    """Inspect, create and manage data nodes."""


@verdi_data.command('plugins')
@click.argument('entry_point', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
@decorators.deprecated_command("This command is deprecated. Use 'verdi plugin list' instead.")
def data_plugins(ctx, entry_point):
    """Print a list of registered data plugins or details of a specific data plugin."""
    ctx.invoke(verdi_plugin.get_command(ctx, 'list'), entry_point_group='aiida.data', entry_point=entry_point)
