###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests for group migrations: 118349c10896 -> 0edcdd5a30f0"""

from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_group_typestring(perform_migrations: PsqlDosMigrator):
    """Test the migration that renames the DbGroup type strings.

    Verify that the type strings are properly migrated.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@118349c10896')  # 118349c10896_default_link_label.py

    # setup the database
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net')
        session.add(default_user)
        session.commit()

        # test user group type_string: 'user' -> 'core'
        group_user = DbGroup(label='01', user_id=default_user.id, type_string='user')
        session.add(group_user)
        # test upf group type_string: 'data.upf' -> 'core.upf'
        group_data_upf = DbGroup(label='02', user_id=default_user.id, type_string='data.upf')
        session.add(group_data_upf)
        # test auto.import group type_string: 'auto.import' -> 'core.import'
        group_autoimport = DbGroup(label='03', user_id=default_user.id, type_string='auto.import')
        session.add(group_autoimport)
        # test auto.run group type_string: 'auto.run' -> 'core.auto'
        group_autorun = DbGroup(label='04', user_id=default_user.id, type_string='auto.run')
        session.add(group_autorun)

        session.commit()

        # Store values for later tests
        group_user_pk = group_user.id
        group_data_upf_pk = group_data_upf.id
        group_autoimport_pk = group_autoimport.id
        group_autorun_pk = group_autorun.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@bf591f31dd12')  # bf591f31dd12_dbgroup_type_string.py

    # perform some checks
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    with perform_migrations.session() as session:
        group_user = session.query(DbGroup).filter(DbGroup.id == group_user_pk).one()
        assert group_user.type_string == 'core'

        # test upf group type_string: 'data.upf' -> 'core.upf'
        group_data_upf = session.query(DbGroup).filter(DbGroup.id == group_data_upf_pk).one()
        assert group_data_upf.type_string == 'core.upf'

        # test auto.import group type_string: 'auto.import' -> 'core.import'
        group_autoimport = session.query(DbGroup).filter(DbGroup.id == group_autoimport_pk).one()
        assert group_autoimport.type_string == 'core.import'

        # test auto.run group type_string: 'auto.run' -> 'core.auto'
        group_autorun = session.query(DbGroup).filter(DbGroup.id == group_autorun_pk).one()
        assert group_autorun.type_string == 'core.auto'


def test_group_extras(perform_migrations: PsqlDosMigrator):
    """Test migration to add the `extras` JSONB column to the `DbGroup` model.

    Verify that the model now has an extras column with empty dictionary as default.
    """
    # starting revision
    perform_migrations.migrate_up('sqlalchemy@bf591f31dd12')  # bf591f31dd12_dbgroup_type_string.py

    # setup the database
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    DbUser = perform_migrations.get_current_table('db_dbuser')
    with perform_migrations.session() as session:
        default_user = DbUser(email='user@aiida.net')
        session.add(default_user)
        session.commit()

        group = DbGroup(label='01', user_id=default_user.id, type_string='user')
        session.add(group)
        session.commit()

        group_pk = group.id

    # migrate up
    perform_migrations.migrate_up('sqlalchemy@0edcdd5a30f0')  # 0edcdd5a30f0_dbgroup_extras.py

    # perform some checks
    DbGroup = perform_migrations.get_current_table('db_dbgroup')
    with perform_migrations.session() as session:
        group = session.query(DbGroup).filter(DbGroup.id == group_pk).one()
        assert group.extras == {}
