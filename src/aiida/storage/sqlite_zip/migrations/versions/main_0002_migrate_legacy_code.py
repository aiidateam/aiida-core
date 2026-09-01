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
an archive containing nodes with the ``data.core.code.Code.`` node type would import them as plain ``Data``, since the
entry point no longer exists.

See ``aiida.storage.psql_dos.migrations.versions.main_0003_migrate_legacy_code`` for the rationale; this is the
archive counterpart of that migration.

Revision ID: main_0002
Revises: main_0001
Create Date: 2026-08-26

"""

from alembic import op
from sqlalchemy import text

revision = 'main_0002'
down_revision = 'main_0001'
branch_labels = None
depends_on = None

LEGACY_NODE_TYPE = 'data.core.code.Code.'

# The node type is rewritten and one attribute key is renamed, so the stored hash no longer describes the node and is
# dropped. ``json_extract`` returns 1/0 for a JSON boolean, and ``json_remove`` ignores keys that are not present.
UPGRADE_STATEMENTS = (
    f"""
    UPDATE db_dbnode
    SET node_type = 'data.core.code.installed.InstalledCode.',
        attributes = json_set(
            json_remove(attributes, '$.is_local', '$.local_executable', '$.remote_exec_path'),
            '$.filepath_executable', COALESCE(json_extract(attributes, '$.remote_exec_path'), '')
        ),
        extras = json_remove(extras, '$._aiida_hash')
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE(json_extract(attributes, '$.is_local'), 0) = 0;
    """,
    f"""
    UPDATE db_dbnode
    SET node_type = 'data.core.code.portable.PortableCode.',
        attributes = json_set(
            json_remove(attributes, '$.is_local', '$.local_executable', '$.remote_exec_path'),
            '$.filepath_executable', COALESCE(json_extract(attributes, '$.local_executable'), '')
        ),
        extras = json_remove(extras, '$._aiida_hash')
    WHERE node_type = '{LEGACY_NODE_TYPE}'
      AND COALESCE(json_extract(attributes, '$.is_local'), 0) = 1;
    """,
)


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    for statement in UPGRADE_STATEMENTS:
        conn.execute(text(statement))


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of main_0002.')
