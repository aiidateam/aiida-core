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
"""Add `db_dblink.type` field, and remove link field uniqueness constraints

Revision ID: django_0003
Revises: django_0002

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0003'
down_revision = 'django_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.add_column('db_dblink', sa.Column('type', sa.VARCHAR(length=255), nullable=False, server_default=''))
    op.alter_column('db_dblink', 'type', server_default=None)
    op.create_index('db_dblink_type_229f212b', 'db_dblink', ['type'])
    op.create_index(
        'db_dblink_type_229f212b_like',
        'db_dblink',
        ['type'],
        postgresql_using='btree',
        postgresql_ops={'type': 'varchar_pattern_ops'},
    )
    op.drop_constraint('db_dblink_input_id_output_id_fbe99cb5_uniq', 'db_dblink', type_='unique')
    op.drop_constraint('db_dblink_output_id_label_00bdb9c7_uniq', 'db_dblink', type_='unique')


def downgrade():
    """Migrations for the downgrade."""
    op.drop_index('db_dblink_type_229f212b_like', table_name='db_dblink')
    op.drop_index('db_dblink_type_229f212b', table_name='db_dblink')
    op.drop_column('db_dblink', 'type')
    op.create_unique_constraint('db_dblink_input_id_output_id_fbe99cb5_uniq', 'db_dblink', ['input_id', 'output_id'])
    op.create_unique_constraint('db_dblink_output_id_label_00bdb9c7_uniq', 'db_dblink', ['output_id', 'label'])
