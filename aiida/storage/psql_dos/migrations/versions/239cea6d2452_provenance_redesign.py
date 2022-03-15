# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Migration after the provenance redesign

Revision ID: 239cea6d2452
Revises: 140c971ae0a3
Create Date: 2018-12-04 21:14:15.250247

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '239cea6d2452'
down_revision = '140c971ae0a3'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    from aiida.storage.psql_dos.migrations.utils import provenance_redesign

    # Migrate calculation nodes by inferring the process type from the type string
    provenance_redesign.migrate_infer_calculation_entry_point(op)

    # Detect if the database contain any unexpected links
    provenance_redesign.detect_unexpected_links(op)

    op.execute(
        """
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
        """
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 239cea6d2452.')
