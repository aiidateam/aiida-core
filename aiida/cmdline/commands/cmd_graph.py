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
    Requires that `graphviz<https://graphviz.org/download>` be installed.
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
    '-f',
    '--output-format',
    help="The output format, something that can be recognized by graphviz"
    "(see http://www.graphviz.org/doc/info/output.html)",
    default='dot')
@decorators.with_dbenv()
def generate(root_node, ancestor_depth, descendant_depth, outputs, inputs, output_format):
    """
    Generate a graph from a given ROOT_NODE user-specified by its pk.
    """
    from aiida.tools.visualization.graphviz import draw_graph

    exit_status, output_file_name = draw_graph(
        root_node,
        ancestor_depth=ancestor_depth,
        descendant_depth=descendant_depth,
        image_format=output_format,
        include_calculation_inputs=inputs,
        include_calculation_outputs=outputs)
    if exit_status:
        echo.echo_critical("Failed to generate graph")
    else:
        echo.echo_success("Output file is {}".format(output_file_name))
