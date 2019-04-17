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

from click.testing import CliRunner

from aiida.backends.tests.utils.configuration import create_mock_profile, with_temporary_config_instance
from aiida.cmdline.commands.cmd_setup import quicksetup
from aiida.manage import configuration


class QuicksetupTestCase(unittest.TestCase):
    """Test `verdi quicksetup`."""

    def setUp(self):
        self.runner = CliRunner()
        self.backend = os.environ.get('TEST_AIIDA_BACKEND', 'django')

    @with_temporary_config_instance
    def test_quicksetup(self):
        """Test `verdi quicksetup` non-interactively."""
        configuration.reset_profile()
        result = self.runner.invoke(quicksetup, [
            '--profile', 'giuseppe-{}'.format(self.backend), '--db-backend={}'.format(
                self.backend), '--email=giuseppe.verdi@ope.ra', '--first-name=Giuseppe', '--last-name=Verdi',
            '--institution=Scala', '--db-name=aiida_giuseppe_{}'.format(
                self.backend), '--repository=aiida_giuseppe_{}'.format(self.backend), '--non-interactive'
        ])
        self.assertFalse(result.exception, msg=get_debug_msg(result))

    @with_temporary_config_instance
    def test_postgres_failure(self):
        """Test `verdi quicksetup` non-interactively with incorrect database connection parameters."""
        configuration.reset_profile()
        result = self.runner.invoke(quicksetup, [
            '--profile', 'giuseppe2-{}'.format(self.backend), '--db-backend={}'.format(
                self.backend), '--email=giuseppe2.verdi@ope.ra', '--first-name=Giuseppe', '--last-name=Verdi',
            '--institution=Scala', '--db-port=1111', '--db-name=aiida_giuseppe2_{}'.format(self.backend),
            '--repository=aiida_giuseppe2_{}'.format(self.backend), '--non-interactive', '--non-interactive'
        ])
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
            config.add_profile(profile)

        config.set_default_profile(self.profile_list[0], overwrite=True).store()

    @with_temporary_config_instance
    def test_delete(self):
        """Test for verdi profile delete command."""
        from aiida.cmdline.commands.cmd_profile import profile_delete, profile_list

        configuration.reset_profile()

        # Create mock profiles
        mock_profiles = ['mock_profile1', 'mock_profile2', 'mock_profile3', 'mock_profile4']
        config = get_config()
        for profile_name in mock_profiles:
            config.add_profile(create_mock_profile(profile_name))
        config.set_default_profile(mock_profiles[0], overwrite=True).store()

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
