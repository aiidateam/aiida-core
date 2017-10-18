"""Integration tests for setup and quicksetup"""
import unittest
import os
from os.path import abspath

from click.testing import CliRunner
from pgtest.pgtest import PGTest

from aiida.cmdline.verdilib import _setup_cmd, quicksetup
from aiida.control.postgres import Postgres
from aiida.backends import settings as backend_settings


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

    def test_postgres_faillure(self):
        result = self.runner.invoke(
            quicksetup, [
                '--profile=giuseppe2',
                '--backend={}'.format(self.backend),
                '--email=giuseppe2.verdi@ope.ra',
                '--first-name=Giuseppe',
                '--last-name=Verdi',
                '--institution=Scala',
                '--db-port=1111',
                '--db-name=aiida_giuseppe2',
                '--repo=aiida_giuseppe2',
                '--no-set-default',
                '--non-interactive'
            ],
            input='nohost\n1111\naiida_giuseppe2\npostgres\n\n',
            catch_exceptions=False
        )
        self.assertFalse(result.exception, msg=get_debug_msg(result))


class SetupTestCase(unittest.TestCase):
    """Test ``verdi setup``"""

    def setUp(self):
        self.runner = CliRunner()
        backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')
        self.backend = 'django' if backend == 'django' else 'sqlalchemy'
        self.pg_test = PGTest()
        self.postgres = Postgres(port=self.pg_test.port, interactive=False, quiet=True)
        self.postgres.dbinfo = self.pg_test.dsn
        self.postgres.determine_setup()
        self.dbuser = 'aiida_SetupTestCase'
        self.dbpass = 'setuptestcase'
        self.dbname = 'aiida_test_setup'
        self.postgres.create_dbuser(self.dbuser, self.dbpass)
        self.postgres.create_db(self.dbuser, self.dbname)
        self.repo = abspath('./aiida_radames')

    def tearDown(self):
        self.postgres.drop_db(self.dbname)
        self.postgres.drop_dbuser(self.dbuser)
        self.pg_test.close()

    def test_user_setup(self):
        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(
            _setup_cmd, [
                'radames',
                '--non-interactive',
                '--backend={}'.format(self.backend),
                '--email=radames.verdi@ope.ra',
                '--first-name=Radames',
                '--last-name=Verdi',
                '--institution=Scala',
                '--repo={}'.format(self.repo),
                '--db_host=localhost',
                '--db_port={}'.format(self.pg_test.port),
                '--db_name={}'.format(self.dbname),
                '--db_user={}'.format(self.dbuser),
                '--db_pass={}'.format(self.dbpass),
                '--no-password'])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    def test_user_configure(self):
        backend_settings.AIIDADB_PROFILE = None
        self.runner.invoke(
            _setup_cmd, [
                'radames2',
                '--non-interactive',
                '--backend={}'.format(self.backend),
                '--email=radames.verdi@ope.ra',
                '--first-name=Radames',
                '--last-name=Verdi',
                '--institution=Scala',
                '--repo={}'.format(self.repo),
                '--db_host=localhost',
                '--db_port={}'.format(self.pg_test.port),
                '--db_name={}'.format(self.dbname),
                '--db_user={}'.format(self.dbuser),
                '--db_pass={}'.format(self.dbpass),
                '--no-password'])

        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(
            _setup_cmd,
            ['radames2', '--only-config'],
            input='yes\nradames.verdi@ope.ra\npostgresql_psycopg2\n\n\n\n\n\n{repo}\nRadames2\nVerdi2\nScala2\nyes\nno\n'.format(
                repo=self.repo
            ),
            catch_exceptions=False
        )
        self.assertFalse(result.exception, msg=get_debug_msg(result))


def get_debug_msg(result):
    msg = '{}\n---\nOutput:\n{}'
    return msg.format(result.exception, result.output)


if __name__ == '__main__':
    unittest.main()
