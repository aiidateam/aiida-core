# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQL statements to detect invalid/ununderstood links for the provenance redesign migration."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

SELECT_CALCULATIONS_WITH_OUTGOING_CALL = """
    SELECT node_in.uuid, node_out.uuid, link.type, link.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link ON node_in.id = link.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link.output_id
    WHERE (
        node_in.type LIKE 'calculation.job.%' OR
        node_in.type LIKE 'calculation.inline.%'
    )
    AND link.type = 'calllink';
    """

SELECT_CALCULATIONS_WITH_OUTGOING_RETURN = """
    SELECT node_in.uuid, node_out.uuid, link.type, link.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link ON node_in.id = link.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link.output_id
    WHERE (
        node_in.type LIKE 'calculation.job.%' OR
        node_in.type LIKE 'calculation.inline.%'
    )
    AND link.type = 'returnlink';
    """

SELECT_WORKFLOWS_WITH_ISOLATED_CREATE_LINK = """
    SELECT node_in.uuid, node_out.uuid, link3.type, link3.label
    FROM db_dbnode AS node_in
    JOIN db_dblink AS link3 ON node_in.id = link3.input_id
    JOIN db_dbnode AS node_out ON node_out.id = link3.output_id
    JOIN
    (
        SELECT node2.id
        FROM db_dbnode AS node2
        JOIN db_dblink AS link2 ON node2.id = link2.input_id
        WHERE (node2.type LIKE 'calculation.work.%' OR node2.type LIKE 'calculation.function.%')
        AND link2.type = 'createlink'
        EXCEPT (
            SELECT returnlinks.input_id
            FROM db_dblink AS returnlinks
            JOIN (
                SELECT node.id, node.type, link.label, link.input_id, link.output_id
                FROM db_dbnode AS node
                JOIN db_dblink AS link ON node.id = link.input_id
                WHERE (node.type LIKE 'calculation.work.%' OR node.type LIKE 'calculation.function.%')
                AND link.type = 'createlink'
            ) AS createlinks
            ON (returnlinks.input_id = createlinks.input_id AND returnlinks.output_id = createlinks.output_id)
            WHERE returnlinks.type = 'returnlink'
        )
        EXCEPT (
            SELECT calllinks.wfid
            FROM db_dblink AS inputlinks
            JOIN
            (
                (
                SELECT node2.id AS wfid, node2.type, link2.label, link2.input_id, link2.output_id AS subwfid
                FROM db_dbnode AS node2 JOIN db_dblink AS link2 ON node2.id = link2.input_id
                WHERE (node2.type LIKE 'calculation.work.%' OR node2.type LIKE 'calculation.function.%')
                AND link2.type = 'calllink'
            ) AS calllinks
            JOIN (
                SELECT node.id AS wfid, node.type, link.label, link.input_id, link.output_id AS dataid
                FROM db_dbnode AS node JOIN db_dblink AS link
                ON node.id = link.input_id
                WHERE (node.type LIKE 'calculation.work.%' OR node.type LIKE 'calculation.function.%')
                AND link.type = 'createlink') AS createlinks
                ON calllinks.wfid = createlinks.wfid
            )
            ON (inputlinks.input_id = createlinks.dataid AND inputlinks.output_id = calllinks.subwfid)
        )
    ) AS node_in_subquery ON node_in.id = node_in_subquery.id
    WHERE link3.type = 'createlink';
    """

INVALID_LINK_SELECT_STATEMENTS = (
    (SELECT_CALCULATIONS_WITH_OUTGOING_CALL, 'detected calculation nodes with outgoing `call` links.'),
    (SELECT_CALCULATIONS_WITH_OUTGOING_RETURN, 'detected calculation nodes with outgoing `return` links.'),
    (SELECT_WORKFLOWS_WITH_ISOLATED_CREATE_LINK, 'detected workflow nodes with isolated `create` links.'),
)
