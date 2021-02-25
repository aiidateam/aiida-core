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
"""Test the migration that updates the attributes of InlineFunctions that have been transformed into CalcFunctions."""
from aiida.backends.general.migrations import utils
from .test_migrations_common import TestMigrations


class TestCalcFunctionAttributesMigration(TestMigrations):
    """Test the migration for the attributes of InlineFunctions that have been transformed into CalcFunctions."""

    migrate_from = '0045_dbgroup_extras'
    migrate_to = '0046_inline_calc_attributes'

    @staticmethod
    def get_source_code(full_file=False):
        """Returns a string containing the source code for the calcfunction"""

        # yapf: disable
        text_i = ('from aiida import orm\n'
                  'from aiida.engine import calcfunction\n'
        )
        text_t = ('@calcfunction\n'
                  'def sum_inline( int1, int2 ):\n'
                  '    return int1 + int2\n'
        )
        text_f = ('num1 = orm.Int(2)\n'
                  'num2 = orm.Int(3)\n'
                  'num3 = sum_inline( int1, int2 )\n'
                  'print(num3)\n'
        )
        # yapf: enable

        if full_file:
            text_t = text_i + '\n' + text_t + '\n' + text_f

        return text_t

    def setUpBeforeMigration(self):
        calcnode_old = self.DbNode(
            node_type='process.calculation.calcfunction.CalcFunctionNode.',
            user_id=self.default_user.id,
            attributes={
                'sealed': True,
                'function_name': 'sum_inline',
                'namespace': '__main__',
                'first_line_source_code': 4,
                'source_code': self.get_source_code(full_file=False),
                'source_file': self.get_source_code(full_file=True),
            },
        )
        calcnode_old.save()
        self.calcnode_old_id = calcnode_old.id

        self.attributes_new = {
            'sealed': True,
            'function_name': 'sum_inline',
            'function_namespace': '__main__',
            'function_starting_line_number': 20,
            'process_label': 'sum_inline',
            'process_state': 'excepted',
            'exit_status': 1,
        }
        calcnode_new = self.DbNode(
            node_type='process.calculation.calcfunction.CalcFunctionNode.',
            user_id=self.default_user.id,
            attributes=self.attributes_new,
        )
        calcnode_new.save()
        self.calcnode_new_id = calcnode_new.id

    def test_data_migrated(self):
        """Test that the attributes were correctly migrated."""
        calcnode = self.load_node(self.calcnode_old_id)

        # Check that new/renamed attributes have the correct value:
        updated_attributes = {
            # Pre existing and renamed attributes
            'sealed': True,
            'function_name': 'sum_inline',
            'function_namespace': '__main__',
            'function_starting_line_number': 4,
            # Newly determined attributes
            'exit_status': 0,
            'process_state': 'finished',
            'process_label': 'Legacy InlineCalculation',
            'function_number_of_lines': 3,
        }
        for key, val in updated_attributes.items():
            self.assertEqual(calcnode.attributes[key], val)

        # Check that removed attributes (and 'version') are no longer there:
        abscent_attributes = ['namespace', 'source_code', 'source_file', 'first_line_source_code', 'version']
        for abscent_attribute in abscent_attributes:
            self.assertFalse(abscent_attribute in calcnode.attributes)

        # Check that the source file is in the repository:
        repo_data = utils.get_object_from_repository(calcnode.uuid, 'source_file')
        self.assertEqual(repo_data, self.get_source_code(full_file=True))

        # Check that the bystander node was not modified:
        calcnode = self.load_node(self.calcnode_new_id)
        self.assertFalse('function_number_of_lines' in calcnode.attributes)
        for key, val in self.attributes_new.items():
            self.assertEqual(calcnode.attributes[key], val)
