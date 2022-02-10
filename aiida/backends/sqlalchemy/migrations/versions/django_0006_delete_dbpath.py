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
"""Drop `db_dbpath` table

Revision ID: django_0006
Revises: django_0005

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0006'
down_revision = 'django_0005'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_table('db_dbpath')

    # Note this was also an undocumented part of the migration
    op.execute(
        """
            DROP TRIGGER IF EXISTS autoupdate_tc ON db_dblink;
            DROP FUNCTION IF EXISTS update_tc();
        """
    )


def downgrade():
    """Migrations for the downgrade."""
    op.create_table(
        'db_dbpath',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbpath_pkey'),
        sa.Column('parent_id', sa.INTEGER(), nullable=False),
        sa.Column('child_id', sa.INTEGER(), nullable=False),
        sa.Column('depth', sa.INTEGER(), nullable=False),
        sa.Column('entry_edge_id', sa.INTEGER(), nullable=True),
        sa.Column('direct_edge_id', sa.INTEGER(), nullable=True),
        sa.Column('exit_edge_id', sa.INTEGER(), nullable=True),
        sa.Index('db_dbpath_child_id_d8228636', 'child_id'),
        sa.Index('db_dbpath_parent_id_3b82d6c8', 'parent_id'),
        sa.ForeignKeyConstraint(
            ['child_id'],
            ['db_dbnode.id'],
            name='db_dbpath_child_id_d8228636_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbnode.id'],
            name='db_dbpath_parent_id_3b82d6c8_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )
