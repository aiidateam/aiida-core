# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi profile`."""

import traceback
from click.testing import CliRunner
import pytest

from aiida import orm
from aiida.backends import BACKEND_DJANGO
from aiida.backends.testbase import AiidaPostgresTestCase
from aiida.cmdline.commands import cmd_setup
from aiida.manage import configuration
from aiida.manage.external.postgres import Postgres

from tests.utils.configuration import with_temporary_config_instance


class TestVerdiSetup(AiidaPostgresTestCase):
    """Tests for `verdi setup` and `verdi quicksetup`."""

    def setUp(self):
        """Create a CLI runner to invoke the CLI commands."""
        if configuration.PROFILE.database_backend == BACKEND_DJANGO:
            pytest.skip('Reenable when #2813 is addressed')
        super().setUp()
        self.backend = configuration.PROFILE.database_backend
        self.cli_runner = CliRunner()

    @with_temporary_config_instance
    def test_help(self):
        """Check that the `--help` option is eager, is not overruled and will properly display the help message.

        If this test hangs, most likely the `--help` eagerness is overruled by another option that has started the
        prompt cycle, which by waiting for input, will block the test from continuing.
        """
        self.cli_runner.invoke(cmd_setup.setup, ['--help'], catch_exceptions=False)
        self.cli_runner.invoke(cmd_setup.quicksetup, ['--help'], catch_exceptions=False)

    @with_temporary_config_instance
    def test_quicksetup(self):
        """Test `verdi quicksetup`."""
        configuration.reset_profile()

        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        options = [
            '--non-interactive', '--profile', profile_name, '--email', user_email, '--first-name', user_first_name,
            '--last-name', user_last_name, '--institution', user_institution, '--db-port', self.pg_test.dsn['port'],
            '--db-backend', self.backend
        ]

        result = self.cli_runner.invoke(cmd_setup.quicksetup, options)
        self.assertClickResultNoException(result)
        self.assertClickSuccess(result)

        config = configuration.get_config()
        self.assertIn(profile_name, config.profile_names)

        profile = config.get_profile(profile_name)
        profile.default_user = user_email

        # Verify that the backend type of the created profile matches that of the profile for the current test session
        self.assertEqual(self.backend, profile.database_backend)

        user = orm.User.objects.get(email=user_email)
        self.assertEqual(user.first_name, user_first_name)
        self.assertEqual(user.last_name, user_last_name)
        self.assertEqual(user.institution, user_institution)

    @with_temporary_config_instance
    def test_quicksetup_from_config_file(self):
        """Test `verdi quicksetup` from configuration file."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile('w') as handle:
            handle.write(
                """---
profile: testing
first_name: Leopold
last_name: Talirz
institution: EPFL
db_backend: {}
email: 123@234.de""".format(self.backend)
            )
            handle.flush()
            result = self.cli_runner.invoke(cmd_setup.quicksetup, ['--config', os.path.realpath(handle.name)])
        self.assertClickResultNoException(result)

    @with_temporary_config_instance
    def test_quicksetup_wrong_port(self):
        """Test `verdi quicksetup` exits if port is wrong."""
        configuration.reset_profile()

        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        options = [
            '--non-interactive', '--profile', profile_name, '--email', user_email, '--first-name', user_first_name,
            '--last-name', user_last_name, '--institution', user_institution, '--db-port',
            self.pg_test.dsn['port'] + 100
        ]

        result = self.cli_runner.invoke(cmd_setup.quicksetup, options)
        self.assertIsNotNone(result.exception, ''.join(traceback.format_exception(*result.exc_info)))

    @with_temporary_config_instance
    def test_setup(self):
        """Test `verdi setup`."""
        postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        postgres.determine_setup()
        db_name = 'aiida_test_setup'
        db_user = 'aiida_test_setup'
        db_pass = 'aiida_test_setup'
        postgres.create_dbuser(db_user, db_pass)
        postgres.create_db(db_user, db_name)
        configuration.reset_profile()

        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        # Keep the `--profile` option last as a regression test for #2897 and #2907. Some of the other options have
        # defaults, callbacks and or contextual defaults that might depend on it, but should not fail if they are parsed
        # before the profile option is parsed.
        options = [
            '--non-interactive', '--email', user_email, '--first-name', user_first_name, '--last-name', user_last_name,
            '--institution', user_institution, '--db-name', db_name, '--db-username', db_user, '--db-password', db_pass,
            '--db-port', self.pg_test.dsn['port'], '--db-backend', self.backend, '--profile', profile_name
        ]

        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertClickResultNoException(result)
        self.assertClickSuccess(result)

        config = configuration.get_config()
        self.assertIn(profile_name, config.profile_names)

        profile = config.get_profile(profile_name)
        profile.default_user = user_email

        # Verify that the backend type of the created profile matches that of the profile for the current test session
        self.assertEqual(self.backend, profile.database_backend)

        user = orm.User.objects.get(email=user_email)
        self.assertEqual(user.first_name, user_first_name)
        self.assertEqual(user.last_name, user_last_name)
        self.assertEqual(user.institution, user_institution)
