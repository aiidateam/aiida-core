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
"""Remove the `node.` prefix from `db_dbnode.type`

Note, this is identical to the sqlalchemy migration 61fc0913fae9.

Revision ID: django_0028
Revises: django_0027

"""
from alembic import op
import sqlalchemy as sa

revision = 'django_0028'
down_revision = 'django_0027'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The `node.` prefix is being dropped from the node type string
    statement = sa.text(
        r"""
        UPDATE db_dbnode
        SET type = regexp_replace(type, '^node.data.', 'data.')
        WHERE type LIKE 'node.data.%';

        UPDATE db_dbnode
        SET type = regexp_replace(type, '^node.process.', 'process.')
        WHERE type LIKE 'node.process.%';
    """
    )
    conn.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0028.')
