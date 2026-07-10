###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Rename the ``core.ssh_async`` transport plugin to ``core.ssh``.

Bring archives in line with the profile database ``main_0003``, so that a computer exported from a
profile that used ``core.ssh_async`` can be imported into a v3 profile.

The rename has no inverse: once both kinds of computers share the ``core.ssh`` transport type, they
can no longer be told apart. The downgrade therefore only restores the schema revision and leaves
the transport types as they are.

Revision ID: main_0003
Revises: main_0002

"""

from alembic import op
from sqlalchemy.sql import text

revision = 'main_0003'
down_revision = 'main_0002'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.get_bind().execute(
        text("UPDATE db_dbcomputer SET transport_type = 'core.ssh' WHERE transport_type = 'core.ssh_async'")
    )


def downgrade():
    """Migrations for the downgrade."""
    pass
