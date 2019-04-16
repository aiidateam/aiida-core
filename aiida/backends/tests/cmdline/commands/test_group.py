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
from aiida.common import exceptions
from aiida.cmdline.commands.cmd_group import (group_list, group_create, group_delete, group_relabel, group_description,
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

        # verdi group relabel
        result = self.cli_runner.invoke(group_relabel, options)
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
        group_01 = orm.Group(label='group_test_delete_01').store()
        group_02 = orm.Group(label='group_test_delete_02').store()

        result = self.cli_runner.invoke(group_delete, ['--force', 'group_test_delete_01'])
        self.assertClickResultNoException(result)

        # Verify that removed group is not present in list
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)
        self.assertNotIn('group_test_delete_01', result.output)

        node_01 = orm.CalculationNode().store()
        node_02 = orm.CalculationNode().store()

        # Add some nodes and then use `verdi group delete --clear` to delete a node even when it contains nodes
        group = orm.load_group(label='group_test_delete_02')
        group.add_nodes([node_01, node_02])
        self.assertEqual(group.count(), 2)

        # Calling delete on a group without the `--clear` option should raise
        result = self.cli_runner.invoke(group_delete, ['--force', 'group_test_delete_02'])
        self.assertIsNotNone(result.exception, result.output)

        # With `--clear` option should delete group and nodes
        result = self.cli_runner.invoke(group_delete, ['--force', '--clear', 'group_test_delete_02'])
        self.assertClickResultNoException(result)

        with self.assertRaises(exceptions.NotExistent):
            group = orm.load_group(label='group_test_delete_02')

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
        description = 'It is a new description'
        group = orm.load_group(label='dummygroup2')
        self.assertNotEqual(group.description, description)

        # Change the description of the group
        result = self.cli_runner.invoke(group_description, [group.label, description])
        self.assertClickResultNoException(result)
        self.assertEqual(group.description, description)

        # When no description argument is passed the command should just echo the current description
        result = self.cli_runner.invoke(group_description, [group.label])
        self.assertClickResultNoException(result)
        self.assertIn(description, result.output)

    def test_relabel(self):
        """Test `verdi group relabel` command."""
        result = self.cli_runner.invoke(group_relabel, ['dummygroup4', 'relabeled_group'])
        self.assertIsNone(result.exception, result.output)

        # check if group list command shows changed group name
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)
        self.assertNotIn('dummygroup4', result.output)
        self.assertIn('relabeled_group', result.output)

    def test_add_remove_nodes(self):
        """Test `verdi group remove-nodes` command."""
        node_01 = orm.CalculationNode().store()
        node_02 = orm.CalculationNode().store()
        node_03 = orm.CalculationNode().store()

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

    def test_copy_existing_group(self):
        """Test user is prompted to continue if destination group exists and is not empty"""
        source_label = "source_copy_existing_group"
        dest_label = "dest_copy_existing_group"

        # Create source group with nodes
        calc_s1 = orm.CalculationNode().store()
        calc_s2 = orm.CalculationNode().store()
        nodes_source_group = {str(node.uuid) for node in [calc_s1, calc_s2]}
        source_group = orm.Group(label=source_label).store()
        source_group.add_nodes([calc_s1, calc_s2])

        # Copy using `verdi group copy` - making sure all is successful
        options = [source_label, dest_label]
        result = self.cli_runner.invoke(group_copy, options)
        self.assertClickResultNoException(result)
        self.assertIn(
            "Success: Nodes copied from group<{}> to group<{}>".format(source_label, dest_label),
            result.output,
            result.exception)

        # Check destination group exists with source group's nodes
        dest_group = orm.load_group(label=dest_label)
        self.assertEqual(dest_group.count(), 2)
        nodes_dest_group = {str(node.uuid) for node in dest_group.nodes}
        self.assertSetEqual(nodes_source_group, nodes_dest_group)

        # Copy again, making sure an abort error is raised, since no user input can be made and default is abort
        result = self.cli_runner.invoke(group_copy, options)
        self.assertIsNotNone(result.exception, result.output)
        self.assertIn(
            "Warning: Destination group<{}> already exists and is not empty.".format(dest_label),
            result.output,
            result.exception)

        # Check destination group is unchanged
        dest_group = orm.load_group(label=dest_label)
        self.assertEqual(dest_group.count(), 2)
        nodes_dest_group = {str(node.uuid) for node in dest_group.nodes}
        self.assertSetEqual(nodes_source_group, nodes_dest_group)
