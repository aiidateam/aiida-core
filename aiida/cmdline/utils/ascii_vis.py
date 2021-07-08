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
__all__ = ('format_call_graph',)

TREE_LAST_ENTRY = '\u2514\u2500\u2500 '
TREE_MIDDLE_ENTRY = '\u251C\u2500\u2500 '
TREE_FIRST_ENTRY = TREE_MIDDLE_ENTRY


def calc_info(node):
    """Return a string with the summary of the state of a CalculationNode."""
    from aiida.orm import ProcessNode, WorkChainNode

    if not isinstance(node, ProcessNode):
        raise TypeError(f'Unknown type: {type(node)}')

    process_label = node.process_label
    process_state = node.process_state.value.capitalize()
    exit_status = node.exit_status

    if exit_status is not None:
        string = f'{process_label}<{node.pk}> {process_state} [{exit_status}]'
    else:
        string = f'{process_label}<{node.pk}> {process_state}'

    if isinstance(node, WorkChainNode) and node.stepper_state_info:
        string += f' [{node.stepper_state_info}]'

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


def format_tree_descending(tree, prefix='', pos=-1):
    """Format a descending tree."""
    # pylint: disable=too-many-branches
    text = []

    if isinstance(tree, tuple):
        info = tree[0]
    else:
        info = tree

    if pos == -1:
        pre = ''
    elif pos == 0:
        pre = f'{prefix}{TREE_FIRST_ENTRY}'
    elif pos == 1:
        pre = f'{prefix}{TREE_MIDDLE_ENTRY}'
    else:
        pre = f'{prefix}{TREE_LAST_ENTRY}'
    text.append(f'{pre}{info}')

    if isinstance(tree, tuple):
        _, value = tree
        num_entries = len(value)
        if pos in [-1, 2]:
            new_prefix = f'{prefix}    '
        else:
            new_prefix = f'{prefix}│   '
        for i, entry in enumerate(value):
            if i == num_entries - 1:
                pos = 2
            elif i == 0:
                pos = 0
            else:
                pos = 1
            text.append(format_tree_descending(entry, new_prefix, pos))

    return '\n'.join(text)
