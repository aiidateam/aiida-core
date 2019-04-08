# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic tests that need the use of the DB."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from click.testing import CliRunner  # pylint: disable=import-error
from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import with_temp_dir
from aiida.cmdline.commands.cmd_export import migrate
from aiida.orm.importexport import import_data
from aiida.backends.tests.utils.fixtures import get_archive_file


class TestExportFileMigrationV03toV04(AiidaTestCase):
    """Test migration of exported files"""

    def setUp(self):
        self.reset_database()
        self.cli_runner = CliRunner()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_v3_to_v4(self, temp_dir):
        """Test migration of exported files from v0.3 to v0.4"""
        input_file = get_archive_file('export_v0.3_no_UPF.aiida', filepath='export/migrate')
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Known export file content used for checks
        node_count = 10
        known_struct_label = ''
        known_cell = [[4, 0, 0], [0, 4, 0], [0, 0, 4]]
        known_kinds = [
            {
                'name': 'Ba',
                'mass': 137.327,
                'weights': [1],
                'symbols': ['Ba']
            },
            {
                'name': 'Ti',
                'mass': 47.867,
                'weights': [1],
                'symbols': ['Ti']
            },
            {
                'name': 'O',
                'mass': 15.9994,
                'weights': [1],
                'symbols': ['O']
            },
        ]

        # Perform the migration
        options = [input_file, output_file]
        result = self.cli_runner.invoke(migrate, options)
        self.assertIsNone(result.exception, result.output)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Do the necessary checks
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), node_count)

        # Verify that CalculationNodes have non-empty attribute dictionaries
        builder = orm.QueryBuilder().append(orm.CalculationNode)
        for [calculation] in builder.iterall():
            self.assertIsInstance(calculation.attributes, dict)
            self.assertNotEqual(len(calculation.attributes), 0)

        # Verify that the StructureData maintained its label, cell, and kinds
        builder = orm.QueryBuilder().append(orm.StructureData)
        structure = builder.all()[0][0]
        self.assertEqual(structure.label, known_struct_label)
        self.assertEqual(structure.cell, known_cell)

        builder = orm.QueryBuilder().append(orm.StructureData, project=['attributes.kinds'])
        for [kinds] in builder.iterall():
            self.assertEqual(len(kinds), len(known_kinds))
            for kind in kinds:
                self.assertIn(kind, known_kinds)

        # Check that there is a StructureData that is an input of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.StructureData, tag='structure')
        builder.append(orm.CalculationNode, with_incoming='structure')
        self.assertGreater(len(builder.all()), 0)

        # Check that there is a RemoteData that is the output of a CalculationNode
        builder = orm.QueryBuilder()
        builder.append(orm.CalculationNode, tag='parent')
        builder.append(orm.RemoteData, with_incoming='parent')
        self.assertGreater(len(builder.all()), 0)

    @with_temp_dir
    def test_no_node_export(self, temp_dir):
        """Test migration of export file that has no Nodes"""
        input_file = get_archive_file('export_v0.3_no_Nodes.aiida', filepath='export/migrate')
        output_file = os.path.join(temp_dir, 'output_file.aiida')

        # Known entities
        computer_uuids = [self.computer.uuid]  # pylint: disable=no-member
        user_emails = [orm.User.objects.get_default().email]

        # Known export file content used for checks
        node_count = 0
        computer_count = 1 + 1  # localhost is always present
        computer_uuids.append('4f33c6fd-b624-47df-9ffb-a58f05d323af')
        user_emails.append('aiida@localhost')

        # Perform the migration
        options = [input_file, output_file]
        result = self.cli_runner.invoke(migrate, options)
        self.assertIsNone(result.exception, result.output)

        # Load the migrated file
        import_data(output_file, silent=True)

        # Check known number of entities is present
        self.assertEqual(orm.QueryBuilder().append(orm.Node).count(), node_count)
        self.assertEqual(orm.QueryBuilder().append(orm.Computer).count(), computer_count)

        # Check unique identifiers
        computers = orm.QueryBuilder().append(orm.Computer, project=['uuid']).all()[0][0]
        users = orm.QueryBuilder().append(orm.User, project=['email']).all()[0][0]
        self.assertIn(computers, computer_uuids)
        self.assertIn(users, user_emails)
