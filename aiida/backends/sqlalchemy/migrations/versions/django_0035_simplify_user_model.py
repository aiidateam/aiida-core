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
"""Simplify `db_dbuser`, by dropping unnecessary columns and join tables

These columns were part of the default Django user model

This migration is similar to de2eaf6978b4

Revision ID: django_0035
Revises: django_0034

"""
from alembic import op

revision = 'django_0035'
down_revision = 'django_0034'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.drop_column('db_dbuser', 'date_joined')
    op.drop_column('db_dbuser', 'is_active')
    op.drop_column('db_dbuser', 'is_staff')
    op.drop_column('db_dbuser', 'is_superuser')
    op.drop_column('db_dbuser', 'last_login')
    op.drop_column('db_dbuser', 'password')
    op.drop_table('db_dbuser_groups')
    op.drop_table('db_dbuser_user_permissions')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0035.')
