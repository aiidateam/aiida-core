# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,import-error,no-name-in-module
"""Simplify `db_dbuser`, by dropping unnecessary columns

These columns were part of the default Django user model

This migration is similar to django_0035

Revision ID: de2eaf6978b4
Revises: 1830c8430131
Create Date: 2019-05-28 11:15:33.242602

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'de2eaf6978b4'
down_revision = '1830c8430131'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_column('db_dbuser', 'is_active')
    op.drop_column('db_dbuser', 'is_superuser')
    op.drop_column('db_dbuser', 'is_staff')
    op.drop_column('db_dbuser', 'last_login')
    op.drop_column('db_dbuser', 'password')
    op.drop_column('db_dbuser', 'date_joined')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of de2eaf6978b4.')
