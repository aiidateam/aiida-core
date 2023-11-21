# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""SQL statements to detect invalid/understood links for the provenance redesign migration."""
from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import column, select, table, text

from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR

from .integrity import infer_calculation_entry_point, write_database_integrity_violation

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


def migrate_infer_calculation_entry_point(alembic_op):
    """Set the process type for calculation nodes by inferring it from their type string."""
    connection = alembic_op.get_bind()
    DbNode = table(  # pylint: disable=invalid-name
        'db_dbnode', column('id', Integer), column('uuid', UUID), column('type', String),
        column('process_type', String)
    )

    query_set = connection.execute(select(DbNode.c.type).where(DbNode.c.type.like('calculation.%'))).fetchall()
    type_strings = set(entry[0] for entry in query_set)
    mapping_node_type_to_entry_point = infer_calculation_entry_point(type_strings=type_strings)

    fallback_cases = []

    for type_string, entry_point_string in mapping_node_type_to_entry_point.items():

        # If the entry point string does not contain the entry point string separator, the mapping function was not able
        # to map the type string onto a known entry point string. As a fallback it uses the modified type string itself.
        # All affected entries should be logged to file that the user can consult.
        if ENTRY_POINT_STRING_SEPARATOR not in entry_point_string:
            query_set = connection.execute(
                select(DbNode.c.uuid).where(DbNode.c.type == alembic_op.inline_literal(type_string))
            ).fetchall()

            uuids = [str(entry.uuid) for entry in query_set]
            for uuid in uuids:
                fallback_cases.append([uuid, type_string, entry_point_string])

        connection.execute(
            DbNode.update().where(DbNode.c.type == alembic_op.inline_literal(type_string)
                                  ).values(process_type=alembic_op.inline_literal(entry_point_string))
        )

    if fallback_cases:
        headers = ['UUID', 'type (old)', 'process_type (fallback)']
        warning_message = 'found calculation nodes with a type string that could not be mapped onto a known entry point'
        action_message = 'inferred `process_type` for all calculation nodes, using fallback for unknown entry points'
        write_database_integrity_violation(fallback_cases, headers, warning_message, action_message)


def detect_unexpected_links(alembic_op):
    """Scan the database for any links that are unexpected.

    The checks will verify that there are no outgoing `call` or `return` links from calculation nodes and that if a
    workflow node has a `create` link, it has at least an accompanying return link to the same data node, or it has a
    `call` link to a calculation node that takes the created data node as input.
    """
    connection = alembic_op.get_bind()
    for sql, warning_message in INVALID_LINK_SELECT_STATEMENTS:
        results = list(connection.execute(text(sql)))
        if results:
            headers = ['UUID source', 'UUID target', 'link type', 'link label']
            write_database_integrity_violation(results, headers, warning_message)
