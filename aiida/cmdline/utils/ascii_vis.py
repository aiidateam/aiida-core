# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to draw ASCII diagrams to the command line."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ete3 import Tree

from aiida.common.links import LinkType

__all__ = ('draw_children', 'draw_parents', 'format_call_graph')

TREE_LAST_ENTRY = u'\u2514\u2500\u2500 '
TREE_MIDDLE_ENTRY = u'\u251C\u2500\u2500 '
TREE_FIRST_ENTRY = TREE_MIDDLE_ENTRY


def draw_parents(node, node_label=None, show_pk=True, dist=2, follow_links_of_type=None):
    """
    Print an ASCII tree of the parents of the given node.

    :param node: The node to draw for
    :type node: :class:`aiida.orm.nodes.data.Data`
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
    return get_ascii_tree(node, node_label, show_pk, dist, follow_links_of_type, False)


def draw_children(node, node_label=None, show_pk=True, dist=2, follow_links_of_type=None):
    """
    Print an ASCII tree of the parents of the given node.

    :param node: The node to draw for
    :type node: :class:`aiida.orm.nodes.data.Data`
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
    return get_ascii_tree(node, node_label, show_pk, dist, follow_links_of_type, True)


def get_ascii_tree(node, node_label=None, show_pk=True, max_depth=1, follow_links_of_type=None, descend=True):
    """
    Get a string representing an ASCII tree for the given node.

    :param node: The node to get the tree for
    :type node: :class:`aiida.orm.nodes.node.Node`
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
    :return: The string giving an ASCII representation of the tree from the node
    :rtype: str
    """
    tree_string = build_tree(node, node_label, show_pk, max_depth, follow_links_of_type, descend)
    tree = Tree('({});'.format(tree_string), format=1)
    return tree.get_ascii(show_internal=True)


def build_tree(node, node_label=None, show_pk=True, max_depth=1, follow_links_of_type=None, descend=True, depth=0):
    """
    Recursively build an ASCII string representation of the node tree

    :param node: The node to get the tree for
    :type node: :class:`aiida.orm.nodes.node.Node`
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
    :param depth: the current depth
    :type depth: int
    :return: The string giving an ASCII representation of the tree from the node
    :rtype: str
    """
    # pylint: disable=too-many-arguments
    out_values = []

    if depth < max_depth:
        relatives = []

        if descend:
            outputs = node.get_outgoing(link_type=follow_links_of_type).all_nodes()
        else:  # ascend
            if follow_links_of_type is None:
                follow_links_of_type = (LinkType.CREATE, LinkType.INPUT_CALC, LinkType.INPUT_WORK)

            outputs = node.get_incoming(link_type=follow_links_of_type).all_nodes()

        for child in sorted(outputs, key=lambda node: node.ctime):
            relatives.append(
                build_tree(child, node_label, show_pk, max_depth, follow_links_of_type, descend, depth + 1)
            )

        if relatives:
            out_values.append('({})'.format(', '.join(relatives)))

    out_values.append(_generate_node_label(node, node_label, show_pk))

    return ''.join(out_values)


def _generate_node_label(node, node_attr, show_pk):
    """
    Generate a label for the node.

    :param node: The node to generate the label for
    :type node: :class:`aiida.orm.nodes.node.Node`
    :param node_attr: The attribute to use as the label, can be None
    :type node_attr: str
    :param show_pk: if True, show the PK alongside the label
    :type show_pk: bool
    :return: The generated label
    :rtype: str
    """
    label = None
    if node_attr is None:
        try:
            label = node.process_label
        except AttributeError:
            label = None
    else:
        try:
            label = str(getattr(node, node_attr))
        except AttributeError:
            try:
                label = node.get_attribute(node_attr)
            except AttributeError:
                pass

    # Couldn't find one, so just use the class name
    if label is None:
        label = node.__class__.__name__

    if show_pk:
        label += ' [{}]'.format(node.pk)

    return label


def calc_info(node):
    """Return a string with the summary of the state of a CalculationNode."""
    from aiida.orm import ProcessNode, WorkChainNode

    if not isinstance(node, ProcessNode):
        raise TypeError('Unknown type: {}'.format(type(node)))

    process_label = node.process_label
    process_state = node.process_state.value.capitalize()
    exit_status = node.exit_status

    if exit_status is not None:
        string = u'{}<{}> {} [{}]'.format(process_label, node.pk, process_state, exit_status)
    else:
        string = u'{}<{}> {}'.format(process_label, node.pk, process_state)

    if isinstance(node, WorkChainNode) and node.stepper_state_info:
        string += u' [{}]'.format(node.stepper_state_info)

    return string


def format_call_graph(calc_node, info_fn=calc_info):
    """
    Print a tree like the POSIX tree command for the calculation call graph

    :param calc_node: The calculation node
    :param info_fn: An optional function that takes the node and returns a string
        of information to be displayed for each node.
    """
    call_tree = build_call_graph(calc_node, info_fn=info_fn)
    return format_tree_descending(call_tree)


def build_call_graph(calc_node, info_fn=calc_info):
    """Build the call graph of a given node."""
    info_string = info_fn(calc_node)
    called = calc_node.called
    called.sort(key=lambda x: x.ctime)
    if called:
        return info_string, [build_call_graph(child, info_fn) for child in called]

    return info_string


def format_tree_descending(tree, prefix=u'', pos=-1):
    """Format a descending tree."""
    # pylint: disable=too-many-branches
    text = []

    if isinstance(tree, tuple):
        info = tree[0]
    else:
        info = tree

    if pos == -1:
        pre = u''
    elif pos == 0:
        pre = u'{}{}'.format(prefix, TREE_FIRST_ENTRY)
    elif pos == 1:
        pre = u'{}{}'.format(prefix, TREE_MIDDLE_ENTRY)
    else:
        pre = u'{}{}'.format(prefix, TREE_LAST_ENTRY)
    text.append(u'{}{}'.format(pre, info))

    if isinstance(tree, tuple):
        _, value = tree
        num_entries = len(value)
        if pos in [-1, 2]:
            new_prefix = u'{}    '.format(prefix)
        else:
            new_prefix = u'{}\u2502   '.format(prefix)
        for i, entry in enumerate(value):
            if i == num_entries - 1:
                pos = 2
            elif i == 0:
                pos = 0
            else:
                pos = 1
            text.append(format_tree_descending(entry, new_prefix, pos))

    return u'\n'.join(text)
