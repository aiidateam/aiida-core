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
"""Drop the columns `nodeversion` and `public` from the `DbNode` model.

Revision ID: 1830c8430131
Revises: 1b8ed3425af9
Create Date: 2019-05-27 15:35:37.404644

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1830c8430131'
down_revision = '1b8ed3425af9'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('db_dbnode', 'nodeversion')
    op.drop_column('db_dbnode', 'public')


def downgrade():
    op.add_column('db_dbnode', sa.Column('public', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.add_column('db_dbnode', sa.Column('nodeversion', sa.INTEGER(), autoincrement=False, nullable=True))
