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

1. Update the foreign keys to be identical
2. Drop the django specific tables

It is of note that a number of foreign keys were missing comparable `ON DELETE` rules in django.
This is because django does not currently add these rules to the database, but instead tries to handle them on the
Python side, see: https://stackoverflow.com/a/35780859/5033292

Revision ID: django_0050
Revises: django_0049

"""
from alembic import op

revision = 'django_0050'
down_revision = 'django_0049'
branch_labels = None
depends_on = None


def upgrade():
    """Migrations for the upgrade."""

    op.drop_constraint('db_dbauthinfo_aiidauser_id_0684fdfb_fk_db_dbuser_id', 'db_dbauthinfo', type_='foreignkey')
    op.create_foreign_key(
        'db_dbauthinfo_aiidauser_id_fkey',
        'db_dbauthinfo',
        'db_dbuser',
        ['aiidauser_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dbauthinfo_dbcomputer_id_424f7ac4_fk_db_dbcomputer_id', 'db_dbauthinfo', type_='foreignkey')
    op.create_foreign_key(
        'db_dbauthinfo_dbcomputer_id_fkey',
        'db_dbauthinfo',
        'db_dbcomputer',
        ['dbcomputer_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dbcomment_dbnode_id_3b812b6b_fk_db_dbnode_id', 'db_dbcomment', type_='foreignkey')
    op.create_foreign_key(
        'db_dbcomment_dbnode_id_fkey',
        'db_dbcomment',
        'db_dbnode',
        ['dbnode_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dbcomment_user_id_8ed5e360_fk_db_dbuser_id', 'db_dbcomment', type_='foreignkey')
    op.create_foreign_key(
        'db_dbcomment_user_id_fkey',
        'db_dbcomment',
        'db_dbuser',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dbgroup_user_id_100f8a51_fk_db_dbuser_id', 'db_dbgroup', type_='foreignkey')
    op.create_foreign_key(
        'db_dbgroup_user_id_fkey',
        'db_dbgroup',
        'db_dbuser',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint(
        'db_dbgroup_dbnodes_dbgroup_id_9d3a0f9d_fk_db_dbgroup_id', 'db_dbgroup_dbnodes', type_='foreignkey'
    )
    op.create_foreign_key(
        'db_dbgroup_dbnodes_dbgroup_id_fkey',
        'db_dbgroup_dbnodes',
        'db_dbgroup',
        ['dbgroup_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint(
        'db_dbgroup_dbnodes_dbnode_id_118b9439_fk_db_dbnode_id', 'db_dbgroup_dbnodes', type_='foreignkey'
    )
    op.create_foreign_key(
        'db_dbgroup_dbnodes_dbnode_id_fkey',
        'db_dbgroup_dbnodes',
        'db_dbnode',
        ['dbnode_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dblink_input_id_9245bd73_fk_db_dbnode_id', 'db_dblink', type_='foreignkey')
    op.create_foreign_key(
        'db_dblink_input_id_fkey',
        'db_dblink',
        'db_dbnode',
        ['input_id'],
        ['id'],
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dblink_output_id_c0167528_fk_db_dbnode_id', 'db_dblink', type_='foreignkey')
    op.create_foreign_key(
        'db_dblink_output_id_fkey',
        'db_dblink',
        'db_dbnode',
        ['output_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dblog_dbnode_id_da34b732_fk_db_dbnode_id', 'db_dblog', type_='foreignkey')
    op.create_foreign_key(
        'db_dblog_dbnode_id_fkey',
        'db_dblog',
        'db_dbnode',
        ['dbnode_id'],
        ['id'],
        ondelete='CASCADE',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dbnode_dbcomputer_id_315372a3_fk_db_dbcomputer_id', 'db_dbnode', type_='foreignkey')
    op.create_foreign_key(
        'db_dbnode_dbcomputer_id_fkey',
        'db_dbnode',
        'db_dbcomputer',
        ['dbcomputer_id'],
        ['id'],
        ondelete='RESTRICT',
        deferrable=True,
        initially='DEFERRED',
    )

    op.drop_constraint('db_dbnode_user_id_12e7aeaf_fk_db_dbuser_id', 'db_dbnode', type_='foreignkey')
    op.create_foreign_key(
        'db_dbnode_user_id_fkey',
        'db_dbnode',
        'db_dbuser',
        ['user_id'],
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
