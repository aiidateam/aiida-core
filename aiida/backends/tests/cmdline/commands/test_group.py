# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `verdi group` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_group import (group_list, group_create, group_delete, group_rename, group_description,
                                              group_add_nodes, group_remove_nodes, group_show, group_copy)


class TestVerdiGroup(AiidaTestCase):
    """Tests for the `verdi group` command."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiGroup, cls).setUpClass(*args, **kwargs)
        for group in ['dummygroup1', 'dummygroup2', 'dummygroup3', 'dummygroup4']:
            orm.Group(label=group).store()

    def setUp(self):
        """Create runner object to run tests."""
        from click.testing import CliRunner
        self.cli_runner = CliRunner()

    def test_help(self):
        """Tests help text for all group sub commands."""
        options = ['--help']

        # verdi group list
        result = self.cli_runner.invoke(group_list, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group create
        result = self.cli_runner.invoke(group_create, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group delete
        result = self.cli_runner.invoke(group_delete, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group rename
        result = self.cli_runner.invoke(group_rename, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group description
        result = self.cli_runner.invoke(group_description, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group addnodes
        result = self.cli_runner.invoke(group_add_nodes, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group removenodes
        result = self.cli_runner.invoke(group_remove_nodes, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group show
        result = self.cli_runner.invoke(group_show, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group copy
        result = self.cli_runner.invoke(group_copy, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

    def test_create(self):
        """Test `verdi group create` command."""
        result = self.cli_runner.invoke(group_create, ['dummygroup5'])
        self.assertClickResultNoException(result)

        # check if newly added group in present in list
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)

        self.assertIn('dummygroup5', result.output)

    def test_list(self):
        """Test `verdi group list` command."""
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)

        for grp in ['dummygroup1', 'dummygroup2']:
            self.assertIn(grp, result.output)

    def test_copy(self):
        """Test `verdi group copy` command."""
        result = self.cli_runner.invoke(group_copy, ['dummygroup1', 'dummygroup2'])
        self.assertClickResultNoException(result)

        self.assertIn('Success', result.output)

    def test_delete(self):
        """Test `verdi group delete` command."""
        result = self.cli_runner.invoke(group_delete, ['--force', 'dummygroup3'])
        self.assertClickResultNoException(result)

        # check if removed group is not present in list
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)
        self.assertNotIn('dummygroup3', result.output)

    def test_show(self):
        """Test `verdi group show` command."""
        result = self.cli_runner.invoke(group_show, ['dummygroup1'])
        self.assertClickResultNoException(result)

        for grpline in [
            'Group label', 'dummygroup1', 'Group type_string', 'user', 'Group description', '<no description>'
        ]:
            self.assertIn(grpline, result.output)

    def test_description(self):
        """Test `verdi group description` command."""
        result = self.cli_runner.invoke(group_description, ['dummygroup2', 'It is a new description'])
        self.assertIsNone(result.exception, result.output)

        result = self.cli_runner.invoke(group_show, ['dummygroup2'])
        self.assertClickResultNoException(result)
        self.assertIn('Group description', result.output)
        self.assertNotIn('<no description>', result.output)
        self.assertIn('It is a new description', result.output)

    def test_rename(self):
        """Test `verdi group rename` command."""
        result = self.cli_runner.invoke(group_rename, ['dummygroup4', 'renamedgroup'])
        self.assertIsNone(result.exception, result.output)

        # check if group list command shows changed group name
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)
        self.assertNotIn('dummygroup4', result.output)
        self.assertIn('renamedgroup', result.output)

    def test_add_remove_nodes(self):
        """Test `verdi group remove-nodes` command."""
        from aiida.orm import CalculationNode

        node_01 = CalculationNode().store()
        node_02 = CalculationNode().store()
        node_03 = CalculationNode().store()

        result = self.cli_runner.invoke(group_add_nodes, ['--force', '--group=dummygroup1', node_01.uuid])
        self.assertClickResultNoException(result)

        # Check if node is added in group using group show command
        result = self.cli_runner.invoke(group_show, ['dummygroup1'])
        self.assertClickResultNoException(result)
        self.assertIn('CalculationNode', result.output)
        self.assertIn(str(node_01.pk), result.output)

        # Remove same node
        result = self.cli_runner.invoke(group_remove_nodes, ['--force', '--group=dummygroup1', node_01.uuid])
        self.assertIsNone(result.exception, result.output)

        # Check if node is added in group using group show command
        result = self.cli_runner.invoke(group_show, ['-r', 'dummygroup1'])
        self.assertClickResultNoException(result)
        self.assertNotIn('CalculationNode', result.output)
        self.assertNotIn(str(node_01.pk), result.output)

        # Add all three nodes and then use `verdi group remove-nodes --clear` to remove them all
        group = orm.load_group(label='dummygroup1')
        group.add_nodes([node_01, node_02, node_03])
        self.assertEqual(group.count(), 3)

        result = self.cli_runner.invoke(group_remove_nodes, ['--force', '--clear', '--group=dummygroup1'])
        self.assertClickResultNoException(result)
        self.assertEqual(group.count(), 0)
