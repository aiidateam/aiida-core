###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test sealing of unsealed processes."""

from uuid import uuid4

from aiida.common import timezone
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_legacy_jobcalc_attrs(perform_migrations: PsqlDosMigrator):
    """Test sealing of unsealed processes."""
    # starting revision
    perform_migrations.migrate_up('django@django_0040')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')

    with perform_migrations.session() as session:
        user = user_model(
            email='user@aiida.net',
            first_name='John',
            last_name='Doe',
            institution='EPFL',
        )
        session.add(user)
        session.commit()
        node_process = node_model(
            uuid=str(uuid4()),
            node_type='process.calculation.calcjob.CalcJobNode.',
            label='test',
            description='',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            attributes={
                'process_state': 'finished',
                'sealed': True,
            },
        )
        node_process_active = node_model(
            uuid=str(uuid4()),
            node_type='process.calculation.calcjob.CalcJobNode.',
            label='test',
            description='',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            attributes={
                'process_state': 'created',
            },
        )
        node_process_legacy = node_model(
            uuid=str(uuid4()),
            node_type='process.calculation.calcjob.CalcFunctionNode.',
            label='test',
            description='',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            attributes={},
        )
        node_data = node_model(
            uuid=str(uuid4()),
            node_type='data.core.dict.Dict.',
            label='test',
            description='',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            attributes={},
        )
        session.add(node_process)
        session.add(node_process_active)
        session.add(node_process_legacy)
        session.add(node_data)
        session.commit()

        node_process_id = node_process.id
        node_process_active_id = node_process_active.id
        node_process_legacy_id = node_process_legacy.id
        node_data_id = node_data.id

    # final revision
    perform_migrations.migrate_up('django@django_0041')

    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        node_process = session.get(node_model, node_process_id)
        assert node_process.attributes['sealed'] is True

        node_process_active = session.get(node_model, node_process_active_id)
        assert 'sealed' not in node_process_active.attributes

        node_process_legacy = session.get(node_model, node_process_legacy_id)
        assert node_process_legacy.attributes['sealed'] is True

        node_data = session.get(node_model, node_data_id)
        assert 'sealed' not in node_data.attributes
