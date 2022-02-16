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
"""Replace serialized dict text fields with JSONB

Revision ID: django_0033
Revises: django_0032

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'django_0033'
down_revision = 'django_0032'
branch_labels = None
depends_on = None

FIELDS = (
    ('db_dbauthinfo', 'metadata'),
    ('db_dbauthinfo', 'auth_params'),
    ('db_dbcomputer', 'metadata'),
    ('db_dbcomputer', 'transport_params'),
    ('db_dblog', 'metadata'),
)


def upgrade():
    """Migrations for the upgrade."""
    for table_name, column in FIELDS:
        op.alter_column(
            table_name, column, existing_type=sa.TEXT, type_=postgresql.JSONB, postgresql_using=f'{column}::jsonb'
        )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0033.')
