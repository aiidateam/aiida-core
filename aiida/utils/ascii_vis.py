# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.common.links import LinkType
from ete3 import Tree


def draw_parents(node, node_label=None, show_pk=True, dist=2,
                  follow_links_of_type=None):
    """
    Print an ASCII tree of the parents of the given node.

    :param node: The node to draw for
    :type node: :class:`aiida.orm.data.Data`
    :param node_label: The label to use for the nodes
    :type node_label: str
    :param show_pk: Show the PK of nodes alongside the label
    :type show_pk: bool
    :param dist: The number of steps away from this node to branch out
    :type dist: int
    :param follow_links_of_type: Follow links of this type when making steps,
        if None then it will follow CREATE and INPUT links
    :type follow_links_of_type: str
    """
    print(get_ascii_tree(node, node_label, show_pk, dist,
                         follow_links_of_type, False))


def draw_children(node, node_label=None, show_pk=True, dist=2,
                  follow_links_of_type=None):
    """
    Print an ASCII tree of the parents of the given node.

    :param node: The node to draw for
    :type node: :class:`aiida.orm.data.Data`
    :param node_label: The label to use for the nodes
    :type node_label: str
    :param show_pk: Show the PK of nodes alongside the label
    :type show_pk: bool
    :param dist: The number of steps away from this node to branch out
    :type dist: int
    :param follow_links_of_type: Follow links of this type when making steps,
        if None then it will follow CREATE and INPUT links
    :type follow_links_of_type: str
    """
    print(get_ascii_tree(node, node_label, show_pk, dist,
                         follow_links_of_type, True))


def get_ascii_tree(node, node_label=None, show_pk=True, max_depth=1,
                   follow_links_of_type=None, descend=True):
    """
    Get a string representing an ASCII tree for the given node.

    :param node: The node to get the tree for
    :type node: :class:`aiida.orm.node.Node`
    :param node_label: What to label the nodes with (can be an attribute name)
    :type node_label: str
    :param show_pk: If True, show the pk with the node label
    :type show_pk: bool
    :param max_depth: The maximum depth to follow starting from the node
    :type max_depth: int
    :param follow_links_of_type: Follow links of a given type, can be None
    :type follow_links_of_type: One of the members from
        :class:`aiida.common.links.LinkType`
    :param descend: if True will follow outputs, if False inputs
    :type descend: bool
    :return: The string giving an ASCII representation of the tree from the
        node
    :rtype: str
    """
    tree_string = build_tree(
       node, node_label, show_pk, max_depth, follow_links_of_type, descend
    )
    t = Tree("({});".format(tree_string), format=1)
    return t.get_ascii(show_internal=True)


def build_tree(node, node_label=None, show_pk=True, max_depth=1,
               follow_links_of_type=None, descend=True, depth=0):
    out_values = []

    if depth < max_depth:
        relatives = []

        if descend:
            outputs = node.get_outputs(link_type=follow_links_of_type)
        else:  # ascend
            if follow_links_of_type is None:
                outputs = node.get_inputs(link_type=LinkType.CREATE)
                outputs.extend(node.get_inputs(link_type=LinkType.INPUT))
            else:
                outputs = node.get_inputs(link_type=follow_links_of_type)

        for child in sorted(outputs, key=_ctime):
            relatives.append(
                build_tree(child, node_label, show_pk, max_depth,
                           follow_links_of_type, descend, depth + 1)
            )

        if relatives:
            out_values.append("({})".format(", ".join(relatives)))

    out_values.append(_generate_node_label(node, node_label, show_pk))

    return "".join(out_values)


def _generate_node_label(node, node_attr, show_pk):
    """
    Generate a label for the node.

    :param node: The node to generate the label for
    :type node: :class:`aiida.orm.node.Node`
    :param node_attr: The attribute to use as the label, can be None
    :type node_attr: str
    :param show_pk: if True, show the PK alongside the label
    :type show_pk: bool
    :return: The generated label
    :rtype: str
    """

    label = None
    if node_attr is None:
        attrs = node.get_attrs()
        # Try a list of default ones
        for l in ['value', 'function_name', '_process_label']:
            try:
                label = str(attrs[l])
            except KeyError:
                pass
    else:
        try:
            label = str(getattr(node, node_attr))
        except AttributeError:
            try:
                label = node.get_attr(node_attr)
            except AttributeError:
                pass

    # Couldn't find one, so just use the class name
    if label is None:
        label = node.__class__.__name__

    if show_pk:
        label += " [{}]".format(node.pk)

    return label


def _ctime(node):
    return node.ctime
