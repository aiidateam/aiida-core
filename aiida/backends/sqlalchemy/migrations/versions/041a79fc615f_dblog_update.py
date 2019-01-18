# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
"""Addition of uuids to the DbLog table.

Revision ID: 041a79fc615f
Revises: 7ca08c391c49
Create Date: 2018-12-28 15:53:14.596810

"""
from __future__ import absolute_import
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '041a79fc615f'
down_revision = '7ca08c391c49'
branch_labels = None
depends_on = None


def upgrade():
    """
    Changing the log table columns to use uuid to reference remote objects and log entries.
    Upgrade function.
    """
    op.drop_column('db_dblog', 'objpk')

    op.add_column('db_dblog', sa.Column('objuuid', postgresql.UUID(), autoincrement=False, nullable=True))
    op.add_column('db_dblog', sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True))
    op.create_index('ix_db_dblog_objuuid', 'db_dblog', ['objuuid'])


def downgrade():
    """
    Downgrade function to the previous schema.
    """
    op.drop_column('db_dblog', 'objuuid')
    op.drop_column('db_dblog', 'uuid')

    op.add_column('db_dblog', sa.Column('objpk', sa.INTEGER(), autoincrement=False, nullable=True))
    op.create_index('ix_db_dblog_objpk', 'db_dblog', ['objpk'])
