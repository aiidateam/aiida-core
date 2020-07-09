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
"""Test migration adding the `repository_metadata` column to the `Node` model."""

from .test_migrations_common import TestMigrations


class TestNodeRepositoryMetadataMigration(TestMigrations):
    """Test migration adding the `repository_metadata` column to the `Node` model."""

    migrate_from = '0045_dbgroup_extras'
    migrate_to = '0046_add_node_repository_metadata'

    def setUpBeforeMigration(self):
        DbNode = self.apps.get_model('db', 'DbNode')
        dbnode = DbNode(user_id=self.default_user.id)
        dbnode.save()
        self.node_pk = dbnode.pk

    def test_group_string_update(self):
        """Test that the column is added and null by default."""
        DbNode = self.apps.get_model('db', 'DbNode')
        node = DbNode.objects.get(pk=self.node_pk)
        assert hasattr(node, 'repository_metadata')
        assert node.repository_metadata is None
