# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Test renaming of type strings: b8b23ddefad4 -> e72ad251bcdb"""
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_group_renaming(perform_migrations: PsqlDosMigrator):
    """Test the migration that renames the DbGroup type strings."""
    # starting revision
    perform_migrations.migrate_up(
        'sqlalchemy@b8b23ddefad4'
    )  # b8b23ddefad4_dbgroup_name_to_label_type_to_type_string.py

    # setup the database
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net', is_superuser=True)
        session.add(default_user)
        session.commit()

        # test user group type_string: '' -> 'user'
        group_user = DbGroup(label='test_user_group', user_id=default_user.id, type_string='')
        session.add(group_user)
        # test upf group type_string: 'data.upf.family' -> 'data.upf'
        group_data_upf = DbGroup(label='test_data_upf_group', user_id=default_user.id, type_string='data.upf.family')
        session.add(group_data_upf)
        # test auto.import group type_string: 'aiida.import' -> 'auto.import'
        group_autoimport = DbGroup(label='test_import_group', user_id=default_user.id, type_string='aiida.import')
        session.add(group_autoimport)
        # test auto.run group type_string: 'autogroup.run' -> 'auto.run'
        group_autorun = DbGroup(label='test_autorun_group', user_id=default_user.id, type_string='autogroup.run')
        session.add(group_autorun)
        session.commit()

        group_user_pk = group_user.id
        group_data_upf_pk = group_data_upf.id
        group_autoimport_pk = group_autoimport.id
        group_autorun_pk = group_autorun.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@e72ad251bcdb')  # e72ad251bcdb_dbgroup_class_change_type_string_values.py

    # perform some checks
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    with perform_migrations.session() as session:
        # test user group type_string: '' -> 'user'
        group_user = session.query(DbGroup).filter(DbGroup.id == group_user_pk).one()
        assert group_user.type_string == 'user'

        # test upf group type_string: 'data.upf.family' -> 'data.upf'
        group_data_upf = session.query(DbGroup).filter(DbGroup.id == group_data_upf_pk).one()
        assert group_data_upf.type_string == 'data.upf'

        # test auto.import group type_string: 'aiida.import' -> 'auto.import'
        group_autoimport = session.query(DbGroup).filter(DbGroup.id == group_autoimport_pk).one()
        assert group_autoimport.type_string == 'auto.import'

        # test auto.run group type_string: 'autogroup.run' -> 'auto.run'
        group_autorun = session.query(DbGroup).filter(DbGroup.id == group_autorun_pk).one()
        assert group_autorun.type_string == 'auto.run'
