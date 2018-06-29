"""
Test suite to test verdi group command
"""

from click.testing import CliRunner
from aiida.backends.testbase import AiidaTestCase
from aiida.cmdline.commands.group import (group_list, group_create, group_delete, group_rename,
                                          group_description, group_addnodes, group_removenodes, group_show)

class TestVerdiGroupSetup(AiidaTestCase):
    """
    Test suite to test verdi group command
    """

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

    def test_subcommands(self):
        """
        Test all  sub commands of verdi group command
        """

        ## create 2 groups
        result = self.runner.invoke(group_create, ["dummygroup1"])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(group_create, ["dummygroup2"])
        self.assertIsNone(result.exception)

        ## list available groups
        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        self.assertIn("dummygroup1", result.output)
        self.assertIn("dummygroup2", result.output)

        ## show group dummygroup1
        result = self.runner.invoke(group_show, ["dummygroup1"])
        self.assertIsNone(result.exception)
        self.assertIn("Group name", result.output)
        self.assertIn("dummygroup1", result.output)
        self.assertIn("Group type", result.output)
        self.assertIn("<user-defined>", result.output)
        self.assertIn("Group description", result.output)
        self.assertIn("<no description>", result.output)

        ## change description
        result = self.runner.invoke(group_description, ["dummygroup1", "It is a new description"])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(group_show, ["dummygroup1"])
        self.assertIsNone(result.exception)
        self.assertIn("Group description", result.output)
        self.assertNotIn("<no description>", result.output)
        self.assertIn("It is a new description", result.output)

        ## rename group
        result = self.runner.invoke(group_rename, ["dummygroup1", "changedgroup"])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        self.assertNotIn("dummygroup1", result.output)
        self.assertIn("changedgroup", result.output)

        ## delete group
        result = self.runner.invoke(group_delete, ["--force", "changedgroup"])
        self.assertIsNone(result.exception)

        result = self.runner.invoke(group_list)
        self.assertIsNone(result.exception)
        self.assertNotIn("changedgroup", result.output)

        ## add and remove nodes
        from aiida.orm.calculation import Calculation
        calc = Calculation()
        calc._set_attr("attr1", "OK")
        calc._set_attr("attr2", "OK")
        calc.store()

        result = self.runner.invoke(group_addnodes, ["--force", "--group=dummygroup2", calc.uuid])
        self.assertIsNone(result.exception)
        result = self.runner.invoke(group_show, ["dummygroup2"])
        self.assertIsNone(result.exception)
        self.assertIn("Calculation", result.output)
        self.assertIn(str(calc.pk), result.output)

        result = self.runner.invoke(group_removenodes, ["--force", "--group=dummygroup2", calc.uuid])
        self.assertIsNone(result.exception)
        result = self.runner.invoke(group_show, ["dummygroup2"])
        self.assertIsNone(result.exception)
        self.assertNotIn("Calculation", result.output)
        self.assertNotIn(str(calc.pk), result.output)




