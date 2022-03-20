# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,line-too-long
"""Finalise parity of the legacy django branch with the sqlalchemy branch.

1. Remove and recreate all (non-unique) indexes, with standard names and postgresql ops.
2. Remove and recreate all unique constraints, with standard names.
3. Remove and recreate all foreign key constraints, with standard names and other rules.
4. Drop the django specific tables

It is of note that a number of foreign keys were missing comparable `ON DELETE` rules in django.
This is because django does not currently add these rules to the database, but instead tries to handle them on the
Python side, see: https://stackoverflow.com/a/35780859/5033292

Revision ID: django_0050
Revises: django_0049

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils.parity import synchronize_schemas

revision = 'django_0050'
down_revision = 'django_0049'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    synchronize_schemas(op)

    for tbl_name in (
        'auth_group_permissions', 'auth_permission', 'auth_group', 'django_content_type', 'django_migrations'
    ):
        op.execute(f'DROP TABLE IF EXISTS {tbl_name} CASCADE')


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0050.')
