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
"""Remove legacy workflows

This is similar to migration 1b8ed3425af9

Revision ID: django_0032
Revises: django_0031

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils.legacy_workflows import export_workflow_data

revision = 'django_0032'
down_revision = 'django_0031'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # Clean data
    export_workflow_data(op.get_bind(), op.get_context().opts['aiida_profile'])

    # drop tables (indexes are also automatically dropped)
    op.drop_table('db_dbworkflowstep_sub_workflows')
    op.drop_table('db_dbworkflowstep_calculations')
    op.drop_table('db_dbworkflowstep')
    op.drop_table('db_dbworkflowdata')
    op.drop_table('db_dbworkflow')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0032.')
