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
import click

from aiida.cmdline.baseclass import VerdiCommand
from aiida.cmdline.commands import verdi_rehash
from aiida.cmdline.params import arguments
from aiida.cmdline.params.types.plugin import PluginParamType
from aiida.cmdline.utils import decorators, echo


class Rehash(VerdiCommand):
    """Re-hash nodes filtered by identifier and or node class."""

    def run(self, *args):
        ctx = rehash.make_context('rehash', list(args))
        with ctx:
            rehash.invoke(ctx)


@verdi_rehash.command('rehash')
@arguments.NODES()
@click.option(
    '-e',
    '--entry-point',
    type=PluginParamType(group=('node', 'calculations', 'data'), load=True),
    default='node',
    help=
    'restrict nodes which are re-hashed to instances that are a sub class of the class identified by this entry point')
@decorators.with_dbenv()
def rehash(nodes, entry_point):
    """Rehash all nodes in the database filtered by their identifier and/or based on their class."""
    from aiida.orm.querybuilder import QueryBuilder

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
