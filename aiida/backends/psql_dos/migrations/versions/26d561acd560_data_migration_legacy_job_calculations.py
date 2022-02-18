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
"""Migrate legacy `JobCalculations`.

These old nodes have already been migrated to the correct `CalcJobNode` type in a previous migration, but they can
still contain a `state` attribute with a deprecated `JobCalcState` value and they are missing a value for the
`process_state`, `process_status`, `process_label` and `exit_status`. The `process_label` is impossible to infer
consistently in SQL so it will be omitted. The other  will be mapped from the `state` attribute as follows:

.. code-block:: text

    Old state            | Process state  | Exit status | Process status
    ---------------------|----------------|-------------|----------------------------------------------------------
    `NEW`                | `Killed`       |    `None`   | Legacy `JobCalculation` with state `NEW`
    `TOSUBMIT`           | `Killed`       |    `None`   | Legacy `JobCalculation` with state `TOSUBMIT`
    `SUBMITTING`         | `Killed`       |    `None`   | Legacy `JobCalculation` with state `SUBMITTING`
    `WITHSCHEDULER`      | `Killed`       |    `None`   | Legacy `JobCalculation` with state `WITHSCHEDULER`
    `COMPUTED`           | `Killed`       |    `None`   | Legacy `JobCalculation` with state `COMPUTED`
    `RETRIEVING`         | `Killed`       |    `None`   | Legacy `JobCalculation` with state `RETRIEVING`
    `PARSING`            | `Killed`       |    `None`   | Legacy `JobCalculation` with state `PARSING`
    `SUBMISSIONFAILED`   | `Excepted`     |    `None`   | Legacy `JobCalculation` with state `SUBMISSIONFAILED`
    `RETRIEVALFAILED`    | `Excepted`     |    `None`   | Legacy `JobCalculation` with state `RETRIEVALFAILED`
    `PARSINGFAILED`      | `Excepted`     |    `None`   | Legacy `JobCalculation` with state `PARSINGFAILED`
    `FAILED`             | `Finished`     |      2      |  -
    `FINISHED`           | `Finished`     |      0      |  -
    `IMPORTED`           |       -        |      -      |  -


Note the `IMPORTED` state was never actually stored in the `state` attribute, so we do not have to consider it.
The old `state` attribute has to be removed after the data is migrated, because its value is no longer valid or useful.

Note: in addition to the three attributes mentioned in the table, all matched nodes will get `Legacy JobCalculation` as
their `process_label` which is one of the default columns of `verdi process list`.

This migration is identical to django_0038

Revision ID: 26d561acd560
Revises: 07fac78e6209
Create Date: 2019-06-22 09:55:25.284168

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module,line-too-long

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '26d561acd560'
down_revision = '07fac78e6209'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()  # pylint: disable=no-member

    # Note that the condition on matching target nodes is done only on the `node_type` amd the `state` attribute value.
    # New `CalcJobs` will have the same node type and while their active can have a `state` attribute with a value
    # of the enum `CalcJobState`, some of which match the deprecated `JobCalcState`, however, the new ones are stored
    # in lower case, so we do not run the risk of matching them by accident.
    statement = text(
        """
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `NEW`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "NEW"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `TOSUBMIT`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "TOSUBMIT"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `SUBMITTING`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "SUBMITTING"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `WITHSCHEDULER`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "WITHSCHEDULER"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `COMPUTED`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "COMPUTED"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `RETRIEVING`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "RETRIEVING"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "killed", "process_status": "Legacy `JobCalculation` with state `PARSING`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "PARSING"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "excepted", "process_status": "Legacy `JobCalculation` with state `SUBMISSIONFAILED`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "SUBMISSIONFAILED"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "excepted", "process_status": "Legacy `JobCalculation` with state `RETRIEVALFAILED`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "RETRIEVALFAILED"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "excepted", "process_status": "Legacy `JobCalculation` with state `PARSINGFAILED`", "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "PARSINGFAILED"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "finished", "exit_status": 2, "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "FAILED"}';
        UPDATE db_dbnode
        SET attributes = attributes - 'state' || '{"process_state": "finished", "exit_status": 0, "process_label": "Legacy JobCalculation"}'
        WHERE node_type = 'process.calculation.calcjob.CalcJobNode.' AND attributes @> '{"state": "FINISHED"}';
    """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 26d561acd560.')
