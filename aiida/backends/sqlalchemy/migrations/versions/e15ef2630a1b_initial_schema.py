# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Initial schema

Revision ID: e15ef2630a1b
Revises: 
Create Date: 2017-06-28 17:12:23.327195

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm.session import Session
from aiida.backends.sqlalchemy.utils import install_tc

# revision identifiers, used by Alembic.
revision = 'e15ef2630a1b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('db_dbuser',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('email', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('password', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('is_superuser', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('first_name', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('last_name', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('institution', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('is_staff', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('last_login', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('date_joined', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbuser_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_db_dbuser_email', 'db_dbuser', ['email'], unique=True)
    op.create_table('db_dbworkflow',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('ctime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('mtime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('label', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('nodeversion', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('lastsyncedversion', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('state', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('report', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('module', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('module_class', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('script_path', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('script_md5', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], [u'db_dbuser.id'], name=u'db_dbworkflow_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'db_dbworkflow_pkey'),
    postgresql_ignore_search_path=False
    )
    op.create_index('ix_db_dbworkflow_label', 'db_dbworkflow', ['label'])
    op.create_table('db_dbworkflowstep',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('parent_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('nextcall', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('state', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], [u'db_dbworkflow.id'], name=u'db_dbworkflowstep_parent_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], [u'db_dbuser.id'], name=u'db_dbworkflowstep_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'db_dbworkflowstep_pkey'),
    sa.UniqueConstraint('parent_id', 'name', name=u'db_dbworkflowstep_parent_id_name_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('db_dbcomputer',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('hostname', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('enabled', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('transport_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('scheduler_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('transport_params', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.Column('metadata', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbcomputer_pkey'),
    sa.UniqueConstraint('name', name=u'db_dbcomputer_name_key')
    )
    op.create_table('db_dbauthinfo',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('aiidauser_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('dbcomputer_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('metadata', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.Column('auth_params', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.Column('enabled', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['aiidauser_id'], [u'db_dbuser.id'], name=u'db_dbauthinfo_aiidauser_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['dbcomputer_id'], [u'db_dbcomputer.id'], name=u'db_dbauthinfo_dbcomputer_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbauthinfo_pkey'),
    sa.UniqueConstraint('aiidauser_id', 'dbcomputer_id', name=u'db_dbauthinfo_aiidauser_id_dbcomputer_id_key')
    )
    op.create_table('db_dbgroup',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], [u'db_dbuser.id'], name=u'db_dbgroup_user_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbgroup_pkey'),
    sa.UniqueConstraint('name', 'type', name=u'db_dbgroup_name_type_key')
    )
    op.create_index('ix_db_dbgroup_name', 'db_dbgroup', ['name'])
    op.create_index('ix_db_dbgroup_type', 'db_dbgroup', ['type'])
    op.create_table('db_dbnode',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('label', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('description', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('ctime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('mtime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('nodeversion', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('public', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('attributes', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.Column('extras', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.Column('dbcomputer_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['dbcomputer_id'], [u'db_dbcomputer.id'], name=u'db_dbnode_dbcomputer_id_fkey', ondelete=u'RESTRICT', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['user_id'], [u'db_dbuser.id'], name=u'db_dbnode_user_id_fkey', ondelete=u'RESTRICT', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbnode_pkey'),postgresql_ignore_search_path=False
    )
    op.create_index('ix_db_dbnode_label', 'db_dbnode', ['label'])
    op.create_index('ix_db_dbnode_type', 'db_dbnode', ['type'])
    op.create_table('db_dbgroup_dbnodes',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('dbgroup_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['dbgroup_id'], [u'db_dbgroup.id'], name=u'db_dbgroup_dbnodes_dbgroup_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['dbnode_id'], [u'db_dbnode.id'], name=u'db_dbgroup_dbnodes_dbnode_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbgroup_dbnodes_pkey')
    )
    op.create_table('db_dblock',
    sa.Column('key', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('creation', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('timeout', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('owner', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('key', name=u'db_dblock_pkey')
    )
    op.create_table('db_dbworkflowdata',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('parent_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('data_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('value_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('json_value', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('aiida_obj_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['aiida_obj_id'], [u'db_dbnode.id'], name=u'db_dbworkflowdata_aiida_obj_id_fkey'),
    sa.ForeignKeyConstraint(['parent_id'], [u'db_dbworkflow.id'], name=u'db_dbworkflowdata_parent_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'db_dbworkflowdata_pkey'),
    sa.UniqueConstraint('parent_id', 'name', 'data_type', name=u'db_dbworkflowdata_parent_id_name_data_type_key')
    )
    op.create_table('db_dblink',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('input_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('output_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('label', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['input_id'], [u'db_dbnode.id'], name=u'db_dblink_input_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['output_id'], [u'db_dbnode.id'], name=u'db_dblink_output_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dblink_pkey'),
    )
    op.create_index('ix_db_dblink_label', 'db_dblink', ['label'])
    op.create_table('db_dbworkflowstep_calculations',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('dbworkflowstep_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['dbnode_id'], [u'db_dbnode.id'], name=u'db_dbworkflowstep_calculations_dbnode_id_fkey'),
    sa.ForeignKeyConstraint(['dbworkflowstep_id'], [u'db_dbworkflowstep.id'], name=u'db_dbworkflowstep_calculations_dbworkflowstep_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'db_dbworkflowstep_calculations_pkey'),
    sa.UniqueConstraint('dbworkflowstep_id', 'dbnode_id', name=u'db_dbworkflowstep_calculations_dbworkflowstep_id_dbnode_id_key')
    )
    op.create_table('db_dbpath',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('parent_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('child_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('depth', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('entry_edge_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('direct_edge_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('exit_edge_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['child_id'], [u'db_dbnode.id'], name=u'db_dbpath_child_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['parent_id'], [u'db_dbnode.id'], name=u'db_dbpath_parent_id_fkey', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbpath_pkey')
    )
    op.create_table('db_dbcalcstate',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('state', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['dbnode_id'], [u'db_dbnode.id'], name=u'db_dbcalcstate_dbnode_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbcalcstate_pkey'),
    sa.UniqueConstraint('dbnode_id', 'state', name=u'db_dbcalcstate_dbnode_id_state_key')
    )
    op.create_index('ix_db_dbcalcstate_state', 'db_dbcalcstate', ['state'])
    op.create_table('db_dbsetting',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('key', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('val', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbsetting_pkey'),
    sa.UniqueConstraint('key', name=u'db_dbsetting_key_key')
    )
    op.create_index('ix_db_dbsetting_key', 'db_dbsetting', ['key'])
    op.create_table('db_dbcomment',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('uuid', postgresql.UUID(), autoincrement=False, nullable=True),
    sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('ctime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('mtime', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('content', sa.TEXT(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['dbnode_id'], [u'db_dbnode.id'], name=u'db_dbcomment_dbnode_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['user_id'], [u'db_dbuser.id'], name=u'db_dbcomment_user_id_fkey', ondelete=u'CASCADE', initially=u'DEFERRED', deferrable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dbcomment_pkey')
    )
    op.create_table('db_dblog',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('loggername', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('levelname', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('objname', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    sa.Column('objpk', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('message', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('metadata', postgresql.JSONB(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name=u'db_dblog_pkey')
    )
    op.create_index('ix_db_dblog_levelname', 'db_dblog', ['levelname'])
    op.create_index('ix_db_dblog_loggername', 'db_dblog', ['loggername'])
    op.create_index('ix_db_dblog_objname', 'db_dblog', ['objname'])
    op.create_index('ix_db_dblog_objpk', 'db_dblog', ['objpk'])
    op.create_table('db_dbworkflowstep_sub_workflows',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('dbworkflowstep_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('dbworkflow_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['dbworkflow_id'], [u'db_dbworkflow.id'], name=u'db_dbworkflowstep_sub_workflows_dbworkflow_id_fkey'),
    sa.ForeignKeyConstraint(['dbworkflowstep_id'], [u'db_dbworkflowstep.id'], name=u'db_dbworkflowstep_sub_workflows_dbworkflowstep_id_fkey'),
    sa.PrimaryKeyConstraint('id', name=u'db_dbworkflowstep_sub_workflows_pkey'),
    sa.UniqueConstraint('dbworkflowstep_id', 'dbworkflow_id', name=u'db_dbworkflowstep_sub_workflo_dbworkflowstep_id_dbworkflow__key')
    )
    # I get the session using the alembic connection
    # (Keep in mind that alembic uses the AiiDA SQLA
    # session)
    session = Session(bind=op.get_bind())
    install_tc(session)


def downgrade():
    op.drop_table('db_dbworkflowstep_calculations')
    op.drop_table('db_dbworkflowstep_sub_workflows')
    op.drop_table('db_dbworkflowdata')
    op.drop_table('db_dbworkflowstep')
    op.drop_table('db_dbworkflow')
    op.drop_table('db_dbgroup_dbnodes')
    op.drop_table('db_dbgroup')
    op.drop_table('db_dblink')
    op.drop_table('db_dbpath')
    op.drop_table('db_dbcalcstate')
    op.drop_table('db_dbcomment')
    op.drop_table('db_dbnode')
    op.drop_table('db_dbauthinfo')
    op.drop_table('db_dbuser')
    op.drop_table('db_dbcomputer')
    op.drop_table('db_dblog')
    op.drop_table('db_dbsetting')
    op.drop_table('db_dblock')
