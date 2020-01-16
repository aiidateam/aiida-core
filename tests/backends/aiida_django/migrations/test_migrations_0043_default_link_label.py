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


class TestSealUnsealedProcessesMigration(TestMigrations):
    """Test the migration that performs a data migration of legacy `JobCalcState`."""

    migrate_from = '0042_prepare_schema_reset'
    migrate_to = '0043_default_link_label'

    def setUpBeforeMigration(self):
        node_process = self.DbNode(
            node_type='process.calculation.calcjob.CalcJobNode.',
            user_id=self.default_user.id,
        )
        node_process.save()
        self.node_process_id = node_process.id

        node_data = self.DbNode(
            node_type='data.dict.Dict.',
            user_id=self.default_user.id,
        )
        node_data.save()
        self.node_data_id = node_data.id

        link = self.DbLink(input=node_data, output=node_process, type='input', label='_return')
        link.save()

    def test_data_migrated(self):
        """Verify that the link label has been renamed."""
        node = self.load_node(self.node_data_id)
        link = self.DbLink.objects.get(input=node)
        self.assertEqual(link.label, 'result')
