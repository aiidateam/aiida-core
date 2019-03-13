# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQL statements that test the integrity of the database with respect to links."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.extendeddicts import AttributeDict
from aiida.common.links import LinkType

VALID_LINK_TYPES = tuple([link_type.value for link_type in LinkType])

SELECT_CALCULATIONS_WITH_OUTGOING_CALL = """
    SELECT link.id, node_in.uuid, node_out.uuid, link.type, link.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link ON node_in.id = link.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link.output_id
    WHERE node_in.node_type LIKE 'process.calculation%'
    AND link.type = 'call_calc' OR link.type = 'call_work';
    """

SELECT_CALCULATIONS_WITH_OUTGOING_RETURN = """
    SELECT link.id, node_in.uuid, node_out.uuid, link.type, link.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link ON node_in.id = link.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link.output_id
    WHERE node_in.node_type LIKE 'process.calculation%'
    AND link.type = 'return';
    """

SELECT_WORKFLOWS_WITH_OUTGOING_CREATE = """
    SELECT link.id, node_in.uuid, node_out.uuid, link.type, link.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link ON node_in.id = link.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link.output_id
    WHERE node_in.node_type LIKE 'process.workflow%'
    AND link.type = 'create';
    """

SELECT_LINKS_WITH_INVALID_TYPE = """
    SELECT link.id, node_in.uuid, node_out.uuid, link.type, link.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link ON node_in.id = link.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link.output_id
    WHERE link.type NOT IN %(valid_link_types)s;
    """

SELECT_MULTIPLE_INCOMING_CREATE = """
    SELECT node.id, node.uuid, node.node_type, COUNT(link.id)
    FROM db_dbnode AS node
    JOIN db_dblink AS link
    ON node.id = link.output_id
    WHERE node.node_type LIKE 'data.%'
    AND link.type = 'create'
    GROUP BY node.id
    HAVING COUNT(link.id) > 1;
    """

SELECT_MULTIPLE_INCOMING_CALL = """
    SELECT node.id, node.uuid, node.node_type, COUNT(link.id)
    FROM db_dbnode AS node
    JOIN db_dblink AS link
    ON node.id = link.output_id
    WHERE node.node_type LIKE 'process.%'
    AND (link.type = 'call_calc' OR link.type = 'call_work')
    GROUP BY node.id
    HAVING COUNT(link.id) > 1;
    """

INVALID_LINK_SELECT_STATEMENTS = (
    AttributeDict({
        'sql': SELECT_CALCULATIONS_WITH_OUTGOING_CALL,
        'parameters': None,
        'headers': ['ID', 'Input node', 'Output node', 'Type', 'Label'],
        'message': 'detected calculation nodes with outgoing `call` links'
    }),
    AttributeDict({
        'sql': SELECT_CALCULATIONS_WITH_OUTGOING_RETURN,
        'parameters': None,
        'headers': ['ID', 'Input node', 'Output node', 'Type', 'Label'],
        'message': 'detected calculation nodes with outgoing `return` links'
    }),
    AttributeDict({
        'sql': SELECT_WORKFLOWS_WITH_OUTGOING_CREATE,
        'parameters': None,
        'headers': ['ID', 'Input node', 'Output node', 'Type', 'Label'],
        'message': 'detected workflow nodes with outgoing `create` links'
    }),
    AttributeDict({
        'sql': SELECT_LINKS_WITH_INVALID_TYPE,
        'parameters': {
            'valid_link_types': VALID_LINK_TYPES
        },
        'headers': ['ID', 'Input node', 'Output node', 'Type', 'Label'],
        'message': 'detected links with invalid type'
    }),
    AttributeDict({
        'sql': SELECT_MULTIPLE_INCOMING_CREATE,
        'parameters': None,
        'headers': ['ID', 'UUID', 'Type', 'Count'],
        'message': 'detected nodes with more than one incoming `create` link'
    }),
    AttributeDict({
        'sql': SELECT_MULTIPLE_INCOMING_CALL,
        'parameters': None,
        'headers': ['ID', 'UUID', 'Type', 'Count'],
        'message': 'detected nodes with more than one incoming `call` link'
    }),
)
