# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Migration after the provenance redesign

Revision ID: 239cea6d2452
Revises: 140c971ae0a3
Create Date: 2018-12-04 21:14:15.250247

"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from alembic import op
from sqlalchemy import String, Integer
from sqlalchemy.sql import table, column, select, text
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '239cea6d2452'
down_revision = '140c971ae0a3'
branch_labels = None
depends_on = None


def migrate_infer_calculation_entry_point(connection):
    """Set the process type for calculation nodes by inferring it from their type string."""
    from aiida.manage.database.integrity import write_database_integrity_violation
    from aiida.manage.database.integrity.plugins import infer_calculation_entry_point
    from aiida.plugins.entry_point import ENTRY_POINT_STRING_SEPARATOR

    DbNode = table('db_dbnode', column('id', Integer), column('uuid', UUID), column('type', String),
                   column('process_type', String))

    query_set = connection.execute(select([DbNode.c.type]).where(DbNode.c.type.like('calculation.%'))).fetchall()
    type_strings = set(entry[0] for entry in query_set)
    mapping_node_type_to_entry_point = infer_calculation_entry_point(type_strings=type_strings)

    fallback_cases = []

    for type_string, entry_point_string in mapping_node_type_to_entry_point.items():

        # If the entry point string does not contain the entry point string separator, the mapping function was not able
        # to map the type string onto a known entry point string. As a fallback it uses the modified type string itself.
        # All affected entries should be logged to file that the user can consult.
        if ENTRY_POINT_STRING_SEPARATOR not in entry_point_string:
            query_set = connection.execute(
                select([DbNode.c.uuid]).where(DbNode.c.type == op.inline_literal(type_string))).fetchall()

            uuids = [str(entry.uuid) for entry in query_set]
            for uuid in uuids:
                fallback_cases.append([uuid, type_string, entry_point_string])

        connection.execute(DbNode.update().where(DbNode.c.type == op.inline_literal(type_string)).values(
            process_type=op.inline_literal(entry_point_string)))

    if fallback_cases:
        headers = ['UUID', 'type (old)', 'process_type (fallback)']
        warning_message = 'found calculation nodes with a type string that could not be mapped onto a known entry point'
        action_message = 'inferred `process_type` for all calculation nodes, using fallback for unknown entry points'
        write_database_integrity_violation(fallback_cases, headers, warning_message, action_message)


def detect_unexpected_links(connection):
    """Scan the database for any links that are unexpected.

    The checks will verify that there are no outgoing `call` or `return` links from calculation nodes and that if a
    workflow node has a `create` link, it has at least an accompanying return link to the same data node, or it has a
    `call` link to a calculation node that takes the created data node as input.
    """
    from aiida.backends.general.migrations.provenance_redesign import INVALID_LINK_SELECT_STATEMENTS
    from aiida.manage.database.integrity import write_database_integrity_violation

    for sql, warning_message in INVALID_LINK_SELECT_STATEMENTS:
        results = list(connection.execute(text(sql)))
        if results:
            headers = ['UUID source', 'UUID target', 'link type', 'link label']
            write_database_integrity_violation(results, headers, warning_message)


def upgrade():
    """The upgrade migration actions."""
    connection = op.get_bind()

    # Migrate calculation nodes by inferring the process type from the type string
    migrate_infer_calculation_entry_point(connection)

    # Detect if the database contain any unexpected links
    detect_unexpected_links(connection)

    statement = text("""
        DELETE FROM db_dblink WHERE db_dblink.id IN (
            SELECT db_dblink.id FROM db_dblink
            INNER JOIN db_dbnode ON db_dblink.input_id = db_dbnode.id
            WHERE
                (db_dbnode.type LIKE 'calculation.job%' OR db_dbnode.type LIKE 'calculation.inline%')
                AND db_dblink.type = 'returnlink'
        ); -- Delete all outgoing RETURN links from JobCalculation and InlineCalculation nodes

        DELETE FROM db_dblink WHERE db_dblink.id IN (
            SELECT db_dblink.id FROM db_dblink
            INNER JOIN db_dbnode ON db_dblink.input_id = db_dbnode.id
            WHERE
                (db_dbnode.type LIKE 'calculation.job%' OR db_dbnode.type LIKE 'calculation.inline%')
                AND db_dblink.type = 'calllink'
        ); -- Delete all outgoing CALL links from JobCalculation and InlineCalculation nodes

        DELETE FROM db_dblink WHERE db_dblink.id IN (
            SELECT db_dblink.id FROM db_dblink
            INNER JOIN db_dbnode ON db_dblink.input_id = db_dbnode.id
            WHERE
                (db_dbnode.type LIKE 'calculation.function%' OR db_dbnode.type LIKE 'calculation.work%')
                AND db_dblink.type = 'createlink'
        ); -- Delete all outgoing CREATE links from WorkCalculation nodes

        UPDATE db_dbnode SET type = 'calculation.work.WorkCalculation.'
        WHERE type = 'calculation.process.ProcessCalculation.';
         -- First migrate very old `ProcessCalculation` to `WorkCalculation`

        UPDATE db_dbnode SET type = 'node.process.workflow.workfunction.WorkFunctionNode.'
        WHERE type = 'calculation.work.WorkCalculation.'
            AND attributes ? 'function_name';
         -- WorkCalculations that have a `function_name` attribute are `WorkFunctionNode`

        UPDATE db_dbnode SET type = 'node.process.workflow.workchain.WorkChainNode.'
        WHERE type = 'calculation.work.WorkCalculation.';
         -- Update type for `WorkCalculation` nodes - all what is left should be `WorkChainNodes`

        UPDATE db_dbnode SET type = 'node.process.calculation.calcjob.CalcJobNode.'
        WHERE type LIKE 'calculation.job.%'; -- Update type for JobCalculation nodes

        UPDATE db_dbnode SET type = 'node.process.calculation.calcfunction.CalcFunctionNode.'
        WHERE type = 'calculation.inline.InlineCalculation.'; -- Update type for InlineCalculation nodes

        UPDATE db_dbnode SET type = 'node.process.workflow.workfunction.WorkFunctionNode.'
        WHERE type = 'calculation.function.FunctionCalculation.'; -- Update type for FunctionCalculation nodes

        UPDATE db_dblink SET type = 'create' WHERE type = 'createlink'; -- Rename `createlink` to `create`
        UPDATE db_dblink SET type = 'return' WHERE type = 'returnlink'; -- Rename `returnlink` to `return`

        UPDATE db_dblink SET type = 'input_calc' FROM db_dbnode
        WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.calculation%'
        AND db_dblink.type = 'inputlink';
         -- Rename `inputlink` to `input_calc` if the target node is a calculation type node

        UPDATE db_dblink SET type = 'input_work' FROM db_dbnode
        WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.workflow%'
        AND db_dblink.type = 'inputlink';
         -- Rename `inputlink` to `input_work` if the target node is a workflow type node

        UPDATE db_dblink SET type = 'call_calc' FROM db_dbnode
        WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.calculation%'
        AND db_dblink.type = 'calllink';
         -- Rename `calllink` to `call_calc` if the target node is a calculation type node

        UPDATE db_dblink SET type = 'call_work' FROM db_dbnode
        WHERE db_dblink.output_id = db_dbnode.id AND db_dbnode.type LIKE 'node.process.workflow%'
        AND db_dblink.type = 'calllink';
         -- Rename `calllink` to `call_work` if the target node is a workflow type node
        """)
    connection.execute(statement)


def downgrade():
    """The downgrade migration actions."""
    connection = op.get_bind()

    statement = text("""
        UPDATE db_dbnode SET type = 'calculation.job.JobCalculation.'
        WHERE type = 'node.process.calculation.calcjob.CalcJobNode.';

        UPDATE db_dbnode SET type = 'calculatison.inline.InlineCalculation.'
        WHERE type = 'node.process.calculation.calcfunction.CalcFunctionNode.';

        UPDATE db_dbnode SET type = 'calculation.function.FunctionCalculation.'
        WHERE type = 'node.process.workflow.workfunction.WorkFunctionNode.';

        UPDATE db_dbnode SET type = 'calculation.work.WorkCalculation.'
        WHERE type = 'node.process.workflow.workchain.WorkChainNode.';


        UPDATE db_dblink SET type = 'inputlink'
        WHERE type = 'input_call' OR type = 'input_work';

        UPDATE db_dblink SET type = 'calllink'
        WHERE type = 'call_call' OR type = 'call_work';

        UPDATE db_dblink SET type = 'createlink'
        WHERE type = 'create';

        UPDATE db_dblink SET type = 'returnlink'
        WHERE type = 'return';
        """)
    connection.execute(statement)
