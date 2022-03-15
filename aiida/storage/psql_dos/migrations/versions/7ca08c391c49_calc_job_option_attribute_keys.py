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
"""Migration of ProcessNode attributes for metadata options whose key changed.

Revision ID: 7ca08c391c49
Revises: e72ad251bcdb
Create Date: 2019-01-15 15:03:43.876133

"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '7ca08c391c49'
down_revision = 'e72ad251bcdb'
branch_labels = None
depends_on = None


def upgrade():
    """Migration of ProcessNode attributes for metadata options whose key changed.

    Renamed attribute keys:

      * `custom_environment_variables` -> `environment_variables` (CalcJobNode)
      * `jobresource_params` -> `resources` (CalcJobNode)
      * `_process_label` -> `process_label` (ProcessNode)
      * `parser` -> `parser_name` (CalcJobNode)

    Deleted attributes:
      * `linkname_retrieved` (We do not actually delete it just in case some relies on it)

    """
    conn = op.get_bind()

    statement = text(
        """
        UPDATE db_dbnode
        SET attributes = jsonb_set(attributes, '{environment_variables}', attributes->'custom_environment_variables')
        WHERE
            attributes ? 'custom_environment_variables' AND
            type = 'node.process.calculation.calcjob.CalcJobNode.';
        UPDATE db_dbnode SET attributes = attributes - 'custom_environment_variables'
        WHERE
            attributes ? 'custom_environment_variables' AND
            type = 'node.process.calculation.calcjob.CalcJobNode.';
        -- custom_environment_variables -> environment_variables

        UPDATE db_dbnode
        SET attributes = jsonb_set(attributes, '{resources}', attributes->'jobresource_params')
        WHERE
            attributes ? 'jobresource_params' AND
            type = 'node.process.calculation.calcjob.CalcJobNode.';
        UPDATE db_dbnode SET attributes = attributes - 'jobresource_params'
        WHERE
            attributes ? 'jobresource_params' AND
            type = 'node.process.calculation.calcjob.CalcJobNode.';
        -- jobresource_params -> resources

        UPDATE db_dbnode
        SET attributes = jsonb_set(attributes, '{process_label}', attributes->'_process_label')
        WHERE
            attributes ? '_process_label' AND
            type like 'node.process.%';
        UPDATE db_dbnode SET attributes = attributes - '_process_label'
        WHERE
            attributes ? '_process_label' AND
            type like 'node.process.%';
        -- _process_label -> process_label

        UPDATE db_dbnode
        SET attributes = jsonb_set(attributes, '{parser_name}', attributes->'parser')
        WHERE
            attributes ? 'parser' AND
            type = 'node.process.calculation.calcjob.CalcJobNode.';
        UPDATE db_dbnode SET attributes = attributes - 'parser'
        WHERE
            attributes ? 'parser' AND
            type = 'node.process.calculation.calcjob.CalcJobNode.';
        -- parser -> parser_name
        """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of 7ca08c391c49.')
