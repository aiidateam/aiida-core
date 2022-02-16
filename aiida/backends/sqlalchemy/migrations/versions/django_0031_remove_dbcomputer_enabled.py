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
"""Remove `db_dbcomputer.enabled`

This is similar to migration 3d6190594e19

Revision ID: django_0031
Revises: django_0030

"""
from alembic import op

revision = 'django_0031'
down_revision = 'django_0030'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_column('db_dbcomputer', 'enabled')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0031.')
