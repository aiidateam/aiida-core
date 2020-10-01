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

from aiida.backends.general.migrations import utils
from .test_migrations_common import TestMigrations


class TestRepositoryMigration(TestMigrations):
    """Test migration of the old file repository to the disk object store."""

    migrate_from = '0046_add_node_repository_metadata'
    migrate_to = '0047_migrate_repository'

    def setUpBeforeMigration(self):
        DbNode = self.apps.get_model('db', 'DbNode')
        dbnode_01 = DbNode(user_id=self.default_user.id)
        dbnode_01.save()
        dbnode_02 = DbNode(user_id=self.default_user.id)
        dbnode_02.save()
        dbnode_03 = DbNode(user_id=self.default_user.id)
        dbnode_03.save()
        self.node_01_pk = dbnode_01.pk
        self.node_02_pk = dbnode_02.pk
        self.node_03_pk = dbnode_03.pk

        utils.put_object_from_string(dbnode_01.uuid, 'sub/path/file_b.txt', 'b')
        utils.put_object_from_string(dbnode_01.uuid, 'sub/file_a.txt', 'a')
        utils.put_object_from_string(dbnode_02.uuid, 'output.txt', 'output')

    def test_migration(self):
        """Test that the files are correctly migrated."""
        DbNode = self.apps.get_model('db', 'DbNode')
        node_01 = DbNode.objects.get(pk=self.node_01_pk)
        node_02 = DbNode.objects.get(pk=self.node_02_pk)
        node_03 = DbNode.objects.get(pk=self.node_03_pk)

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
        assert node_03.repository_metadata is None

        for hashkey, content in (
            (node_01.repository_metadata['o']['sub']['o']['path']['o']['file_b.txt']['k'], b'b'),
            (node_01.repository_metadata['o']['sub']['o']['file_a.txt']['k'], b'a'),
            (node_02.repository_metadata['o']['output.txt']['k'], b'output'),
        ):
            assert utils.get_repository_object(hashkey) == content
