# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,too-few-public-methods
"""Data migration for legacy `JobCalculations`.

These old nodes have already been migrated to the correct `CalcJobNode` type in a previous migration, but they can
still contain a `state` attribute with a deprecated `JobCalcState` value and they are missing a value for the
`process_state`, `process_status`, `process_label` and `exit_status`. The `process_label` is impossible to infer
consistently in SQL so it will be omitted. The other  will be mapped from the `state` attribute as follows:

.. code-block:: text

    Old state            | Process state  | Exit status | Process status
    ---------------------|----------------|-------------|----------------------------------------------------------
    `NEW`                | `killed`       |    `None`   | Legacy `JobCalculation` with state `NEW`
    `TOSUBMIT`           | `killed`       |    `None`   | Legacy `JobCalculation` with state `TOSUBMIT`
    `SUBMITTING`         | `killed`       |    `None`   | Legacy `JobCalculation` with state `SUBMITTING`
    `WITHSCHEDULER`      | `killed`       |    `None`   | Legacy `JobCalculation` with state `WITHSCHEDULER`
    `COMPUTED`           | `killed`       |    `None`   | Legacy `JobCalculation` with state `COMPUTED`
    `RETRIEVING`         | `killed`       |    `None`   | Legacy `JobCalculation` with state `RETRIEVING`
    `PARSING`            | `killed`       |    `None`   | Legacy `JobCalculation` with state `PARSING`
    `SUBMISSIONFAILED`   | `excepted`     |    `None`   | Legacy `JobCalculation` with state `SUBMISSIONFAILED`
    `RETRIEVALFAILED`    | `excepted`     |    `None`   | Legacy `JobCalculation` with state `RETRIEVALFAILED`
    `PARSINGFAILED`      | `excepted`     |    `None`   | Legacy `JobCalculation` with state `PARSINGFAILED`
    `FAILED`             | `finished`     |      2      |  -
    `FINISHED`           | `finished`     |      0      |  -
    `IMPORTED`           |       -        |      -      |  -

Note the `IMPORTED` state was never actually stored in the `state` attribute, so we do not have to consider it.
The old `state` attribute has to be removed after the data is migrated, because its value is no longer valid or useful.

Note: in addition to the three attributes mentioned in the table, all matched nodes will get `Legacy JobCalculation` as
their `process_label` which is one of the default columns of `verdi process list`.
"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from django.db import migrations
from aiida.backends.djsite.db.migrations import upgrade_schema_version

REVISION = '1.0.38'
DOWN_REVISION = '1.0.37'


class Migration(migrations.Migration):
    """Data migration for legacy `JobCalculations`."""

    dependencies = [
        ('db', '0037_attributes_extras_settings_json'),
    ]

    # Note that the condition on matching target nodes is done only on the `node_type` amd the `state` attribute value.
    # New `CalcJobs` will have the same node type and while their active can have a `state` attribute with a value
    # of the enum `CalcJobState`, some of which match the deprecated `JobCalcState`, however, the new ones are stored
    # in lower case, so we do not run the risk of matching them by accident.
    operations = [
        migrations.RunSQL(
            sql=r"""
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
                """,
            reverse_sql=''
        ),
        upgrade_schema_version(REVISION, DOWN_REVISION)
    ]
