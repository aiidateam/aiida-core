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
"""Tests for the migrations of legacy process attributes."""

from .test_migrations_common import TestMigrations


class TestLegacyProcessAttributeDataMigration(TestMigrations):
    """Test the migration that performs a data migration of legacy `JobCalcState`."""

    migrate_from = '0039_reset_hash'
    migrate_to = '0040_data_migration_legacy_process_attributes'

    def setUpBeforeMigration(self):
        node_process = self.DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=self.default_user.id,
            attributes={
                'process_state': 'finished',
                '_sealed': True,
                '_finished': True,
                '_failed': False,
                '_aborted': False,
                '_do_abort': False,
            }
        )
        node_process.save()
        self.node_process_id = node_process.id

        # This is an "active" modern process, due to its `process_state` and should *not* receive the `sealed` attribute
        node_process_active = self.DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=self.default_user.id,
            attributes={
                'process_state': 'created',
                '_finished': True,
                '_failed': False,
                '_aborted': False,
                '_do_abort': False,
            }
        )
        node_process_active.save()
        self.node_process_active_id = node_process_active.id

        # Note that `Data` nodes should not have these attributes in real databases but the migration explicitly
        # excludes data nodes, which is what this test is verifying, by checking they are not deleted
        node_data = self.DbNode(
            node_type='data.dict.Dict.',
            user_id=self.default_user.id,
            attributes={
                '_sealed': True,
                '_finished': True,
                '_failed': False,
                '_aborted': False,
                '_do_abort': False,
            }
        )
        node_data.save()
        self.node_data_id = node_data.id

    def test_data_migrated(self):
        """Verify that the correct attributes are removed."""
        deleted_keys = ['_sealed', '_finished', '_failed', '_aborted', '_do_abort']

        node_process = self.load_node(self.node_process_id)
        self.assertEqual(node_process.attributes['sealed'], True)
        for key in deleted_keys:
            self.assertNotIn(key, node_process.attributes)

        node_process_active = self.load_node(self.node_process_active_id)
        self.assertNotIn('sealed', node_process_active.attributes)
        for key in deleted_keys:
            self.assertNotIn(key, node_process_active.attributes)

        node_data = self.load_node(self.node_data_id)
        self.assertEqual(node_data.attributes.get('sealed', None), None)
        for key in deleted_keys:
            self.assertIn(key, node_data.attributes)
