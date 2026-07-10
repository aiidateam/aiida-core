###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Rename the ``core.ssh_async`` transport plugin to ``core.ssh``.

See the ``main_0003`` revision of the ``psql_dos`` backend for the full rationale.

Note that this migration is irreversible: once both kinds of computers share the ``core.ssh``
transport type, they can no longer be told apart.

Revision ID: main_0003
Revises: main_0002
Create Date: 2026-07-09

"""

from alembic import op
from sqlalchemy.sql import text

from aiida.storage.log import MIGRATE_LOGGER

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # Count the legacy computers *before* renaming, otherwise the renamed ones are counted as well.
    legacy_count = conn.execute(
        text("SELECT count(*) FROM db_dbcomputer WHERE transport_type = 'core.ssh'")
    ).fetchall()[0][0]

    result = conn.execute(
        text("UPDATE db_dbcomputer SET transport_type = 'core.ssh' WHERE transport_type = 'core.ssh_async'")
    )
    renamed_count = result.rowcount

    if renamed_count > 0:
        MIGRATE_LOGGER.report(
            f'Renamed the transport of {renamed_count} computer(s) from `core.ssh_async` to `core.ssh`.'
        )

    if legacy_count > 0:
        MIGRATE_LOGGER.warning(
            f'{legacy_count} computer(s) use the legacy `core.ssh` transport plugin, which has been replaced by the '
            'asynchronous implementation (formerly `core.ssh_async`). Their stored connection parameters are reused, '
            'but please verify each of them with `verdi computer test`.'
        )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of main_0003.')
