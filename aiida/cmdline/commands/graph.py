# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import argparse
import sys

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.common.exceptions import NotExistent



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

        # Usual boilerplate to set the environment
        if not is_dbenv_loaded():
            load_dbenv()

        self.valid_subcommands = {
            'generate': (self.graph_generate, self.complete_none)
            # TODO: add a command to find connections between two points
        }

    def graph_generate(self, *args):
        """
        Function to generate a graph given a root node user-specified by its pk.
        :param args: root_pk
        :return: Generate a .dot file that can be rendered by graphviz utility dot
        """
        from aiida.orm import load_node
        from aiida.common.graph import draw_graph


        def PositiveInt(value):
            try:
                ivalue=int(value)
                if ivalue < 0:
                    raise Exception("Negative value")
                return ivalue
            except Exception as e:
                print e
                raise argparse.ArgumentTypeError("%s is not a non-negative integer" % value)

        # Parse input arguments
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Generate a graph from a root node')

        parser.add_argument('ROOT', help="The pk of the root node",
                            type=int)
        parser.add_argument('-a', '--ancestor-depth', help="The maximum depth when "
                "recursing upwards, if not set it will recurse to the end", type=PositiveInt)
        parser.add_argument('-d', '--descendant-depth', help="The maximum depth when "
                "recursing through the descendants, if not set it will recurse to the end", type=PositiveInt)
        parser.add_argument('--outputs', help="Always show all outputs of a calculation", action='store_true')
        parser.add_argument('--inputs', help="Always show all inputs of a calculation", action='store_true')
        parser.add_argument('-f', '--format', help="The output format, something that "
            "can be recognized by graphvix (see http://www.graphviz.org/doc/info/output.html)", default='dot')
        # Parse args and retrieve root pk
        args = list(args)
        parsed_args = parser.parse_args(args)
        root_pk = parsed_args.ROOT

        # Try to retrieve the node
        try:
            n = load_node(root_pk)
        except NotExistent as e:
            print >> sys.stderr, e.message
            sys.exit(1)
        exit_status, output_file_name = draw_graph(n, 
                ancestor_depth=parsed_args.ancestor_depth, descendant_depth=parsed_args.descendant_depth, format=parsed_args.format,
                include_calculation_inputs=parsed_args.inputs, include_calculation_outputs=parsed_args.outputs)
        if not exit_status:
            print "Output file is {}".format(output_file_name)


