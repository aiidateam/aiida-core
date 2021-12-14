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
"""Parity with Django backend (rev: 0049),
part 3: Add PostgreSQL-specific indexes

Revision ID: 1de112340b17
Revises: 2b40c8131fe0
Create Date: 2021-08-25 04:28:52.102767

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '1de112340b18'
down_revision = '1de112340b17'
branch_labels = None
depends_on = None

# table name, column name, index name
MISSING_STANDARD_INDEXES = (
    ('db_dbauthinfo', ('aiidauser_id',), False, 'db_dbauthinfo_aiidauser_id_0684fdfb'),
    ('db_dbauthinfo', ('dbcomputer_id',), False, 'db_dbauthinfo_dbcomputer_id_424f7ac4'),
    ('db_dbcomment', ('dbnode_id',), False, 'db_dbcomment_dbnode_id_3b812b6b'),
    ('db_dbcomment', ('user_id',), False, 'db_dbcomment_user_id_8ed5e360'),
    # ('db_dbcomment', ('uuid',), True, 'db_dbcomment_uuid_49bac08c_uniq'),
    # ('db_dbcomputer', ('label',), True, 'db_dbcomputer_label_bc480bab_uniq'),
    # ('db_dbcomputer', ('uuid',), True, 'db_dbcomputer_uuid_f35defa6_uniq'),
    ('db_dbgroup', ('user_id',), False, 'db_dbgroup_user_id_100f8a51'),
    ('db_dblog', ('dbnode_id',), False, 'db_dblog_dbnode_id_da34b732'),
    ('db_dbnode', ('ctime',), False, 'db_dbnode_ctime_71626ef5'),
    ('db_dbnode', ('mtime',), False, 'db_dbnode_mtime_0554ea3d'),
    ('db_dbnode', ('dbcomputer_id',), False, 'db_dbnode_dbcomputer_id_315372a3'),
    ('db_dbnode', ('user_id',), False, 'db_dbnode_user_id_12e7aeaf'),
    # ('db_dbgroup', ('uuid',), True, 'db_dbgroup_uuid_af896177_uniq'),
    # ('db_dblog', ('uuid',), True, 'db_dblog_uuid_9cf77df3_uniq'),
    # ('db_dbnode', ('uuid',), True, 'db_dbnode_uuid_62e0bf98_uniq'),
)

# table name, column names, index name
MISSING_VARCHAR_INDEXES = (
    ('db_dbcomputer', ('label',), 'db_dbcomputer_label_bc480bab_like'),
    ('db_dbgroup', ('label',), 'db_dbgroup_name_66c75272_like'),
    ('db_dbgroup', ('type_string',), 'db_dbgroup_type_23b2a748_like'),
    ('db_dblink', ('label',), 'db_dblink_label_f1343cfb_like'),
    ('db_dblink', ('type',), 'db_dblink_type_229f212b_like'),
    ('db_dblog', ('levelname',), 'db_dblog_levelname_ad5dc346_like'),
    ('db_dblog', ('loggername',), 'db_dblog_loggername_00b5ba16_like'),
    ('db_dbnode', ('label',), 'db_dbnode_label_6469539e_like'),
    ('db_dbnode', ('node_type',), 'db_dbnode_type_a8ce9753_like'),
    ('db_dbnode', ('process_type',), 'db_dbnode_process_type_df7298d0_like'),
    ('db_dbsetting', ('key',), 'db_dbsetting_key_1b84beb4_like'),
    ('db_dbuser', ('email',), 'db_dbuser_email_30150b7e_like'),
)

DROP_UNIQUE_CONSTRAINTS = (
    ('db_dbauthinfo', ('aiidauser_id', 'dbcomputer_id'), 'db_dbauthinfo_aiidauser_id_dbcomputer_id_key'),
    ('db_dbcomment', ('uuid',), 'db_dbcomment_uuid_key'),
    ('db_dbcomputer', ('label',), 'db_dbcomputer_label_key'),
    ('db_dbcomputer', ('uuid',), 'db_dbcomputer_uuid_key'),
    ('db_dbgroup', ('label', 'type_string'), 'db_dbgroup_label_type_string_key'),
    ('db_dbgroup_dbnodes', ('dbgroup_id', 'dbnode_id'), 'db_dbgroup_dbnodes_dbgroup_id_dbnode_id_key'),
    ('db_dbgroup', ('uuid',), 'db_dbgroup_uuid_key'),
    ('db_dblog', ('uuid',), 'db_dblog_uuid_key'),
    ('db_dbnode', ('uuid',), 'db_dbnode_uuid_key'),
    ('db_dbsetting', ('key',), 'db_dbsetting_key_key'),
)

ADD_UNIQUE_CONSTRAINTS = (
    ('db_dbauthinfo', ('aiidauser_id', 'dbcomputer_id'), 'db_dbauthinfo_aiidauser_id_dbcomputer_id_777cdaa8_uniq'),
    ('db_dbcomment', ('uuid',), 'db_dbcomment_uuid_49bac08c_uniq'),
    ('db_dbcomputer', ('label',), 'db_dbcomputer_label_bc480bab_uniq'),
    ('db_dbcomputer', ('uuid',), 'db_dbcomputer_uuid_f35defa6_uniq'),
    ('db_dbgroup', ('label', 'type_string'), 'db_dbgroup_name_type_12656f33_uniq'),
    ('db_dbgroup', ('uuid',), 'db_dbgroup_uuid_af896177_uniq'),
    ('db_dbgroup_dbnodes', ('dbgroup_id', 'dbnode_id'), 'db_dbgroup_dbnodes_dbgroup_id_dbnode_id_eee23cce_uniq'),
    ('db_dblog', ('uuid',), 'db_dblog_uuid_9cf77df3_uniq'),
    ('db_dbnode', ('uuid',), 'db_dbnode_uuid_62e0bf98_uniq'),
    ('db_dbuser', ('email',), 'db_dbuser_email_30150b7e_uniq'),
    ('db_dbsetting', ('key',), 'db_dbsetting_key_1b84beb4_uniq'),
)

# table name, column names, unique, old name, new name
RENAMED_INDEXES = (
    ('db_dbgroup', ('label',), False, 'ix_db_dbgroup_label', 'db_dbgroup_name_66c75272'),
    ('db_dbgroup', ('type_string',), False, 'ix_db_dbgroup_type_string', 'db_dbgroup_type_23b2a748'),
    (
        'db_dbgroup_dbnodes', ('dbgroup_id',), False, 'db_dbgroup_dbnodes_dbgroup_id_idx',
        'db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d'
    ),
    (
        'db_dbgroup_dbnodes', ('dbnode_id',), False, 'db_dbgroup_dbnodes_dbnode_id_idx',
        'db_dbgroup_dbnodes_dbnode_id_118b9439'
    ),
    ('db_dblink', ('input_id',), False, 'ix_db_dblink_input_id', 'db_dblink_input_id_9245bd73'),
    ('db_dblink', ('label',), False, 'ix_db_dblink_label', 'db_dblink_label_f1343cfb'),
    ('db_dblink', ('output_id',), False, 'ix_db_dblink_output_id', 'db_dblink_output_id_c0167528'),
    ('db_dblink', ('type',), False, 'ix_db_dblink_type', 'db_dblink_type_229f212b'),
    ('db_dblog', ('levelname',), False, 'ix_db_dblog_levelname', 'db_dblog_levelname_ad5dc346'),
    ('db_dblog', ('loggername',), False, 'ix_db_dblog_loggername', 'db_dblog_loggername_00b5ba16'),
    ('db_dbnode', ('label',), False, 'ix_db_dbnode_label', 'db_dbnode_label_6469539e'),
    ('db_dbnode', ('node_type',), False, 'ix_db_dbnode_node_type', 'db_dbnode_type_a8ce9753'),
    ('db_dbnode', ('process_type',), False, 'ix_db_dbnode_process_type', 'db_dbnode_process_type_df7298d0'),
    # ('db_dbsetting', ('key',), True, 'ix_db_dbsetting_key', 'db_dbsetting_key_1b84beb4_uniq'),
    # ('db_dbuser', ('email',), True, 'ix_db_dbuser_email', 'db_dbuser_email_30150b7e_uniq'),
)

# table name, column names, unique, name
DROP_INDEXES = (
    ('db_dbsetting', ('key',), True, 'ix_db_dbsetting_key'),
    ('db_dbuser', ('email',), True, 'ix_db_dbuser_email'),
)


def upgrade():
    """Add indexes."""
    # drop unique constraints
    for tbl_name, _, con_name in DROP_UNIQUE_CONSTRAINTS:
        op.drop_constraint(
            con_name,
            tbl_name,
        )
    # drop indexes
    for tbl_name, _, _, con_name in DROP_INDEXES:
        op.drop_index(
            con_name,
            table_name=tbl_name,
        )
    # Add missing standard indexes
    for tbl_name, col_names, unique, key_name in MISSING_STANDARD_INDEXES:
        op.create_index(
            key_name,
            table_name=tbl_name,
            columns=col_names,
            unique=unique,
        )

    # Add missing PostgreSQL-specific indexes for strings
    # these improve perform for filtering on string regexes
    for tbl_name, col_names, key_name in MISSING_VARCHAR_INDEXES:
        op.create_index(
            key_name,
            tbl_name,
            col_names,
            unique=False,
            postgresql_using='btree',
            postgresql_ops={'data': 'varchar_pattern_ops'},
        )
    # rename indexes
    for tbl_name, columns, unique, old_col_name, new_col_name in RENAMED_INDEXES:
        op.drop_index(
            old_col_name,
            table_name=tbl_name,
        )
        op.create_index(
            new_col_name,
            tbl_name,
            columns,
            unique=unique,
        )
    # add unique constraints
    for tbl_name, columns, con_name in ADD_UNIQUE_CONSTRAINTS:
        op.create_unique_constraint(
            con_name,
            tbl_name,
            columns,
        )


def downgrade():
    """Remove indexes."""
    # drop unique constraints
    for tbl_name, _, con_name in ADD_UNIQUE_CONSTRAINTS:
        op.drop_constraint(
            con_name,
            tbl_name,
        )
    # Drop missing standard indexes
    for tbl_name, _, _, key_name in MISSING_STANDARD_INDEXES:
        op.drop_index(
            key_name,
            table_name=tbl_name,
        )

    # Drop missing postgresql-specific indexes
    for tbl_name, _, key_name in MISSING_VARCHAR_INDEXES:
        op.drop_index(
            key_name, table_name=tbl_name, postgresql_using='btree', postgresql_ops={'data': 'varchar_pattern_ops'}
        )
    # drop renamed indexes
    for tbl_name, _, _, _, new_col_name in RENAMED_INDEXES:
        op.drop_index(
            new_col_name,
            table_name=tbl_name,
        )
    # add renamed indexes
    for tbl_name, columns, unique, old_col_name, _ in RENAMED_INDEXES:
        op.create_index(
            old_col_name,
            tbl_name,
            columns,
            unique=unique,
        )
    # add indexes
    for tbl_name, columns, unique, con_name in DROP_INDEXES:
        op.create_index(
            con_name,
            tbl_name,
            columns,
            unique=unique,
        )
    # add unique constraints
    for tbl_name, columns, con_name in DROP_UNIQUE_CONSTRAINTS:
        op.create_unique_constraint(
            con_name,
            tbl_name,
            columns,
        )
