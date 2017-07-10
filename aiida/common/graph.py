import os, tempfile

def draw_graph(origin_node, ancestor_depth=None, descendant_depth=None, format='dot'):
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
    from aiida.orm.data.array.kpoints import KpointsData
    from aiida.orm.data.structure import StructureData
    from aiida.orm.calculation.inline import InlineCalculation


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


    # Breadth-first search of all ancestors and descendant nodes of a given node
    links = []  # Accumulate links here
    nodes = {origin_node.pk: draw_node_settings(origin_node, style='filled', color='lightblue')} #Accumulate nodes specs here

    last_nodes = [origin_node] # Put the nodes whose links have not been scanned yet

    # Go through the graph on-ward (i.e. look at inputs)
    depth = 0
    while last_nodes:
        depth += 1
        if ancestor_depth is not None and depth > ancestor_depth:
            break

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
    last_nodes = [origin_node]
    depth = 0
    while last_nodes:
        depth += 1
        if descendant_depth is not None and depth > descendant_depth:
            break
        new_nodes = []
        for node in last_nodes:
            outputs = node.get_outputs(also_labels=True)
            for linkname, out in outputs:
                links.append((node.pk, out.pk, linkname))
                if out.pk not in nodes:
                    nodes[out.pk] = draw_node_settings(out)
                    new_nodes.append(out)
        last_nodes = new_nodes

    # Writing the graph to a temporary file
    fd, fname = tempfile.mkstemp(suffix='.dot')
    with open(fname, 'w') as fout:
        fout.write("digraph G {\n")
        for l in links:
            fout.write('    {} -> {} [label="{}"];\n'.format("N{}".format(l[0]),  "N{}".format(l[1]), l[2]))
        for n_name, n_values in nodes.iteritems():
            fout.write("    {}\n".format(n_values))
        fout.write("}\n")

    # Now I am producing the output file
    output_file_name = "{0}.{format}".format(origin_node.pk, format=format)
    exit_status = os.system('dot -T{format} {0} -o {1}'.format(fname, output_file_name, format=format))
    # cleaning up by removing the temporary file
    os.remove(fname)
    return exit_status, output_file_name
