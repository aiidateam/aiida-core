###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Versioned operations for introducing owned-container storage."""

import sqlalchemy as sa
from alembic import op

OWNER_INDEX = 'ix_db_dbnode_db_dbnode_owner_id'
OWNER_FK = 'fk_db_dbnode_owner_id_db_dbnode'


def create_ownership_schema() -> None:
    """Create the ownership schema without changing existing nodes or links."""
    if op.get_bind().dialect.name == 'sqlite':
        # Adding an inline foreign key to a nullable column avoids rebuilding
        # db_dbnode while live provenance links still reference it.
        op.execute(
            sa.text(
                f'ALTER TABLE db_dbnode ADD COLUMN owner_id INTEGER CONSTRAINT {OWNER_FK} '
                'REFERENCES db_dbnode (id) DEFERRABLE INITIALLY DEFERRED'
            )
        )
    else:
        op.add_column('db_dbnode', sa.Column('owner_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            OWNER_FK, 'db_dbnode', 'db_dbnode', ['owner_id'], ['id'], deferrable=True, initially='DEFERRED'
        )
    op.create_index(op.f(OWNER_INDEX), 'db_dbnode', ['owner_id'])
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
    if op.get_bind().dialect.name == 'postgresql':
        op.create_index('ix_membership_child_hash', 'db_dbmembership', ['child_id'], postgresql_using='hash')
