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
"""Add indexes on `db_dbnode.mtime` and `db_dbnode.mtime`

Revision ID: django_0005
Revises: django_0004

"""
from alembic import op

revision = 'django_0005'
down_revision = 'django_0004'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.create_index('db_dbnode_ctime_71626ef5', 'db_dbnode', ['ctime'], unique=False)
    op.create_index('db_dbnode_mtime_0554ea3d', 'db_dbnode', ['mtime'], unique=False)


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0005.')
