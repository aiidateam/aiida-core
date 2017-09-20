"""Bug regression tests for ``verdi help``"""
import unittest

from .common import captured_output


class VerdiHelpTest(unittest.TestCase):
    """Make sure fixed bugs stay fixed"""

    def setUp(self):
        from aiida.cmdline.verdilib import Help
        self.help_cmd = Help()

    def test_verdi_help_full_string(self):
        with captured_output() as (out, err):
            try:
                self.help_cmd.run()
            finally:
                output = out.getvalue().strip()
                self.assertIn(output, '* import        Import nodes and group of nodes')
