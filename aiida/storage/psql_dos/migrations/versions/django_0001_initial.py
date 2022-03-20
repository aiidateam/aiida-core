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
"""Initial django schema

Revision ID: django_0001
Revises:
Create Date: 2017-06-28 17:12:23.327195

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'django_0001'
down_revision = None
branch_labels = ('django',)
depends_on = None


def upgrade():
    """Migrations for the upgrade."""

    # dummy django tables
    op.create_table(
        'auth_group',
        sa.Column('id', sa.INTEGER(), nullable=False, primary_key=True),
    )
    op.create_table(
        'auth_group_permissions',
        sa.Column('id', sa.INTEGER(), nullable=False, primary_key=True),
    )
    op.create_table(
        'auth_permission',
        sa.Column('id', sa.INTEGER(), nullable=False, primary_key=True),
    )
    op.create_table(
        'django_content_type',
        sa.Column('id', sa.INTEGER(), nullable=False, primary_key=True),
    )
    op.create_table(
        'django_migrations',
        sa.Column('id', sa.INTEGER(), nullable=False, primary_key=True),
    )

    op.create_table(
        'db_dbuser',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbuser_pkey'),
        sa.Column('email', sa.VARCHAR(length=75), nullable=False),
        sa.Column('password', sa.VARCHAR(length=128), nullable=False),
        sa.Column('is_superuser', sa.BOOLEAN(), nullable=False),
        sa.Column('first_name', sa.VARCHAR(length=254), nullable=False),
        sa.Column('last_name', sa.VARCHAR(length=254), nullable=False),
        sa.Column('institution', sa.VARCHAR(length=254), nullable=False),
        sa.Column('is_staff', sa.BOOLEAN(), nullable=False),
        sa.Column('is_active', sa.BOOLEAN(), nullable=False),
        sa.Column('last_login', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('date_joined', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('email', name='db_dbuser_email_key'),
        sa.Index(
            'db_dbuser_email_30150b7e_like',
            'email',
            postgresql_using='btree',
            postgresql_ops={'email': 'varchar_pattern_ops'},
        ),
    )

    op.create_table(
        'db_dbcomputer',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcomputer_pkey'),
        sa.Column('uuid', sa.VARCHAR(length=36), nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('hostname', sa.VARCHAR(length=255), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('enabled', sa.BOOLEAN(), nullable=False),
        sa.Column('transport_type', sa.VARCHAR(length=255), nullable=False),
        sa.Column('scheduler_type', sa.VARCHAR(length=255), nullable=False),
        sa.Column('transport_params', sa.TEXT(), nullable=False),
        sa.Column('metadata', sa.TEXT(), nullable=False),
        sa.UniqueConstraint('name', name='db_dbcomputer_name_key'),
        sa.Index(
            'db_dbcomputer_name_f1800b1a_like',
            'name',
            postgresql_using='btree',
            postgresql_ops={'name': 'varchar_pattern_ops'},
        ),
    )

    op.create_table(
        'db_dbgroup',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbgroup_pkey'),
        sa.Column('uuid', sa.VARCHAR(length=36), nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('type', sa.VARCHAR(length=255), nullable=False),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.UniqueConstraint('name', 'type', name='db_dbgroup_name_type_12656f33_uniq'),
        sa.Index('db_dbgroup_name_66c75272', 'name'),
        sa.Index('db_dbgroup_type_23b2a748', 'type'),
        sa.Index('db_dbgroup_user_id_100f8a51', 'user_id'),
        sa.Index(
            'db_dbgroup_name_66c75272_like',
            'name',
            postgresql_using='btree',
            postgresql_ops={'name': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dbgroup_type_23b2a748_like',
            'type',
            postgresql_using='btree',
            postgresql_ops={'type': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbgroup_user_id_100f8a51_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dblock',
        sa.Column('key', sa.VARCHAR(length=255), nullable=False),
        sa.PrimaryKeyConstraint('key', name='db_dblock_pkey'),
        sa.Column('creation', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('timeout', sa.INTEGER(), nullable=False),
        sa.Column('owner', sa.VARCHAR(length=255), nullable=False),
        sa.Index(
            'db_dblock_key_048c6767_like',
            'key',
            postgresql_using='btree',
            postgresql_ops={'key': 'varchar_pattern_ops'},
        ),
    )

    op.create_table(
        'db_dblog',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dblog_pkey'),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('loggername', sa.VARCHAR(length=255), nullable=False),
        sa.Column('levelname', sa.VARCHAR(length=50), nullable=False),
        sa.Column('objname', sa.VARCHAR(length=255), nullable=False),
        sa.Column('objpk', sa.INTEGER(), nullable=True),
        sa.Column('message', sa.TEXT(), nullable=False),
        sa.Column('metadata', sa.TEXT(), nullable=False),
        sa.Index('db_dblog_levelname_ad5dc346', 'levelname'),
        sa.Index('db_dblog_loggername_00b5ba16', 'loggername'),
        sa.Index('db_dblog_objname_69932b1e', 'objname'),
        sa.Index('db_dblog_objpk_fc47afa9', 'objpk'),
        sa.Index(
            'db_dblog_levelname_ad5dc346_like',
            'levelname',
            postgresql_using='btree',
            postgresql_ops={'levelname': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dblog_loggername_00b5ba16_like',
            'loggername',
            postgresql_using='btree',
            postgresql_ops={'loggername': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dblog_objname_69932b1e_like',
            'objname',
            postgresql_using='btree',
            postgresql_ops={'objname': 'varchar_pattern_ops'},
        ),
    )

    op.create_table(
        'db_dbnode',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbnode_pkey'),
        sa.Column('uuid', sa.VARCHAR(length=36), nullable=False),
        sa.Column('type', sa.VARCHAR(length=255), nullable=False),
        sa.Column('label', sa.VARCHAR(length=255), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('ctime', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('mtime', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('nodeversion', sa.INTEGER(), nullable=False),
        sa.Column('public', sa.BOOLEAN(), nullable=False),
        sa.Column('dbcomputer_id', sa.INTEGER(), nullable=True),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Index('db_dbnode_dbcomputer_id_315372a3', 'dbcomputer_id'),
        sa.Index('db_dbnode_label_6469539e', 'label'),
        sa.Index('db_dbnode_type_a8ce9753', 'type'),
        sa.Index('db_dbnode_user_id_12e7aeaf', 'user_id'),
        sa.Index(
            'db_dbnode_label_6469539e_like',
            'label',
            postgresql_using='btree',
            postgresql_ops={'label': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dbnode_type_a8ce9753_like',
            'type',
            postgresql_using='btree',
            postgresql_ops={'type': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'],
            ['db_dbcomputer.id'],
            name='db_dbnode_dbcomputer_id_315372a3_fk_db_dbcomputer_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbnode_user_id_12e7aeaf_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbattribute',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbattribute_pkey'),
        sa.Column('datatype', sa.VARCHAR(length=10), nullable=False),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.Column('key', sa.VARCHAR(length=1024), nullable=False),
        sa.Column('bval', sa.BOOLEAN(), nullable=True),
        sa.Column('ival', sa.INTEGER(), nullable=True),
        sa.Column('fval', sa.FLOAT(), nullable=True),
        sa.Column('tval', sa.TEXT(), nullable=False),
        sa.Column('dval', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint('dbnode_id', 'key', name='db_dbattribute_dbnode_id_key_c589e447_uniq'),
        sa.Index('db_dbattribute_datatype_91c4dc04', 'datatype'),
        sa.Index('db_dbattribute_dbnode_id_253bf153', 'dbnode_id'),
        sa.Index('db_dbattribute_key_ac2bc4e4', 'key'),
        sa.Index(
            'db_dbattribute_datatype_91c4dc04_like',
            'datatype',
            postgresql_using='btree',
            postgresql_ops={'datatype': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dbattribute_key_ac2bc4e4_like',
            'key',
            postgresql_using='btree',
            postgresql_ops={'key': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbattribute_dbnode_id_253bf153_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
    )

    op.create_table(
        'db_dbextra',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbextra_pkey'),
        sa.Column('datatype', sa.VARCHAR(length=10), nullable=False),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.Column('key', sa.VARCHAR(length=1024), nullable=False),
        sa.Column('bval', sa.BOOLEAN(), nullable=True),
        sa.Column('ival', sa.INTEGER(), nullable=True),
        sa.Column('fval', sa.FLOAT(), nullable=True),
        sa.Column('tval', sa.TEXT(), nullable=False),
        sa.Column('dval', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint('dbnode_id', 'key', name='db_dbextra_dbnode_id_key_aa56fd37_uniq'),
        sa.Index('db_dbextra_datatype_2eba38c6', 'datatype'),
        sa.Index('db_dbextra_dbnode_id_c7fe8961', 'dbnode_id'),
        sa.Index('db_dbextra_key_b1a8abc6', 'key'),
        sa.Index(
            'db_dbextra_datatype_2eba38c6_like',
            'datatype',
            postgresql_using='btree',
            postgresql_ops={'datatype': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dbextra_key_b1a8abc6_like',
            'key',
            postgresql_using='btree',
            postgresql_ops={'key': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbextra_dbnode_id_c7fe8961_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
    )

    op.create_table(
        'db_dblink',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dblink_pkey'),
        sa.Column('input_id', sa.INTEGER(), nullable=False),
        sa.Column('output_id', sa.INTEGER(), nullable=False),
        sa.Column('label', sa.VARCHAR(length=255), nullable=False),
        sa.UniqueConstraint('input_id', 'output_id', name='db_dblink_input_id_output_id_fbe99cb5_uniq'),
        sa.UniqueConstraint('output_id', 'label', name='db_dblink_output_id_label_00bdb9c7_uniq'),
        sa.Index('db_dblink_input_id_9245bd73', 'input_id'),
        sa.Index('db_dblink_label_f1343cfb', 'label'),
        sa.Index('db_dblink_output_id_c0167528', 'output_id'),
        sa.Index(
            'db_dblink_label_f1343cfb_like',
            'label',
            postgresql_using='btree',
            postgresql_ops={'label': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['input_id'],
            ['db_dbnode.id'],
            name='db_dblink_input_id_9245bd73_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['output_id'],
            ['db_dbnode.id'],
            name='db_dblink_output_id_c0167528_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbgroup_dbnodes',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbgroup_dbnodes_pkey'),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.Column('dbgroup_id', sa.INTEGER(), nullable=False),
        sa.UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_eee23cce_uniq'),
        sa.Index('db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d', 'dbgroup_id'),
        sa.Index('db_dbgroup_dbnodes_dbnode_id_118b9439', 'dbnode_id'),
        sa.ForeignKeyConstraint(
            ['dbgroup_id'],
            ['db_dbgroup.id'],
            name='db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d_fk_db_dbgroup_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbgroup_dbnodes_dbnode_id_118b9439_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbcalcstate',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcalcstate_pkey'),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.Column('state', sa.VARCHAR(length=25), nullable=False),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.UniqueConstraint('dbnode_id', 'state', name='db_dbcalcstate_dbnode_id_state_b4a14db3_uniq'),
        sa.Index('db_dbcalcstate_dbnode_id_f217a84c', 'dbnode_id'),
        sa.Index('db_dbcalcstate_state_0bf54584', 'state'),
        sa.Index(
            'db_dbcalcstate_state_0bf54584_like',
            'state',
            postgresql_using='btree',
            postgresql_ops={'state': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbcalcstate_dbnode_id_f217a84c_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
    )

    op.create_table(
        'db_dbcomment',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcomment_pkey'),
        sa.Column('uuid', sa.VARCHAR(length=36), nullable=False),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.Column('ctime', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('mtime', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('content', sa.TEXT(), nullable=False),
        sa.Index('db_dbcomment_dbnode_id_3b812b6b', 'dbnode_id'),
        sa.Index('db_dbcomment_user_id_8ed5e360', 'user_id'),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbcomment_dbnode_id_3b812b6b_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbcomment_user_id_8ed5e360_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
    )

    op.create_table(
        'db_dbpath',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbpath_pkey'),
        sa.Column('parent_id', sa.INTEGER(), nullable=False),
        sa.Column('child_id', sa.INTEGER(), nullable=False),
        sa.Column('depth', sa.INTEGER(), nullable=False),
        sa.Column('entry_edge_id', sa.INTEGER(), nullable=True),
        sa.Column('direct_edge_id', sa.INTEGER(), nullable=True),
        sa.Column('exit_edge_id', sa.INTEGER(), nullable=True),
        sa.Index('db_dbpath_child_id_d8228636', 'child_id'),
        sa.Index('db_dbpath_parent_id_3b82d6c8', 'parent_id'),
        sa.ForeignKeyConstraint(
            ['child_id'],
            ['db_dbnode.id'],
            name='db_dbpath_child_id_d8228636_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbnode.id'],
            name='db_dbpath_parent_id_3b82d6c8_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbsetting',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbsetting_pkey'),
        sa.Column('key', sa.VARCHAR(length=1024), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('datatype', sa.VARCHAR(length=10), nullable=False),
        sa.Column('bval', sa.BOOLEAN(), nullable=True),
        sa.Column('ival', sa.INTEGER(), nullable=True),
        sa.Column('fval', sa.FLOAT(), nullable=True),
        sa.Column('tval', sa.TEXT(), nullable=False),
        sa.Column('dval', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint('key', name='db_dbsetting_key_1b84beb4_uniq'),
        sa.Index('db_dbsetting_datatype_49f4397c', 'datatype'),
        sa.Index('db_dbsetting_key_1b84beb4', 'key'),
        sa.Index(
            'db_dbsetting_datatype_49f4397c_like',
            'datatype',
            postgresql_using='btree',
            postgresql_ops={'datatype': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dbsetting_key_1b84beb4_like',
            'key',
            postgresql_using='btree',
            postgresql_ops={'key': 'varchar_pattern_ops'},
        ),
    )

    op.create_table(
        'db_dbuser_groups',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbuser_groups_pkey'),
        sa.Column('dbuser_id', sa.INTEGER(), nullable=False),
        sa.Column('group_id', sa.INTEGER(), nullable=False),
        sa.UniqueConstraint('dbuser_id', 'group_id', name='db_dbuser_groups_dbuser_id_group_id_9155eb4f_uniq'),
        sa.Index('db_dbuser_groups_dbuser_id_480b3520', 'dbuser_id'),
        sa.Index('db_dbuser_groups_group_id_8478d87e', 'group_id'),
        sa.ForeignKeyConstraint(
            ['dbuser_id'],
            ['db_dbuser.id'],
            name='db_dbuser_groups_dbuser_id_480b3520_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['auth_group.id'],
            name='db_dbuser_groups_group_id_8478d87e_fk_auth_group_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbuser_user_permissions',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbuser_user_permissions_pkey'),
        sa.Column('dbuser_id', sa.INTEGER(), nullable=False),
        sa.Column('permission_id', sa.INTEGER(), nullable=False),
        sa.UniqueConstraint(
            'dbuser_id', 'permission_id', name='db_dbuser_user_permissio_dbuser_id_permission_id_e6cbabe4_uniq'
        ),
        sa.Index('db_dbuser_user_permissions_dbuser_id_364456ee', 'dbuser_id'),
        sa.Index('db_dbuser_user_permissions_permission_id_c5aafc54', 'permission_id'),
        sa.ForeignKeyConstraint(
            ['dbuser_id'],
            ['db_dbuser.id'],
            name='db_dbuser_user_permissions_dbuser_id_364456ee_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['permission_id'],
            ['auth_permission.id'],
            name='db_dbuser_user_permi_permission_id_c5aafc54_fk_auth_perm',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbworkflow',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflow_pkey'),
        sa.Column('uuid', sa.VARCHAR(length=36), nullable=False),
        sa.Column('ctime', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('mtime', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('label', sa.VARCHAR(length=255), nullable=False),
        sa.Column('description', sa.TEXT(), nullable=False),
        sa.Column('nodeversion', sa.INTEGER(), nullable=False),
        sa.Column('lastsyncedversion', sa.INTEGER(), nullable=False),
        sa.Column('state', sa.VARCHAR(length=255), nullable=False),
        sa.Column('report', sa.TEXT(), nullable=False),
        sa.Column('module', sa.TEXT(), nullable=False),
        sa.Column('module_class', sa.TEXT(), nullable=False),
        sa.Column('script_path', sa.TEXT(), nullable=False),
        sa.Column('script_md5', sa.VARCHAR(length=255), nullable=False),
        sa.Index('db_dbworkflow_label_7368f34a', 'label'),
        sa.Index('db_dbworkflow_user_id_ef1f3251', 'user_id'),
        sa.Index(
            'db_dbworkflow_label_7368f34a_like',
            'label',
            postgresql_using='btree',
            postgresql_ops={'label': 'varchar_pattern_ops'},
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbworkflow_user_id_ef1f3251_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbworkflowstep',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_pkey'),
        sa.Column('parent_id', sa.INTEGER(), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('nextcall', sa.VARCHAR(length=255), nullable=False),
        sa.Column('state', sa.VARCHAR(length=255), nullable=False),
        sa.UniqueConstraint('parent_id', 'name', name='db_dbworkflowstep_parent_id_name_111027e3_uniq'),
        sa.Index('db_dbworkflowstep_parent_id_ffb754d9', 'parent_id'),
        sa.Index('db_dbworkflowstep_user_id_04282431', 'user_id'),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbworkflow.id'],
            name='db_dbworkflowstep_parent_id_ffb754d9_fk_db_dbworkflow_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbworkflowstep_user_id_04282431_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbworkflowdata',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowdata_pkey'),
        sa.Column('parent_id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('time', postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('data_type', sa.VARCHAR(length=255), nullable=False),
        sa.Column('value_type', sa.VARCHAR(length=255), nullable=False),
        sa.Column('json_value', sa.TEXT(), nullable=False),
        sa.Column('aiida_obj_id', sa.INTEGER(), nullable=True),
        sa.UniqueConstraint(
            'parent_id', 'name', 'data_type', name='db_dbworkflowdata_parent_id_name_data_type_a4b50dae_uniq'
        ),
        sa.Index('db_dbworkflowdata_aiida_obj_id_70a2d33b', 'aiida_obj_id'),
        sa.Index('db_dbworkflowdata_parent_id_ff4dbf8d', 'parent_id'),
        sa.ForeignKeyConstraint(
            ['aiida_obj_id'],
            ['db_dbnode.id'],
            name='db_dbworkflowdata_aiida_obj_id_70a2d33b_fk_db_dbnode_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbworkflow.id'],
            name='db_dbworkflowdata_parent_id_ff4dbf8d_fk_db_dbworkflow_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbworkflowstep_calculations',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_calculations_pkey'),
        sa.Column('dbworkflowstep_id', sa.INTEGER(), nullable=False),
        sa.Column('dbnode_id', sa.INTEGER(), nullable=False),
        sa.UniqueConstraint(
            'dbworkflowstep_id', 'dbnode_id', name='db_dbworkflowstep_calcul_dbworkflowstep_id_dbnode_60f50d02_uniq'
        ),
        sa.Index('db_dbworkflowstep_calculations_dbnode_id_0d07b7a7', 'dbnode_id'),
        sa.Index('db_dbworkflowstep_calculations_dbworkflowstep_id_575c3637', 'dbworkflowstep_id'),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbworkflowstep_ca_dbnode_id_0d07b7a7_fk_db_dbnode',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['dbworkflowstep_id'],
            ['db_dbworkflowstep.id'],
            name='db_dbworkflowstep_ca_dbworkflowstep_id_575c3637_fk_db_dbwork',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbworkflowstep_sub_workflows',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_sub_workflows_pkey'),
        sa.Column('dbworkflowstep_id', sa.INTEGER(), nullable=False),
        sa.Column('dbworkflow_id', sa.INTEGER(), nullable=False),
        sa.UniqueConstraint(
            'dbworkflowstep_id',
            'dbworkflow_id',
            name='db_dbworkflowstep_sub_wo_dbworkflowstep_id_dbwork_e9b2b624_uniq',
        ),
        sa.Index('db_dbworkflowstep_sub_workflows_dbworkflow_id_dca4d103', 'dbworkflow_id'),
        sa.Index('db_dbworkflowstep_sub_workflows_dbworkflowstep_id_e183bbb7', 'dbworkflowstep_id'),
        sa.ForeignKeyConstraint(
            ['dbworkflow_id'],
            ['db_dbworkflow.id'],
            name='db_dbworkflowstep_su_dbworkflow_id_dca4d103_fk_db_dbwork',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['dbworkflowstep_id'],
            ['db_dbworkflowstep.id'],
            name='db_dbworkflowstep_su_dbworkflowstep_id_e183bbb7_fk_db_dbwork',
            initially='DEFERRED',
            deferrable=True,
        ),
    )

    op.create_table(
        'db_dbauthinfo',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbauthinfo_pkey'),
        sa.Column('aiidauser_id', sa.INTEGER(), nullable=False),
        sa.Column('dbcomputer_id', sa.INTEGER(), nullable=False),
        sa.Column('metadata', sa.TEXT(), nullable=False),
        sa.Column('auth_params', sa.TEXT(), nullable=False),
        sa.Column('enabled', sa.BOOLEAN(), nullable=False),
        sa.UniqueConstraint(
            'aiidauser_id', 'dbcomputer_id', name='db_dbauthinfo_aiidauser_id_dbcomputer_id_777cdaa8_uniq'
        ),
        sa.Index('db_dbauthinfo_aiidauser_id_0684fdfb', 'aiidauser_id'),
        sa.Index('db_dbauthinfo_dbcomputer_id_424f7ac4', 'dbcomputer_id'),
        sa.ForeignKeyConstraint(
            ['aiidauser_id'],
            ['db_dbuser.id'],
            name='db_dbauthinfo_aiidauser_id_0684fdfb_fk_db_dbuser_id',
            initially='DEFERRED',
            deferrable=True,
        ),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'],
            ['db_dbcomputer.id'],
            name='db_dbauthinfo_dbcomputer_id_424f7ac4_fk_db_dbcomputer_id',
            initially='DEFERRED',
            deferrable=True,
        ),
    )


def downgrade():
    """Migrations for the downgrade."""
    op.drop_table('db_dbauthinfo')
    op.drop_table('db_dbworkflowstep_calculations')
    op.drop_table('db_dbworkflowstep_sub_workflows')
    op.drop_table('db_dbworkflowdata')
    op.drop_table('db_dbworkflowstep')
    op.drop_table('db_dbworkflow')
    op.drop_table('db_dbuser_user_permissions')
    op.drop_table('db_dbuser_groups')
    op.drop_table('db_dbgroup_dbnodes')
    op.drop_table('db_dbgroup')
    op.drop_table('db_dblink')
    op.drop_table('db_dbpath')
    op.drop_table('db_dbcalcstate')
    op.drop_table('db_dbcomment')
    op.drop_table('db_dbattribute')
    op.drop_table('db_dbextra')
    op.drop_table('db_dbnode')
    op.drop_table('db_dbcomputer')
    op.drop_table('db_dblog')
    op.drop_table('db_dbsetting')
    op.drop_table('db_dblock')
    op.drop_table('db_dbuser')

    op.drop_table('auth_group_permissions')
    op.drop_table('auth_permission')
    op.drop_table('auth_group')
    op.drop_table('django_content_type')
    op.drop_table('django_migrations')
