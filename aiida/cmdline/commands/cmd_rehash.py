# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi rehash` command."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.cmdline.utils import decorators


@verdi.command('rehash')
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node rehash' instead.")
@arguments.NODES()
@click.option(
    '-e',
    '--entry-point',
    type=PluginParamType(group=('aiida.calculations', 'aiida.data', 'aiida.workflows'), load=True),
    default=None,
    help='Only include nodes that are class or sub class of the class identified by this entry point.'
)
@options.FORCE()
@decorators.with_dbenv()
@click.pass_context
def rehash(ctx, nodes, entry_point, force):
    """Recompute the hash for nodes in the database.

    The set of nodes that will be rehashed can be filtered by their identifier and/or based on their class.
    """
    from aiida.cmdline.commands.cmd_node import rehash as node_rehash

    result = ctx.invoke(node_rehash, nodes=nodes, entry_point=entry_point, force=force)
    return result
