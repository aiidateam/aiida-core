###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Add node version lineage columns.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-08-02

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None

_TABLE = 'db_dbnode'
_INDEX = 'ix_db_dbnode_db_dbnode_lineage_uuid'
_UNIQUE = 'uq_dbnode_lineage_version'


def _has_column(column_name: str) -> bool:
    """Return whether the node table already has the given column."""
    inspector = sa.inspect(op.get_bind())
    return column_name in {column['name'] for column in inspector.get_columns(_TABLE)}


def _has_index(index_name: str) -> bool:
    """Return whether the node table already has the given index."""
    inspector = sa.inspect(op.get_bind())
    return index_name in {index['name'] for index in inspector.get_indexes(_TABLE)}


def _has_unique_constraint(constraint_name: str) -> bool:
    """Return whether the node table already has the given unique constraint."""
    inspector = sa.inspect(op.get_bind())
    return constraint_name in {constraint['name'] for constraint in inspector.get_unique_constraints(_TABLE)}


def upgrade():
    """Migrations for the upgrade."""
    if not _has_column('lineage_uuid'):
        op.add_column(_TABLE, sa.Column('lineage_uuid', postgresql.UUID(as_uuid=True), nullable=True))
    if not _has_column('version'):
        op.add_column(_TABLE, sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    if not _has_index(_INDEX):
        op.create_index(_INDEX, _TABLE, ['lineage_uuid'], unique=False)
    if not _has_unique_constraint(_UNIQUE):
        op.create_unique_constraint(_UNIQUE, _TABLE, ['lineage_uuid', 'version'])


def downgrade():
    """Migrations for the downgrade."""
    if _has_unique_constraint(_UNIQUE):
        op.drop_constraint(_UNIQUE, _TABLE, type_='unique')
    if _has_index(_INDEX):
        op.drop_index(_INDEX, table_name=_TABLE)
    if _has_column('version'):
        op.drop_column(_TABLE, 'version')
    if _has_column('lineage_uuid'):
        op.drop_column(_TABLE, 'lineage_uuid')
