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
"""Drop `db_dbcalcstate` table

Revision ID: django_0017
Revises: django_0016

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'django_0017'
down_revision = 'django_0016'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_table('db_dbcalcstate')


def downgrade():
    """Migrations for the downgrade."""
    op.create_table(
        'db_dbcalcstate',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcalcstate_pkey'),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.Column('state', sa.VARCHAR(length=25), nullable=False),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('dbnode_id', 'state', name='db_dbcalcstate_dbnode_id_state_b4a14db3_uniq'),
        sa.Index('db_dbcalcstate_dbnode_id_f217a84c', 'dbnode_id'),
        sa.Index('db_dbcalcstate_state_0bf54584', 'state'),
        sa.Index(
            'db_dbcalcstate_state_0bf54584_like',
            'state',
            postgresql_using='btree',
            postgresql_ops={'state': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbcalcstate_dbnode_id_f217a84c_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
    )
