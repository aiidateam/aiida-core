# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-member
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


# TODO do the names of the indexes need to be exactly the same as in django?
# if so should we (incorrectly) name them the same as django here, then rename later
# the django ones include uuid like chars, are these always the same?
VARCHAR_INDEXES = (
        ('db_dbcomputer', 'label', 'db_dbcomputer_label_like'),
        ('db_dbgroup', 'label', 'db_dbgroup_label_like'),
        ('db_dbgroup', 'type_string', 'db_dbgroup_type_string_like'),
        ('db_dblink', 'label', 'db_dblink_label_like'),
        ('db_dblink', 'type', 'db_dblink_type_like'),
        ('db_dblog', 'levelname', 'db_dblog_levelname_like'),
        ('db_dblog', 'loggername', 'db_dblog_loggername_like'),
        ('db_dbnode', 'label', 'db_dbnode_label_like'),
        ('db_dbnode', 'node_type', 'db_dbnode_type_like'),
        ('db_dbnode', 'process_type', 'db_dbnode_process_type_like'),
        ('db_dbsetting', 'key', 'db_dbsetting_key_like'),
        ('db_dbuser', 'email', 'db_dbuser_email_like'),
    )

def upgrade():

    for tbl_name, col_name, key_name in VARCHAR_INDEXES:
        op.create_index(
            key_name,
            tbl_name, [col_name],
            unique=False,
            postgresql_using='btree',
            postgresql_ops={'data': 'varchar_pattern_ops'}
        )


def downgrade():

    for tbl_name, _, key_name in VARCHAR_INDEXES:
        op.drop_index(
            key_name,
            table_name=tbl_name,
            postgresql_using='btree',
            postgresql_ops={'data': 'varchar_pattern_ops'}
        )


# ('db_dbauthinfo', 'db_dbauthinfo_pkey', 'CREATE UNIQUE INDEX db_dbauthinfo_pkey ON public.db_dbauthinfo USING btree (id)')
# ('db_dbauthinfo', 'db_dbauthinfo_aiidauser_id_dbcomputer_id_777cdaa8_uniq', 'CREATE UNIQUE INDEX db_dbauthinfo_aiidauser_id_dbcomputer_id_777cdaa8_uniq ON public.db_dbauthinfo USING btree (aiidauser_id, dbcomputer_id)')
# --
# ('db_dbauthinfo', 'db_dbauthinfo_aiidauser_id_0684fdfb', 'CREATE INDEX db_dbauthinfo_aiidauser_id_0684fdfb ON public.db_dbauthinfo USING btree (aiidauser_id)')
# ('db_dbauthinfo', 'db_dbauthinfo_dbcomputer_id_424f7ac4', 'CREATE INDEX db_dbauthinfo_dbcomputer_id_424f7ac4 ON public.db_dbauthinfo USING btree (dbcomputer_id)')

# ('db_dbcomment', 'db_dbcomment_pkey', 'CREATE UNIQUE INDEX db_dbcomment_pkey ON public.db_dbcomment USING btree (id)')
# ('db_dbcomment', 'db_dbcomment_uuid_49bac08c_uniq', 'CREATE UNIQUE INDEX db_dbcomment_uuid_49bac08c_uniq ON public.db_dbcomment USING btree (uuid)')
# --
# ('db_dbcomment', 'db_dbcomment_dbnode_id_3b812b6b', 'CREATE INDEX db_dbcomment_dbnode_id_3b812b6b ON public.db_dbcomment USING btree (dbnode_id)')
# ('db_dbcomment', 'db_dbcomment_user_id_8ed5e360', 'CREATE INDEX db_dbcomment_user_id_8ed5e360 ON public.db_dbcomment USING btree (user_id)')

# rename name -> label?: ('db_dbcomputer', 'db_dbcomputer_name_key', 'CREATE UNIQUE INDEX db_dbcomputer_name_key ON public.db_dbcomputer USING btree (label)')
# ('db_dbcomputer', 'db_dbcomputer_pkey', 'CREATE UNIQUE INDEX db_dbcomputer_pkey ON public.db_dbcomputer USING btree (id)')
# ('db_dbcomputer', 'db_dbcomputer_uuid_f35defa6_uniq', 'CREATE UNIQUE INDEX db_dbcomputer_uuid_f35defa6_uniq ON public.db_dbcomputer USING btree (uuid)')
# ++
# ('db_dbcomputer', 'db_dbcomputer_name_f1800b1a_like', 'CREATE INDEX db_dbcomputer_name_f1800b1a_like ON public.db_dbcomputer USING btree (label varchar_pattern_ops)')

# rename name -> label?: ('db_dbgroup', 'db_dbgroup_name_type_12656f33_uniq', 'CREATE UNIQUE INDEX db_dbgroup_name_type_12656f33_uniq ON public.db_dbgroup USING btree (label, type_string)')
# ('db_dbgroup', 'db_dbgroup_pkey', 'CREATE UNIQUE INDEX db_dbgroup_pkey ON public.db_dbgroup USING btree (id)')
# ('db_dbgroup', 'db_dbgroup_uuid_af896177_uniq', 'CREATE UNIQUE INDEX db_dbgroup_uuid_af896177_uniq ON public.db_dbgroup USING btree (uuid)')
# rename name -> label?: ('db_dbgroup', 'db_dbgroup_name_66c75272', 'CREATE INDEX db_dbgroup_name_66c75272 ON public.db_dbgroup USING btree (label)')
# ('db_dbgroup', 'db_dbgroup_type_23b2a748', 'CREATE INDEX db_dbgroup_type_23b2a748 ON public.db_dbgroup USING btree (type_string)')
# ++
# ('db_dbgroup', 'db_dbgroup_type_23b2a748_like', 'CREATE INDEX db_dbgroup_type_23b2a748_like ON public.db_dbgroup USING btree (type_string varchar_pattern_ops)')
# rename name -> label?: ('db_dbgroup', 'db_dbgroup_name_66c75272_like', 'CREATE INDEX db_dbgroup_name_66c75272_like ON public.db_dbgroup USING btree (label varchar_pattern_ops)')
# --
# ('db_dbgroup', 'db_dbgroup_user_id_100f8a51', 'CREATE INDEX db_dbgroup_user_id_100f8a51 ON public.db_dbgroup USING btree (user_id)')

# ('db_dbgroup_dbnodes', 'db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d', 'CREATE INDEX db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d ON public.db_dbgroup_dbnodes USING btree (dbgroup_id)')
# ('db_dbgroup_dbnodes', 'db_dbgroup_dbnodes_dbgroup_id_dbnode_id_eee23cce_uniq', 'CREATE UNIQUE INDEX db_dbgroup_dbnodes_dbgroup_id_dbnode_id_eee23cce_uniq ON public.db_dbgroup_dbnodes USING btree (dbgroup_id, dbnode_id)')
# ('db_dbgroup_dbnodes', 'db_dbgroup_dbnodes_dbnode_id_118b9439', 'CREATE INDEX db_dbgroup_dbnodes_dbnode_id_118b9439 ON public.db_dbgroup_dbnodes USING btree (dbnode_id)')
# ('db_dbgroup_dbnodes', 'db_dbgroup_dbnodes_pkey', 'CREATE UNIQUE INDEX db_dbgroup_dbnodes_pkey ON public.db_dbgroup_dbnodes USING btree (id)')

# ('db_dblink', 'db_dblink_pkey', 'CREATE UNIQUE INDEX db_dblink_pkey ON public.db_dblink USING btree (id)')
# ('db_dblink', 'db_dblink_input_id_9245bd73', 'CREATE INDEX db_dblink_input_id_9245bd73 ON public.db_dblink USING btree (input_id)')
# ('db_dblink', 'db_dblink_label_f1343cfb', 'CREATE INDEX db_dblink_label_f1343cfb ON public.db_dblink USING btree (label)')
# ('db_dblink', 'db_dblink_output_id_c0167528', 'CREATE INDEX db_dblink_output_id_c0167528 ON public.db_dblink USING btree (output_id)')
# ('db_dblink', 'db_dblink_type_229f212b', 'CREATE INDEX db_dblink_type_229f212b ON public.db_dblink USING btree (type)')
# ++
# ('db_dblink', 'db_dblink_label_f1343cfb_like', 'CREATE INDEX db_dblink_label_f1343cfb_like ON public.db_dblink USING btree (label varchar_pattern_ops)')
# ('db_dblink', 'db_dblink_type_229f212b_like', 'CREATE INDEX db_dblink_type_229f212b_like ON public.db_dblink USING btree (type varchar_pattern_ops)')

# ('db_dblog', 'db_dblog_pkey', 'CREATE UNIQUE INDEX db_dblog_pkey ON public.db_dblog USING btree (id)')
# ('db_dblog', 'db_dblog_uuid_9cf77df3_uniq', 'CREATE UNIQUE INDEX db_dblog_uuid_9cf77df3_uniq ON public.db_dblog USING btree (uuid)')
# ('db_dblog', 'db_dblog_levelname_ad5dc346', 'CREATE INDEX db_dblog_levelname_ad5dc346 ON public.db_dblog USING btree (levelname)')
# ('db_dblog', 'db_dblog_loggername_00b5ba16', 'CREATE INDEX db_dblog_loggername_00b5ba16 ON public.db_dblog USING btree (loggername)')
# ++
# ('db_dblog', 'db_dblog_levelname_ad5dc346_like', 'CREATE INDEX db_dblog_levelname_ad5dc346_like ON public.db_dblog USING btree (levelname varchar_pattern_ops)')
# ('db_dblog', 'db_dblog_loggername_00b5ba16_like', 'CREATE INDEX db_dblog_loggername_00b5ba16_like ON public.db_dblog USING btree (loggername varchar_pattern_ops)')
# --
# ('db_dblog', 'db_dblog_dbnode_id_da34b732', 'CREATE INDEX db_dblog_dbnode_id_da34b732 ON public.db_dblog USING btree (dbnode_id)')

# ('db_dbnode', 'db_dbnode_pkey', 'CREATE UNIQUE INDEX db_dbnode_pkey ON public.db_dbnode USING btree (id)')
# ('db_dbnode', 'db_dbnode_uuid_62e0bf98_uniq', 'CREATE UNIQUE INDEX db_dbnode_uuid_62e0bf98_uniq ON public.db_dbnode USING btree (uuid)')
# ('db_dbnode', 'db_dbnode_label_6469539e', 'CREATE INDEX db_dbnode_label_6469539e ON public.db_dbnode USING btree (label)')
# ('db_dbnode', 'db_dbnode_type_a8ce9753', 'CREATE INDEX db_dbnode_type_a8ce9753 ON public.db_dbnode USING btree (node_type)')
# ('db_dbnode', 'db_dbnode_process_type_df7298d0', 'CREATE INDEX db_dbnode_process_type_df7298d0 ON public.db_dbnode USING btree (process_type)')
# ++
# ('db_dbnode', 'db_dbnode_label_6469539e_like', 'CREATE INDEX db_dbnode_label_6469539e_like ON public.db_dbnode USING btree (label varchar_pattern_ops)')
# ('db_dbnode', 'db_dbnode_process_type_df7298d0_like', 'CREATE INDEX db_dbnode_process_type_df7298d0_like ON public.db_dbnode USING btree (process_type varchar_pattern_ops)')
# ('db_dbnode', 'db_dbnode_type_a8ce9753_like', 'CREATE INDEX db_dbnode_type_a8ce9753_like ON public.db_dbnode USING btree (node_type varchar_pattern_ops)')
# --
# ('db_dbnode', 'db_dbnode_ctime_71626ef5', 'CREATE INDEX db_dbnode_ctime_71626ef5 ON public.db_dbnode USING btree (ctime)')
# ('db_dbnode', 'db_dbnode_mtime_0554ea3d', 'CREATE INDEX db_dbnode_mtime_0554ea3d ON public.db_dbnode USING btree (mtime)')
# ('db_dbnode', 'db_dbnode_dbcomputer_id_315372a3', 'CREATE INDEX db_dbnode_dbcomputer_id_315372a3 ON public.db_dbnode USING btree (dbcomputer_id)')
# ('db_dbnode', 'db_dbnode_user_id_12e7aeaf', 'CREATE INDEX db_dbnode_user_id_12e7aeaf ON public.db_dbnode USING btree (user_id)')

# ('db_dbsetting', 'db_dbsetting_key_1b84beb4_uniq', 'CREATE UNIQUE INDEX db_dbsetting_key_1b84beb4_uniq ON public.db_dbsetting USING btree (key)')
# ('db_dbsetting', 'db_dbsetting_pkey', 'CREATE UNIQUE INDEX db_dbsetting_pkey ON public.db_dbsetting USING btree (id)')
# ++
# ('db_dbsetting', 'db_dbsetting_key_1b84beb4_like', 'CREATE INDEX db_dbsetting_key_1b84beb4_like ON public.db_dbsetting USING btree (key varchar_pattern_ops)')
## sqla has one more CREATE INDEX on key, necessary or remove?

# ('db_dbuser', 'db_dbuser_pkey', 'CREATE UNIQUE INDEX db_dbuser_pkey ON public.db_dbuser USING btree (id)')
# ('db_dbuser', 'db_dbuser_email_30150b7e_uniq', 'CREATE UNIQUE INDEX db_dbuser_email_30150b7e_uniq ON public.db_dbuser USING btree (email)')
# ++
# ('db_dbuser', 'db_dbuser_email_30150b7e_like', 'CREATE INDEX db_dbuser_email_30150b7e_like ON public.db_dbuser USING btree (email varchar_pattern_ops)')
