# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# yapf: disable
"""Initial schema of schema generation 2.

Revision ID: 00be6389ab31
Revises:
Create Date: 2019-07-25 10:33:49.962321

"""
# pylint: disable=invalid-name,no-member
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-name-in-module,import-error
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '00be6389ab31'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    op.create_table('db_dbcomputer',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('scheduler_type', sa.String(length=255), nullable=True),
        sa.Column('transport_type', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('uuid')
    )

    op.create_table('db_dbsetting',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('val', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index(op.f('ix_db_dbsetting_key'), 'db_dbsetting', ['key'], unique=False)

    op.create_table('db_dbuser',
    sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=True),
        sa.Column('first_name', sa.String(length=254), nullable=True),
        sa.Column('last_name', sa.String(length=254), nullable=True),
        sa.Column('institution', sa.String(length=254), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_db_dbuser_email'), 'db_dbuser', ['email'], unique=True)

    op.create_table('db_dbauthinfo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aiidauser_id', sa.Integer(), nullable=True),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('auth_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(
            ['aiidauser_id'], ['db_dbuser.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'], ['db_dbcomputer.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('aiidauser_id', 'dbcomputer_id')
    )

    op.create_table('db_dbgroup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('type_string', sa.String(length=255), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['db_dbuser.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('label', 'type_string'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_db_dbgroup_label'), 'db_dbgroup', ['label'], unique=False)
    op.create_index(op.f('ix_db_dbgroup_type_string'), 'db_dbgroup', ['type_string'], unique=False)

    op.create_table('db_dbnode',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('node_type', sa.String(length=255), nullable=True),
        sa.Column('process_type', sa.String(length=255), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'], ['db_dbcomputer.id'], ondelete='RESTRICT', initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['db_dbuser.id'], ondelete='restrict', initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_db_dbnode_label'), 'db_dbnode', ['label'], unique=False)
    op.create_index(op.f('ix_db_dbnode_node_type'), 'db_dbnode', ['node_type'], unique=False)
    op.create_index(op.f('ix_db_dbnode_process_type'), 'db_dbnode', ['process_type'], unique=False)

    op.create_table('db_dbcomment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dbnode_id', sa.Integer(), nullable=True),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ['dbnode_id'], ['db_dbnode.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(
            ['user_id'], ['db_dbuser.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )

    op.create_table('db_dbgroup_dbnodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=True),
        sa.Column('dbgroup_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['dbgroup_id'], ['db_dbgroup.id'], initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(['dbnode_id'], ['db_dbnode.id'], initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key')
    )
    op.create_index('db_dbgroup_dbnodes_dbgroup_id_idx', 'db_dbgroup_dbnodes', ['dbgroup_id'], unique=False)
    op.create_index('db_dbgroup_dbnodes_dbnode_id_idx', 'db_dbgroup_dbnodes', ['dbnode_id'], unique=False)

    op.create_table('db_dblink',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('input_id', sa.Integer(), nullable=True),
        sa.Column('output_id', sa.Integer(), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['input_id'], ['db_dbnode.id'], initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(
            ['output_id'], ['db_dbnode.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_db_dblink_input_id'), 'db_dblink', ['input_id'], unique=False)
    op.create_index(op.f('ix_db_dblink_label'), 'db_dblink', ['label'], unique=False)
    op.create_index(op.f('ix_db_dblink_output_id'), 'db_dblink', ['output_id'], unique=False)
    op.create_index(op.f('ix_db_dblink_type'), 'db_dblink', ['type'], unique=False)

    op.create_table('db_dblog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('loggername', sa.String(length=255), nullable=True),
        sa.Column('levelname', sa.String(length=255), nullable=True),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ['dbnode_id'], ['db_dbnode.id'], ondelete='CASCADE', initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_db_dblog_levelname'), 'db_dblog', ['levelname'], unique=False)
    op.create_index(op.f('ix_db_dblog_loggername'), 'db_dblog', ['loggername'], unique=False)

    connection = op.get_bind()
    statement = text("""
        INSERT INTO db_dbsetting (key, val, description, time)
        VALUES ('schema_generation', '"2"', 'Database schema generation', NOW());""")
    connection.execute(statement)


def downgrade():
    """Migrations for the downgrade."""
    op.drop_index(op.f('ix_db_dblog_loggername'), table_name='db_dblog')
    op.drop_index(op.f('ix_db_dblog_levelname'), table_name='db_dblog')
    op.drop_table('db_dblog')
    op.drop_index(op.f('ix_db_dblink_type'), table_name='db_dblink')
    op.drop_index(op.f('ix_db_dblink_output_id'), table_name='db_dblink')
    op.drop_index(op.f('ix_db_dblink_label'), table_name='db_dblink')
    op.drop_index(op.f('ix_db_dblink_input_id'), table_name='db_dblink')
    op.drop_table('db_dblink')
    op.drop_index('db_dbgroup_dbnodes_dbnode_id_idx', table_name='db_dbgroup_dbnodes')
    op.drop_index('db_dbgroup_dbnodes_dbgroup_id_idx', table_name='db_dbgroup_dbnodes')
    op.drop_table('db_dbgroup_dbnodes')
    op.drop_table('db_dbcomment')
    op.drop_index(op.f('ix_db_dbnode_process_type'), table_name='db_dbnode')
    op.drop_index(op.f('ix_db_dbnode_node_type'), table_name='db_dbnode')
    op.drop_index(op.f('ix_db_dbnode_label'), table_name='db_dbnode')
    op.drop_table('db_dbnode')
    op.drop_index(op.f('ix_db_dbgroup_type_string'), table_name='db_dbgroup')
    op.drop_index(op.f('ix_db_dbgroup_label'), table_name='db_dbgroup')
    op.drop_table('db_dbgroup')
    op.drop_table('db_dbauthinfo')
    op.drop_index(op.f('ix_db_dbuser_email'), table_name='db_dbuser')
    op.drop_table('db_dbuser')
    op.drop_index(op.f('ix_db_dbsetting_key'), table_name='db_dbsetting')
    op.drop_table('db_dbsetting')
    op.drop_table('db_dbcomputer')
