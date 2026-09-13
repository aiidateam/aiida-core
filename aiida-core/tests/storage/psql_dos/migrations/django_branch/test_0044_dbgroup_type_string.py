###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migration of `type_string` after the `Group` class became pluginnable."""

from uuid import uuid4

from aiida.common import timezone
from aiida.storage.psql_dos.migrator import PsqlDosMigrator


def test_group_type_string(perform_migrations: PsqlDosMigrator):
    """Test migration of `type_string` after the `Group` class became pluginnable."""
    # starting revision
    perform_migrations.migrate_up('django@django_0043')

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
        group_user = group_model(uuid=str(uuid4()), type_string='user', **kwargs)
        session.add(group_user)
        group_data_upf = group_model(uuid=str(uuid4()), type_string='data.upf', **kwargs)
        session.add(group_data_upf)
        group_autoimport = group_model(uuid=str(uuid4()), type_string='auto.import', **kwargs)
        session.add(group_autoimport)
        group_autorun = group_model(uuid=str(uuid4()), type_string='auto.run', **kwargs)
        session.add(group_autorun)

        session.commit()

        group_user_id = group_user.id
        group_data_upf_id = group_data_upf.id
        group_autoimport_id = group_autoimport.id
        group_autorun_id = group_autorun.id

    # final revision
    perform_migrations.migrate_up('django@django_0044')

    group_model = perform_migrations.get_current_table('db_dbgroup')
    with perform_migrations.session() as session:
        # 'user' -> 'core'
        group_user = session.get(group_model, group_user_id)
        assert group_user.type_string == 'core'

        # 'data.upf' -> 'core.upf'
        group_data_upf = session.get(group_model, group_data_upf_id)
        assert group_data_upf.type_string == 'core.upf'

        # 'auto.import' -> 'core.import'
        group_autoimport = session.get(group_model, group_autoimport_id)
        assert group_autoimport.type_string == 'core.import'

        # 'auto.run' -> 'core.auto'
        group_autorun = session.get(group_model, group_autorun_id)
        assert group_autorun.type_string == 'core.auto'
