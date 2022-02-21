# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
"""Remove legacy workflows

This is similar to migration django_0032

Revision ID: 1b8ed3425af9
Revises: 3d6190594e19
Create Date: 2019-04-03 17:11:44.073582

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils.legacy_workflows import export_workflow_data

# revision identifiers, used by Alembic.
revision = '1b8ed3425af9'
down_revision = '3d6190594e19'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # Clean data
    export_workflow_data(op.get_bind(), op.get_context().opts['aiida_profile'])

    op.drop_table('db_dbworkflowstep_sub_workflows')
    op.drop_table('db_dbworkflowstep_calculations')
    op.drop_table('db_dbworkflowstep')
    op.drop_index('ix_db_dbworkflowdata_aiida_obj_id', table_name='db_dbworkflowdata')
    op.drop_index('ix_db_dbworkflowdata_parent_id', table_name='db_dbworkflowdata')
    op.drop_table('db_dbworkflowdata')
    op.drop_index('ix_db_dbworkflow_label', table_name='db_dbworkflow')
    op.drop_table('db_dbworkflow')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Removal of legacy workflows is not reversible.')
