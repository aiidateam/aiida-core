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
"""Add indices to `db_dbattribute.tval` and `db_dbnode.uuid`

Revision ID: django_0004
Revises: django_0003

"""
from alembic import op

revision = 'django_0004'
down_revision = 'django_0003'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.execute(
        """
        CREATE INDEX tval_idx_for_daemon
        ON db_dbattribute (tval)
        WHERE ("db_dbattribute"."tval"
        IN ('COMPUTED', 'WITHSCHEDULER', 'TOSUBMIT'))"""
    )
    op.create_index('db_dbnode_uuid_62e0bf98', 'db_dbnode', ['uuid'])
    op.create_index(
        'db_dbnode_uuid_62e0bf98_like',
        'db_dbnode',
        ['uuid'],
        postgresql_using='btree',
        postgresql_ops={'uuid': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0004.')
