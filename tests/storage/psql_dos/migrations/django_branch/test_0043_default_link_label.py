# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test update of link labels."""
from uuid import uuid4

from aiida.common import timezone
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_legacy_jobcalc_attrs(perform_migrations: PsqlDosMigrator):
    """Test update of link labels."""
    # starting revision
    perform_migrations.migrate_up('django@django_0042')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    link_model = perform_migrations.get_current_table('db_dblink')

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
        )
        node_data = node_model(
            uuid=str(uuid4()),
            node_type='data.core.dict.Dict.',
            label='test',
            description='',
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
        )
        session.add(node_process)
        session.add(node_data)
        session.commit()

        link = link_model(
            input_id=node_data.id,
            output_id=node_process.id,
            type='input',
            label='_return',
        )
        session.add(link)
        session.commit()
        link_id = link.id

    # final revision
    perform_migrations.migrate_up('django@django_0043')

    link_model = perform_migrations.get_current_table('db_dblink')
    with perform_migrations.session() as session:
        link = session.get(link_model, link_id)
        assert link.label == 'result'
