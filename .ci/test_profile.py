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
Integration tests for setup, quicksetup, and delete

These can not be added to test_profile.py in the locally run test suite as long as that does
not use a separate (temporary) configuration directory:
 * it might overwrite user profiles
 * it might leave behind partial profiles
 * it does not clean up the file system behind itself

Possible ways of solving this problem:

 * migrate all tests to the fixtures in aiida.utils.fixtures, which already provide this functionality
 * implement the functionality in the Aiidatestcase
 * implement the functionality specifically for the verdi profile tests (using setUp and tearDown methods)

It has not been done yet due to time constraints.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
import os
from os.path import abspath

from click.testing import CliRunner
from pgtest.pgtest import PGTest

from aiida.backends import settings as backend_settings
from aiida.backends.tests.utils.configuration import create_mock_profile, with_temporary_config_instance
from aiida.cmdline.commands.cmd_setup import setup
from aiida.cmdline.commands.cmd_quicksetup import quicksetup
from aiida.manage.external.postgres import Postgres


class QuicksetupTestCase(unittest.TestCase):
    """Test `verdi quicksetup`."""

    def setUp(self):
        self.runner = CliRunner()
        self.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')

    @with_temporary_config_instance
    def test_user_setup(self):
        """Test `verdi quicksetup` non-interactively."""
        result = self.runner.invoke(quicksetup, [
            '--backend={}'.format(self.backend), '--email=giuseppe.verdi@ope.ra', '--first-name=Giuseppe',
            '--last-name=Verdi', '--institution=Scala', '--db-name=aiida_giuseppe_{}'.format(
                self.backend), '--repository=aiida_giuseppe_{}'.format(self.backend), 'giuseppe-{}'.format(self.backend)
        ])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    @with_temporary_config_instance
    def test_postgres_failure(self):
        """Test `verdi quicksetup` non-interactively."""
        result = self.runner.invoke(
            quicksetup, [
                '--backend={}'.format(self.backend), '--email=giuseppe2.verdi@ope.ra', '--first-name=Giuseppe',
                '--last-name=Verdi', '--institution=Scala', '--db-port=1111', '--db-name=aiida_giuseppe2_{}'.format(
                    self.backend), '--repository=aiida_giuseppe2_{}'.format(
                        self.backend), '--non-interactive', 'giuseppe2-{}'.format(self.backend)
            ],
            input='nohost\n1111\naiida_giuseppe2_{}\npostgres\n\n'.format(self.backend),
            catch_exceptions=False)
        self.assertFalse(result.exception, msg=get_debug_msg(result))


class SetupTestCase(unittest.TestCase):
    """Test `verdi setup`."""

    def setUp(self):
        self.runner = CliRunner()
        backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')
        self.backend = 'django' if backend == 'django' else 'sqlalchemy'
        self.pg_test = PGTest()
        self.postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        self.postgres.determine_setup()
        self.dbuser = 'aiida_SetupTestCase'
        self.dbpass = 'setuptestcase'
        self.dbname = 'aiida_test_setup_{}'.format(self.backend)
        self.postgres.create_dbuser(self.dbuser, self.dbpass)
        self.postgres.create_db(self.dbuser, self.dbname)
        self.repository = abspath('./aiida_radames_{}'.format(self.backend))

    def tearDown(self):
        self.postgres.drop_db(self.dbname)
        self.postgres.drop_dbuser(self.dbuser)
        self.pg_test.close()

    def test_user_setup(self):
        """
        Test `verdi setup` non-interactively
        """
        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(setup, [
            '--non-interactive', '--backend={}'.format(self.backend), '--email=radames.verdi@ope.ra',
            '--first-name=Radames', '--last-name=Verdi', '--institution=Scala', '--repository={}'.format(
                self.repository), '--db-host=localhost', '--db-port={}'.format(
                    self.pg_test.port), '--db-name={}'.format(self.dbname), '--db-username={}'.format(
                        self.dbuser), '--db-password={}'.format(self.dbpass), 'radames_{}'.format(self.backend)
        ])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    def test_user_configure(self):
        """
        Test `verdi setup` configure user
        """
        backend_settings.AIIDADB_PROFILE = None
        self.runner.invoke(setup, [
            '--non-interactive', '--backend={}'.format(self.backend), '--email=radames.verdi@ope.ra',
            '--first-name=Radames', '--last-name=Verdi', '--institution=Scala', '--repository={}'.format(
                self.repository), '--db-host=localhost', '--db-port={}'.format(
                    self.pg_test.port), '--db-name={}'.format(self.dbname), '--db-username={}'.format(
                        self.dbuser), '--db-password={}'.format(self.dbpass), 'radames2_{}'.format(self.backend)
        ])

        tpl = '{email}\n{first_name}\n{last_name}\n{institution}\nyes\n{email}\n{engine}\n\n\n\n\n\n{repo}\nno\n\n'
        backend_settings.AIIDADB_PROFILE = None
        result = self.runner.invoke(
            setup, ['radames2_{}'.format(self.backend), '--only-config'],
            input=tpl.format(
                email='radames.verdi@ope.ra',
                first_name='Radames2',
                last_name='Verdi2',
                institution='Scala2',
                engine='postgresql_psycopg2',
                repo=self.repository),
            catch_exceptions=False)
        self.assertFalse(result.exception, msg=get_debug_msg(result))


class DeleteTestCase(unittest.TestCase):
    """Test `verdi profile delete`."""

    def setUp(self):
        self.runner = CliRunner()
        self.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')
        self.profile_list = ['mock_profile1', 'mock_profile2', 'mock_profile3', 'mock_profile4']

    def mock_profiles(self):
        """Create mock profiles and a runner object to invoke the CLI commands.

        Note: this cannot be done in the `setUp` or `setUpClass` methods, because the temporary configuration instance
        is not generated until the test function is entered, which calls the `with_temporary_config_instance`
        decorator.
        """
        from aiida.manage.configuration import get_config

        config = get_config()

        for profile_name in self.profile_list:
            profile = create_mock_profile(profile_name)
            config.add_profile(profile_name, profile)

        config.set_default_profile(self.profile_list[0], overwrite=True).store()

    @with_temporary_config_instance
    def test_delete(self):
        """Test for verdi profile delete command."""
        from aiida.cmdline.commands.cmd_profile import profile_delete, profile_list

        self.mock_profiles()

        # Delete single profile
        result = self.runner.invoke(profile_delete, ['--force', self.profile_list[1]])
        self.assertIsNone(result.exception, result.output)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception, result.output)

        self.assertNotIn(self.profile_list[1], result.output)
        self.assertIsNone(result.exception, result.output)

        # Delete multiple profiles
        result = self.runner.invoke(profile_delete, ['--force', self.profile_list[2], self.profile_list[3]])
        self.assertIsNone(result.exception, result.output)

        result = self.runner.invoke(profile_list)
        self.assertIsNone(result.exception, result.output)
        self.assertNotIn(self.profile_list[2], result.output)
        self.assertNotIn(self.profile_list[3], result.output)
        self.assertIsNone(result.exception, result.output)


def get_debug_msg(result):
    msg = '{}\n---\nOutput:\n{}'
    return msg.format(result.exception, result.output)


if __name__ == '__main__':
    unittest.main()
