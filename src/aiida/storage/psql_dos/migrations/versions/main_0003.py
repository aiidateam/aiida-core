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
    conn = op.get_bind()
    migrate_ssh_transports(conn)
    _migrate_legacy_codes(conn)
    _migrate_code_hidden_extra(conn)


def downgrade():
    """Migrations for the downgrade."""
