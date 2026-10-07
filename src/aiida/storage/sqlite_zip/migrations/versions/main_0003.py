###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Prepare the storage schema for main_0003.

Migration steps:

1. Rename the ``core.ssh_async`` transport plugin to ``core.ssh``.
2. Migrate the deprecated ``Code`` data plugin to modern code plugins.
3. Rename the visibility extra on built-in Code nodes.
4. Owned data containers: add ``db_dbnode.owner_id``, ``db_dbnode.container_element_type``, and the
   ``db_dbmembership`` table, per ``orm-container-spec.md`` sections 2-3, so archives stay in line
   with the profile databases. Membership rows are containment edges, never provenance links.
   Existing archived nodes remain standalone: no owner, unset element type.

Bring archives in line with the profile database ``main_0003``, so that a computer exported from a
profile that used ``core.ssh_async`` can be imported into a v3 profile. Archives carry no client
configuration of their own, so unlike the profile databases, only the rename is needed here and not
the legacy ``core.ssh`` conversion. See ``aiida.storage.psql_dos.migrations.versions.main_0003``
for the rationale.

The rename has no inverse: once both kinds of computers share the ``core.ssh`` transport type, they
can no longer be told apart. The downgrade therefore only restores the schema revision and leaves
the transport types as they are.

Without the code migration, an archive containing nodes with the ``data.core.code.Code.`` node type
would import them as plain ``Data``, since the entry point no longer exists. See
``aiida.storage.psql_dos.migrations.versions.main_0003`` for the rationale.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

from aiida.storage.migrations.legacy_code import (
    SQLITE_HIDDEN_UPGRADE_STATEMENT,
    SQLITE_UPGRADE_STATEMENTS,
    check_sqlite_executables,
)

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()
    conn.execute(text("UPDATE db_dbcomputer SET transport_type = 'core.ssh' WHERE transport_type = 'core.ssh_async'"))

    check_sqlite_executables(conn)
    for statement in SQLITE_UPGRADE_STATEMENTS:
        conn.execute(text(statement))
    conn.execute(text(SQLITE_HIDDEN_UPGRADE_STATEMENT))
    # SQLite does not support ALTER TABLE ... ADD CONSTRAINT, so the existing table is migrated in batch
    # (copy-and-move) mode, which recreates it with the new columns, indexes, and foreign key.
    with op.batch_alter_table('db_dbnode') as batch_op:
        batch_op.add_column(sa.Column('owner_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('container_element_type', sa.String(length=255), nullable=True))
        batch_op.create_index('ix_db_dbnode_db_dbnode_owner_id', ['owner_id'])
        batch_op.create_index('ix_db_dbnode_db_dbnode_container_element_type', ['container_element_type'])
        batch_op.create_foreign_key(
            'fk_db_dbnode_owner_id_db_dbnode',
            'db_dbnode',
            ['owner_id'],
            ['id'],
            deferrable=True,
            initially='DEFERRED',
        )
    op.create_table(
        'db_dbmembership',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('owner_id', sa.Integer(), nullable=False, index=True),
        sa.Column('child_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=True, index=True),
        sa.ForeignKeyConstraint(['owner_id'], ['db_dbnode.id'], deferrable=True, initially='DEFERRED'),
        sa.ForeignKeyConstraint(['child_id'], ['db_dbnode.id'], deferrable=True, initially='DEFERRED'),
        sa.UniqueConstraint('child_id', name='uq_db_dbmembership_child_id'),
        sa.UniqueConstraint('owner_id', 'position', name='uq_db_dbmembership_owner_id_position'),
        sa.UniqueConstraint('owner_id', 'key', name='uq_db_dbmembership_owner_id_key'),
        sa.CheckConstraint('position >= 0', name='ck_db_dbmembership_position_nonnegative'),
        sa.CheckConstraint('owner_id != child_id', name='ck_db_dbmembership_no_self_ownership'),
    )


def downgrade():
    """Migrations for the downgrade."""
    op.drop_table('db_dbmembership')
    with op.batch_alter_table('db_dbnode') as batch_op:
        batch_op.drop_constraint('fk_db_dbnode_owner_id_db_dbnode', type_='foreignkey')
        batch_op.drop_index('ix_db_dbnode_db_dbnode_container_element_type')
        batch_op.drop_index('ix_db_dbnode_db_dbnode_owner_id')
        batch_op.drop_column('container_element_type')
        batch_op.drop_column('owner_id')
