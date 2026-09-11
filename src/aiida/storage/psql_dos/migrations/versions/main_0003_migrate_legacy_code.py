###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migrate the deprecated ``Code`` data plugin to ``InstalledCode`` and ``PortableCode``.

The ``Code`` plugin was deprecated in ``aiida-core==2.0`` and removed in ``aiida-core==3.0``. Without this migration,
stored nodes with the ``data.core.code.Code.`` node type would no longer resolve to a code class at all: the entry
point is gone, so they would silently load as plain ``Data`` and lose the entire code API.

A stored legacy code carries everything needed to become a modern one. The ``is_local`` attribute distinguishes the
two cases:

* ``is_local=False``: a code installed on a remote computer, i.e. an ``InstalledCode``. The executable is recorded
  under ``remote_exec_path`` and the computer is already set on the node.
* ``is_local=True``: a code whose files live in the node repository, i.e. a ``PortableCode``. The executable is
  recorded under ``local_executable`` and the repository contents are left untouched.

Both replacements record the executable under ``filepath_executable``, so the rewrite is a node type change plus a
rename of one attribute key. All other attributes (``input_plugin``, ``prepend_text``, ``append_text``, ...) use the
same keys on ``AbstractCode`` and are left as they are.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-08-26

"""

from alembic import op
from sqlalchemy import text

from aiida.storage.log import MIGRATE_LOGGER

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None

LEGACY_NODE_TYPE = 'data.core.code.Code.'

# The node type is rewritten and one attribute key is renamed, so the stored hash no longer describes the node. It is
# dropped rather than recomputed, which is what the other data migrations that touch attributes do as well.
UPGRADE_STATEMENTS = f"""
    UPDATE db_dbnode
    SET node_type = 'data.core.code.installed.InstalledCode.',
        attributes = (attributes - 'is_local' - 'local_executable' - 'remote_exec_path')
            || jsonb_build_object('filepath_executable', COALESCE(attributes -> 'remote_exec_path', '""'::jsonb)),
        extras = extras - '_aiida_hash'
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE((attributes ->> 'is_local')::boolean, false) IS FALSE;

    UPDATE db_dbnode
    SET node_type = 'data.core.code.portable.PortableCode.',
        attributes = (attributes - 'is_local' - 'local_executable' - 'remote_exec_path')
            || jsonb_build_object('filepath_executable', COALESCE(attributes -> 'local_executable', '""'::jsonb)),
        extras = extras - '_aiida_hash'
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE((attributes ->> 'is_local')::boolean, false) IS TRUE;
"""


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    count = conn.execute(text(f"SELECT count(*) FROM db_dbnode WHERE node_type = '{LEGACY_NODE_TYPE}';")).scalar()

    if count:
        MIGRATE_LOGGER.report(
            f'Migrating {count} legacy `Code` node(s) to `InstalledCode`/`PortableCode`. Their hashes are invalidated; '
            'run `verdi node rehash` to recompute them.'
        )

    conn.execute(text(UPGRADE_STATEMENTS))


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of main_0003.')
