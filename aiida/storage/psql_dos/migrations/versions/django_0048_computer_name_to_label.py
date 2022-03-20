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
"""Rename `db_dbcomputer.name` to `db_dbcomputer.label`

Revision ID: django_0048
Revises: django_0047

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils import ReflectMigrations

revision = 'django_0048'
down_revision = 'django_0047'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    reflect = ReflectMigrations(op)
    reflect.drop_unique_constraints('db_dbcomputer', ['name'])  # db_dbcomputer_name_key
    reflect.drop_indexes('db_dbcomputer', 'name')  # db_dbcomputer_name_f1800b1a_like
    op.alter_column('db_dbcomputer', 'name', new_column_name='label')
    op.create_unique_constraint('db_dbcomputer_label_bc480bab_uniq', 'db_dbcomputer', ['label'])
    op.create_index(
        'db_dbcomputer_label_bc480bab_like',
        'db_dbcomputer',
        ['label'],
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0048.')
