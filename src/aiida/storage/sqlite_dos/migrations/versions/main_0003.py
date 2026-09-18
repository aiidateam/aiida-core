###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Add the settings table and rename the ``core.ssh_async`` transport plugin to ``core.ssh``.

The initial SQLite migration was based on the archive schema, which does not
contain the settings table. The ``sqlite_dos`` backend, however, requires it
for the repository UUID.

See the ``main_0003`` revision of the ``psql_dos`` backend for the rationale of the transport
rename, which likewise has no inverse: the downgrade only restores the schema revision.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import text

from aiida.storage.log import MIGRATE_LOGGER
from aiida.storage.psql_dos.migrations.utils.legacy_ssh_computers import migrate_legacy_ssh_computers

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def add_settings_table() -> None:
    """Create the settings table, unless the database was initialised with it already."""
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


def rename_ssh_async_transport() -> None:
    """Rewrite the ``transport_type`` of all ``core.ssh_async`` computers."""
    result = op.get_bind().execute(
        text("UPDATE db_dbcomputer SET transport_type = 'core.ssh' WHERE transport_type = 'core.ssh_async'")
    )

    if result.rowcount > 0:
        MIGRATE_LOGGER.report(
            f'Renamed the transport of {result.rowcount} computer(s) from `core.ssh_async` to `core.ssh`.'
        )


def upgrade():
    """Migrations for the upgrade."""
    add_settings_table()
    # Before the rename, which is what still tells the two kinds of computer apart.
    migrate_legacy_ssh_computers(op.get_bind())
    rename_ssh_async_transport()


def downgrade():
    """Migrations for the downgrade."""
    pass
