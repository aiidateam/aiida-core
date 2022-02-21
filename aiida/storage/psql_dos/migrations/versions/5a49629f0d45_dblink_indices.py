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
"""Adding indices on the `input_id`, `output_id` and `type` column of the `DbLink` table

Revision ID: 5a49629f0d45
Revises: 5ddd24e52864
Create Date: 2019-03-04 16:38:42.249231

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
from alembic import op

# revision identifiers, used by Alembic.
revision = '5a49629f0d45'
down_revision = '5ddd24e52864'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.create_index(op.f('ix_db_dblink_input_id'), 'db_dblink', ['input_id'], unique=False)
    op.create_index(op.f('ix_db_dblink_output_id'), 'db_dblink', ['output_id'], unique=False)
    op.create_index(op.f('ix_db_dblink_type'), 'db_dblink', ['type'], unique=False)


def downgrade():
    """Migrations for the downgrade."""
    op.drop_index(op.f('ix_db_dblink_type'), table_name='db_dblink')
    op.drop_index(op.f('ix_db_dblink_output_id'), table_name='db_dblink')
    op.drop_index(op.f('ix_db_dblink_input_id'), table_name='db_dblink')
