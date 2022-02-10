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
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('scheduler_type', sa.String(length=255), nullable=False),
        sa.Column('transport_type', sa.String(length=255), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('label', name='db_dbcomputer_label_bc480bab_uniq'),
        sa.UniqueConstraint('uuid', name='db_dbcomputer_uuid_f35defa6_uniq'),
    )
    op.create_index(
        'db_dbcomputer_label_bc480bab_like',
        'db_dbcomputer', ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'}
    )
    op.create_table(
        'db_dbsetting',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=1024), nullable=False),
        sa.Column('val', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', name='db_dbsetting_key_1b84beb4_uniq'),
    )
    op.create_index(
        'db_dbsetting_key_1b84beb4_like',
        'db_dbsetting',
        ['key'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'key': 'varchar_pattern_ops'},
    )
    op.create_table(
        'db_dbuser',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=254), nullable=False),
        sa.Column('first_name', sa.String(length=254), nullable=False),
        sa.Column('last_name', sa.String(length=254), nullable=False),
        sa.Column('institution', sa.String(length=254), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='db_dbuser_email_30150b7e_uniq'),
    )
    op.create_index(
        'db_dbuser_email_30150b7e_like',
        'db_dbuser',
        ['email'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'email': 'varchar_pattern_ops'},
    )
    op.create_table(
        'db_dbauthinfo',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aiidauser_id', sa.Integer(), nullable=False),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'aiidauser_id', 'dbcomputer_id', name='db_dbauthinfo_aiidauser_id_dbcomputer_id_777cdaa8_uniq'
        ),
    )
    op.create_index('db_dbauthinfo_aiidauser_id_0684fdfb', 'db_dbauthinfo', ['aiidauser_id'], unique=False)
    op.create_index('db_dbauthinfo_dbcomputer_id_424f7ac4', 'db_dbauthinfo', ['dbcomputer_id'], unique=False)
    op.create_table(
        'db_dbgroup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('type_string', sa.String(length=255), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('label', 'type_string', name='db_dbgroup_name_type_12656f33_uniq'),
        sa.UniqueConstraint('uuid', name='db_dbgroup_uuid_af896177_uniq'),
    )
    op.create_index('db_dbgroup_name_66c75272', 'db_dbgroup', ['label'], unique=False)
    op.create_index(
        'db_dbgroup_name_66c75272_like',
        'db_dbgroup',
        ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index('db_dbgroup_type_23b2a748', 'db_dbgroup', ['type_string'], unique=False)
    op.create_index(
        'db_dbgroup_type_23b2a748_like',
        'db_dbgroup',
        ['type_string'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'type_string': 'varchar_pattern_ops'},
    )
    op.create_index('db_dbgroup_user_id_100f8a51', 'db_dbgroup', ['user_id'], unique=False)
    op.create_table(
        'db_dbnode',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('node_type', sa.String(length=255), nullable=False),
        sa.Column('process_type', sa.String(length=255), nullable=True),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('repository_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='db_dbnode_uuid_62e0bf98_uniq'),
    )
    op.create_index('db_dbnode_ctime_71626ef5', 'db_dbnode', ['ctime'], unique=False)
    op.create_index('db_dbnode_dbcomputer_id_315372a3', 'db_dbnode', ['dbcomputer_id'], unique=False)
    op.create_index('db_dbnode_label_6469539e', 'db_dbnode', ['label'], unique=False)
    op.create_index(
        'db_dbnode_label_6469539e_like',
        'db_dbnode',
        ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index('db_dbnode_mtime_0554ea3d', 'db_dbnode', ['mtime'], unique=False)
    op.create_index('db_dbnode_process_type_df7298d0', 'db_dbnode', ['process_type'], unique=False)
    op.create_index(
        'db_dbnode_process_type_df7298d0_like',
        'db_dbnode',
        ['process_type'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'process_type': 'varchar_pattern_ops'},
    )
    op.create_index('db_dbnode_type_a8ce9753', 'db_dbnode', ['node_type'], unique=False)
    op.create_index(
        'db_dbnode_type_a8ce9753_like',
        'db_dbnode',
        ['node_type'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'node_type': 'varchar_pattern_ops'},
    )
    op.create_index('db_dbnode_user_id_12e7aeaf', 'db_dbnode', ['user_id'], unique=False)
    op.create_table(
        'db_dbcomment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='db_dbcomment_uuid_49bac08c_uniq'),
    )
    op.create_index('db_dbcomment_dbnode_id_3b812b6b', 'db_dbcomment', ['dbnode_id'], unique=False)
    op.create_index('db_dbcomment_user_id_8ed5e360', 'db_dbcomment', ['user_id'], unique=False)
    op.create_table(
        'db_dbgroup_dbnodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('dbgroup_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['dbgroup_id'], ['db_dbgroup.id'], initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(['dbnode_id'], ['db_dbnode.id'], initially='DEFERRED', deferrable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_eee23cce_uniq'),
    )
    op.create_index('db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d', 'db_dbgroup_dbnodes', ['dbgroup_id'], unique=False)
    op.create_index('db_dbgroup_dbnodes_dbnode_id_118b9439', 'db_dbgroup_dbnodes', ['dbnode_id'], unique=False)
    op.create_table(
        'db_dblink',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('input_id', sa.Integer(), nullable=False),
        sa.Column('output_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['input_id'], ['db_dbnode.id'], initially='DEFERRED', deferrable=True),
        sa.ForeignKeyConstraint(
            ['output_id'],
            ['db_dbnode.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('db_dblink_input_id_9245bd73', 'db_dblink', ['input_id'], unique=False)
    op.create_index('db_dblink_label_f1343cfb', 'db_dblink', ['label'], unique=False)
    op.create_index(
        'db_dblink_label_f1343cfb_like',
        'db_dblink',
        ['label'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'},
    )
    op.create_index('db_dblink_output_id_c0167528', 'db_dblink', ['output_id'], unique=False)
    op.create_index('db_dblink_type_229f212b', 'db_dblink', ['type'], unique=False)
    op.create_index(
        'db_dblink_type_229f212b_like',
        'db_dblink',
        ['type'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'type': 'varchar_pattern_ops'},
    )
    op.create_table(
        'db_dblog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('loggername', sa.String(length=255), nullable=False),
        sa.Column('levelname', sa.String(length=50), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            ondelete='CASCADE',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('uuid', name='db_dblog_uuid_9cf77df3_uniq'),
    )
    op.create_index('db_dblog_dbnode_id_da34b732', 'db_dblog', ['dbnode_id'], unique=False)
    op.create_index('db_dblog_levelname_ad5dc346', 'db_dblog', ['levelname'], unique=False)
    op.create_index(
        'db_dblog_levelname_ad5dc346_like',
        'db_dblog',
        ['levelname'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'levelname': 'varchar_pattern_ops'},
    )
    op.create_index('db_dblog_loggername_00b5ba16', 'db_dblog', ['loggername'], unique=False)
    op.create_index(
        'db_dblog_loggername_00b5ba16_like',
        'db_dblog',
        ['loggername'],
        unique=False,
        postgresql_using='btree',
        postgresql_ops={'loggername': 'varchar_pattern_ops'},
    )


def downgrade():
    """Migrations for the downgrade."""
    op.drop_index(
        'db_dblog_loggername_00b5ba16_like',
        table_name='db_dblog',
        postgresql_using='btree',
        postgresql_ops={'loggername': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dblog_loggername_00b5ba16', table_name='db_dblog')
    op.drop_index(
        'db_dblog_levelname_ad5dc346_like',
        table_name='db_dblog',
        postgresql_using='btree',
        postgresql_ops={'levelname': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dblog_levelname_ad5dc346', table_name='db_dblog')
    op.drop_index('db_dblog_dbnode_id_da34b732', table_name='db_dblog')
    op.drop_table('db_dblog')
    op.drop_index(
        'db_dblink_type_229f212b_like',
        table_name='db_dblink',
        postgresql_using='btree',
        postgresql_ops={'type': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dblink_type_229f212b', table_name='db_dblink')
    op.drop_index('db_dblink_output_id_c0167528', table_name='db_dblink')
    op.drop_index(
        'db_dblink_label_f1343cfb_like',
        table_name='db_dblink',
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dblink_label_f1343cfb', table_name='db_dblink')
    op.drop_index('db_dblink_input_id_9245bd73', table_name='db_dblink')
    op.drop_table('db_dblink')
    op.drop_index('db_dbgroup_dbnodes_dbnode_id_118b9439', table_name='db_dbgroup_dbnodes')
    op.drop_index('db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d', table_name='db_dbgroup_dbnodes')
    op.drop_table('db_dbgroup_dbnodes')
    op.drop_index('db_dbcomment_user_id_8ed5e360', table_name='db_dbcomment')
    op.drop_index('db_dbcomment_dbnode_id_3b812b6b', table_name='db_dbcomment')
    op.drop_table('db_dbcomment')
    op.drop_index('db_dbnode_user_id_12e7aeaf', table_name='db_dbnode')
    op.drop_index(
        'db_dbnode_type_a8ce9753_like',
        table_name='db_dbnode',
        postgresql_using='btree',
        postgresql_ops={'node_type': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dbnode_type_a8ce9753', table_name='db_dbnode')
    op.drop_index(
        'db_dbnode_process_type_df7298d0_like',
        table_name='db_dbnode',
        postgresql_using='btree',
        postgresql_ops={'process_type': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dbnode_process_type_df7298d0', table_name='db_dbnode')
    op.drop_index('db_dbnode_mtime_0554ea3d', table_name='db_dbnode')
    op.drop_index(
        'db_dbnode_label_6469539e_like',
        table_name='db_dbnode',
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dbnode_label_6469539e', table_name='db_dbnode')
    op.drop_index('db_dbnode_dbcomputer_id_315372a3', table_name='db_dbnode')
    op.drop_index('db_dbnode_ctime_71626ef5', table_name='db_dbnode')
    op.drop_table('db_dbnode')
    op.drop_index('db_dbgroup_user_id_100f8a51', table_name='db_dbgroup')
    op.drop_index(
        'db_dbgroup_type_23b2a748_like',
        table_name='db_dbgroup',
        postgresql_using='btree',
        postgresql_ops={'type_string': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dbgroup_type_23b2a748', table_name='db_dbgroup')
    op.drop_index(
        'db_dbgroup_name_66c75272_like',
        table_name='db_dbgroup',
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'}
    )
    op.drop_index('db_dbgroup_name_66c75272', table_name='db_dbgroup')
    op.drop_table('db_dbgroup')
    op.drop_index('db_dbauthinfo_dbcomputer_id_424f7ac4', table_name='db_dbauthinfo')
    op.drop_index('db_dbauthinfo_aiidauser_id_0684fdfb', table_name='db_dbauthinfo')
    op.drop_table('db_dbauthinfo')
    op.drop_index(
        'db_dbuser_email_30150b7e_like',
        table_name='db_dbuser',
        postgresql_using='btree',
        postgresql_ops={'email': 'varchar_pattern_ops'}
    )
    op.drop_table('db_dbuser')
    op.drop_index(
        'db_dbsetting_key_1b84beb4_like',
        table_name='db_dbsetting',
        postgresql_using='btree',
        postgresql_ops={'key': 'varchar_pattern_ops'}
    )
    op.drop_table('db_dbsetting')
    op.drop_index(
        'db_dbcomputer_label_bc480bab_like',
        table_name='db_dbcomputer',
        postgresql_using='btree',
        postgresql_ops={'label': 'varchar_pattern_ops'}
    )
    op.drop_table('db_dbcomputer')
