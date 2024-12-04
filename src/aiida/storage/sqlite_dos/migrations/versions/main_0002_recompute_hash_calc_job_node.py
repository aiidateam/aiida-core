###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Drop the hashes for all ``CalcJobNode`` instances.

The computed hash erroneously included the hash of the file repository. This was present as of v2.0 and so all nodes
created with versions since then will have incorrect hashes.

Revision ID: main_0002
Revises: main_0001
Create Date: 2024-05-29
"""

from __future__ import annotations

from alembic import op

from aiida.common.log import AIIDA_LOGGER

LOGGER = AIIDA_LOGGER.getChild(__file__)

revision = 'main_0002'
down_revision = 'main_0001'
branch_labels = None
depends_on = None


def drop_hashes(conn, hash_extra_key: str, entry_point_string: str | None = None) -> None:
    """Drop hashes of nodes.

    Print warning only if the DB actually contains nodes.

    :param hash_extra_key: The key in the extras used to store the hash at the time of this migration.
    :param entry_point_string: Optional entry point string of a node type to narrow the subset of nodes to reset. The
        value should be a complete entry point string, e.g., ``aiida.node:process.calculation.calcjob`` to drop the hash
        of all ``CalcJobNode`` rows.
    """
    from sqlalchemy.sql import text

    from aiida.orm.utils.node import get_type_string_from_class
    from aiida.plugins import load_entry_point_from_string

    if entry_point_string is not None:
        entry_point = load_entry_point_from_string(entry_point_string)
        node_type = get_type_string_from_class(entry_point.__module__, entry_point.__name__)
    else:
        node_type = None

    if node_type:
        statement_count = text(f"SELECT count(*) FROM db_dbnode WHERE node_type = '{node_type}';")
        statement_update = text(
            f"UPDATE db_dbnode SET extras = json_remove(db_dbnode.extras, '$.{hash_extra_key}')  WHERE node_type = '{node_type}';"  # noqa: E501
        )
    else:
        statement_count = text('SELECT count(*) FROM db_dbnode;')
        statement_update = text(f"UPDATE db_dbnode SET extras = json_remove(db_dbnode.extras, '$.{hash_extra_key}');")

    node_count = conn.execute(statement_count).fetchall()[0][0]

    if node_count > 0:
        if entry_point_string:
            msg = f'Invalidating the hashes of certain nodes. Please run `verdi node rehash -e {entry_point_string}`.'
        else:
            msg = 'Invalidating the hashes of all nodes. Please run `verdi node rehash`.'
        LOGGER.warning(msg)

    conn.execute(statement_update)


def upgrade():
    """Migrations for the upgrade."""
    drop_hashes(
        op.get_bind(), hash_extra_key='_aiida_hash', entry_point_string='aiida.node:process.calculation.calcjob'
    )


def downgrade():
    """Migrations for the downgrade."""
    drop_hashes(
        op.get_bind(), hash_extra_key='_aiida_hash', entry_point_string='aiida.node:process.calculation.calcjob'
    )
