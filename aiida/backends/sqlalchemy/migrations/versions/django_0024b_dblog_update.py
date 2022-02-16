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
"""Clean the log records from non-Node entity records (part b).

We need to add the unique constraint on the `uuid` column in a new transaction.

Revision ID: django_0024
Revises: django_0024a

"""
from alembic import op

revision = 'django_0024'
down_revision = 'django_0024a'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.create_unique_constraint('db_dblog_uuid_9cf77df3_uniq', 'db_dblog', ['uuid'])


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0024.')
