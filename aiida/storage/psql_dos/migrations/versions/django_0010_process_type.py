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
"""Add `db_dbnode.process_type`

Revision ID: django_0010
Revises: django_0009

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0010'
down_revision = 'django_0009'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.add_column('db_dbnode', sa.Column('process_type', sa.String(length=255), nullable=True))
    op.create_index('db_dbnode_process_type_df7298d0', 'db_dbnode', ['process_type'])
    op.create_index(
        'db_dbnode_process_type_df7298d0_like',
        'db_dbnode',
        ['process_type'],
        postgresql_using='btree',
        postgresql_ops={'process_type': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0010.')
