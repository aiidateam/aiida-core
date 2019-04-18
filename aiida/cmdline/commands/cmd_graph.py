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
    '-a',
    '--ancestor-depth',
    help="The maximum depth when recursing upwards, if not set it will recurse to the end",
    type=click.IntRange(min=0))
@click.option(
    '-d',
    '--descendant-depth',
    help="The maximum depth when recursing through the descendants, if not set it will recurse to the end",
    type=click.IntRange(min=0))
@click.option('-o', '--outputs', is_flag=True, help="Always show all outputs of a calculation")
@click.option('-i', '--inputs', is_flag=True, help="Always show all inputs of a calculation")
@click.option(
    '-e',
    '--engine',
    help="the graphviz engine, e.g. dot, circo"
    "(see http://www.graphviz.org/doc/info/output.html)",
    default='dot')
@click.option(
    '-f', '--file-format', help="The output format used for rendering (``'pdf'``, ``'png'``, etc.).", default='pdf')
@click.option('-v', '--view', is_flag=True, help="Open the rendered result with the default application")
@decorators.with_dbenv()
def generate(root_node, ancestor_depth, descendant_depth, outputs, inputs, engine, file_format, view):
    """
    Generate a graph from a given ROOT_NODE user-specified by its pk.
    """
    # pylint: disable=too-many-arguments
    from aiida.tools.visualization.graph import Graph

    graph = Graph(engine=engine)
    graph.recurse_ancestors(root_node, depth=ancestor_depth, annotate_links="both", include_calculation_outputs=outputs)
    graph.recurse_descendants(
        root_node, depth=descendant_depth, annotate_links="both", include_calculation_inputs=inputs)
    output_file_name = graph.graphviz.render(filename=root_node + '.dot', format=file_format, view=view, cleanup=True)

    echo.echo_success("Output file is {}".format(output_file_name))
