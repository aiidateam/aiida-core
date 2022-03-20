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

Final data migration for `Nodes` after `aiida.orm.nodes` reorganization was finalized to remove the `node.` prefix

Note, this is identical to the django_0028 migration.

Revision ID: 61fc0913fae9
Revises: ce56d84bcc35
Create Date: 2019-02-16 15:32:42.745450

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module

from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '61fc0913fae9'
down_revision = 'ce56d84bcc35'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    conn = op.get_bind()

    # The `node.` prefix is being dropped from the node type string
    statement = text(
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
    raise NotImplementedError('Downgrade of 61fc0913fae9.')
