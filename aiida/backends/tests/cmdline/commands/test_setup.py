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

import os
import unittest

from click.testing import CliRunner
from pgtest.pgtest import PGTest

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import with_temporary_config_instance
from aiida.cmdline.commands import cmd_setup
from aiida.manage.configuration import get_config
from aiida.manage.external.postgres import Postgres


@unittest.skip('Reenable when #2759 is addressed')
class TestVerdiQuickSetup(AiidaTestCase):
    """Tests for `verdi quicksetup`."""

    def setUp(self):
        """Create a CLI runner to invoke the CLI commands."""
        super(TestVerdiQuickSetup, self).setUp()
        self.cli_runner = CliRunner()
        self.pg_test = PGTest()
        self.database_user = 'aiida'
        self.database_pass = 'password'
        self.database_name = 'aiida_db'

    def tearDown(self):
        self.pg_test.close()

    @with_temporary_config_instance
    def test_setup(self):
        """Test `verdi quicksetup`."""
        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        options = [
            '--non-interactive',
            '--profile',
            profile_name,
            '--email',
            user_email,
            '--first-name',
            user_first_name,
            '--last-name',
            user_last_name,
            '--institution',
            user_institution,
        ]

        result = self.cli_runner.invoke(cmd_setup.quicksetup, options)
        self.assertClickResultNoException(result)
        self.assertClickSuccess(result)

        config = get_config()
        self.assertIn(profile_name, config.profile_names)

        profile = config.get_profile(profile_name)
        profile.default_user = user_email

        user = orm.User.objects.get(email=user_email)
        self.assertEqual(user.first_name, user_first_name)
        self.assertEqual(user.last_name, user_last_name)
        self.assertEqual(user.institution, user_institution)


@unittest.skip('Reenable when #2759 is addressed')
class TestVerdiSetup(AiidaTestCase):
    """Tests for `verdi setup`."""

    def setUp(self):
        """Create a CLI runner to invoke the CLI commands."""
        super(TestVerdiSetup, self).setUp()
        self.cli_runner = CliRunner()
        self.pg_test = PGTest()
        self.postgres = Postgres(interactive=False, quiet=True, dbinfo=self.pg_test.dsn)
        self.postgres.determine_setup()
        self.db_name = 'aiida_test_setup'
        self.db_user = 'aiida_test_setup'
        self.db_pass = 'aiida_test_setup'
        self.postgres.create_dbuser(self.db_user, self.db_pass)
        self.postgres.create_db(self.db_user, self.db_name)
        self.repository = os.path.abspath('./aiida_test_setup')

    def tearDown(self):
        self.postgres.drop_db(self.db_name)
        self.postgres.drop_dbuser(self.db_user)
        self.pg_test.close()

    @with_temporary_config_instance
    def test_setup(self):
        """Test `verdi setup`."""
        profile_name = 'testing'
        user_email = 'some@email.com'
        user_first_name = 'John'
        user_last_name = 'Smith'
        user_institution = 'ECMA'

        options = [
            '--non-interactive', '--profile', profile_name, '--email', user_email, '--first-name', user_first_name,
            '--last-name', user_last_name, '--institution', user_institution, '--db-name', self.db_name,
            '--db-username', self.db_user, '--db-password', self.db_pass
        ]

        result = self.cli_runner.invoke(cmd_setup.setup, options)
        self.assertClickResultNoException(result)
        self.assertClickSuccess(result)

        config = get_config()
        self.assertIn(profile_name, config.profile_names)

        profile = config.get_profile(profile_name)
        profile.default_user = user_email

        user = orm.User.objects.get(email=user_email)
        self.assertEqual(user.first_name, user_first_name)
        self.assertEqual(user.last_name, user_last_name)
        self.assertEqual(user.institution, user_institution)
