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
"""Drop `db_dblock` table

Revision ID: django_0012
Revises: django_0011

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'django_0012'
down_revision = 'django_0011'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_table('db_dblock')


def downgrade():
    """Migrations for the downgrade."""
    op.create_table(
        'db_dblock',
        sa.Column('key', sa.VARCHAR(length=255), nullable=False),
        sa.PrimaryKeyConstraint('key', name='db_dblock_pkey'),
        sa.Column('creation', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('timeout', sa.INTEGER(), nullable=False),
        sa.Column('owner', sa.VARCHAR(length=255), nullable=False),
        sa.Index(
            'db_dblock_key_048c6767_like',
            'key',
            postgresql_using='btree',
            postgresql_ops={'key': 'varchar_pattern_ops'},
        ),
    )
