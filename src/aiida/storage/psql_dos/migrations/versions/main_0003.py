###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Prepare the storage schema for main_0003.

Migration steps:

1. :func:`~aiida.storage.migrations.legacy_ssh.migrate_ssh_transports`: migrate SSH computers to the
   asynchronous ``core.ssh`` transport plugin.
2. :func:`_migrate_legacy_codes`: migrate the deprecated ``Code`` data plugin.
3. :func:`_migrate_code_hidden_extra`: rename the visibility extra on built-in Code nodes.
4. Owned data containers: add ``db_dbnode.owner_id`` (indexed, nullable self-FK, deferred),
   the ``db_dbcontainer`` table (``node_id`` PK/FK to ``db_dbnode``, ``element_type``, ``layout``)
   with the ``db_dblistcontainer``/``db_dbdictcontainer`` kind markers, and the ``db_dbmembership``
   table (``owner_id`` FK to ``db_dbcontainer``), per ``orm-container-spec.md`` sections 2-3 and
   ``orm-container-adr-01.md`` §3. Membership rows are containment edges, never
   provenance links. Existing nodes remain standalone: no owner, no container rows.

The legacy paramiko-based ``core.ssh`` transport plugin was removed in v3.0, and the asynchronous plugin (formerly
``core.ssh_async``) took over its entry point name. Consequently:

* computers configured with ``core.ssh_async`` have their ``transport_type`` rewritten to
  ``core.ssh``, and keep working unchanged;
* computers configured with the legacy ``core.ssh`` keep their ``transport_type`` as is, and are now
  served by the asynchronous plugin. That plugin has none of the connection parameters the legacy
  one stored in ``db_dbauthinfo.auth_params`` (username, port, key_filename, proxy_jump, ...), so
  they are written out as an OpenSSH client configuration entry and replaced by the alias of that
  entry. See :mod:`~aiida.storage.migrations.legacy_ssh`.

Note that neither step has an inverse: once both kinds of computers share the ``core.ssh`` transport
type they can no longer be told apart, and the parameters that were converted are gone from the
database. The downgrade therefore only restores the schema revision.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-09-07
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

from aiida.storage.log import MIGRATE_LOGGER
from aiida.storage.migrations.legacy_code import INSTALLED_NODE_TYPE, LEGACY_NODE_TYPE, PORTABLE_NODE_TYPE
from aiida.storage.migrations.legacy_ssh import migrate_ssh_transports

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


# The node type is rewritten and one attribute key is renamed, so the stored hash no longer describes the node. It is
# dropped rather than recomputed, which is what the other data migrations that touch attributes do as well.
UPGRADE_STATEMENTS = (
    f"""
    UPDATE db_dbnode
    SET node_type = '{INSTALLED_NODE_TYPE}',
        attributes = (attributes - 'is_local' - 'local_executable' - 'remote_exec_path')
            || jsonb_build_object('filepath_executable',
                COALESCE(NULLIF(attributes -> 'remote_exec_path', 'null'::jsonb), attributes -> 'filepath_executable')),
        extras = extras - '_aiida_hash'
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE((attributes ->> 'is_local')::boolean, false) IS FALSE;
    """,
    f"""
    UPDATE db_dbnode
    SET node_type = '{PORTABLE_NODE_TYPE}',
        attributes = (attributes - 'is_local' - 'local_executable' - 'remote_exec_path')
            || jsonb_build_object('filepath_executable',
                COALESCE(NULLIF(attributes -> 'local_executable', 'null'::jsonb), attributes -> 'filepath_executable')),
        extras = extras - '_aiida_hash'
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE((attributes ->> 'is_local')::boolean, false) IS TRUE;
    """,
)


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

    missing = conn.execute(
        text(
            f"SELECT count(*) FROM db_dbnode WHERE node_type = '{LEGACY_NODE_TYPE}' AND "
            "COALESCE(CASE WHEN COALESCE((attributes ->> 'is_local')::boolean, false) "
            "THEN attributes ->> 'local_executable' ELSE attributes ->> 'remote_exec_path' END, "
            "attributes ->> 'filepath_executable', '') = ''"
        )
    ).scalar()
    if missing:
        msg = f'Cannot migrate {missing} legacy Code node(s) without an executable path.'
        raise ValueError(msg)

    for statement in UPGRADE_STATEMENTS:
        conn.execute(text(statement))


def _migrate_code_hidden_extra(conn):
    """Rename the visibility extra on all built-in code types."""
    conn.execute(
        text(
            "UPDATE db_dbnode SET extras = (extras - 'hidden') || jsonb_build_object('is_hidden', extras -> 'hidden') "
            "WHERE node_type LIKE 'data.core.code.%' AND extras ? 'hidden'"
        )
    )


def upgrade():
    """Migrations for the upgrade."""
    # NOTE: DDL first, then data migrations. PostgreSQL forbids ``ALTER TABLE`` after ``UPDATE``s on the
    # same table in one transaction (``cannot ALTER TABLE ... because it has pending trigger events``),
    # see ``django_0024a_dblog_update``. The new foreign keys are deferred, so the subsequent ``UPDATE``s
    # are safe once the schema changes are in place.
    op.add_column('db_dbnode', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_index('ix_db_dbnode_db_dbnode_owner_id', 'db_dbnode', ['owner_id'], unique=False)
    op.create_foreign_key(
        'fk_db_dbnode_owner_id_db_dbnode',
        'db_dbnode',
        'db_dbnode',
        ['owner_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    op.create_table(
        'db_dbcontainer',
        sa.Column('node_id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('element_type', sa.String(length=255), nullable=True, index=True),
        sa.Column('layout', sa.String(length=32), nullable=False, server_default='row', index=True),
        sa.ForeignKeyConstraint(['node_id'], ['db_dbnode.id'], deferrable=True, initially='DEFERRED'),
    )
    op.create_table(
        'db_dblistcontainer',
        sa.Column('node_id', sa.Integer(), nullable=False, primary_key=True),
        sa.ForeignKeyConstraint(['node_id'], ['db_dbcontainer.node_id'], deferrable=True, initially='DEFERRED'),
    )
    op.create_table(
        'db_dbdictcontainer',
        sa.Column('node_id', sa.Integer(), nullable=False, primary_key=True),
        sa.ForeignKeyConstraint(['node_id'], ['db_dbcontainer.node_id'], deferrable=True, initially='DEFERRED'),
    )
    op.create_table(
        'db_dbmembership',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('owner_id', sa.Integer(), nullable=False, index=True),
        sa.Column('child_id', sa.Integer(), nullable=False, index=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=True, index=True),
        sa.ForeignKeyConstraint(['owner_id'], ['db_dbcontainer.node_id'], deferrable=True, initially='DEFERRED'),
        sa.ForeignKeyConstraint(['child_id'], ['db_dbnode.id'], deferrable=True, initially='DEFERRED'),
        sa.UniqueConstraint('child_id', name='uq_db_dbmembership_child_id'),
        sa.UniqueConstraint('owner_id', 'position', name='uq_db_dbmembership_owner_id_position'),
        sa.UniqueConstraint('owner_id', 'key', name='uq_db_dbmembership_owner_id_key'),
        sa.CheckConstraint('position >= 0', name='ck_db_dbmembership_position_nonnegative'),
        sa.CheckConstraint('owner_id != child_id', name='ck_db_dbmembership_no_self_ownership'),
    )
    conn = op.get_bind()
    migrate_ssh_transports(conn)
    _migrate_legacy_codes(conn)
    _migrate_code_hidden_extra(conn)


def downgrade():
    """Migrations for the downgrade."""
    op.drop_table('db_dbmembership')
    op.drop_table('db_dbdictcontainer')
    op.drop_table('db_dblistcontainer')
    op.drop_table('db_dbcontainer')
    op.drop_constraint('fk_db_dbnode_owner_id_db_dbnode', 'db_dbnode', type_='foreignkey')
    op.drop_index('ix_db_dbnode_db_dbnode_owner_id', table_name='db_dbnode')
    op.drop_column('db_dbnode', 'owner_id')
