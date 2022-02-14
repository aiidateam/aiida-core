# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,no-member,line-too-long
"""Finalise parity of the legacy django branch with the sqlalchemy branch.

1. Recreate schema (non-unique) indexes, with current names.
2. Recreate schema unique constraints, with current names.
3. Recreate foreign key constraints, with current names.
4. Drop the django specific tables

It is of note that a number of foreign keys were missing comparable `ON DELETE` rules in django.
This is because django does not currently add these rules to the database, but instead tries to handle them on the
Python side, see: https://stackoverflow.com/a/35780859/5033292

Revision ID: django_0050
Revises: django_0049

"""
from alembic import op

from aiida.backends.sqlalchemy.migrations.utils import ReflectMigrations

revision = 'django_0050'
down_revision = 'django_0049'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""
    reflect = ReflectMigrations(op)

    # drop all current non-unique indexes, then add the new ones
    for tbl_name in (
        'db_dbauthinfo', 'db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbgroup_dbnodes', 'db_dblink', 'db_dblog',
        'db_dbnode', 'db_dbsetting', 'db_dbuser'
    ):
        reflect.drop_all_indexes(tbl_name)
    for name, tbl_name, column, psql_op in (
        ('db_dbauthinfo_aiidauser_id_0684fdfb', 'db_dbauthinfo', 'aiidauser_id', None),
        ('db_dbauthinfo_dbcomputer_id_424f7ac4', 'db_dbauthinfo', 'dbcomputer_id', None),
        ('db_dbcomment_dbnode_id_3b812b6b', 'db_dbcomment', 'dbnode_id', None),
        ('db_dbcomment_user_id_8ed5e360', 'db_dbcomment', 'user_id', None),
        ('db_dbcomputer_label_bc480bab_like', 'db_dbcomputer', 'label', 'varchar_pattern_ops'),
        ('db_dbgroup_name_66c75272', 'db_dbgroup', 'label', None),
        ('db_dbgroup_name_66c75272_like', 'db_dbgroup', 'label', 'varchar_pattern_ops'),
        ('db_dbgroup_type_23b2a748', 'db_dbgroup', 'type_string', None),
        ('db_dbgroup_type_23b2a748_like', 'db_dbgroup', 'type_string', 'varchar_pattern_ops'),
        ('db_dbgroup_user_id_100f8a51', 'db_dbgroup', 'user_id', None),
        ('db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d', 'db_dbgroup_dbnodes', 'dbgroup_id', None),
        ('db_dbgroup_dbnodes_dbnode_id_118b9439', 'db_dbgroup_dbnodes', 'dbnode_id', None),
        ('db_dblink_input_id_9245bd73', 'db_dblink', 'input_id', None),
        ('db_dblink_label_f1343cfb', 'db_dblink', 'label', None),
        ('db_dblink_label_f1343cfb_like', 'db_dblink', 'label', 'varchar_pattern_ops'),
        ('db_dblink_output_id_c0167528', 'db_dblink', 'output_id', None),
        ('db_dblink_type_229f212b', 'db_dblink', 'type', None),
        ('db_dblink_type_229f212b_like', 'db_dblink', 'type', 'varchar_pattern_ops'),
        ('db_dblog_dbnode_id_da34b732', 'db_dblog', 'dbnode_id', None),
        ('db_dblog_levelname_ad5dc346', 'db_dblog', 'levelname', None),
        ('db_dblog_levelname_ad5dc346_like', 'db_dblog', 'levelname', 'varchar_pattern_ops'),
        ('db_dblog_loggername_00b5ba16', 'db_dblog', 'loggername', None),
        ('db_dblog_loggername_00b5ba16_like', 'db_dblog', 'loggername', 'varchar_pattern_ops'),
        ('db_dbnode_ctime_71626ef5', 'db_dbnode', 'ctime', None),
        ('db_dbnode_dbcomputer_id_315372a3', 'db_dbnode', 'dbcomputer_id', None),
        ('db_dbnode_label_6469539e', 'db_dbnode', 'label', None),
        ('db_dbnode_label_6469539e_like', 'db_dbnode', 'label', 'varchar_pattern_ops'),
        ('db_dbnode_mtime_0554ea3d', 'db_dbnode', 'mtime', None),
        ('db_dbnode_process_type_df7298d0', 'db_dbnode', 'process_type', None),
        ('db_dbnode_process_type_df7298d0_like', 'db_dbnode', 'process_type', 'varchar_pattern_ops'),
        ('db_dbnode_type_a8ce9753', 'db_dbnode', 'node_type', None),
        ('db_dbnode_type_a8ce9753_like', 'db_dbnode', 'node_type', 'varchar_pattern_ops'),
        ('db_dbnode_user_id_12e7aeaf', 'db_dbnode', 'user_id', None),
        ('db_dbsetting_key_1b84beb4_like', 'db_dbsetting', 'key', 'varchar_pattern_ops'),
        ('db_dbuser_email_30150b7e_like', 'db_dbuser', 'email', 'varchar_pattern_ops'),
    ):
        kwargs = {'unique': False}
        if psql_op is not None:
            kwargs['postgresql_ops'] = {column: psql_op}
        op.create_index(name, tbl_name, [column], **kwargs)

    # drop all current unique constraints, then add the new ones
    for tbl_name in (
        'db_dbauthinfo', 'db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbgroup_dbnodes', 'db_dblink', 'db_dblog',
        'db_dbnode', 'db_dbsetting', 'db_dbuser'
    ):
        reflect.drop_all_unique_constraints(tbl_name)
    for name, tbl_name, columns in (
        ('db_dbauthinfo_aiidauser_id_dbcomputer_id_777cdaa8_uniq', 'db_dbauthinfo', ('aiidauser_id', 'dbcomputer_id')),
        ('db_dbcomment_uuid_49bac08c_uniq', 'db_dbcomment', ('uuid',)),
        ('db_dbcomputer_label_bc480bab_uniq', 'db_dbcomputer', ('label',)),
        ('db_dbcomputer_uuid_f35defa6_uniq', 'db_dbcomputer', ('uuid',)),
        ('db_dbgroup_name_type_12656f33_uniq', 'db_dbgroup', ('label', 'type_string')),
        ('db_dbgroup_uuid_af896177_uniq', 'db_dbgroup', ('uuid',)),
        ('db_dbgroup_dbnodes_dbgroup_id_dbnode_id_eee23cce_uniq', 'db_dbgroup_dbnodes', ('dbgroup_id', 'dbnode_id')),
        ('db_dblog_uuid_9cf77df3_uniq', 'db_dblog', ('uuid',)),
        ('db_dbnode_uuid_62e0bf98_uniq', 'db_dbnode', ('uuid',)),
        ('db_dbsetting_key_1b84beb4_uniq', 'db_dbsetting', ('key',)),
        ('db_dbuser_email_30150b7e_uniq', 'db_dbuser', ('email',)),
    ):
        op.create_unique_constraint(name, tbl_name, columns)

    reflect.replace_foreign_key(
        'db_dbauthinfo_aiidauser_id_fkey',
        'db_dbauthinfo',
        ['aiidauser_id'],
        'db_dbuser',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbauthinfo_dbcomputer_id_fkey',
        'db_dbauthinfo',
        ['dbcomputer_id'],
        'db_dbcomputer',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbcomment_dbnode_id_fkey',
        'db_dbcomment',
        ['dbnode_id'],
        'db_dbnode',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbcomment_user_id_fkey',
        'db_dbcomment',
        ['user_id'],
        'db_dbuser',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbgroup_user_id_fkey',
        'db_dbgroup',
        ['user_id'],
        'db_dbuser',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbgroup_dbnodes_dbgroup_id_fkey',
        'db_dbgroup_dbnodes',
        ['dbgroup_id'],
        'db_dbgroup',
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbgroup_dbnodes_dbnode_id_fkey',
        'db_dbgroup_dbnodes',
        ['dbnode_id'],
        'db_dbnode',
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dblink_input_id_fkey',
        'db_dblink',
        ['input_id'],
        'db_dbnode',
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dblink_output_id_fkey',
        'db_dblink',
        ['output_id'],
        'db_dbnode',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dblog_dbnode_id_fkey',
        'db_dblog',
        ['dbnode_id'],
        'db_dbnode',
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbnode_dbcomputer_id_fkey',
        'db_dbnode',
        ['dbcomputer_id'],
        'db_dbcomputer',
        ['id'],
        ondelete='RESTRICT',
        deferrable=True,
        initially='DEFERRED',
    )
    reflect.replace_foreign_key(
        'db_dbnode_user_id_fkey',
        'db_dbnode',
        ['user_id'],
        'db_dbuser',
        ['id'],
        ondelete='RESTRICT',
        deferrable=True,
        initially='DEFERRED',
    )

    for tbl_name in (
        'auth_group_permissions', 'auth_permission', 'auth_group', 'django_content_type', 'django_migrations'
    ):
        op.execute(f'DROP TABLE IF EXISTS {tbl_name} CASCADE')


def downgrade():
    """Migrations for the downgrade."""
