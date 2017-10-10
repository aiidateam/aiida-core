"""Integration tests for setup and quicksetup"""
import unittest
import os

from click.testing import CliRunner

from aiida.cmdline.verdilib import _setup_cmd, quicksetup
from aiida.control.postgres import Postgres


class QuicksetupTestCase(unittest.TestCase):
    """Test ``verdi quicksetup``"""

    def setUp(self):
        self.runner = CliRunner()
        self.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')

    def test_user_setup(self):
        result = self.runner.invoke(
            quicksetup, [
                '--profile=giuseppe',
                '--backend={}'.format(self.backend),
                '--email=giuseppe.verdi@ope.ra',
                '--first-name=Giuseppe',
                '--last-name=Verdi',
                '--institution=Scala',
                '--db-name=aiida_giuseppe',
                '--repo=aiida_giuseppe',
                '--no-set-default'])
        self.assertFalse(result.exception, msg=get_debug_msg(result))


class SetupTestCase(unittest.TestCase):
    """Test ``verdi setup``"""

    def setUp(self):
        self.runner = CliRunner()
        self.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')
        self.postgres = Postgres(interactive=False, quiet=False)


    def test_user_setup(self):
        dbuser = 'aiida_SetupTestCase'
        dbpass = 'setuptestcase'
        dbname = 'aiida_test_setup'
        self.postgres.create_dbuser(dbuser, dbpass)
        self.postgres.create_db(dbuser, dbname)
        result = self.runner.invoke(
            _setup_cmd, [
                'radames',
                '--non-interactive',
                '--backend={}'.format(self.backend),
                '--email=radames.verdi@ope.ra',
                '--first-name=Radames',
                '--last-name=Verdi',
                '--institution=Scala',
                '--repo=aiida_radames',
                '--db_host=localhost',
                '--db_port=5432',
                '--db_name={}'.format(dbname),
                '--db_user={}'.format(dbuser),
                '--db_pass={}'.format(dbpass),
                '--no-password'])


def get_debug_msg(result):
    msg = '{}\n---\nOutput:\n{}'
    return msg.format(result.exception, result.output)


if __name__ == '__main__':
    unittest.main()
