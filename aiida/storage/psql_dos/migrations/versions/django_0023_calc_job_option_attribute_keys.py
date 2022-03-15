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
"""Rename `ProcessNode` attributes for metadata options whose key changed

Renamed attribute keys:

    * `custom_environment_variables` -> `environment_variables` (CalcJobNode)
    * `jobresource_params` -> `resources` (CalcJobNode)
    * `_process_label` -> `process_label` (ProcessNode)
    * `parser` -> `parser_name` (CalcJobNode)

Deleted attributes:
    * `linkname_retrieved` (We do not actually delete it just in case some relies on it)

Note this is similar to the sqlalchemy migration 7ca08c391c49

Revision ID: django_0023
Revises: django_0022

"""
from alembic import op

revision = 'django_0023'
down_revision = 'django_0022'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.execute(
        r"""
        UPDATE db_dbattribute AS attribute
        SET key =  regexp_replace(attribute.key, '^custom_environment_variables', 'environment_variables')
        FROM db_dbnode AS node
        WHERE
            (
                attribute.key = 'custom_environment_variables' OR
                attribute.key LIKE 'custom\_environment\_variables.%'
            ) AND
            node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
            node.id = attribute.dbnode_id;
        -- custom_environment_variables -> environment_variables

        UPDATE db_dbattribute AS attribute
        SET key =  regexp_replace(attribute.key, '^jobresource_params', 'resources')
        FROM db_dbnode AS node
        WHERE
            (
                attribute.key = 'jobresource_params' OR
                attribute.key LIKE 'jobresource\_params.%'
            ) AND
            node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
            node.id = attribute.dbnode_id;
        -- jobresource_params -> resources

        UPDATE db_dbattribute AS attribute
        SET key =  regexp_replace(attribute.key, '^_process_label', 'process_label')
        FROM db_dbnode AS node
        WHERE
            attribute.key = '_process_label' AND
            node.type LIKE 'node.process.%' AND
            node.id = attribute.dbnode_id;
        -- _process_label -> process_label

        UPDATE db_dbattribute AS attribute
        SET key =  regexp_replace(attribute.key, '^parser', 'parser_name')
        FROM db_dbnode AS node
        WHERE
            attribute.key = 'parser' AND
            node.type = 'node.process.calculation.calcjob.CalcJobNode.' AND
            node.id = attribute.dbnode_id;
        -- parser -> parser_name
        """
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0023.')
