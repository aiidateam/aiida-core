# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migration that updates node types after `core.` prefix was added to entry point names."""
from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_entry_point_core_prefix(perform_migrations: PsqlDosMigrator):
    """Test the renaming of `name` to `label` for `db_dbcomputer`.

    Verify that the column was successfully renamed.
    """
    # starting revision
    perform_migrations.migrate_up('django@django_0048')

    # setup the database
    comp_model = perform_migrations.get_current_table('db_dbcomputer')
    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        user = user_model(
            email='user@aiida.net',
            first_name='John',
            last_name='Doe',
            institution='EPFL',
        )
        computer = comp_model(
            uuid=get_new_uuid(),
            label='testing',
            hostname='localhost',
            description='',
            transport_type='local',
            scheduler_type='direct',
            metadata={},
        )
        session.add_all((user, computer))
        session.commit()
        computer_id = computer.id

        calcjob = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='process.calcjob.',
            process_type='aiida.calculations:core.arithmetic.add',
            attributes={'parser_name': 'core.arithmetic.add'},
            repository_metadata={},
        )
        workflow = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='process.workflow.',
            process_type='aiida.workflows:arithmetic.add_multiply',
            repository_metadata={},
        )

        session.add_all((calcjob, workflow))
        session.commit()

        calcjob_id = calcjob.id
        workflow_id = workflow.id

    # migrate up
    perform_migrations.migrate_up('django@django_0049')

    # perform some checks
    comp_model = perform_migrations.get_current_table('db_dbcomputer')
    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        computer = session.query(comp_model).filter(comp_model.id == computer_id).one()
        assert computer.scheduler_type == 'core.direct'
        assert computer.transport_type == 'core.local'

        calcjob = session.query(node_model).filter(node_model.id == calcjob_id).one()
        assert calcjob.process_type == 'aiida.calculations:core.arithmetic.add'
        assert calcjob.attributes['parser_name'] == 'core.arithmetic.add'

        workflow = session.query(node_model).filter(node_model.id == workflow_id).one()
        assert workflow.process_type == 'aiida.workflows:core.arithmetic.add_multiply'
