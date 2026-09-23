###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests shared by profile storage backends for ``main_0003``."""

from aiida.common import timezone
from aiida.common.utils import get_new_uuid


def test_migrate_legacy_code(migration_profile):
    """Test that legacy ``Code`` nodes are rewritten to modern code plugins."""
    migrator_class = migration_profile.storage_cls.migrator

    with migrator_class(migration_profile) as migrator:
        migrator.migrate_up('main@main_0002')

        user_model = migrator.get_current_table('db_dbuser')
        node_model = migrator.get_current_table('db_dbnode')

        with migrator.session() as session:
            user = user_model(email='test', first_name='test', last_name='test', institution='test')
            session.add(user)
            session.commit()

            remote = node_model(
                uuid=get_new_uuid(),
                user_id=user.id,
                ctime=timezone.now(),
                mtime=timezone.now(),
                label='test',
                description='',
                node_type='data.core.code.Code.',
                repository_metadata={},
                attributes={
                    'is_local': False,
                    'remote_exec_path': '/usr/bin/add.sh',
                    'input_plugin': 'core.arithmetic.add',
                    'prepend_text': 'module load add',
                    'append_text': '',
                },
                extras={'_aiida_hash': 'hash', 'hidden': True},
            )
            local = node_model(
                uuid=get_new_uuid(),
                user_id=user.id,
                ctime=timezone.now(),
                mtime=timezone.now(),
                label='test',
                description='',
                node_type='data.core.code.Code.',
                repository_metadata={},
                attributes={'is_local': True, 'local_executable': 'add.sh', 'input_plugin': 'core.arithmetic.add'},
                extras={'_aiida_hash': 'hash'},
            )
            local_with_filepath = node_model(
                uuid=get_new_uuid(),
                user_id=user.id,
                ctime=timezone.now(),
                mtime=timezone.now(),
                label='test',
                description='',
                node_type='data.core.code.Code.',
                repository_metadata={},
                attributes={'is_local': True, 'filepath_executable': 'existing.sh'},
                extras={},
            )
            installed = node_model(
                uuid=get_new_uuid(),
                user_id=user.id,
                ctime=timezone.now(),
                mtime=timezone.now(),
                label='test',
                description='',
                node_type='data.core.code.installed.InstalledCode.',
                repository_metadata={},
                attributes={'filepath_executable': '/usr/bin/bash'},
                extras={'_aiida_hash': 'hash'},
            )
            session.add_all((remote, local, local_with_filepath, installed))
            session.commit()

            remote_id = remote.id
            local_id = local.id
            local_with_filepath_id = local_with_filepath.id
            installed_id = installed.id

        migrator.migrate_up('main@main_0003')

        assert migrator.get_schema_version_profile() == 'main_0003'

        node_model = migrator.get_current_table('db_dbnode')

        with migrator.session() as session:
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
            assert local.attributes == {'filepath_executable': 'add.sh', 'input_plugin': 'core.arithmetic.add'}
            assert local.extras == {}

            local_with_filepath = session.query(node_model).filter(node_model.id == local_with_filepath_id).one()
            assert local_with_filepath.node_type == 'data.core.code.portable.PortableCode.'
            assert local_with_filepath.attributes == {'filepath_executable': 'existing.sh'}

            installed = session.query(node_model).filter(node_model.id == installed_id).one()
            assert installed.node_type == 'data.core.code.installed.InstalledCode.'
            assert installed.attributes == {'filepath_executable': '/usr/bin/bash'}
            assert installed.extras == {'_aiida_hash': 'hash'}

        # Downgrade only restores the schema revision; it cannot reconstruct the original legacy codes.
        migrator.migrate_down('main@main_0002')
        with migrator.session() as session:
            remote = session.query(node_model).filter(node_model.id == remote_id).one()
            assert remote.node_type == 'data.core.code.installed.InstalledCode.'
