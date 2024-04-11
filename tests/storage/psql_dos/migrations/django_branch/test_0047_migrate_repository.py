###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test migration of the old file repository to the disk object store."""

import hashlib
import os
from uuid import uuid4

from aiida.common import timezone
from aiida.storage.psql_dos.backend import get_filepath_container
from aiida.storage.psql_dos.migrations.utils import utils
from aiida.storage.psql_dos.migrator import PsqlDosMigrator

REPOSITORY_UUID_KEY = 'repository|uuid'


def test_node_repository(perform_migrations: PsqlDosMigrator):
    """Test migration of the old file repository to the disk object store."""
    # starting revision
    perform_migrations.migrate_up('django@django_0046')

    repo_path = get_filepath_container(perform_migrations.profile).parent

    # setup the storage
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
        kwargs = dict(
            user_id=user.id,
            ctime=timezone.now(),
            mtime=timezone.now(),
            label='test',
            description='',
            node_type='data.',
            repository_metadata={},
        )
        dbnode_01 = node_model(uuid=str(uuid4()), **kwargs)
        dbnode_02 = node_model(uuid=str(uuid4()), **kwargs)
        dbnode_03 = node_model(uuid=str(uuid4()), **kwargs)
        dbnode_04 = node_model(uuid=str(uuid4()), **kwargs)

        session.add_all((dbnode_01, dbnode_02, dbnode_03, dbnode_04))
        session.commit()

        dbnode_01_id = dbnode_01.id
        dbnode_02_id = dbnode_02.id
        dbnode_03_id = dbnode_03.id
        dbnode_04_id = dbnode_04.id

        utils.put_object_from_string(repo_path, dbnode_01.uuid, 'sub/path/file_b.txt', 'b')
        utils.put_object_from_string(repo_path, dbnode_01.uuid, 'sub/file_a.txt', 'a')
        utils.put_object_from_string(repo_path, dbnode_02.uuid, 'output.txt', 'output')
        utils.put_object_from_string(repo_path, dbnode_04.uuid, '.gitignore', 'test')

        # If both `path` and `raw_input` subfolders are present and `.gitignore` is in `path`, it should be ignored.
        # Cannot use `put_object_from_string` here as it statically writes under the `path` folder.
        os.makedirs(utils.get_node_repository_sub_folder(repo_path, dbnode_04.uuid, 'raw_input'), exist_ok=True)
        with open(
            os.path.join(utils.get_node_repository_sub_folder(repo_path, dbnode_04.uuid, 'raw_input'), 'input.txt'),
            'w',
            encoding='utf-8',
        ) as handle:
            handle.write('input')

    # migrate up
    perform_migrations.migrate_up('django@django_0047')

    node_model = perform_migrations.get_current_table('db_dbnode')
    setting_model = perform_migrations.get_current_table('db_dbsetting')
    with perform_migrations.session() as session:
        # check that the repository uuid is set
        repository_uuid = session.query(setting_model).filter(setting_model.key == REPOSITORY_UUID_KEY).one()
        assert repository_uuid.val is not None
        assert repository_uuid.val != ''
        assert isinstance(repository_uuid.val, str)

        node_01 = session.get(node_model, dbnode_01_id)
        node_02 = session.get(node_model, dbnode_02_id)
        node_03 = session.get(node_model, dbnode_03_id)
        node_04 = session.get(node_model, dbnode_04_id)

        assert node_01 is not None
        assert node_02 is not None
        assert node_03 is not None
        assert node_04 is not None

        assert node_01.repository_metadata == {
            'o': {
                'sub': {
                    'o': {
                        'path': {'o': {'file_b.txt': {'k': hashlib.sha256('b'.encode('utf-8')).hexdigest()}}},
                        'file_a.txt': {'k': hashlib.sha256('a'.encode('utf-8')).hexdigest()},
                    }
                }
            }
        }
        assert node_02.repository_metadata == {
            'o': {'output.txt': {'k': hashlib.sha256('output'.encode('utf-8')).hexdigest()}}
        }
        assert node_03.repository_metadata == {}
        assert node_04.repository_metadata == {
            'o': {'input.txt': {'k': hashlib.sha256('input'.encode('utf-8')).hexdigest()}}
        }

        for hashkey, content in (
            (node_01.repository_metadata['o']['sub']['o']['path']['o']['file_b.txt']['k'], b'b'),
            (node_01.repository_metadata['o']['sub']['o']['file_a.txt']['k'], b'a'),
            (node_02.repository_metadata['o']['output.txt']['k'], b'output'),
            (node_04.repository_metadata['o']['input.txt']['k'], b'input'),
        ):
            assert utils.get_repository_object(perform_migrations.profile, hashkey) == content
