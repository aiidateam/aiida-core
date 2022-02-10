# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Remove legacy workflows

This is similar to migration django_0032

Revision ID: 1b8ed3425af9
Revises: 3d6190594e19
Create Date: 2019-04-03 17:11:44.073582

"""
# Remove when https://github.com/PyCQA/pylint/issues/1931 is fixed
# pylint: disable=no-member,import-error,no-name-in-module
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from aiida.backends.sqlalchemy.migrations.utils.legacy_workflows import export_workflow_data

# revision identifiers, used by Alembic.
revision = '1b8ed3425af9'
down_revision = '3d6190594e19'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    # Clean data
    export_workflow_data(op.get_bind(), op.get_context().opts['aiida_profile'])

    op.drop_table('db_dbworkflowstep_sub_workflows')
    op.drop_table('db_dbworkflowstep_calculations')
    op.drop_table('db_dbworkflowstep')
    op.drop_index('ix_db_dbworkflowdata_aiida_obj_id', table_name='db_dbworkflowdata')
    op.drop_index('ix_db_dbworkflowdata_parent_id', table_name='db_dbworkflowdata')
    op.drop_table('db_dbworkflowdata')
    op.drop_index('ix_db_dbworkflow_label', table_name='db_dbworkflow')
    op.drop_table('db_dbworkflow')


def downgrade():
    """Migrations for the downgrade."""
    op.create_table(
        'db_dbworkflow',
        sa.Column(
            'id',
            sa.INTEGER(),
            server_default=sa.text("nextval('db_dbworkflow_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False
        ),
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
        sa.ForeignKeyConstraint(['user_id'], ['db_dbuser.id'], name='db_dbworkflow_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflow_pkey'),
        sa.UniqueConstraint('uuid', name='db_dbworkflow_uuid_key'),
        postgresql_ignore_search_path=False
    )
    op.create_index('ix_db_dbworkflow_label', 'db_dbworkflow', ['label'], unique=False)
    op.create_table(
        'db_dbworkflowdata', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('parent_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column('data_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('value_type', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('json_value', sa.TEXT(), autoincrement=False, nullable=True),
        sa.Column('aiida_obj_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['aiida_obj_id'], ['db_dbnode.id'], name='db_dbworkflowdata_aiida_obj_id_fkey'),
        sa.ForeignKeyConstraint(['parent_id'], ['db_dbworkflow.id'], name='db_dbworkflowdata_parent_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowdata_pkey'),
        sa.UniqueConstraint('parent_id', 'name', 'data_type', name='db_dbworkflowdata_parent_id_name_data_type_key')
    )
    op.create_index('ix_db_dbworkflowdata_parent_id', 'db_dbworkflowdata', ['parent_id'], unique=False)
    op.create_index('ix_db_dbworkflowdata_aiida_obj_id', 'db_dbworkflowdata', ['aiida_obj_id'], unique=False)
    op.create_table(
        'db_dbworkflowstep', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('parent_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('name', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
        sa.Column('nextcall', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.Column('state', sa.VARCHAR(length=255), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['parent_id'], ['db_dbworkflow.id'], name='db_dbworkflowstep_parent_id_fkey'),
        sa.ForeignKeyConstraint(['user_id'], ['db_dbuser.id'], name='db_dbworkflowstep_user_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_pkey'),
        sa.UniqueConstraint('parent_id', 'name', name='db_dbworkflowstep_parent_id_name_key')
    )
    op.create_table(
        'db_dbworkflowstep_calculations', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('dbworkflowstep_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('dbnode_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['dbnode_id'], ['db_dbnode.id'], name='db_dbworkflowstep_calculations_dbnode_id_fkey'),
        sa.ForeignKeyConstraint(['dbworkflowstep_id'], ['db_dbworkflowstep.id'],
                                name='db_dbworkflowstep_calculations_dbworkflowstep_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_calculations_pkey'),
        sa.UniqueConstraint('dbworkflowstep_id', 'dbnode_id', name='db_dbworkflowstep_calculations_id_dbnode_id_key')
    )
    op.create_table(
        'db_dbworkflowstep_sub_workflows', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column('dbworkflowstep_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column('dbworkflow_id', sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['dbworkflow_id'], ['db_dbworkflow.id'],
                                name='db_dbworkflowstep_sub_workflows_dbworkflow_id_fkey'),
        sa.ForeignKeyConstraint(['dbworkflowstep_id'], ['db_dbworkflowstep.id'],
                                name='db_dbworkflowstep_sub_workflows_dbworkflowstep_id_fkey'),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_sub_workflows_pkey'),
        sa.UniqueConstraint(
            'dbworkflowstep_id', 'dbworkflow_id', name='db_dbworkflowstep_sub_workflows_id_dbworkflow__key'
        )
    )
