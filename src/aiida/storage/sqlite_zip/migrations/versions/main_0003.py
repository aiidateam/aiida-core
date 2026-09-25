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

from alembic import op
from sqlalchemy.sql import text

from aiida.storage.migrations.legacy_code import (
    SQLITE_HIDDEN_UPGRADE_STATEMENT,
    SQLITE_UPGRADE_STATEMENTS,
    check_sqlite_executables,
    warn_sqlite_executable_fallback,
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
    warn_sqlite_executable_fallback(conn)
    for statement in SQLITE_UPGRADE_STATEMENTS:
        conn.execute(text(statement))
    conn.execute(text(SQLITE_HIDDEN_UPGRADE_STATEMENT))


def downgrade():
    """Migrations for the downgrade."""
    pass
