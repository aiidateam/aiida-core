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
Integration tests for setup and quicksetup

These can not be added to the locally run test suite as long as that does
not use a separate (temporary) configuration directory, it might overwrite
user profiles and leave behind partial profiles. It also does not clean up
the file system behind itself.

These problems could also be addressed in tearDown methods of the test cases instead.
It has not been done due to time constraints yet.
"""
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
        """
        Test ``verdi quicksetup`` non-interactively
        """
        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(quicksetup, [
            '--profile=giuseppe-{}'.format(self.backend), '--backend={}'.format(
                self.backend), '--email=giuseppe.verdi@ope.ra',
            '--first-name=Giuseppe', '--last-name=Verdi', '--institution=Scala', '--db-name=aiida_giuseppe_{}'.format(
                self.backend), '--repo=aiida_giuseppe_{}'.format(self.backend), '--no-set-default'
        ])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    def test_postgres_failure(self):
        """
        Test ``verdi quicksetup`` non-interactively
        """
        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(
            quicksetup, [
                '--profile=giuseppe2-{}'.format(self.backend), '--backend={}'.format(
                    self.backend), '--email=giuseppe2.verdi@ope.ra', '--first-name=Giuseppe', '--last-name=Verdi',
                '--institution=Scala', '--db-port=1111', '--db-name=aiida_giuseppe2_{}'.format(self.backend),
                '--repo=aiida_giuseppe2_{}'.format(self.backend), '--no-set-default', '--non-interactive'
            ],
            input='nohost\n1111\naiida_giuseppe2_{}\npostgres\n\n'.format(self.backend),
            catch_exceptions=False)
        self.assertFalse(result.exception, msg=get_debug_msg(result))


@unittest.skip('wait until #1722 is fixed')
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
        self.dbname = 'aiida_test_setup_{}'.format(self.backend)
        self.postgres.create_dbuser(self.dbuser, self.dbpass)
        self.postgres.create_db(self.dbuser, self.dbname)
        self.repo = abspath('./aiida_radames_{}'.format(self.backend))

    def tearDown(self):
        self.postgres.drop_db(self.dbname)
        self.postgres.drop_dbuser(self.dbuser)
        self.pg_test.close()

    def test_user_setup(self):
        """
        Test ``verdi setup`` non-interactively
        """
        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(_setup_cmd, [
            'radames_{}'.format(self.backend), '--non-interactive', '--backend={}'.format(
                self.backend), '--email=radames.verdi@ope.ra', '--first-name=Radames', '--last-name=Verdi',
            '--institution=Scala', '--repo={}'.format(self.repo), '--db_host=localhost', '--db_port={}'.format(
                self.pg_test.port), '--db_name={}'.format(self.dbname), '--db_user={}'.format(
                    self.dbuser), '--db_pass={}'.format(self.dbpass), '--no-password'
        ])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    def test_user_configure(self):
        """
        Test ``verdi setup`` configure user
        """
        backend_settings.AIIDADB_PROFILE = None
        self.runner.invoke(_setup_cmd, [
            'radames2_{}'.format(self.backend), '--non-interactive', '--backend={}'.format(
                self.backend), '--email=radames.verdi@ope.ra', '--first-name=Radames', '--last-name=Verdi',
            '--institution=Scala', '--repo={}'.format(self.repo), '--db_host=localhost', '--db_port={}'.format(
                self.pg_test.port), '--db_name={}'.format(self.dbname), '--db_user={}'.format(
                    self.dbuser), '--db_pass={}'.format(self.dbpass), '--no-password'
        ])

        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(
            _setup_cmd, ['radames2_{}'.format(self.backend), '--only-config'],
            input=
            'yes\nradames.verdi@ope.ra\npostgresql_psycopg2\n\n\n\n\n\n{repo}\nRadames2\nVerdi2\nScala2\nyes\nno\n'.
            format(repo=self.repo),
            catch_exceptions=False)
        self.assertFalse(result.exception, msg=get_debug_msg(result))


def get_debug_msg(result):
    msg = '{}\n---\nOutput:\n{}'
    return msg.format(result.exception, result.output)


if __name__ == '__main__':
    unittest.main()
