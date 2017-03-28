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
    More specifically it allow the user to:
        1) Generate and render graph
        2) (TODO) Find if two nodes of a graph are connected
        3) (TODO) Extend functionalities

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
        from aiida.orm.calculation import Calculation
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm.code import Code
        from aiida.orm.data.array.kpoints import KpointsData
        from aiida.orm.data.structure import StructureData
        from aiida.orm.calculation.inline import InlineCalculation

        # Parse input arguments
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Generate a graph from a root node')

        parser.add_argument('ROOT', help="The pk of the root node",
                            type=int)

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

        # The algorithm starts from the root_pk and goes both input-ward and output-ward via a breadth-first algorithm
        # until the connected part of the graph that contains the root_pk is fully explored.
        # TODO this command deserves to be improved, with options and further subcommands


        def kpoints_desc(node):
            """
            Returns a string with infos retrieved from  kpoints node's properties.
            :param node:
            :return: retstr
            """
            try:
                mesh = node.get_kpoints_mesh()
                return "{}x{}x{} (+{:.1f},{:.1f},{:.1f})".format(
                    mesh[0][0], mesh[0][1], mesh[0][2],
                    mesh[1][0], mesh[1][1], mesh[1][2])
            except AttributeError:
                return '({} kpts)'.format(len(node.get_kpoints()))

        def pw_desc(node):
            """
            Returns a string with infos retrieved from  PwCalculation node's properties.
            :param node:
            :return: retsrt:
            """
            ############I won't use this until node.inp. methods won't be working correctly
            # return '{}'.format(node.inp.parameters.dict.CONTROL['calculation'])
            ###########

            ###############3I rather use this black magic
            return '{}'.format(dict(node.get_inputs(also_labels=True))['parameters'].dict.CONTROL['calculation'])

        def get_additional_string(node):
            """
            Returns a string with infos retrieved from  PwCalculation node's properties.
            The actual returned string depends on the node class
            :param node:
            :return: retstr
            """
            class_name = node.__class__.__name__

            func_mapping = {
                "StructureData": lambda x: x.get_formula(mode='hill_compact'),
                "InlineCalculation": lambda x: "{}()".format(x.get_function_name()),
                "KpointsData": kpoints_desc,
                "PwCalculation": pw_desc,
            }

            func = func_mapping.get(class_name, None)
            if func is None:
                retstr = ""

            else:
                retstr = "{}".format(func(node))

            if isinstance(node, JobCalculation):
                retstr = " ".join([retstr, node.get_state(from_attribute=True)])

            if retstr:
                return "\n{}".format(retstr)
            else:
                return ""

        def draw_node_settings(node, **kwargs):
            """
            Returns a string with all infos needed in a .dot file  to define a node of a graph.
            :param node:
            :param kwargs: Additional key-value pairs to be added to the returned string
            :return: a string
            """
            if isinstance(node, Calculation):
                shape = "shape=polygon,sides=4"
            elif isinstance(node, Code):
                shape = "shape=diamond"
            else:
                shape = "shape=ellipse"
            if kwargs:
                additional_params = ",{}".format(
                    ",".join('{}="{}"'.format(k, v) for k, v in kwargs.iteritems()))
            else:
                additional_params = ""
            additional_string = get_additional_string(node)
            if node.label:
                label_string = "\n'{}'".format(node.label)
            else:
                label_string = ""
            labelstring = 'label="{} ({}){}{}"'.format(
                node.__class__.__name__, node.pk, label_string,
                additional_string)
            return "N{} [{},{}{}];".format(node.pk, shape, labelstring,
                                           additional_params)


        # Breadth-first search of all ancestors and descendant nodes of a given node
        links = []  # Accumulate links here
        nodes = {n.pk: draw_node_settings(n, style='filled', color='lightblue')} #Accumulate nodes specs here

        last_nodes = [n] # Put the nodes whose links have not been scanned yet

        # Go through the graph on-ward (i.e. look at inputs)
        while last_nodes:
            new_nodes = []
            for node in last_nodes:
                inputs = node.get_inputs(also_labels=True)
                for linkname, inp in inputs:
                    links.append((inp.pk, node.pk, linkname))
                    if inp.pk not in nodes:
                        nodes[inp.pk] = draw_node_settings(inp)
                        new_nodes.append(inp)
            last_nodes = new_nodes

        # Go through the graph down-ward (i.e. look at outputs)
        last_nodes = [n]
        while last_nodes:
            new_nodes = []
            for node in last_nodes:
                outputs = node.get_outputs(also_labels=True)
                for linkname, out in outputs:
                    links.append((node.pk, out.pk, linkname))
                    if out.pk not in nodes:
                        nodes[out.pk] = draw_node_settings(out)
                        new_nodes.append(out)
            last_nodes = new_nodes

        # Generate name of the output file. Default
        out_file_name = "{}.dot".format(root_pk)
        print "out_file_name ", out_file_name
        with open(out_file_name,'w') as fout:

            fout.write("digraph G {\n")

            for l in links:
                fout.write('    {} -> {} [label="{}"];\n'.format("N{}".format(l[0]),  "N{}".format(l[1]), l[2]))
            for n_name, n_values in nodes.iteritems():
                fout.write("    {}\n".format(n_values))

            fout.write("}\n")
