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
"""Migration to add the `repository_metadata` JSONB column.

Revision ID: 7536a82b2cc4
Revises: 0edcdd5a30f0
Create Date: 2020-07-09 11:32:39.924151

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7536a82b2cc4'
down_revision = '0edcdd5a30f0'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.add_column(
        'db_dbnode',
        sa.Column('repository_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}')
    )
    op.alter_column('db_dbnode', 'repository_metadata', server_default=None)


def downgrade():
    """Migrations for the downgrade."""
    op.drop_column('db_dbnode', 'repository_metadata')
