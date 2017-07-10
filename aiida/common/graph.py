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
        return '    {} -> {} [label="{}"];'.format("N{}".format(inp_id),  "N{}".format(out_id), link_label)

    # Breadth-first search of all ancestors and descendant nodes of a given node
    links = {}  # Accumulate links here
    nodes = {origin_node.pk: draw_node_settings(origin_node, style='filled', color='lightblue')} #Accumulate nodes specs here
    additional_nodes = {}

    last_nodes = [origin_node] # Put the nodes whose links have not been scanned yet

    # Go through the graph on-ward (i.e. look at inputs)
    depth = 0
    while last_nodes:
        depth += 1
        if ancestor_depth is not None and depth > ancestor_depth:
            break

        new_nodes = []
        for node in last_nodes:
            input_query = QueryBuilder()
            input_query.append(Node, filters={'id':node.pk}, tag='n')
            input_query.append(Node, input_of='n', edge_project=('id', 'label', 'type'), project='*', tag='inp')
            for inp, link_id, link_label, link_type in input_query.iterall():
                if link_id not in links:
                    links[link_id] = draw_link_settings(inp.pk, node.pk, link_label, link_type)
                if inp.pk not in nodes:
                    nodes[inp.pk] = draw_node_settings(inp)
                    new_nodes.append(inp)
                

            if include_calculation_outputs and isinstance(node, Calculation):
                output_query = QueryBuilder()
                output_query.append(Node, filters={'id':node.pk}, tag='n')
                output_query.append(Node, output_of='n', edge_project=('id', 'label', 'type'), project='*', tag='out')

                for out, link_id, link_label, link_type in output_query.iterall():
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
        if descendant_depth is not None and depth > descendant_depth:
            break
        new_nodes = []

        for node in last_nodes:
            output_query = QueryBuilder()
            output_query.append(Node, filters={'id':node.pk}, tag='n')
            output_query.append(Node, output_of='n', edge_project=('id', 'label', 'type'), project='*', tag='out')

            for out, link_id, link_label, link_type in output_query.iterall():
                if link_id not in links:
                    links[link_id] = draw_link_settings(node.pk, out.pk, link_label, link_type)
                if out.pk not in nodes:
                    nodes[out.pk] = draw_node_settings(out)
                    new_nodes.append(out)

            if include_calculation_inputs and isinstance(node, Calculation):
                input_query = QueryBuilder()
                input_query.append(Node, filters={'id':node.pk}, tag='n')
                input_query.append(Node, input_of='n', edge_project=('id', 'label', 'type'), project='*', tag='inp')
                for inp, link_id, link_label, link_type in input_query.iterall():
                    if link_id not in links:
                        links[link_id] = draw_link_settings(inp.pk, node.pk, link_label, link_type)
                    if out.pk not in nodes and out.pk not in additional_nodes:
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
