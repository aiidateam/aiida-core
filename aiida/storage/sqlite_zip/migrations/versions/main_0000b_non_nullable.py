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
"""Alter columns to be non-nullable (to bring inline with psql_dos main_0001).

Revision ID: main_0000b
Revises: main_0000a
Create Date: 2022-03-04

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'main_0000b'
down_revision = 'main_0000a'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database schema."""
    # see https://alembic.sqlalchemy.org/en/latest/batch.html#running-batch-migrations-for-sqlite-and-other-databases
    # for why we run these in batches
    with op.batch_alter_table('db_dbauthinfo') as batch_op:
        batch_op.alter_column('aiidauser_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('dbcomputer_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('metadata', existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column('auth_params', existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column('enabled', existing_type=sa.BOOLEAN(), nullable=False)

    with op.batch_alter_table('db_dbcomment') as batch_op:
        batch_op.alter_column('dbnode_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('user_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.alter_column('content', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('ctime', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('mtime', existing_type=sa.DateTime(timezone=True), nullable=False)

    with op.batch_alter_table('db_dbcomputer') as batch_op:
        batch_op.alter_column('description', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('hostname', existing_type=sa.String(255), nullable=False)
        batch_op.alter_column('metadata', existing_type=sa.JSON(), nullable=False)
        batch_op.alter_column('scheduler_type', existing_type=sa.String(255), nullable=False)
        batch_op.alter_column('transport_type', existing_type=sa.String(255), nullable=False)

    with op.batch_alter_table('db_dbgroup') as batch_op:
        batch_op.alter_column('description', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('time', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('type_string', existing_type=sa.String(255), nullable=False)

    with op.batch_alter_table('db_dblog') as batch_op:
        batch_op.alter_column('levelname', existing_type=sa.String(50), nullable=False)
        batch_op.alter_column('loggername', existing_type=sa.String(255), nullable=False)
        batch_op.alter_column('message', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('time', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('metadata', existing_type=sa.JSON(), nullable=False)

    with op.batch_alter_table('db_dbnode') as batch_op:
        batch_op.alter_column('ctime', existing_type=sa.DateTime(timezone=True), nullable=False)
        batch_op.alter_column('description', existing_type=sa.TEXT(), nullable=False)
        batch_op.alter_column('label', existing_type=sa.String(255), nullable=False)
        batch_op.alter_column('mtime', existing_type=sa.DateTime(timezone=True), nullable=False)

    with op.batch_alter_table('db_dbuser') as batch_op:
        batch_op.alter_column('first_name', existing_type=sa.String(254), nullable=False)
        batch_op.alter_column('last_name', existing_type=sa.String(254), nullable=False)
        batch_op.alter_column('institution', existing_type=sa.String(254), nullable=False)


def downgrade():
    """Downgrade database schema."""
    raise NotImplementedError('Downgrade of main_0000b.')
