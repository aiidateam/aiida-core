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
from pgtest.pgtest import PGTest
import pytest

from aiida.cmdline.commands import cmd_profile, cmd_verdi
from aiida.manage import configuration
from tests.utils.configuration import create_mock_profile


@pytest.fixture(scope='class')
def pg_test_cluster():
    """Create a standalone Postgres cluster, for setup tests."""
    pg_test = PGTest()
    yield pg_test
    pg_test.close()


class TestVerdiProfileSetup:
    """Tests for `verdi profile`."""

    @pytest.fixture(autouse=True)
    def init_profile(self, pg_test_cluster, empty_config, run_cli_command):  # pylint: disable=redefined-outer-name,unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init
        self.storage_backend_name = 'psql_dos'
        self.pg_test = pg_test_cluster
        self.cli_runner = run_cli_command
        self.config = configuration.get_config()
        self.profile_list = []

    def mock_profiles(self, **kwargs):
        """Create mock profiles and a runner object to invoke the CLI commands.

        Note: this cannot be done in the `setUp` or `setUpClass` methods, because the temporary configuration instance
        is not generated until the test function is entered, which calls the `config_with_profile` test fixture.
        """
        # pylint: disable=attribute-defined-outside-init
        self.profile_list = ['mock_profile1', 'mock_profile2', 'mock_profile3', 'mock_profile4']

        for profile_name in self.profile_list:
            profile = create_mock_profile(profile_name, **kwargs)
            self.config.add_profile(profile)

        self.config.set_default_profile(self.profile_list[0], overwrite=True).store()

    def test_help(self):
        """Tests help text for all `verdi profile` commands."""
        self.mock_profiles()

        options = ['--help']

        result = self.cli_runner(cmd_profile.profile_list, options)
        assert 'Usage' in result.output

        result = self.cli_runner(cmd_profile.profile_setdefault, options)
        assert 'Usage' in result.output

        result = self.cli_runner(cmd_profile.profile_delete, options)
        assert 'Usage' in result.output

        result = self.cli_runner(cmd_profile.profile_show, options)
        assert 'Usage' in result.output

    def test_list(self):
        """Test the `verdi profile list` command."""
        self.mock_profiles()

        result = self.cli_runner(cmd_profile.profile_list)
        assert f'Report: configuration folder: {self.config.dirpath}' in result.output
        assert f'* {self.profile_list[0]}' in result.output
        assert self.profile_list[1] in result.output

    def test_setdefault(self):
        """Test the `verdi profile setdefault` command."""
        self.mock_profiles()

        self.cli_runner(cmd_profile.profile_setdefault, [self.profile_list[1]])
        result = self.cli_runner(cmd_profile.profile_list)

        assert f'Report: configuration folder: {self.config.dirpath}' in result.output
        assert f'* {self.profile_list[1]}' in result.output

    def test_show(self):
        """Test the `verdi profile show` command."""
        self.mock_profiles()

        config = configuration.get_config()
        profile_name = self.profile_list[0]
        profile = config.get_profile(profile_name)

        result = self.cli_runner(cmd_profile.profile_show, [profile_name])
        for key, value in profile.dictionary.items():
            if isinstance(value, str):
                assert key in result.output
                assert value in result.output

    def test_show_with_profile_option(self):
        """Test the `verdi profile show` command in combination with `-p/--profile."""
        self.mock_profiles()

        profile_name_non_default = self.profile_list[1]

        # Specifying the non-default profile as argument should override the default
        result = self.cli_runner(cmd_profile.profile_show, [profile_name_non_default])
        assert profile_name_non_default in result.output

        # Specifying `-p/--profile` should not override the argument default (which should be the default profile)
        result = self.cli_runner(cmd_verdi.verdi, ['-p', profile_name_non_default, 'profile', 'show'])
        assert profile_name_non_default not in result.output

    def test_delete_partial(self):
        """Test the `verdi profile delete` command.

        .. note:: we skip deleting the database as this might require sudo rights and this is tested in the CI tests
            defined in the file `.github/system_tests/test_profile.py`
        """
        self.mock_profiles()

        self.cli_runner(cmd_profile.profile_delete, ['--force', '--skip-db', self.profile_list[1]])
        result = self.cli_runner(cmd_profile.profile_list)
        assert self.profile_list[1] not in result.output

    def test_delete(self):
        """Test for verdi profile delete command."""
        from aiida.cmdline.commands.cmd_profile import profile_delete, profile_list

        kwargs = {'database_port': self.pg_test.dsn['port']}
        self.mock_profiles(**kwargs)

        # Delete single profile
        self.cli_runner(profile_delete, ['--force', self.profile_list[1]])
        result = self.cli_runner(profile_list)
        assert self.profile_list[1] not in result.output

        # Delete multiple profiles
        self.cli_runner(profile_delete, ['--force', self.profile_list[2], self.profile_list[3]])
        result = self.cli_runner(profile_list)
        assert self.profile_list[2] not in result.output
        assert self.profile_list[3] not in result.output
