# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for synchronizing the django and sqlalchemy schema."""
import alembic

from aiida.storage.psql_dos.migrations.utils import ReflectMigrations


def synchronize_schemas(alembic_op: alembic.op) -> None:
    """This function is used by the final migration step, of django/sqlalchemy branches, to synchronize their schemas.

    1. Remove and recreate all (non-unique) indexes, with standard names and postgresql ops.
    2. Remove and recreate all unique constraints, with standard names.
    3. Remove and recreate all foreign key constraints, with standard names and other rules.

    Schema naming conventions are defined ``aiida/storage/sqlalchemy/models/base.py::naming_convention``.

    Note we assume here that (a) all primary keys are already correct, and (b) there are no check constraints.
    """
    reflect = ReflectMigrations(alembic_op)

    # drop all current non-unique indexes, then add the new ones
    for tbl_name in (
        'db_dbauthinfo', 'db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbgroup_dbnodes', 'db_dblink', 'db_dblog',
        'db_dbnode', 'db_dbsetting', 'db_dbuser'
    ):
        reflect.drop_all_indexes(tbl_name)
    for name, tbl_name, column, psql_op in (
        ('ix_db_dbauthinfo_aiidauser_id', 'db_dbauthinfo', 'aiidauser_id', None),
        ('ix_db_dbauthinfo_dbcomputer_id', 'db_dbauthinfo', 'dbcomputer_id', None),
        ('ix_db_dbcomment_dbnode_id', 'db_dbcomment', 'dbnode_id', None),
        ('ix_db_dbcomment_user_id', 'db_dbcomment', 'user_id', None),
        ('ix_pat_db_dbcomputer_label', 'db_dbcomputer', 'label', 'varchar_pattern_ops'),
        ('ix_db_dbgroup_label', 'db_dbgroup', 'label', None),
        ('ix_pat_db_dbgroup_label', 'db_dbgroup', 'label', 'varchar_pattern_ops'),
        ('ix_db_dbgroup_type_string', 'db_dbgroup', 'type_string', None),
        ('ix_pat_db_dbgroup_type_string', 'db_dbgroup', 'type_string', 'varchar_pattern_ops'),
        ('ix_db_dbgroup_user_id', 'db_dbgroup', 'user_id', None),
        ('ix_db_dbgroup_dbnodes_dbgroup_id', 'db_dbgroup_dbnodes', 'dbgroup_id', None),
        ('ix_db_dbgroup_dbnodes_dbnode_id', 'db_dbgroup_dbnodes', 'dbnode_id', None),
        ('ix_db_dblink_input_id', 'db_dblink', 'input_id', None),
        ('ix_db_dblink_label', 'db_dblink', 'label', None),
        ('ix_pat_db_dblink_label', 'db_dblink', 'label', 'varchar_pattern_ops'),
        ('ix_db_dblink_output_id', 'db_dblink', 'output_id', None),
        ('ix_db_dblink_type', 'db_dblink', 'type', None),
        ('ix_pat_db_dblink_type', 'db_dblink', 'type', 'varchar_pattern_ops'),
        ('ix_db_dblog_dbnode_id', 'db_dblog', 'dbnode_id', None),
        ('ix_db_dblog_levelname', 'db_dblog', 'levelname', None),
        ('ix_pat_db_dblog_levelname', 'db_dblog', 'levelname', 'varchar_pattern_ops'),
        ('ix_db_dblog_loggername', 'db_dblog', 'loggername', None),
        ('ix_pat_db_dblog_loggername', 'db_dblog', 'loggername', 'varchar_pattern_ops'),
        ('ix_db_dbnode_ctime', 'db_dbnode', 'ctime', None),
        ('ix_db_dbnode_dbcomputer_id', 'db_dbnode', 'dbcomputer_id', None),
        ('ix_db_dbnode_label', 'db_dbnode', 'label', None),
        ('ix_pat_db_dbnode_label', 'db_dbnode', 'label', 'varchar_pattern_ops'),
        ('ix_db_dbnode_mtime', 'db_dbnode', 'mtime', None),
        ('ix_db_dbnode_process_type', 'db_dbnode', 'process_type', None),
        ('ix_pat_db_dbnode_process_type', 'db_dbnode', 'process_type', 'varchar_pattern_ops'),
        ('ix_db_dbnode_node_type', 'db_dbnode', 'node_type', None),
        ('ix_pat_db_dbnode_node_type', 'db_dbnode', 'node_type', 'varchar_pattern_ops'),
        ('ix_db_dbnode_user_id', 'db_dbnode', 'user_id', None),
        ('ix_pat_db_dbsetting_key', 'db_dbsetting', 'key', 'varchar_pattern_ops'),
        ('ix_pat_db_dbuser_email', 'db_dbuser', 'email', 'varchar_pattern_ops'),
    ):
        kwargs = {'unique': False}
        if psql_op is not None:
            kwargs['postgresql_ops'] = {column: psql_op}
        alembic_op.create_index(name, tbl_name, [column], **kwargs)

    # drop all current unique constraints, then add the new ones
    for tbl_name in (
        'db_dbauthinfo', 'db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbgroup_dbnodes', 'db_dblink', 'db_dblog',
        'db_dbnode', 'db_dbsetting', 'db_dbuser'
    ):
        reflect.drop_all_unique_constraints(tbl_name)
    reflect.reset_cache()
    for name, tbl_name, columns in (
        ('uq_db_dbauthinfo_aiidauser_id_dbcomputer_id', 'db_dbauthinfo', ('aiidauser_id', 'dbcomputer_id')),
        ('uq_db_dbcomment_uuid', 'db_dbcomment', ('uuid',)),
        ('uq_db_dbcomputer_label', 'db_dbcomputer', ('label',)),
        ('uq_db_dbcomputer_uuid', 'db_dbcomputer', ('uuid',)),
        ('uq_db_dbgroup_label_type_string', 'db_dbgroup', ('label', 'type_string')),
        ('uq_db_dbgroup_uuid', 'db_dbgroup', ('uuid',)),
        ('uq_db_dbgroup_dbnodes_dbgroup_id_dbnode_id', 'db_dbgroup_dbnodes', ('dbgroup_id', 'dbnode_id')),
        ('uq_db_dblog_uuid', 'db_dblog', ('uuid',)),
        ('uq_db_dbnode_uuid', 'db_dbnode', ('uuid',)),
        ('uq_db_dbsetting_key', 'db_dbsetting', ('key',)),
        ('uq_db_dbuser_email', 'db_dbuser', ('email',)),
    ):
        reflect.drop_indexes(tbl_name, columns, unique=True)  # drop any remaining indexes
        alembic_op.create_unique_constraint(name, tbl_name, columns)

    # drop all current foreign key constraints, then add the new ones
    for tbl_name in (
        'db_dbauthinfo', 'db_dbcomment', 'db_dbcomputer', 'db_dbgroup', 'db_dbgroup_dbnodes', 'db_dblink', 'db_dblog',
        'db_dbnode', 'db_dbsetting', 'db_dbuser'
    ):
        reflect.drop_all_foreign_keys(tbl_name)

    alembic_op.create_foreign_key(
        'fk_db_dbauthinfo_aiidauser_id_db_dbuser',
        'db_dbauthinfo',
        'db_dbuser',
        ['aiidauser_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbauthinfo_dbcomputer_id_db_dbcomputer',
        'db_dbauthinfo',
        'db_dbcomputer',
        ['dbcomputer_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbcomment_dbnode_id_db_dbnode',
        'db_dbcomment',
        'db_dbnode',
        ['dbnode_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbcomment_user_id_db_dbuser',
        'db_dbcomment',
        'db_dbuser',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'db_dbgroup_user_id_db_dbuser',
        'db_dbgroup',
        'db_dbuser',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbgroup_dbnodes_dbgroup_id_db_dbgroup',
        'db_dbgroup_dbnodes',
        'db_dbgroup',
        ['dbgroup_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbgroup_dbnodes_dbnode_id_db_dbnode',
        'db_dbgroup_dbnodes',
        'db_dbnode',
        ['dbnode_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dblink_input_id_db_dbnode',
        'db_dblink',
        'db_dbnode',
        ['input_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dblink_output_id_db_dbnode',
        'db_dblink',
        'db_dbnode',
        ['output_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dblog_dbnode_id_db_dbnode',
        'db_dblog',
        'db_dbnode',
        ['dbnode_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbnode_dbcomputer_id_db_dbcomputer',
        'db_dbnode',
        'db_dbcomputer',
        ['dbcomputer_id'],
        ['id'],
        ondelete='RESTRICT',
        deferrable=True,
        initially='DEFERRED',
    )
    alembic_op.create_foreign_key(
        'fk_db_dbnode_user_id_db_dbuser',
        'db_dbnode',
        'db_dbuser',
        ['user_id'],
        ['id'],
        ondelete='RESTRICT',
        deferrable=True,
        initially='DEFERRED',
    )
