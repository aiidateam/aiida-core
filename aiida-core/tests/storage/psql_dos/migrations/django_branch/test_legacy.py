###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migrations of legacy django databases.

In django, it is not possible to explicitly specify constraints/indexes and their names,
instead they are implicitly created by internal "auto-generation" code
(as opposed to sqlalchemy, where one can explicitly specify the names).
For a specific django version, this auto-generation code is deterministic,
however, over time it has changed.
So is not possible to know declaratively exactly what constraints/indexes are present on a users database,
withtout knowing the exact django version that created it (and run migrations).
Therefore, we need to check that the migration code handles this correctly.
"""

import sqlalchemy as sa

from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_v0x_django_0003(perform_migrations: PsqlDosMigrator, reflect_schema, data_regression):
    """Test against an archive database schema, created in aiida-core v0.x, at revision django_0003."""
    metadata = generate_schema()
    connection = perform_migrations.connection
    metadata.create_all(connection.engine)
    with perform_migrations._migration_context() as context:
        assert context.script
        context.stamp(context.script, 'django@django_0003')
    connection.commit()

    perform_migrations.migrate_up('django@django_0050')
    data_regression.check(reflect_schema(perform_migrations.profile))


def generate_schema() -> sa.MetaData:
    """This database schema was reverse-engineered from an archive database,
    created in aiida-core v0.x, at revision django_0003.
    """
    metadata = sa.MetaData()
    sa.Table('auth_group', metadata, sa.Column('id', sa.Integer, primary_key=True))
    sa.Table('auth_group_permissions', metadata, sa.Column('id', sa.Integer, primary_key=True))
    sa.Table('auth_permission', metadata, sa.Column('id', sa.Integer, primary_key=True))
    sa.Table('django_content_type', metadata, sa.Column('id', sa.Integer, primary_key=True))
    sa.Table('django_migrations', metadata, sa.Column('id', sa.Integer, primary_key=True))
    sa.Table(
        'db_dbattribute',
        metadata,
        sa.Column('bval', sa.Boolean(), nullable=True),
        sa.Column('datatype', sa.String(length=10), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('dval', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fval', sa.Float(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ival', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(length=1024), nullable=False),
        sa.Column('tval', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbattribute_pkey'),
        sa.UniqueConstraint('dbnode_id', 'key', name='db_dbattribute_dbnode_id_10206dc8cec3d0be_uniq'),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbattribute_dbnode_id_783fe2b9b1ee948f_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbattribute_3931108d', 'datatype'),
        sa.Index('db_dbattribute_3c6e0b8a', 'key'),
        sa.Index('db_dbattribute_7a672316', 'dbnode_id'),
        sa.Index(
            'db_dbattribute_datatype_7e609aede7da800c_like',
            'datatype',
            postgresql_ops={'datatype': 'varchar_pattern_ops'},
        ),
        sa.Index('db_dbattribute_key_6936ff5c4f96a1be_like', 'key', postgresql_ops={'key': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbauthinfo',
        metadata,
        sa.Column('aiidauser_id', sa.Integer(), nullable=False),
        sa.Column('auth_params', sa.Text(), nullable=False),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbauthinfo_pkey'),
        sa.UniqueConstraint('aiidauser_id', 'dbcomputer_id', name='db_dbauthinfo_aiidauser_id_5b91ddd9ac6ddd83_uniq'),
        sa.ForeignKeyConstraint(
            ['aiidauser_id'],
            ['db_dbuser.id'],
            name='db_dbauthinfo_aiidauser_id_b4dbd2ecdabaa58_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'],
            ['db_dbcomputer.id'],
            name='db_dbauthinfo_dbcomputer_id_be3c9b99107479b_fk_db_dbcomputer_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbauthinfo_669c815a', 'aiidauser_id'),
        sa.Index('db_dbauthinfo_9ed6a91c', 'dbcomputer_id'),
    )
    sa.Table(
        'db_dbcalcstate',
        metadata,
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(length=25), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcalcstate_pkey'),
        sa.UniqueConstraint('dbnode_id', 'state', name='db_dbcalcstate_dbnode_id_45de92d4e5e6b644_uniq'),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbcalcstate_dbnode_id_5ab286e6811907a3_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbcalcstate_7a672316', 'dbnode_id'),
        sa.Index('db_dbcalcstate_9ed39e2e', 'state'),
        sa.Index(
            'db_dbcalcstate_state_7b15f131504dbe38_like', 'state', postgresql_ops={'state': 'varchar_pattern_ops'}
        ),
    )
    sa.Table(
        'db_dbcomment',
        metadata,
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcomment_pkey'),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbcomment_dbnode_id_e225ac462eb8f6c_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbcomment_user_id_2e215134d026c3a3_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbcomment_7a672316', 'dbnode_id'),
        sa.Index('db_dbcomment_e8701ad4', 'user_id'),
    )
    sa.Table(
        'db_dbcomputer',
        metadata,
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('hostname', sa.String(length=255), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('scheduler_type', sa.String(length=255), nullable=False),
        sa.Column('transport_params', sa.Text(), nullable=False),
        sa.Column('transport_type', sa.String(length=255), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbcomputer_pkey'),
        sa.UniqueConstraint('name', name='db_dbcomputer_name_key'),
        sa.Index('db_dbcomputer_name_538c8da7bbe500af_like', 'name', postgresql_ops={'name': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbextra',
        metadata,
        sa.Column('bval', sa.Boolean(), nullable=True),
        sa.Column('datatype', sa.String(length=10), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('dval', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fval', sa.Float(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ival', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(length=1024), nullable=False),
        sa.Column('tval', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbextra_pkey'),
        sa.UniqueConstraint('dbnode_id', 'key', name='db_dbextra_dbnode_id_2a99ce873931fdd4_uniq'),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbextra_dbnode_id_c556b194c79dec1_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbextra_3931108d', 'datatype'),
        sa.Index('db_dbextra_3c6e0b8a', 'key'),
        sa.Index('db_dbextra_7a672316', 'dbnode_id'),
        sa.Index(
            'db_dbextra_datatype_12730358b2c29a0a_like', 'datatype', postgresql_ops={'datatype': 'varchar_pattern_ops'}
        ),
        sa.Index('db_dbextra_key_67f77eb2ec05ed40_like', 'key', postgresql_ops={'key': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbgroup',
        metadata,
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbgroup_pkey'),
        sa.UniqueConstraint('name', 'type', name='db_dbgroup_name_680159c7377fefd_uniq'),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbgroup_user_id_698e239e754dccc5_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbgroup_599dcce2', 'type'),
        sa.Index('db_dbgroup_b068931c', 'name'),
        sa.Index('db_dbgroup_e8701ad4', 'user_id'),
        sa.Index('db_dbgroup_name_30351f1c64285f22_like', 'name', postgresql_ops={'name': 'varchar_pattern_ops'}),
        sa.Index('db_dbgroup_type_49745d6ede76abdd_like', 'type', postgresql_ops={'type': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbgroup_dbnodes',
        metadata,
        sa.Column('dbgroup_id', sa.Integer(), nullable=False),
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbgroup_dbnodes_pkey'),
        sa.UniqueConstraint('dbgroup_id', 'dbnode_id', name='db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key'),
        sa.ForeignKeyConstraint(
            ['dbgroup_id'],
            ['db_dbgroup.id'],
            name='db_dbgroup_dbnodes_dbgroup_id_32d69f1acbc4c03c_fk_db_dbgroup_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbgroup_dbnodes_dbnode_id_53a1829a1973b99c_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbgroup_dbnodes_7a672316', 'dbnode_id'),
        sa.Index('db_dbgroup_dbnodes_a0b4eda0', 'dbgroup_id'),
    )
    sa.Table(
        'db_dblink',
        metadata,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('input_id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('output_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dblink_pkey'),
        sa.ForeignKeyConstraint(
            ['input_id'],
            ['db_dbnode.id'],
            name='db_dblink_input_id_6feafb02380ed56f_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['output_id'],
            ['db_dbnode.id'],
            name='db_dblink_output_id_6345a663e713ed93_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dblink_599dcce2', 'type'),
        sa.Index('db_dblink_b082bddd', 'input_id'),
        sa.Index('db_dblink_d304ba20', 'label'),
        sa.Index('db_dblink_f7f1d83a', 'output_id'),
        sa.Index('db_dblink_label_8f8811d475657bc_like', 'label', postgresql_ops={'label': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dblock',
        metadata,
        sa.Column('creation', sa.DateTime(timezone=True), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('owner', sa.String(length=255), nullable=False),
        sa.Column('timeout', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('key', name='db_dblock_pkey'),
        sa.Index('db_dblock_key_47b06099dbb553de_like', 'key', postgresql_ops={'key': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dblog',
        metadata,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('levelname', sa.String(length=50), nullable=False),
        sa.Column('loggername', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('metadata', sa.Text(), nullable=False),
        sa.Column('objname', sa.String(length=255), nullable=False),
        sa.Column('objpk', sa.Integer(), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dblog_pkey'),
        sa.Index('db_dblog_269f51f9', 'levelname'),
        sa.Index('db_dblog_358be7bf', 'loggername'),
        sa.Index('db_dblog_850eed5f', 'objpk'),
        sa.Index('db_dblog_e3898037', 'objname'),
        sa.Index(
            'db_dblog_levelname_14b334f2645c4b06_like', 'levelname', postgresql_ops={'levelname': 'varchar_pattern_ops'}
        ),
        sa.Index(
            'db_dblog_loggername_4f4ecb812e82233_like',
            'loggername',
            postgresql_ops={'loggername': 'varchar_pattern_ops'},
        ),
        sa.Index(
            'db_dblog_objname_704cbe43c1c08fe5_like', 'objname', postgresql_ops={'objname': 'varchar_pattern_ops'}
        ),
    )
    sa.Table(
        'db_dbnode',
        metadata,
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('dbcomputer_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('nodeversion', sa.Integer(), nullable=False),
        sa.Column('public', sa.Boolean(), nullable=False),
        sa.Column('type', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbnode_pkey'),
        sa.ForeignKeyConstraint(
            ['dbcomputer_id'],
            ['db_dbcomputer.id'],
            name='db_dbnode_dbcomputer_id_2195c2d4d9b222ff_fk_db_dbcomputer_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbnode_user_id_43fd81cadf67f183_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbnode_599dcce2', 'type'),
        sa.Index('db_dbnode_9ed6a91c', 'dbcomputer_id'),
        sa.Index('db_dbnode_d304ba20', 'label'),
        sa.Index('db_dbnode_e8701ad4', 'user_id'),
        sa.Index('db_dbnode_label_6242931c5b984b78_like', 'label', postgresql_ops={'label': 'varchar_pattern_ops'}),
        sa.Index('db_dbnode_type_4cda33f938ccd765_like', 'type', postgresql_ops={'type': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbpath',
        metadata,
        sa.Column('child_id', sa.Integer(), nullable=False),
        sa.Column('depth', sa.Integer(), nullable=False),
        sa.Column('direct_edge_id', sa.Integer(), nullable=True),
        sa.Column('entry_edge_id', sa.Integer(), nullable=True),
        sa.Column('exit_edge_id', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbpath_pkey'),
        sa.ForeignKeyConstraint(
            ['child_id'],
            ['db_dbnode.id'],
            name='db_dbpath_child_id_29b8c02ce4515a02_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbnode.id'],
            name='db_dbpath_parent_id_56b6292fab1ae2a1_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbpath_6be37982', 'parent_id'),
        sa.Index('db_dbpath_f36263a3', 'child_id'),
    )
    sa.Table(
        'db_dbsetting',
        metadata,
        sa.Column('bval', sa.Boolean(), nullable=True),
        sa.Column('datatype', sa.String(length=10), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('dval', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fval', sa.Float(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ival', sa.Integer(), nullable=True),
        sa.Column('key', sa.String(length=1024), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tval', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbsetting_pkey'),
        sa.UniqueConstraint('key', name='db_dbsetting_key_4cac773d062e1744_uniq'),
        sa.Index('db_dbsetting_3931108d', 'datatype'),
        sa.Index('db_dbsetting_3c6e0b8a', 'key'),
        sa.Index(
            'db_dbsetting_datatype_50c0180f460a7006_like',
            'datatype',
            postgresql_ops={'datatype': 'varchar_pattern_ops'},
        ),
        sa.Index('db_dbsetting_key_4cac773d062e1744_like', 'key', postgresql_ops={'key': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbuser',
        metadata,
        sa.Column('date_joined', sa.DateTime(timezone=True), nullable=False),
        sa.Column('email', sa.String(length=75), nullable=False),
        sa.Column('first_name', sa.String(length=254), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('institution', sa.String(length=254), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_staff', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_name', sa.String(length=254), nullable=False),
        sa.Column('password', sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbuser_pkey'),
        sa.UniqueConstraint('email', name='db_dbuser_email_key'),
        sa.Index('db_dbuser_email_e02af7a860b2501_like', 'email', postgresql_ops={'email': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbuser_groups',
        metadata,
        sa.Column('dbuser_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbuser_groups_pkey'),
        sa.UniqueConstraint('dbuser_id', 'group_id', name='db_dbuser_groups_dbuser_id_group_id_key'),
        sa.ForeignKeyConstraint(
            ['dbuser_id'],
            ['db_dbuser.id'],
            name='db_dbuser_groups_dbuser_id_6024db9daf8ecba_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['group_id'],
            ['auth_group.id'],
            name='db_dbuser_groups_group_id_78e325354186e2b_fk_auth_group_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbuser_groups_0e939a4f', 'group_id'),
        sa.Index('db_dbuser_groups_b2c441d1', 'dbuser_id'),
    )
    sa.Table(
        'db_dbuser_user_permissions',
        metadata,
        sa.Column('dbuser_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbuser_user_permissions_pkey'),
        sa.UniqueConstraint(
            'dbuser_id', 'permission_id', name='db_dbuser_user_permissions_dbuser_id_permission_id_key'
        ),
        sa.ForeignKeyConstraint(
            ['permission_id'],
            ['auth_permission.id'],
            name='db_dbuser__permission_id_77342b1287a009fe_fk_auth_permission_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['dbuser_id'],
            ['db_dbuser.id'],
            name='db_dbuser_user_permi_dbuser_id_325dd28d66e30790_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbuser_user_permissions_8373b171', 'permission_id'),
        sa.Index('db_dbuser_user_permissions_b2c441d1', 'dbuser_id'),
    )
    sa.Table(
        'db_dbworkflow',
        metadata,
        sa.Column('ctime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=False),
        sa.Column('lastsyncedversion', sa.Integer(), nullable=False),
        sa.Column('module', sa.Text(), nullable=False),
        sa.Column('module_class', sa.Text(), nullable=False),
        sa.Column('mtime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('nodeversion', sa.Integer(), nullable=False),
        sa.Column('report', sa.Text(), nullable=False),
        sa.Column('script_md5', sa.String(length=255), nullable=False),
        sa.Column('script_path', sa.Text(), nullable=False),
        sa.Column('state', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflow_pkey'),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbworkflow_user_id_745f0415fc9f135a_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbworkflow_d304ba20', 'label'),
        sa.Index('db_dbworkflow_e8701ad4', 'user_id'),
        sa.Index('db_dbworkflow_label_55e5f0a232defa37_like', 'label', postgresql_ops={'label': 'varchar_pattern_ops'}),
    )
    sa.Table(
        'db_dbworkflowdata',
        metadata,
        sa.Column('aiida_obj_id', sa.Integer(), nullable=True),
        sa.Column('data_type', sa.String(length=255), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('json_value', sa.Text(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('value_type', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowdata_pkey'),
        sa.UniqueConstraint('data_type', 'name', 'parent_id', name='db_dbworkflowdata_parent_id_1f60f874e728c5f0_uniq'),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbworkflow.id'],
            name='db_dbworkflowdat_parent_id_74e8079e6f1c8441_fk_db_dbworkflow_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['aiida_obj_id'],
            ['db_dbnode.id'],
            name='db_dbworkflowdata_aiida_obj_id_28130672924934ca_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbworkflowdata_668c0731', 'aiida_obj_id'),
        sa.Index('db_dbworkflowdata_6be37982', 'parent_id'),
    )
    sa.Table(
        'db_dbworkflowstep',
        metadata,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('nextcall', sa.String(length=255), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(length=255), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_pkey'),
        sa.UniqueConstraint('name', 'parent_id', name='db_dbworkflowstep_parent_id_57c505d36f0f2dd3_uniq'),
        sa.ForeignKeyConstraint(
            ['parent_id'],
            ['db_dbworkflow.id'],
            name='db_dbworkflowste_parent_id_33a89b7df301ebbd_fk_db_dbworkflow_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['db_dbuser.id'],
            name='db_dbworkflowstep_user_id_32681ba845c275dc_fk_db_dbuser_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbworkflowstep_6be37982', 'parent_id'),
        sa.Index('db_dbworkflowstep_e8701ad4', 'user_id'),
    )
    sa.Table(
        'db_dbworkflowstep_calculations',
        metadata,
        sa.Column('dbnode_id', sa.Integer(), nullable=False),
        sa.Column('dbworkflowstep_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_calculations_pkey'),
        sa.UniqueConstraint(
            'dbnode_id', 'dbworkflowstep_id', name='db_dbworkflowstep_calculations_dbworkflowstep_id_dbnode_id_key'
        ),
        sa.ForeignKeyConstraint(
            ['dbworkflowstep_id'],
            ['db_dbworkflowstep.id'],
            name='db_d_dbworkflowstep_id_1f84ab0dccc60762_fk_db_dbworkflowstep_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['dbnode_id'],
            ['db_dbnode.id'],
            name='db_dbworkflowstep_ca_dbnode_id_5ac7aa3704de0639_fk_db_dbnode_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbworkflowstep_calculations_1df98a0a', 'dbworkflowstep_id'),
        sa.Index('db_dbworkflowstep_calculations_7a672316', 'dbnode_id'),
    )
    sa.Table(
        'db_dbworkflowstep_sub_workflows',
        metadata,
        sa.Column('dbworkflow_id', sa.Integer(), nullable=False),
        sa.Column('dbworkflowstep_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='db_dbworkflowstep_sub_workflows_pkey'),
        sa.UniqueConstraint(
            'dbworkflow_id', 'dbworkflowstep_id', name='db_dbworkflowstep_sub_workflo_dbworkflowstep_id_dbworkflow__key'
        ),
        sa.ForeignKeyConstraint(
            ['dbworkflowstep_id'],
            ['db_dbworkflowstep.id'],
            name='db_d_dbworkflowstep_id_7798ce4345e8e576_fk_db_dbworkflowstep_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.ForeignKeyConstraint(
            ['dbworkflow_id'],
            ['db_dbworkflow.id'],
            name='db_dbworkflo_dbworkflow_id_4a3395f4c392c63c_fk_db_dbworkflow_id',
            deferrable=True,
            initially='DEFERRED',
        ),
        sa.Index('db_dbworkflowstep_sub_workflows_1df98a0a', 'dbworkflowstep_id'),
        sa.Index('db_dbworkflowstep_sub_workflows_b6a7b7c8', 'dbworkflow_id'),
    )
    return metadata
