# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests the database migration from legacy calculations."""
from __future__ import annotations

from uuid import uuid4

from aiida.common import timezone
from aiida.storage.psql_dos.migrations.utils.calc_state import STATE_MAPPING, StateMapping
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_legacy_jobcalcstate(perform_migrations: PsqlDosMigrator):
    """Test the migration that performs a data migration of legacy `JobCalcState`."""
    # starting revision
    perform_migrations.migrate_up('django@django_0037')

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
        nodes: dict[int, StateMapping] = {}
        for state, mapping in STATE_MAPPING.items():
            node = node_model(
                uuid=str(uuid4()),
                node_type='process.calculation.calcjob.CalcJobNode.',
                attributes={'state': state},
                label='test',
                description='',
                user_id=user.id,
                ctime=timezone.now(),
                mtime=timezone.now(),
            )
            session.add(node)
            session.commit()
            nodes[node.id] = mapping

    # final revision
    perform_migrations.migrate_up('django@django_0038')

    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        for node_id, mapping in nodes.items():
            attributes = session.get(node_model, node_id).attributes  # type: ignore[union-attr]
            assert attributes.get('process_state', None) == mapping.process_state
            assert attributes.get('process_status', None) == mapping.process_status
            assert attributes.get('exit_status', None) == mapping.exit_status
            assert attributes.get('process_label', None) == 'Legacy JobCalculation'
            assert attributes.get('state', None) is None
            assert attributes.get('exit_message', None) is None or isinstance(attributes.get('exit_message'), int)
