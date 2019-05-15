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

import six

from click.testing import CliRunner

from aiida.backends.testbase import AiidaPostgresTestCase
from aiida.cmdline.commands import cmd_profile, cmd_verdi
from aiida.backends.tests.utils.configuration import create_mock_profile, with_temporary_config_instance
from aiida.manage import configuration


class TestVerdiProfileSetup(AiidaPostgresTestCase):
    """Tests for `verdi profile`."""

    def setUp(self):
        """Create a CLI runner to invoke the CLI commands."""
        super(TestVerdiProfileSetup, self).setUp()
        self.cli_runner = CliRunner()
        self.config = None
        self.profile_list = []

    def mock_profiles(self, **kwargs):
        """Create mock profiles and a runner object to invoke the CLI commands.

        Note: this cannot be done in the `setUp` or `setUpClass` methods, because the temporary configuration instance
        is not generated until the test function is entered, which calls the `with_temporary_config_instance`
        decorator.
        """
        self.config = configuration.get_config()
        self.profile_list = ['mock_profile1', 'mock_profile2', 'mock_profile3', 'mock_profile4']

        for profile_name in self.profile_list:
            profile = create_mock_profile(profile_name, **kwargs)
            self.config.add_profile(profile)

        self.config.set_default_profile(self.profile_list[0], overwrite=True).store()

    @with_temporary_config_instance
    def test_help(self):
        """Tests help text for all `verdi profile` commands."""
        self.mock_profiles()

        options = ['--help']

        result = self.cli_runner.invoke(cmd_profile.profile_list, options)
        self.assertClickSuccess(result)
        self.assertIn('Usage', result.output)

        result = self.cli_runner.invoke(cmd_profile.profile_setdefault, options)
        self.assertClickSuccess(result)
        self.assertIn('Usage', result.output)

        result = self.cli_runner.invoke(cmd_profile.profile_delete, options)
        self.assertClickSuccess(result)
        self.assertIn('Usage', result.output)

        result = self.cli_runner.invoke(cmd_profile.profile_show, options)
        self.assertClickSuccess(result)
        self.assertIn('Usage', result.output)

    @with_temporary_config_instance
    def test_list(self):
        """Test the `verdi profile list` command."""
        self.mock_profiles()

        result = self.cli_runner.invoke(cmd_profile.profile_list)
        self.assertClickSuccess(result)
        self.assertIn('Info: configuration folder: ' + self.config.dirpath, result.output)
        self.assertIn('* {}'.format(self.profile_list[0]), result.output)
        self.assertIn(self.profile_list[1], result.output)

    @with_temporary_config_instance
    def test_setdefault(self):
        """Test the `verdi profile setdefault` command."""
        self.mock_profiles()

        result = self.cli_runner.invoke(cmd_profile.profile_setdefault, [self.profile_list[1]])
        self.assertClickSuccess(result)

        result = self.cli_runner.invoke(cmd_profile.profile_list)

        self.assertClickSuccess(result)
        self.assertIn('Info: configuration folder: ' + self.config.dirpath, result.output)
        self.assertIn('* {}'.format(self.profile_list[1]), result.output)
        self.assertClickSuccess(result)

    @with_temporary_config_instance
    def test_show(self):
        """Test the `verdi profile show` command."""
        self.mock_profiles()

        config = configuration.get_config()
        profile_name = self.profile_list[0]
        profile = config.get_profile(profile_name)

        result = self.cli_runner.invoke(cmd_profile.profile_show, [profile_name])
        self.assertClickSuccess(result)
        for key, value in profile.dictionary.items():
            if isinstance(value, six.string_types):
                self.assertIn(key.lower(), result.output)
                self.assertIn(value, result.output)

    @with_temporary_config_instance
    def test_show_with_profile_option(self):
        """Test the `verdi profile show` command in combination with `-p/--profile."""
        self.mock_profiles()

        profile_name_non_default = self.profile_list[1]

        # Specifying the non-default profile as argument should override the default
        result = self.cli_runner.invoke(cmd_profile.profile_show, [profile_name_non_default])
        self.assertClickSuccess(result)
        self.assertTrue(profile_name_non_default in result.output)

        # Specifying `-p/--profile` should override the configured default
        result = self.cli_runner.invoke(cmd_verdi.verdi, ['-p', profile_name_non_default, 'profile', 'show'])
        self.assertClickSuccess(result)
        self.assertTrue(profile_name_non_default in result.output)

    @with_temporary_config_instance
    def test_delete_partial(self):
        """Test the `verdi profile delete` command.

        .. note:: we skip deleting the database as this might require sudo rights and this is tested in the CI tests
            defined in the file `.ci/test_profile.py`
        """
        self.mock_profiles()

        result = self.cli_runner.invoke(cmd_profile.profile_delete, ['--force', '--skip-db', self.profile_list[1]])
        self.assertClickSuccess(result)

        result = self.cli_runner.invoke(cmd_profile.profile_list)
        self.assertClickSuccess(result)
        self.assertNotIn(self.profile_list[1], result.output)

    @with_temporary_config_instance
    def test_delete(self):
        """Test for verdi profile delete command."""
        from aiida.cmdline.commands.cmd_profile import profile_delete, profile_list

        configuration.reset_profile()

        kwargs = {'database_port': self.pg_test.dsn['port']}
        self.mock_profiles(**kwargs)

        # Delete single profile
        result = self.cli_runner.invoke(profile_delete, ['--force', self.profile_list[1]])
        self.assertIsNone(result.exception, result.output)

        result = self.cli_runner.invoke(profile_list)
        self.assertIsNone(result.exception, result.output)

        self.assertNotIn(self.profile_list[1], result.output)
        self.assertIsNone(result.exception, result.output)

        # Delete multiple profiles
        result = self.cli_runner.invoke(profile_delete, ['--force', self.profile_list[2], self.profile_list[3]])
        self.assertIsNone(result.exception, result.output)

        result = self.cli_runner.invoke(profile_list)
        self.assertIsNone(result.exception, result.output)
        self.assertNotIn(self.profile_list[2], result.output)
        self.assertNotIn(self.profile_list[3], result.output)
        self.assertIsNone(result.exception, result.output)
