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
Create Date: 2023-05-05

"""

from alembic import op

from aiida.storage.psql_dos.migrations.utils.integrity import drop_hashes

revision = 'main_0002'
down_revision = 'main_0001'
branch_labels = None
depends_on = None


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
