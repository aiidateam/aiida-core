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
"""Renames `db_dbgroup.name`/`db_dbgroup.type` -> `db_dbgroup.label`/`db_dbgroup.type_string`

Note, this is simliar to sqlalchemy migration b8b23ddefad4

Revision ID: django_0021
Revises: django_0020

"""
from alembic import op

from aiida.storage.psql_dos.migrations.utils import ReflectMigrations

revision = 'django_0021'
down_revision = 'django_0020'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # drop old constraint and indexes
    reflect = ReflectMigrations(op)
    reflect.drop_unique_constraints('db_dbgroup', ['name', 'type'])
    reflect.drop_indexes('db_dbgroup', 'name')
    reflect.drop_indexes('db_dbgroup', 'type')

    # renaming
    op.alter_column('db_dbgroup', 'name', new_column_name='label')
    op.alter_column('db_dbgroup', 'type', new_column_name='type_string')

    # create new constraint and indexes
    # note the naming here is actually incorrect, but inherited from the django migrations
    op.create_unique_constraint('db_dbgroup_name_type_12656f33_uniq', 'db_dbgroup', ['label', 'type_string'])
    op.create_index('db_dbgroup_name_66c75272', 'db_dbgroup', ['label'])
    op.create_index(
        'db_dbgroup_name_66c75272_like',
        'db_dbgroup',
        ['label'],
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index('db_dbgroup_type_23b2a748', 'db_dbgroup', ['type_string'])
    op.create_index(
        'db_dbgroup_type_23b2a748_like',
        'db_dbgroup',
        ['type_string'],
        postgresql_using='btree',
        postgresql_ops={'type_string': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0021.')
