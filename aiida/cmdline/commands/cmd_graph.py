# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi graph` commands"""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators


@verdi.group('graph')
@decorators.deprecated_command("This command group has been deprecated. Please use 'verdi node graph' instead.")
def verdi_graph():
    """Create visual representations of the provenance graph."""


@verdi_graph.command('generate')
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node graph generate' instead.")
@arguments.NODE('root_node')
@click.option(
    '-l',
    '--link-types',
    help=(
        'The link types to include: '
        "'data' includes only 'input_calc' and 'create' links (data provenance only), "
        "'logic' includes only 'input_work' and 'return' links (logical provenance only)."
    ),
    default='all',
    type=click.Choice(['all', 'data', 'logic'])
)
@click.option(
    '--identifier',
    help='the type of identifier to use within the node text',
    default='uuid',
    type=click.Choice(['pk', 'uuid', 'label'])
)
@click.option(
    '-a',
    '--ancestor-depth',
    help='The maximum depth when recursing upwards, if not set it will recurse to the end.',
    type=click.IntRange(min=0)
)
@click.option(
    '-d',
    '--descendant-depth',
    help='The maximum depth when recursing through the descendants. If not set it will recurse to the end.',
    type=click.IntRange(min=0)
)
@click.option('-o', '--process-out', is_flag=True, help='Show outgoing links for all processes.')
@click.option('-i', '--process-in', is_flag=True, help='Show incoming links for all processes.')
@options.VERBOSE(help='Print verbose information of the graph traversal.')
@click.option(
    '-e',
    '--engine',
    help="The graphviz engine, e.g. 'dot', 'circo', ... "
    '(see http://www.graphviz.org/doc/info/output.html)',
    default='dot'
)
@click.option('-f', '--output-format', help="The output format used for rendering ('pdf', 'png', etc.).", default='pdf')
@click.option('-s', '--show', is_flag=True, help='Open the rendered result with the default application.')
@click.pass_context
@decorators.with_dbenv()
def generate(  # pylint: disable=too-many-arguments, unused-argument
    ctx, root_node, link_types, identifier, ancestor_depth, descendant_depth, process_out, process_in, engine, verbose,
    output_format, show
):
    """
    Generate a graph from a ROOT_NODE (specified by pk or uuid).
    """
    from aiida.cmdline.commands.cmd_node import graph_generate as node_generate

    ctx.forward(node_generate)
