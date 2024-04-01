###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migration that renames all index/constraint names, to have parity between django/sqlalchemy."""

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_schema_parity(perform_migrations: PsqlDosMigrator):
    """Test the renaming of indexes and constaints works, when data is in the database."""
    # starting revision
    perform_migrations.migrate_up('django@django_0049')

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
            transport_type='core.local',
            scheduler_type='core.direct',
            metadata={},
        )
        session.add_all((user, computer))
        session.commit()

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
            process_type='aiida.workflows:core.arithmetic.add_multiply',
            repository_metadata={},
        )

        session.add_all((calcjob, workflow))
        session.commit()

    # migrate up
    perform_migrations.migrate_up('django@django_0050')
