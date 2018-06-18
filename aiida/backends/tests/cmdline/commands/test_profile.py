from click.testing import CliRunner
from aiida.backends.testbase import AiidaTestCase

class TestVerdiProfileSetup(AiidaTestCase):

    def setUp(self):
        self.runner = CliRunner()

    def test_help(self):
        options = ["--help"]
        from aiida.cmdline.commands.profile import (profile_list,
                                                    profile_setdefault,
                                                    profile_delete)
        result = self.runner.invoke(profile_list, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        result = self.runner.invoke(profile_setdefault, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

        result = self.runner.invoke(profile_delete, options)
        self.assertIsNone(result.exception)
        self.assertIn('Usage', result.output)

    def test_list(self):
        from aiida.cmdline.commands.profile import profile_list
        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception)
        self.assertIn('Configuration folder:', result.output)
        self.assertIn('*', result.output)
