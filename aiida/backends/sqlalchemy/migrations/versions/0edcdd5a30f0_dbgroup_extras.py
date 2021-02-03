# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-member,invalid-name
"""Migration to add the `extras` JSONB column to the `DbGroup` model.

Revision ID: 0edcdd5a30f0
Revises: bf591f31dd12
Create Date: 2019-04-03 14:38:50.585639

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0edcdd5a30f0'
down_revision = 'bf591f31dd12'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade: Add the extras column to the 'db_dbgroup' table"""
    op.add_column(
        'db_dbgroup', sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}')
    )
    op.alter_column('db_dbgroup', 'extras', server_default=None)


def downgrade():
    """Downgrade: Drop the extras column from the 'db_dbgroup' table"""
    op.drop_column('db_dbgroup', 'extras')
