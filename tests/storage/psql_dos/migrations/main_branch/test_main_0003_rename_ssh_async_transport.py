###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003_rename_ssh_async_transport.py``."""

import logging

from aiida.common.utils import get_new_uuid
from aiida.storage.psql_dos.migrator import PsqlDosMigrator

LEGACY_AUTH_PARAMS = {'username': 'alice', 'port': 2222, 'proxy_jump': 'gw', 'key_policy': 'AutoAddPolicy'}


def test_migration(perform_migrations: PsqlDosMigrator, caplog):
    """Test that ``core.ssh_async`` computers are renamed to ``core.ssh`` and the others are untouched."""
    perform_migrations.migrate_up('main@main_0002')

    computer_model = perform_migrations.get_current_table('db_dbcomputer')
    user_model = perform_migrations.get_current_table('db_dbuser')
    authinfo_model = perform_migrations.get_current_table('db_dbauthinfo')

    with perform_migrations.session() as session:
        for label, transport_type in (
            ('async', 'core.ssh_async'),
            ('async_two', 'core.ssh_async'),
            ('legacy', 'core.ssh'),
            ('local', 'core.local'),
        ):
            session.add(
                computer_model(
                    uuid=get_new_uuid(),
                    label=label,
                    hostname='localhost',
                    description='',
                    transport_type=transport_type,
                    scheduler_type='core.direct',
                    metadata={},
                )
            )
        user = user_model(email='a@b.c', first_name='', last_name='', institution='')
        session.add(user)
        session.commit()

        computer = session.query(computer_model).filter(computer_model.label == 'legacy').one()
        session.add(
            authinfo_model(
                aiidauser_id=user.id,
                dbcomputer_id=computer.id,
                metadata={},
                auth_params=LEGACY_AUTH_PARAMS,
                enabled=True,
            )
        )
        session.commit()

    # Perform the migration that is being tested.
    with caplog.at_level(logging.WARNING, logger='aiida'):
        perform_migrations.migrate_up('main@main_0003')

    computer_model = perform_migrations.get_current_table('db_dbcomputer')
    authinfo_model = perform_migrations.get_current_table('db_dbauthinfo')

    with perform_migrations.session() as session:
        transport_types = {computer.label: computer.transport_type for computer in session.query(computer_model).all()}
        auth_params = session.query(authinfo_model).one().auth_params

    # The legacy ``core.ssh`` computer keeps its transport type: it is now served by the asynchronous
    # plugin, which honors the connection parameters it had stored in ``auth_params``.
    assert transport_types == {
        'async': 'core.ssh',
        'async_two': 'core.ssh',
        'legacy': 'core.ssh',
        'local': 'core.local',
    }
    assert auth_params == LEGACY_AUTH_PARAMS

    # Only the legacy computer is reported, not the two that were just renamed.
    assert '1 computer(s) use the legacy `core.ssh` transport plugin' in caplog.text
