# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Test suite to test verdi group command
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from click.testing import CliRunner
import traceback
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_group import (group_list, group_create, group_delete, group_rename, group_description,
                                              group_addnodes, group_removenodes, group_show, group_copy)


class TestVerdiGroupSetup(AiidaTestCase):
    """
    Test suite to test verdi group command
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiGroupSetup, cls).setUpClass(*args, **kwargs)
        from aiida.orm import Group
        for grp in ["dummygroup1", "dummygroup2", "dummygroup3", "dummygroup4"]:
            Group(label=grp).store()

    def setUp(self):
        """
        Create runner object to run tests
        """
        self.cli_runner = CliRunner()

    def test_help(self):
        """
        Tests help text for all group sub commands
        """
        options = ["--help"]

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
        result = self.cli_runner.invoke(group_addnodes, options)
        self.assertIsNone(result.exception, result.output)
        self.assertIn('Usage', result.output)

        # verdi group removenodes
        result = self.cli_runner.invoke(group_removenodes, options)
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
        """Test group create command."""
        result = self.cli_runner.invoke(group_create, ["dummygroup5"])
        self.assertClickResultNoException(result)

        # check if newly added group in present in list
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)

        self.assertIn("dummygroup5", result.output)

    def test_list(self):
        """Test group list command."""
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)

        for grp in ["dummygroup1", "dummygroup2"]:
            self.assertIn(grp, result.output)

    def test_copy(self):
        """Test group copy command."""
        result = self.cli_runner.invoke(group_copy, ["dummygroup1", "dummygroup2"])
        self.assertClickResultNoException(result)

        self.assertIn("Success", result.output)

    def test_delete(self):
        """
        Test group delete command
        """
        result = self.cli_runner.invoke(group_delete, ["--force", "dummygroup3"])
        self.assertClickResultNoException(result)

        # check if removed group is not present in list
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)
        self.assertNotIn("dummygroup3", result.output)

    def test_show(self):
        """
        Test group show command
        """
        result = self.cli_runner.invoke(group_show, ["dummygroup1"])
        self.assertClickResultNoException(result)

        for grpline in [
            "Group label", "dummygroup1", "Group type_string", "user", "Group description", "<no description>"
        ]:
            self.assertIn(grpline, result.output)

    def test_description(self):
        """
        Test group description command
        """
        result = self.cli_runner.invoke(group_description, ["dummygroup2", "It is a new description"])
        self.assertIsNone(result.exception, result.output)

        result = self.cli_runner.invoke(group_show, ["dummygroup2"])
        self.assertClickResultNoException(result)
        self.assertIn("Group description", result.output)
        self.assertNotIn("<no description>", result.output)
        self.assertIn("It is a new description", result.output)

    def test_rename(self):
        """
        Test group rename command
        """
        result = self.cli_runner.invoke(group_rename, ["dummygroup4", "renamedgroup"])
        self.assertIsNone(result.exception, result.output)

        # check if group list command shows changed group name
        result = self.cli_runner.invoke(group_list)
        self.assertClickResultNoException(result)
        self.assertNotIn("dummygroup4", result.output)
        self.assertIn("renamedgroup", result.output)

    def test_addremovenodes(self):
        """
        Test group addnotes command
        """
        from aiida.orm import CalculationNode

        node = CalculationNode()
        node.set_attribute('attr1', 'OK')
        node.set_attribute('attr2', 'OK')
        node.store()

        result = self.cli_runner.invoke(group_addnodes, ['--force', '--group=dummygroup1', node.uuid])
        self.assertIsNone(result.exception, result.output)
        # check if node is added in group using group show command
        result = self.cli_runner.invoke(group_show, ['dummygroup1'])
        self.assertClickResultNoException(result)
        self.assertIn('CalculationNode', result.output)
        self.assertIn(str(node.pk), result.output)

        # remove same node
        result = self.cli_runner.invoke(group_removenodes, ['--force', '--group=dummygroup1', node.uuid])
        self.assertIsNone(result.exception, result.output)
        # check if node is added in group using group show command
        result = self.cli_runner.invoke(group_show, ['-r', 'dummygroup1'])
        self.assertIsNone(result.exception, result.output)
        self.assertNotIn('CalculationNode', result.output)
        self.assertNotIn(str(node.pk), result.output)
