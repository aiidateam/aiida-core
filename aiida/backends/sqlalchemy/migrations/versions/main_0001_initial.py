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
"""Initial main branch schema

This revision is compatible with the heads of the django and sqlalchemy branches.

Revision ID: main_0001
Revises:
Create Date: 2021-02-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'main_0001'
down_revision = None
branch_labels = ('main',)
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.create_table(
        'db_dbcomputer',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('label', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('scheduler_type', sa.String(length=255), nullable=False),
        sa.Column('transport_type', sa.String(length=255), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index(
        'ix_pat_db_dbcomputer_label',
        'db_dbcomputer', ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'}
    )
    op.create_table(
        'db_dbsetting',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('key', sa.String(length=1024), nullable=False, unique=True),
        sa.Column('val', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        'ix_pat_db_dbsetting_key',
        'db_dbsetting',
        ['key'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'key': 'varchar_pattern_ops'},
    )
    op.create_table(
        'db_dbuser',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('email', sa.String(length=254), nullable=False, unique=True),
        sa.Column('first_name', sa.String(length=254), nullable=False),
        sa.Column('last_name', sa.String(length=254), nullable=False),
        sa.Column('institution', sa.String(length=254), nullable=False),
    )
    op.create_index(
        'ix_pat_db_dbuser_email',
        'db_dbuser',
        ['email'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'email': 'varchar_pattern_ops'},
    )
    op.create_table(
        'db_dbauthinfo',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('aiidauser_id', sa.Integer(), nullable=False, index=True),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=False, index=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('auth_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ['aiidauser_id'],
            ['db_dbuser.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'],
            ['db_dbcomputer.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.UniqueConstraint('aiidauser_id', 'dbcomputer_id'),
    )
    op.create_table(
        'db_dbgroup',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('label', sa.String(length=255), nullable=False, index=True),
        sa.Column('type_string', sa.String(length=255), nullable=False, index=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.UniqueConstraint('label', 'type_string'),
    )
    op.create_index(
        'ix_pat_db_dbgroup_label',
        'db_dbgroup',
        ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index(
        'ix_pat_db_dbgroup_type_string',
        'db_dbgroup',
        ['type_string'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'type_string': 'varchar_pattern_ops'},
    )

    op.create_table(
        'db_dbnode',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('node_type', sa.String(length=255), nullable=False, index=True),
        sa.Column('process_type', sa.String(length=255), nullable=True, index=True),
        sa.Column('label', sa.String(length=255), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('repository_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'],
            ['db_dbcomputer.id'],
            ondelete='RESTRICT',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            ondelete='restrict',
            initially='DEFERRED',
            deferrable=True,
        ),
    )
    op.create_index(
        'ix_pat_db_dbnode_label',
        'db_dbnode',
        ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index(
        'ix_pat_db_dbnode_process_type',
        'db_dbnode',
        ['process_type'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'process_type': 'varchar_pattern_ops'},
    )
    op.create_index(
        'ix_pat_db_dbnode_node_type',
        'db_dbnode',
        ['node_type'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'node_type': 'varchar_pattern_ops'},
    )

    op.create_table(
        'db_dbcomment',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('dbnode_id', sa.Integer(), nullable=False, index=True),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbgroup_dbnodes',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('dbnode_id', sa.Integer(), nullable=False, index=True),
        sa.Column('dbgroup_id', sa.Integer(), nullable=False, index=True),
        sa.ForeignKeyConstraint(['dbgroup_id'], ['db_dbgroup.id'], initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(['dbnode_id'], ['db_dbnode.id'], initially='DEFERRED', deferrable=True),
        sa.UniqueConstraint('dbgroup_id', 'dbnode_id'),
    )
    op.create_table(
        'db_dblink',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('input_id', sa.Integer(), nullable=False, index=True),
        sa.Column('output_id', sa.Integer(), nullable=False, index=True),
        sa.Column('label', sa.String(length=255), nullable=False, index=True),
        sa.Column('type', sa.String(length=255), nullable=False, index=True),
        sa.ForeignKeyConstraint(['input_id'], ['db_dbnode.id'], initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(
            ['output_id'],
            ['db_dbnode.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
    )
    op.create_index(
        'ix_pat_db_dblink_label',
        'db_dblink',
        ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index(
        'ix_pat_db_dblink_type',
        'db_dblink',
        ['type'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'type': 'varchar_pattern_ops'},
    )

    op.create_table(
        'db_dblog',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('loggername', sa.String(length=255), nullable=False, index=True),
        sa.Column('levelname', sa.String(length=50), nullable=False, index=True),
        sa.Column('dbnode_id', sa.Integer(), nullable=False, index=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
    )
    op.create_index(
        'ix_pat_db_dblog_levelname',
        'db_dblog',
        ['levelname'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'levelname': 'varchar_pattern_ops'},
    )
    op.create_index(
        'ix_pat_db_dblog_loggername',
        'db_dblog',
        ['loggername'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'loggername': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    raise NotImplementedError('Downgrade of main_0001.')
