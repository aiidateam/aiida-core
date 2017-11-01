# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os, tempfile

def draw_graph(origin_node, ancestor_depth=None, descendant_depth=None, format='dot',
        include_calculation_inputs=False, include_calculation_outputs=False):
    """
    The algorithm starts from the original node and goes both input-ward and output-ward via a breadth-first algorithm.

    :param origin_node: An Aiida node, the starting point for drawing the graph
    :param int ancestor_depth: The maximum depth of the ancestors drawn. If left to None, we recurse until the graph is fully explored
    :param int descendant_depth: The maximum depth of the descendants drawn. If left to None, we recurse until the graph is fully explored
    :param str format: The format, by default dot

    :returns: The exit_status of the os.system call that produced the valid file
    :returns: The file name of the final output

    ..note::
        If an invalid format is provided graphviz prints a helpful message, so this doesn't need to be implemented here.
    """
    # 
    # until the connected part of the graph that contains the root_pk is fully explored.
    # TODO this command deserves to be improved, with options and further subcommands

    from aiida.orm.calculation import Calculation
    from aiida.orm.calculation.job import JobCalculation
    from aiida.orm.code import Code
    from aiida.orm.node import Node
    from aiida.common.links import LinkType
    from aiida.orm.querybuilder import QueryBuilder

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
        if node.label:
            label_string = "\n'{}'".format(node.label)
            additional_string = ""
        else:
            additional_string = "\n {}".format(node.get_desc())
            label_string = ""
        labelstring = 'label="{} ({}){}{}"'.format(
            node.__class__.__name__, node.pk, label_string,
            additional_string)
        return "N{} [{},{}{}];".format(node.pk, shape, labelstring,
                                       additional_params)

    def draw_link_settings(inp_id, out_id, link_label, link_type):
        if link_type in (LinkType.CREATE.value, LinkType.INPUT.value):
            style='solid'  # Solid lines and black colors
            color = "0.0 0.0 0.0" # for CREATE and INPUT (The provenance graph)
        elif link_type == LinkType.RETURN.value:
            style='dotted'  # Dotted  lines of
            color = "0.0 0.0 0.0" # black color for Returns
        elif link_type == LinkType.CALL.value:
            style='bold' # Bold lines and
            color = "0.0 1.0 1.0" # Bright red for calls
        else:
            style='solid'   # Solid and
            color="0.0 0.0 0.5" #grey lines for unspecified links!
        return '    {} -> {} [label="{}", color="{}", style="{}"];'.format("N{}".format(inp_id),  "N{}".format(out_id), link_label, color, style)

    # Breadth-first search of all ancestors and descendant nodes of a given node
    links = {}  # Accumulate links here
    nodes = {origin_node.pk: draw_node_settings(origin_node, style='filled', color='lightblue')} #Accumulate nodes specs here
    # Additional nodes (the ones added with either one of  include_calculation_inputs or include_calculation_outputs
    # is set to true. I have to put them in a different dictionary because nodes is the one used for the recursion,
    # whereas these should not be used for the recursion:
    additional_nodes = {}

    last_nodes = [origin_node] # Put the nodes whose links have not been scanned yet

    # Go through the graph on-ward (i.e. look at inputs)
    depth = 0
    while last_nodes:
        # I augment depth every time I get through a new iteration
        depth += 1
        # I check whether I should stop here:
        if ancestor_depth is not None and depth > ancestor_depth:
            break
        # I continue by adding new nodes here!
        new_nodes = []
        for node in last_nodes:
            # This query gives me all the inputs of this node, and link labels and types!
            input_query = QueryBuilder()
            input_query.append(Node, filters={'id':node.pk}, tag='n')
            input_query.append(Node, input_of='n', edge_project=('id', 'label', 'type'), project='*', tag='inp')
            for inp, link_id, link_label, link_type in input_query.iterall():
                # I removed this check, to me there is no way that this link was already referred to!
                # if link_id not in links:
                links[link_id] = draw_link_settings(inp.pk, node.pk, link_label, link_type)
                # For the nodes I need to check, maybe this same node is referred to multiple times.
                if inp.pk not in nodes:
                    nodes[inp.pk] = draw_node_settings(inp)
                    new_nodes.append(inp)

            # Checking whether I also should include all the outputs of a calculation into the drawing:
            if include_calculation_outputs and isinstance(node, Calculation):
                # Query for the outputs, giving me also link labels and types:
                output_query = QueryBuilder()
                output_query.append(Node, filters={'id':node.pk}, tag='n')
                output_query.append(Node, output_of='n', edge_project=('id', 'label', 'type'), project='*', tag='out')
                # Iterate through results
                for out, link_id, link_label, link_type in output_query.iterall():
                    # This link might have been drawn already, because the output is maybe
                    # already drawn.
                    # To check: Maybe it's more efficient not to check this, since
                    # the dictionaries are large and contain many keys...
                    # I.e. just always draw, also when overwriting an existing (identical) entry.
                    if link_id not in links:
                        links[link_id] = draw_link_settings(node.pk, out.pk, link_label, link_type)
                    if out.pk not in nodes and out.pk not in additional_nodes:
                        additional_nodes[out.pk] = draw_node_settings(out)

        last_nodes = new_nodes


    # Go through the graph down-ward (i.e. look at outputs)
    last_nodes = [origin_node]
    depth = 0
    while last_nodes:
        depth += 1
        # Also here, checking of maximum descendant depth is set and applies.
        if descendant_depth is not None and depth > descendant_depth:
            break
        new_nodes = []

        for node in last_nodes:
            # Query for the outputs:
            output_query = QueryBuilder()
            output_query.append(Node, filters={'id':node.pk}, tag='n')
            output_query.append(Node, output_of='n', edge_project=('id', 'label', 'type'), project='*', tag='out')

            for out, link_id, link_label, link_type in output_query.iterall():
                # Draw the link
                links[link_id] = draw_link_settings(node.pk, out.pk, link_label, link_type)
                if out.pk not in nodes:
                    nodes[out.pk] = draw_node_settings(out)
                    new_nodes.append(out)

            if include_calculation_inputs and isinstance(node, Calculation):
                input_query = QueryBuilder()
                input_query.append(Node, filters={'id':node.pk}, tag='n')
                input_query.append(Node, input_of='n', edge_project=('id', 'label', 'type'), project='*', tag='inp')
                for inp, link_id, link_label, link_type in input_query.iterall():
                    # Also here, maybe it's just better not to check?
                    if link_id not in links:
                        links[link_id] = draw_link_settings(inp.pk, node.pk, link_label, link_type)
                    if inp.pk not in nodes and inp.pk not in additional_nodes:
                        additional_nodes[inp.pk] = draw_node_settings(inp)
        last_nodes = new_nodes

    # Writing the graph to a temporary file
    fd, fname = tempfile.mkstemp(suffix='.dot')
    with open(fname, 'w') as fout:
        fout.write("digraph G {\n")
        for l_name, l_values in links.iteritems():
            fout.write('    {}\n'.format(l_values))
        for n_name, n_values in nodes.iteritems():
            fout.write("    {}\n".format(n_values))
        for n_name, n_values in additional_nodes.iteritems():
            fout.write("    {}\n".format(n_values))
        fout.write("}\n")

    # Now I am producing the output file
    output_file_name = "{0}.{format}".format(origin_node.pk, format=format)
    exit_status = os.system('dot -T{format} {0} -o {1}'.format(fname, output_file_name, format=format))
    # cleaning up by removing the temporary file
    os.remove(fname)
    return exit_status, output_file_name
