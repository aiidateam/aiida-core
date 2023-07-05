# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0002_recompute_hash_calc_job_node.py``."""
from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_migration(perform_migrations: PsqlDosMigrator):
    """Test the migration removes the ``_aiida_hash`` extra of all ``CalcJobNodes`` and those nodes only."""
    perform_migrations.migrate_up('main@main_0001')

    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')

    with perform_migrations.session() as session:
        user = user_model(email='test', first_name='test', last_name='test', institution='test')
        session.add(user)
        session.commit()

        calcjob = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='process.calculation.calcjob.CalcJobNode.',
            process_type='aiida.calculations:core.arithmetic.add',
            attributes={'parser_name': 'core.arithmetic.add'},
            repository_metadata={},
            extras={
                '_aiida_hash': 'hash',
                'other_extra': 'value'
            }
        )
        workflow = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='process.workflow.workchain.WorkChainNode.',
            process_type='aiida.workflows:core.arithmetic.add_multiply',
            repository_metadata={},
            extras={
                '_aiida_hash': 'hash',
                'other_extra': 'value'
            }
        )
        session.add_all((calcjob, workflow))
        session.commit()

        calcjob_id = calcjob.id
        workflow_id = workflow.id

    # Perform the migration that is being tested.
    perform_migrations.migrate_up('main@main_0002')

    node_model = perform_migrations.get_current_table('db_dbnode')

    # Check that the ``_aiida_hash`` extra was removed, and only that extra, and only for the calcjob, not the workflow.
    with perform_migrations.session() as session:
        calcjob = session.query(node_model).filter(node_model.id == calcjob_id).one()
        assert calcjob.extras == {'other_extra': 'value'}

        workflow = session.query(node_model).filter(node_model.id == workflow_id).one()
        assert workflow.extras == {'_aiida_hash': 'hash', 'other_extra': 'value'}
