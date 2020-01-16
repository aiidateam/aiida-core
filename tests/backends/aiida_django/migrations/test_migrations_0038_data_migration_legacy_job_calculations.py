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
"""
Tests for the migrations of the attributes, extras and settings from EAV to JSONB
Migration 0037_attributes_extras_settings_json
"""
from aiida.backends.general.migrations.calc_state import STATE_MAPPING
from .test_migrations_common import TestMigrations


class TestLegacyJobCalcStateDataMigration(TestMigrations):
    """Test the migration that performs a data migration of legacy `JobCalcState`."""

    migrate_from = '0037_attributes_extras_settings_json'
    migrate_to = '0038_data_migration_legacy_job_calculations'

    def setUpBeforeMigration(self):
        self.nodes = {}

        for state in STATE_MAPPING:
            node = self.DbNode(
                node_type='process.calculation.calcjob.CalcJobNode.',
                user_id=self.default_user.id,
                attributes={'state': state}
            )
            node.save()

            self.nodes[state] = node.id

    def test_data_migrated(self):
        """Verify that the `process_state`, `process_status` and `exit_status` are set correctly."""
        for state, pk in self.nodes.items():
            node = self.load_node(pk)
            self.assertEqual(node.attributes.get('process_state', None), STATE_MAPPING[state].process_state)
            self.assertEqual(node.attributes.get('process_status', None), STATE_MAPPING[state].process_status)
            self.assertEqual(node.attributes.get('exit_status', None), STATE_MAPPING[state].exit_status)
            self.assertEqual(
                node.attributes.get('process_label'), 'Legacy JobCalculation'
            )  # All nodes should have this label
            self.assertIsNone(node.attributes.get('state', None))  # The old state should have been removed

            exit_status = node.attributes.get('exit_status', None)
            if exit_status is not None:
                self.assertIsInstance(exit_status, int)
