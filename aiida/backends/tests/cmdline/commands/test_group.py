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

from __future__ import absolute_import
from click.testing import CliRunner
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.cmd_group import (group_list, group_create, group_delete, group_rename, group_description,
                                          group_addnodes, group_removenodes, group_show)


class TestVerdiGroupSetup(AiidaTestCase):
    """
    Test suite to test verdi group command
    """

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super(TestVerdiGroupSetup, cls).setUpClass(*args, **kwargs)
        from aiida.orm import Group
        for grp in ["dummygroup1", "dummygroup2", "dummygroup3", "dummygroup4"]:
            Group(name=grp).store()

    def setUp(self):
        """
        Create runner object to run tests
        """
        self.runner = CliRunner()

    def test_help(self):
        """
        Tests help text for all group sub commands
        """
        options = ["--help"]

        # verdi group list
        result = self.runner.invoke(group_list, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group create
        result = self.runner.invoke(group_create, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group delete
        result = self.runner.invoke(group_delete, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group rename
        result = self.runner.invoke(group_rename, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group description
        result = self.runner.invoke(group_description, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group addnodes
        result = self.runner.invoke(group_addnodes, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group removenodes
        result = self.runner.invoke(group_removenodes, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        # verdi group show
        result = self.runner.invoke(group_show, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

    def test_create(self):
        """
        Test group create command
        """
        result = self.runner.invoke(group_create, ["dummygroup5"])
        self.assertIsNone(result.exception)

        ## check if newly added group in present in list
        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        self.assertIn("dummygroup5", result.output)

    def test_list(self):
        """
        Test group list command
        """
        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        for grp in ["dummygroup1", "dummygroup2"]:
            self.assertIn(grp, result.output)

    def test_delete(self):
        """
        Test group delete command
        """
        result = self.runner.invoke(group_delete, ["--force", "dummygroup3"])
        self.assertIsNone(result.exception)

        ## check if removed group is not present in list
        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        self.assertNotIn("dummygroup3", result.output)

    def test_show(self):
        """
        Test group show command
        """
        result = self.runner.invoke(group_show, ["dummygroup1"])
        self.assertIsNone(result.exception)
        for grpline in [
                "Group name", "dummygroup1", "Group type", "<user-defined>", "Group description", "<no description>"
        ]:
            self.assertIn(grpline, result.output)

    def test_description(self):
        """
        Test group description command
        """
        result = self.runner.invoke(group_description, ["dummygroup2", "It is a new description"])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(group_show, ["dummygroup2"])
        self.assertIsNone(result.exception)
        self.assertIn("Group description", result.output)
        self.assertNotIn("<no description>", result.output)
        self.assertIn("It is a new description", result.output)

    def test_rename(self):
        """
        Test group rename command
        """
        result = self.runner.invoke(group_rename, ["dummygroup4", "renamedgroup"])
        self.assertIsNone(result.exception)

        ## check if group list command shows changed group name
        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        self.assertNotIn("dummygroup4", result.output)
        self.assertIn("renamedgroup", result.output)

    def test_addremovenodes(self):
        """
        Test group addnotes command
        """
        from aiida.orm.calculation import Calculation
        calc = Calculation()
        calc._set_attr("attr1", "OK")  # pylint: disable=protected-access
        calc._set_attr("attr2", "OK")  # pylint: disable=protected-access
        calc.store()

        result = self.runner.invoke(group_addnodes, ["--force", "--group=dummygroup1", calc.uuid])
        self.assertIsNone(result.exception)
        # check if node is added in group using group show command
        result = self.runner.invoke(group_show, ["dummygroup1"])
        self.assertIsNone(result.exception)
        self.assertIn("Calculation", result.output)
        self.assertIn(str(calc.pk), result.output)

        ## remove same node
        result = self.runner.invoke(group_removenodes, ["--force", "--group=dummygroup1", calc.uuid])
        self.assertIsNone(result.exception)
        # check if node is added in group using group show command
        result = self.runner.invoke(group_show, ['-r', 'dummygroup1'])
        self.assertIsNone(result.exception)
        self.assertNotIn("Calculation", result.output)
        self.assertNotIn(str(calc.pk), result.output)
