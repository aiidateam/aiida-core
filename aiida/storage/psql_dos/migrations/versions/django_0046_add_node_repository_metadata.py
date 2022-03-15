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
"""Add the `db_dbnode.repository_metadata` JSONB column.

Revision ID: django_0046
Revises: django_0045

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'django_0046'
down_revision = 'django_0045'
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
