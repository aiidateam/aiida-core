###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test the node hash reset."""

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_reset_hash(perform_migrations: PsqlDosMigrator):
    """Test the node hash reset."""
    # starting revision
    perform_migrations.migrate_up('django@django_0038')

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
        node = node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='data.',
            extras={'something': 123, '_aiida_hash': 'abcd'},
        )
        session.add(node)
        session.commit()
        node_id = node.id

    # final revision
    perform_migrations.migrate_up('django@django_0039')

    node_model = perform_migrations.get_current_table('db_dbnode')
    with perform_migrations.session() as session:
        node = session.get(node_model, node_id)
        # The hash extra should have been removed
        assert node.extras == {'something': 123}
