# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi, verdi_graph
from aiida.cmdline.params import arguments
from aiida.cmdline.utils import decorators, echo


class Graph(VerdiCommandWithSubcommands):
    """
    Utility to explore the nodes in the database graph
    More specifically it allow the user to::

        - Generate and render graph
        - (TODO) Find if two nodes of a graph are connected
        - (TODO) Extend functionalities

    A list dictionary with available subcommands can be found in __init__ function
    """

    def __init__(self):
        """
        A dictionary with valid subcommands as keys and corresponding functions as values
        """

        self.valid_subcommands = {
            'generate': (self.cli, self.complete_none)
            # TODO: add a command to find connections between two points
        }

    def cli(self, *args):
        verdi()


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
@click.option(
    '-o', 
    '--outputs', 
    is_flag=True, 
    help="Always show all outputs of a calculation")
@click.option(
    '-i', 
    '--inputs', 
    is_flag=True, 
    help="Always show all inputs of a calculation")
@click.option(
    '-f',
    '--output-format',
    help="The output format, something that can be recognized by graphvix"
    "(see http://www.graphviz.org/doc/info/output.html)",
    default='dot')
@decorators.with_dbenv()
def generate(root_node, ancestor_depth, descendant_depth, outputs, inputs, output_format):
    """
    Generate a graph given a ROOT_NODE user-specified by its pk.
    """
    from aiida.orm import load_node
    from aiida.common.graph import draw_graph

    exit_status, output_file_name = draw_graph(
        root_node,
        ancestor_depth=ancestor_depth,
        descendant_depth=descendant_depth,
        format=output_format,
        include_calculation_inputs=inputs,
        include_calculation_outputs=outputs)
    if not exit_status:
        echo.echo_success("Output file is {}".format(output_file_name))
