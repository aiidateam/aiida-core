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
    needs_lineage_uuid = not _has_column('lineage_uuid')
    needs_version = not _has_column('version')
    needs_unique = not _has_unique_constraint(_UNIQUE)

    if needs_lineage_uuid or needs_version or needs_unique:
        with op.batch_alter_table(_TABLE) as batch_op:
            if needs_lineage_uuid:
                batch_op.add_column(sa.Column('lineage_uuid', sa.String(length=32), nullable=True))
            if needs_version:
                batch_op.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
            if needs_unique:
                batch_op.create_unique_constraint(_UNIQUE, ['lineage_uuid', 'version'])

    if not _has_index(_INDEX):
        op.create_index(_INDEX, _TABLE, ['lineage_uuid'], unique=False)


def downgrade():
    """Migrations for the downgrade."""
    needs_drop_unique = _has_unique_constraint(_UNIQUE)
    needs_drop_version = _has_column('version')
    needs_drop_lineage_uuid = _has_column('lineage_uuid')

    if _has_index(_INDEX):
        op.drop_index(_INDEX, table_name=_TABLE)

    if needs_drop_unique or needs_drop_version or needs_drop_lineage_uuid:
        with op.batch_alter_table(_TABLE) as batch_op:
            if needs_drop_unique:
                batch_op.drop_constraint(_UNIQUE, type_='unique')
            if needs_drop_version:
                batch_op.drop_column('version')
            if needs_drop_lineage_uuid:
                batch_op.drop_column('lineage_uuid')
