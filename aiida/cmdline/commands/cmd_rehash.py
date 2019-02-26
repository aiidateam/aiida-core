# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi rehash` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.cmdline.utils import decorators, echo


@verdi.command('rehash')
@arguments.NODES()
@click.option(
    '-e',
    '--entry-point',
    type=PluginParamType(group=('aiida.calculations', 'aiida.data', 'aiida.workflows'), load=True),
    default=None,
    help='Only include nodes that are class or sub class of the class identified by this entry point.')
@decorators.with_dbenv()
def rehash(nodes, entry_point):
    """Recompute the hash for nodes in the database

    The set of nodes that will be rehashed can be filtered by their identifier and/or based on their class.
    """
    from aiida.orm import Data, ProcessNode, QueryBuilder

    # If no explicit entry point is defined, rehash all nodes, which are either Data nodes or ProcessNodes
    if entry_point is None:
        entry_point = (Data, ProcessNode)

    if nodes:
        to_hash = [(node,) for node in nodes if isinstance(node, entry_point)]
    else:
        builder = QueryBuilder()
        builder.append(entry_point, tag='node')
        to_hash = builder.all()

    if not to_hash:
        echo.echo_critical('no matching nodes found')

    count = 0

    for i, (node,) in enumerate(to_hash):

        if i % 100 == 0:
            echo.echo('.', nl=False)

        node.rehash()
        count += 1

    echo.echo('')
    echo.echo_success('{} nodes re-hashed'.format(count))
