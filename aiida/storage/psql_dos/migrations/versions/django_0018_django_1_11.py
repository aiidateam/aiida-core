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
"""Change UUID type and add uniqueness constraints.

Revision ID: django_0018
Revises: django_0017

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from aiida.storage.psql_dos.migrations.utils import ReflectMigrations
from aiida.storage.psql_dos.migrations.utils.duplicate_uuids import verify_uuid_uniqueness

revision = 'django_0018'
down_revision = 'django_0017'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    reflect = ReflectMigrations(op)

    reflect.drop_indexes('db_dbnode', 'uuid')  # db_dbnode_uuid_62e0bf98_like
    for table, unique in (
        ('db_dbcomment', 'db_dbcomment_uuid_49bac08c_uniq'),
        ('db_dbcomputer', 'db_dbcomputer_uuid_f35defa6_uniq'),
        ('db_dbgroup', 'db_dbgroup_uuid_af896177_uniq'),
        ('db_dbnode', None),
        ('db_dbworkflow', 'db_dbworkflow_uuid_08947ee2_uniq'),
    ):
        op.alter_column(
            table,
            'uuid',
            existing_type=sa.VARCHAR(length=36),
            type_=postgresql.UUID(as_uuid=True),
            nullable=False,
            postgresql_using='uuid::uuid'
        )
        if unique:
            verify_uuid_uniqueness(table, op.get_bind())
            op.create_unique_constraint(unique, table, ['uuid'])

    op.create_unique_constraint('db_dbuser_email_30150b7e_uniq', 'db_dbuser', ['email'])
    op.create_index(
        'db_dbuser_email_30150b7e_like',
        'db_dbuser',
        ['email'],
        postgresql_using='btree',
        postgresql_ops={'email': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of django_0018.')
