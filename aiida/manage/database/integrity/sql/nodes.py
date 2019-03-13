# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQL statements that test the integrity of the database with respect to nodes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.extendeddicts import AttributeDict
from aiida.orm import Data, CalculationNode, WorkflowNode


def format_type_string_regex(node_class):
    """Format the type string regex to match nodes that are a sub class of the given node class.

    For example, for the CalculationNode class, the type string is given by::

        node.process.calculation.CalculationNode.

    To obtain the regex string that can be used to match sub classes, one has to strip the last period and
    the class name::

        nodes.process.calculation.

    Any node with a type string that starts with this sub string is a sub class of the `CalculationNode` class.

    :param node_class: the node class for which to get the sub class regex string
    :return: a string that can be used as regex to match nodes that are a sub class of the given node class
    """
    # 'nodes.process.calculation.CalculationNode.'
    type_string = node_class._plugin_type_string  # pylint: disable=protected-access

    # ['nodes', 'process', 'calculation']
    type_parts = type_string.split('.')[:-2]

    # 'nodes.process.calculation.'
    type_string_regex = '{}.'.format('.'.join(type_parts))

    return type_string_regex


VALID_NODE_BASE_CLASSES = [Data, CalculationNode, WorkflowNode]
VALID_NODE_TYPE_STRING = '({})%'.format('|'.join([format_type_string_regex(cls) for cls in VALID_NODE_BASE_CLASSES]))

SELECT_NODES_WITH_INVALID_TYPE = """
    SELECT node.id, node.uuid, node.node_type
    FROM db_dbnode AS node
    WHERE node.node_type NOT SIMILAR TO %(valid_node_types)s;
    """

INVALID_NODE_SELECT_STATEMENTS = (AttributeDict({
    'sql': SELECT_NODES_WITH_INVALID_TYPE,
    'parameters': {
        'valid_node_types': VALID_NODE_TYPE_STRING
    },
    'headers': ['ID', 'UUID', 'Type'],
    'message': 'detected nodes with invalid type'
}),)
