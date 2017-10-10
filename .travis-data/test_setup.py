"""Integration tests for setup and quicksetup"""
import unittest
import os

from click.testing import TestRunner

from aiida.cmdline.verdilib import _setup_cmd, Quicksetup


class QuicksetupTestCase(unittest.TestCase):
    """Test ``verdi setup``"""

    def setUp(self):
        self.runner = TestRunner()
        self.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')

    def _get_msg(self, result):
        msg = '{}\n---\nOutput:\n{}'
        return msg.format(result.exception, result.output)

    def test_user_setup(self):
        result = self.runner.invoke(
            'verdi', [
                'quicksetup',
                '--non-interactive',
                '--profile=giuseppe'
                '--backend={}'.format(self.backend),
                '--email=giuseppe.verdi@ope.ra',
                '--first-name=Giuseppe',
                '--last-name=Verdi',
                '--institution=Scala',
                '--db-name=aiida_giuseppe',
                '--repo=aiida_giuseppe',
                '--no-set-default'])
        self.assertFalse(result.exception, msg=self._get_msg(result))


if __name__ == '__main__':
    unittest.main()
