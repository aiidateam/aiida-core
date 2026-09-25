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
3. :func:`_migrate_legacy_codes`: migrate the deprecated ``Code`` data plugin.
4. Rename the visibility extra on built-in Code nodes.

See the ``main_0003`` revision of the ``psql_dos`` backend for the rationale of the transport
rename, which likewise has no inverse: the downgrade only restores the schema revision.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text
from sqlalchemy.dialects.sqlite import JSON

from aiida.storage.log import MIGRATE_LOGGER
from aiida.storage.migrations.legacy_code import (
    LEGACY_NODE_TYPE,
    SQLITE_HIDDEN_UPGRADE_STATEMENT,
    SQLITE_UPGRADE_STATEMENTS,
    check_sqlite_executables,
    warn_sqlite_executable_fallback,
)
from aiida.storage.migrations.legacy_ssh import migrate_ssh_transports

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def _migrate_legacy_codes(conn):
    """Migrate the deprecated ``Code`` data plugin to ``InstalledCode``/``PortableCode``.

    The ``Code`` plugin was deprecated in ``aiida-core==2.0`` and removed in ``aiida-core==3.0``. Without this
    migration, stored nodes with the ``data.core.code.Code.`` node type would no longer resolve to a code class
    at all: the entry point is gone, so they would silently load as plain ``Data`` and lose the entire code API.

    A stored legacy code carries everything needed to become a modern one. The ``is_local`` attribute
    distinguishes the two cases:

    * ``is_local=False``: a code installed on a remote computer, i.e. an ``InstalledCode``. The executable is
      recorded under ``remote_exec_path`` (or already under ``filepath_executable``), and the computer is set.
    * ``is_local=True``: a code whose files live in the node repository, i.e. a ``PortableCode``. The
      executable is under ``local_executable`` (or already ``filepath_executable``); the repository is unchanged.

    Both replacements record the executable under ``filepath_executable``, so the rewrite changes the node type
    and, where necessary, renames the executable key. All other attributes (``input_plugin``, ``prepend_text``,
    ``append_text``, ...) use the same keys on ``Code`` and are left as they are.
    """
    count = conn.execute(text(f"SELECT count(*) FROM db_dbnode WHERE node_type = '{LEGACY_NODE_TYPE}';")).scalar()

    if count:
        MIGRATE_LOGGER.report(
            f'Migrating {count} legacy `Code` node(s) to `InstalledCode`/`PortableCode`. Their hashes are '
            'invalidated; run `verdi node rehash` to recompute them.'
        )

    check_sqlite_executables(conn)
    warn_sqlite_executable_fallback(conn)
    for statement in SQLITE_UPGRADE_STATEMENTS:
        conn.execute(text(statement))


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
    conn = op.get_bind()
    migrate_ssh_transports(conn)
    _migrate_legacy_codes(conn)
    conn.execute(text(SQLITE_HIDDEN_UPGRADE_STATEMENT))


def downgrade():
    """Migrations for the downgrade."""
    pass
