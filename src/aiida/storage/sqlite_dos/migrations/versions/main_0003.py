###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Prepare the storage schema for main_0003.

Migration steps:

1. :func:`add_settings_table`: backfill the settings table.
2. :func:`~aiida.storage.migrations.legacy_ssh.migrate_ssh_transports`: migrate SSH computers to the
   asynchronous ``core.ssh`` transport plugin.

See the ``main_0003`` revision of the ``psql_dos`` backend for the rationale of the transport
rename, which likewise has no inverse: the downgrade only restores the schema revision.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.sqlite import JSON

from aiida.storage.migrations.legacy_ssh import migrate_ssh_transports

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def add_settings_table() -> None:
    """Backfill the settings table if absent.

    The initial SQLite migration was based on the archive schema, which does not contain the settings table.
    The ``sqlite_dos`` backend, however, requires it for the repository UUID. Fresh profiles created before
    this migration therefore miss the table, while other databases already have it.
    """
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


def upgrade():
    """Migrations for the upgrade."""
    add_settings_table()
    migrate_ssh_transports(op.get_bind())


def downgrade():
    """Migrations for the downgrade."""
    pass
