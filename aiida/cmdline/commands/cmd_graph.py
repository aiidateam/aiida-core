# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi graph` commands"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import decorators, echo


@verdi.group('graph')
def verdi_graph():
    """
    Create visual representations of part of the provenance graph.
    Requires that `python-graphviz<https://graphviz.readthedocs.io>` be installed.
    """


@verdi_graph.command('generate')
@arguments.NODE('root_node')
@click.option(
    "-l",
    "--link-types",
    help="The link types to include: 'data' includes only 'input_calc' and 'create' links (data provenance only),  'logic' includes only 'input_work' and 'return' links (logical provenance only).",
    default="all",
    type=click.Choice(['all', 'data', 'logic']))
@click.option(
    '-a',
    '--ancestor-depth',
    help='The maximum depth when recursing upwards, if not set it will recurse to the end.',
    type=click.IntRange(min=0))
@click.option(
    '-d',
    '--descendant-depth',
    help='The maximum depth when recursing through the descendants. If not set it will recurse to the end.',
    type=click.IntRange(min=0))
@click.option('-o', '--process-out', is_flag=True, help='Show outgoing links for all processes.')
@click.option('-i', '--process-in', is_flag=True, help='Show incoming links for all processes.')
@click.option('-p', '--print-info', is_flag=True, help="Print verbose information of the graph traversal.")
@click.option(
    '-e',
    '--engine',
    help="The graphviz engine, e.g. 'dot', 'circo', ... "
    "(see http://www.graphviz.org/doc/info/output.html)",
    default='dot')
@click.option('-f', '--output-format', help="The output format used for rendering ('pdf', 'png', etc.).", default='pdf')
@click.option('-v', '--view', is_flag=True, help="Open the rendered result with the default application.")
@decorators.with_dbenv()
def generate(root_node, link_types, ancestor_depth, descendant_depth, process_out, process_in, engine, print_info,
             output_format, view):
    """
    Generate a graph from a ROOT_NODE (specified by pk or uuid).
    """
    # pylint: disable=too-many-arguments
    from aiida.tools.visualization.graph import Graph
    print_func = echo.echo_info if print_info else None
    link_types = {"all": (), "logic": ("input_work", "return"), "data": ("input_calc", "create")}[link_types]

    echo.echo_info("Initiating graphviz engine: {}".format(engine))
    graph = Graph(engine=engine)
    echo.echo_info("Recursing ancestors, max depth={}".format(ancestor_depth))
    graph.recurse_ancestors(
        root_node,
        depth=ancestor_depth,
        link_types=link_types,
        annotate_links="both",
        include_process_outputs=process_out,
        print_func=print_func)
    echo.echo_info("Recursing descendants, max depth={}".format(descendant_depth))
    graph.recurse_descendants(
        root_node,
        depth=descendant_depth,
        link_types=link_types,
        annotate_links="both",
        include_process_inputs=process_in,
        print_func=print_func)
    output_file_name = graph.graphviz.render(
        filename='{}.{}'.format(root_node.pk, engine), format=output_format, view=view, cleanup=True)

    echo.echo_success("Output file: {}".format(output_file_name))
