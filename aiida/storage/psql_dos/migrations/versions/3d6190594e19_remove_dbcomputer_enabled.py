# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Remove `db_dbcomputer.enabled`

This is similar to migration django_0031

Revision ID: 3d6190594e19
Revises: 5a49629f0d45
Create Date: 2019-04-03 14:38:50.585639

"""

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,no-name-in-module,import-error
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d6190594e19'
down_revision = '5a49629f0d45'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('db_dbcomputer', 'enabled')


def downgrade():
    op.add_column('db_dbcomputer', sa.Column('enabled', sa.BOOLEAN(), autoincrement=False, nullable=True))
