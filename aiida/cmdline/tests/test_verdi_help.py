"""Bug regression tests for ``verdi help``"""
import unittest

from aiida.cmdline.verdilib import Help, Import

from .common import captured_output


class VerdiHelpTest(unittest.TestCase):
    """Make sure fixed bugs stay fixed"""

    def setUp(self):
        self.help_cmd = Help()

    def test_verdi_help_full_string(self):
        """
        Prevent regression of bug #700

        ``verdi help`` was printing only the first letter of the docstring
        of non-click commands
        """
        self.assertFalse(
            hasattr(Import, '_ctx'),
            'This test must use a non-click verdi subcommand')
        fail_msg = ('Has the docstring for ``verdi import`` changed? '
                    'If not, this is a regression of #700')
        with captured_output() as (out, _):
            try:
                self.help_cmd.run()
            except SystemExit:
                pass
            finally:
                output = [l.strip() for l in out.getvalue().split('\n')]
                self.assertIn('* import        Import nodes and group of nodes',
                              output, fail_msg)
