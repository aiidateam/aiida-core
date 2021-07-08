# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module,invalid-name
"""Test migration of the old file repository to the disk object store."""
import hashlib
import os

from aiida.backends.general.migrations import utils
from .test_migrations_common import TestMigrations

REPOSITORY_UUID_KEY = 'repository|uuid'


class TestRepositoryMigration(TestMigrations):
    """Test migration of the old file repository to the disk object store."""

    migrate_from = '0046_add_node_repository_metadata'
    migrate_to = '0047_migrate_repository'

    def setUpBeforeMigration(self):
        DbNode = self.apps.get_model('db', 'DbNode')
        DbSetting = self.apps.get_model('db', 'DbSetting')

        dbnode_01 = DbNode(user_id=self.default_user.id)
        dbnode_01.save()
        dbnode_02 = DbNode(user_id=self.default_user.id)
        dbnode_02.save()
        dbnode_03 = DbNode(user_id=self.default_user.id)
        dbnode_03.save()
        dbnode_04 = DbNode(user_id=self.default_user.id)
        dbnode_04.save()

        self.node_01_pk = dbnode_01.pk
        self.node_02_pk = dbnode_02.pk
        self.node_03_pk = dbnode_03.pk
        self.node_04_pk = dbnode_04.pk

        utils.put_object_from_string(dbnode_01.uuid, 'sub/path/file_b.txt', 'b')
        utils.put_object_from_string(dbnode_01.uuid, 'sub/file_a.txt', 'a')
        utils.put_object_from_string(dbnode_02.uuid, 'output.txt', 'output')
        utils.put_object_from_string(dbnode_04.uuid, '.gitignore', 'test')

        # If both `path` and `raw_input` subfolders are present and `.gitignore` is in `path`, it should be ignored.
        # Cannot use `put_object_from_string` here as it statically writes under the `path` folder.
        raw_input_sub_folder = utils.get_node_repository_sub_folder(dbnode_04.uuid, subfolder='raw_input')
        os.makedirs(raw_input_sub_folder, exist_ok=True)
        with open(os.path.join(raw_input_sub_folder, 'input.txt'), 'w', encoding='utf-8') as handle:
            handle.write('input')

        # When multiple migrations are ran, it is possible that migration 0047 is run at a point where the repository
        # container does not have a UUID (at that point in the migration) and so the setting gets set to `None`. This
        # should only happen during testing, and in this case we delete it first so the actual migration gets to set it.
        if DbSetting.objects.filter(key=REPOSITORY_UUID_KEY).exists():
            DbSetting.objects.get(key=REPOSITORY_UUID_KEY).delete()

    def test_migration(self):
        """Test that the files are correctly migrated."""
        DbNode = self.apps.get_model('db', 'DbNode')
        DbSetting = self.apps.get_model('db', 'DbSetting')

        node_01 = DbNode.objects.get(pk=self.node_01_pk)
        node_02 = DbNode.objects.get(pk=self.node_02_pk)
        node_03 = DbNode.objects.get(pk=self.node_03_pk)
        node_04 = DbNode.objects.get(pk=self.node_04_pk)

        assert node_01.repository_metadata == {
            'o': {
                'sub': {
                    'o': {
                        'path': {
                            'o': {
                                'file_b.txt': {
                                    'k': hashlib.sha256('b'.encode('utf-8')).hexdigest()
                                }
                            }
                        },
                        'file_a.txt': {
                            'k': hashlib.sha256('a'.encode('utf-8')).hexdigest()
                        }
                    }
                }
            }
        }
        assert node_02.repository_metadata == {
            'o': {
                'output.txt': {
                    'k': hashlib.sha256('output'.encode('utf-8')).hexdigest()
                }
            }
        }
        assert node_03.repository_metadata == {}
        assert node_04.repository_metadata == {
            'o': {
                'input.txt': {
                    'k': hashlib.sha256('input'.encode('utf-8')).hexdigest()
                }
            }
        }

        for hashkey, content in (
            (node_01.repository_metadata['o']['sub']['o']['path']['o']['file_b.txt']['k'], b'b'),
            (node_01.repository_metadata['o']['sub']['o']['file_a.txt']['k'], b'a'),
            (node_02.repository_metadata['o']['output.txt']['k'], b'output'),
            (node_04.repository_metadata['o']['input.txt']['k'], b'input'),
        ):
            assert utils.get_repository_object(hashkey) == content

        repository_uuid = DbSetting.objects.get(key=REPOSITORY_UUID_KEY)
        assert repository_uuid is not None
        assert isinstance(repository_uuid.val, str)
