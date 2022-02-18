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
"""Update `db_dbuser.last_login` and `db_dbuser.email`

Revision ID: django_0013
Revises: django_0012

"""
from alembic import op
import sqlalchemy as sa

from aiida.storage.psql_dos.migrations.utils import ReflectMigrations

revision = 'django_0013'
down_revision = 'django_0012'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.alter_column(
        'db_dbuser',
        'last_login',
        existing_type=sa.DATETIME(),
        nullable=True,
    )
    op.alter_column(
        'db_dbuser',
        'email',
        existing_type=sa.VARCHAR(length=75),
        type_=sa.VARCHAR(length=254),
    )
    # Note, I imagine the following was actually a mistake, it is re-added in django_0018
    reflect = ReflectMigrations(op)
    reflect.drop_unique_constraints('db_dbuser', ['email'])  # db_dbuser_email_key
    reflect.drop_indexes('db_dbuser', 'email', unique=False)  # db_dbuser_email_30150b7e_like


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0013.')
