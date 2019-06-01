# -*- coding: utf-8 -*-
"""Drop the columns `nodeversion` and `public` from the `DbNode` model.

Revision ID: 1830c8430131
Revises: 1b8ed3425af9
Create Date: 2019-05-27 15:35:37.404644

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import sqlalchemy as sa
from alembic import op

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
