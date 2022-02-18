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
"""Drop `db_dbcomputer.transport_params`

This is similar to migration django_0036

Revision ID: 07fac78e6209
Revises: de2eaf6978b4
Create Date: 2019-02-16 15:32:42.745450

"""
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '07fac78e6209'
down_revision = 'de2eaf6978b4'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_column('db_dbcomputer', 'transport_params')


def downgrade():
    """Migrations for the downgrade."""
    op.add_column(
        'db_dbcomputer',
        sa.Column('transport_params', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True)
    )
