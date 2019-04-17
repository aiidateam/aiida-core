# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi profile`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import traceback

from click.testing import CliRunner

from aiida import orm
from aiida.backends.testbase import AiidaPostgresTestCase
from aiida.backends.tests.utils.configuration import with_temporary_config_instance
from aiida.cmdline.commands import cmd_setup
from aiida.manage import configuration
from aiida.manage.external.postgres import Postgres


class TestVerdiSetup(AiidaPostgresTestCase):
    """Tests for `verdi quicksetup`."""

    def setUp(self):
        """Create a CLI runner to invoke the CLI commands."""
        super(TestVerdiSetup, self).setUp()
        self.cli_runner = CliRunner()

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
            '--last-name', user_last_name, '--institution', user_institution, '--db-port', self.pg_test.dsn['port']
        ]

        result = self.cli_runner.invoke(cmd_setup.quicksetup, options)
        self.assertClickResultNoException(result)
        self.assertClickSuccess(result)

        config = configuration.get_config()
        self.assertIn(profile_name, config.profile_names)

        profile = config.get_profile(profile_name)
        profile.default_user = user_email

        user = orm.User.objects.get(email=user_email)
        self.assertEqual(user.first_name, user_first_name)
        self.assertEqual(user.last_name, user_last_name)
        self.assertEqual(user.institution, user_institution)

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

        options = [
            '--non-interactive', '--profile', profile_name, '--email', user_email, '--first-name', user_first_name,
            '--last-name', user_last_name, '--institution', user_institution, '--db-name', db_name, '--db-username',
            db_user, '--db-password', db_pass
        ]

        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertClickResultNoException(result)
        self.assertClickSuccess(result)

        config = configuration.get_config()
        self.assertIn(profile_name, config.profile_names)

        profile = config.get_profile(profile_name)
        profile.default_user = user_email

        user = orm.User.objects.get(email=user_email)
        self.assertEqual(user.first_name, user_first_name)
        self.assertEqual(user.last_name, user_last_name)
        self.assertEqual(user.institution, user_institution)
