###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the migrations of the attributes, extras and settings from EAV to JSONB."""

from datetime import datetime

from sqlalchemy import select

from aiida.common import timezone
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_attr_extra_migration(perform_migrations: PsqlDosMigrator):
    """A "simple" test for the attributes and extra migration from EAV to JSONB.
    It stores a sample dictionary using the EAV deserialization of AiiDA Django
    for the attributes and extras. Then the test checks that they are correctly
    converted to JSONB.
    """
    # starting revision
    perform_migrations.migrate_up('django@django_0036')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    attr_model = perform_migrations.get_current_table('db_dbattribute')
    extra_model = perform_migrations.get_current_table('db_dbextra')

    with perform_migrations.session() as session:
        user = user_model(
            email='user@aiida.net',
            first_name='John',
            last_name='Doe',
            institution='EPFL',
        )
        session.add(user)
        session.commit()
        node = node_model(
            uuid='00000000-0000-0000-0000-000000000000',
            node_type='any',
            label='test',
            description='',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
        )
        session.add(node)
        session.commit()
        node_id = node.id

        for idx, kwargs in enumerate(
            (
                {'datatype': 'txt', 'tval': 'test'},
                {'datatype': 'int', 'ival': 1},
                {'datatype': 'bool', 'bval': True},
                {'datatype': 'float', 'fval': 1.0},
                {'datatype': 'date', 'dval': datetime.fromisoformat('2022-01-01')},
            )
        ):
            kwargs['tval'] = 'test'  # type: ignore[index]
            attr = attr_model(dbnode_id=node.id, key=f'attr_{idx}', **kwargs)
            session.add(attr)
            session.commit()

            extra = extra_model(dbnode_id=node.id, key=f'extra_{idx}', **kwargs)
            session.add(extra)
            session.commit()

    # final revision
    perform_migrations.migrate_up('django@django_0037')

    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        attrs = session.execute(select(node_model.attributes).where(node_model.id == node_id)).scalar_one()
        extras = session.execute(select(node_model.extras).where(node_model.id == node_id)).scalar_one()

    attrs['attr_4'] = datetime.fromisoformat(attrs['attr_4']).year
    extras['extra_4'] = datetime.fromisoformat(extras['extra_4']).year
    assert attrs == {'attr_0': 'test', 'attr_1': 1, 'attr_2': True, 'attr_3': 1.0, 'attr_4': 2022}
    assert extras == {'extra_0': 'test', 'extra_1': 1, 'extra_2': True, 'extra_3': 1.0, 'extra_4': 2022}


def test_settings_migration(perform_migrations: PsqlDosMigrator):
    """This test checks the correct migration of the settings.
    Setting records were used as an example from a typical settings table of Django EAV.
    """
    # starting revision
    perform_migrations.migrate_up('django@django_0036')

    # setup the database
    setting_model = perform_migrations.get_current_table('db_dbsetting')

    with perform_migrations.session() as session:
        kwargs: dict
        for idx, kwargs in enumerate(  # type: ignore[assignment]
            (
                {'datatype': 'txt', 'tval': 'test'},
                {'datatype': 'int', 'ival': 1},
                {'datatype': 'bool', 'bval': True},
                {'datatype': 'float', 'fval': 1.0},
                {'datatype': 'date', 'dval': datetime.fromisoformat('2022-01-01')},
            )
        ):
            kwargs['tval'] = 'test'
            kwargs['description'] = 'description'
            kwargs['time'] = datetime.fromisoformat('2022-01-01')
            attr = setting_model(key=f'key_{idx}', **kwargs)
            session.add(attr)
            session.commit()

    # final revision
    perform_migrations.migrate_up('django@django_0037')

    setting_model = perform_migrations.get_current_table('db_dbsetting')
    with perform_migrations.session() as session:
        settings = {
            row[0]: row[1]
            for row in session.execute(select(setting_model.key, setting_model.val).order_by(setting_model.key)).all()
        }

    settings['key_4'] = datetime.fromisoformat(settings['key_4']).year
    assert settings == {'key_0': 'test', 'key_1': 1, 'key_2': True, 'key_3': 1.0, 'key_4': 2022}
