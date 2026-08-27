###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test ``main_0003_migrate_legacy_code.py``."""

import pytest

from aiida.common import timezone
from aiida.common.utils import get_new_uuid
from aiida.storage.sqlite_dos.backend import SqliteDosMigrator


@pytest.fixture
def perform_migrations(uninitialised_profile):
    """A fixture to setup a database for migration tests."""
    with SqliteDosMigrator(uninitialised_profile) as migrator:
        yield migrator


def test_migration(perform_migrations: SqliteDosMigrator):
    """Test that legacy ``Code`` nodes are rewritten to ``InstalledCode`` and ``PortableCode``."""
    perform_migrations.migrate_up('main@main_0002')

    user_model = perform_migrations.get_current_table('db_dbuser')
    node_model = perform_migrations.get_current_table('db_dbnode')

    def create_node(node_type, attributes, extras):
        return node_model(
            uuid=get_new_uuid(),
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type=node_type,
            repository_metadata={},
            attributes=attributes,
            extras=extras,
        )

    with perform_migrations.session() as session:
        user = user_model(email='test', first_name='test', last_name='test', institution='test')
        session.add(user)
        session.commit()

        remote = create_node(
            'data.core.code.Code.',
            {
                'is_local': False,
                'remote_exec_path': '/usr/bin/add.sh',
                'input_plugin': 'core.arithmetic.add',
                'prepend_text': 'module load add',
                'append_text': '',
            },
            {'_aiida_hash': 'hash', 'hidden': True},
        )
        local = create_node(
            'data.core.code.Code.',
            {'is_local': True, 'local_executable': 'add.sh', 'input_plugin': 'core.arithmetic.add'},
            {'_aiida_hash': 'hash'},
        )
        installed = create_node(
            'data.core.code.installed.InstalledCode.',
            {'filepath_executable': '/usr/bin/bash'},
            {'_aiida_hash': 'hash'},
        )
        session.add_all((remote, local, installed))
        session.commit()

        remote_id = remote.id
        local_id = local.id
        installed_id = installed.id

    # Perform the migration that is being tested.
    perform_migrations.migrate_up('main@main_0003')

    node_model = perform_migrations.get_current_table('db_dbnode')

    with perform_migrations.session() as session:
        remote = session.query(node_model).filter(node_model.id == remote_id).one()
        assert remote.node_type == 'data.core.code.installed.InstalledCode.'
        assert remote.attributes == {
            'filepath_executable': '/usr/bin/add.sh',
            'input_plugin': 'core.arithmetic.add',
            'prepend_text': 'module load add',
            'append_text': '',
        }
        assert remote.extras == {'hidden': True}

        local = session.query(node_model).filter(node_model.id == local_id).one()
        assert local.node_type == 'data.core.code.portable.PortableCode.'
        assert local.attributes == {
            'filepath_executable': 'add.sh',
            'input_plugin': 'core.arithmetic.add',
        }
        assert local.extras == {}

        # A code that was already migrated to the modern plugins is left untouched, hash included.
        installed = session.query(node_model).filter(node_model.id == installed_id).one()
        assert installed.node_type == 'data.core.code.installed.InstalledCode.'
        assert installed.attributes == {'filepath_executable': '/usr/bin/bash'}
        assert installed.extras == {'_aiida_hash': 'hash'}
