###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migration to add the `extras` JSONB column to the `DbGroup` model."""
from uuid import uuid4

from aiida.common import timezone
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_group_extras(perform_migrations: PsqlDosMigrator):
    """Test migration to add the `extras` JSONB column to the `DbGroup` model."""
    # starting revision
    perform_migrations.migrate_up('django@django_0044')

    # setup the database
    user_model = perform_migrations.get_current_table('db_dbuser')
    group_model = perform_migrations.get_current_table('db_dbgroup')
    with perform_migrations.session() as session:
        user = user_model(
            email='user@aiida.net',
            first_name='John',
            last_name='Doe',
            institution='EPFL',
        )
        session.add(user)
        session.commit()
        kwargs = {
            'user_id': user.id,
            'time': timezone.now(),
            'label': 'test',
            'description': '',
        }
        group_user = group_model(uuid=str(uuid4()), type_string='core', **kwargs)
        session.add(group_user)
        session.commit()
        group_user_id = group_user.id

    # final revision
    perform_migrations.migrate_up('django@django_0045')

    group_model = perform_migrations.get_current_table('db_dbgroup')
    with perform_migrations.session() as session:
        group_user = session.get(group_model, group_user_id)
        assert group_user.extras == {}
