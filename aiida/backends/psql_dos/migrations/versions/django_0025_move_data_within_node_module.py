# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member
"""Change type string for `Data` nodes, from `data.*` to `node.data.*`

Note, this is identical to sqlalchemy migration 6a5c2ea1439d

Revision ID: django_0025
Revises: django_0024

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0025'
down_revision = 'django_0024'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The type string for `Data` nodes changed from `data.*` to `node.data.*`.
    statement = sa.text(
        r"""
        UPDATE db_dbnode
        SET type = regexp_replace(type, '^data.', 'node.data.')
        WHERE type LIKE 'data.%'
    """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0025.')
