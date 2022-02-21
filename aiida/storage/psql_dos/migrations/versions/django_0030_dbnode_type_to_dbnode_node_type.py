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
"""Rename `db_dbnode.type` to `db_dbnode.node_type`

This is similar to migration 5ddd24e52864

Revision ID: django_0030
Revises: django_0029

"""
from alembic import op

revision = 'django_0030'
down_revision = 'django_0029'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.alter_column('db_dbnode', 'type', new_column_name='node_type')  # pylint: disable=no-member
    # note index names are (mistakenly) not changed here


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0030.')
