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
    migrate_to = '0046_inline_attributes'

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
        calcnode = self.DbNode(
            node_type='process.calculation.calcfunction.CalcFunctionNode.',
            user_id=self.default_user.id,
            attributes={
                'sealed': True,
                'namespace': '__main__',
                'source_code': self.get_source_code(full_file=False),
                'source_file': self.get_source_code(full_file=True),
                'function_name': 'sum_inline',
                'first_line_source_code': 4,
            },
        )
        calcnode.save()
        self.calcnode_id = calcnode.id
        #print(self.load_node(self.calcnode_id).attributes)
        #calcnode.attributes['function_namespace'] = calcnode.attributes['namespace']
        #calcnode.save()
        #print(self.load_node(self.calcnode_id).attributes)

    def test_data_migrated(self):
        """Test that the model now has an extras column with empty dictionary as default."""
        calcnode = self.load_node(self.calcnode_id)

        # Pre existing and renamed attributes
        self.assertEqual(calcnode.attributes['sealed'], True)
        self.assertEqual(calcnode.attributes['function_name'], 'sum_inline')
        self.assertEqual(calcnode.attributes['function_namespace'], '__main__')
        self.assertEqual(calcnode.attributes['function_starting_line_number'], 4)

        # Newly determined attributes
        self.assertEqual(calcnode.attributes['exit_status'], 0)
        self.assertEqual(calcnode.attributes['process_state'], 'finished')  #USE ENUM?
        self.assertEqual(calcnode.attributes['process_label'], 'Legacy InlineCalculation')
        self.assertEqual(calcnode.attributes['function_number_of_lines'], 3)

        # Old attributes that got renamed or removed
        with self.assertRaises(KeyError):
            _ = calcnode.attributes['namespace']
        with self.assertRaises(KeyError):
            _ = calcnode.attributes['source_code']
        with self.assertRaises(KeyError):
            _ = calcnode.attributes['source_file']
        with self.assertRaises(KeyError):
            _ = calcnode.attributes['first_line_source_code']

        # New attributes that are not set
        with self.assertRaises(KeyError):
            _ = calcnode.attributes['version']

        # Source file in repository:
        repo_data = utils.get_object_from_repository(calcnode.uuid, 'source_file')
        self.assertEqual(repo_data, self.get_source_code(full_file=True))
