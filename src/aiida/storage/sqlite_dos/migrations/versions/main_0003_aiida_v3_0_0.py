###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Add the settings table.

The initial SQLite migration was based on the archive schema, which does not
contain the settings table. The ``sqlite_dos`` backend, however, requires it
for the repository UUID.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.sqlite import JSON

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    if sa.inspect(op.get_bind()).has_table('db_dbsetting'):
        return

    op.create_table(
        'db_dbsetting',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=1024), nullable=False),
        sa.Column('val', JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbsetting_pkey'),
        sa.UniqueConstraint('key', name='uq_db_dbsetting_key'),
    )


def downgrade():
    """Migrations for the downgrade."""
    pass
