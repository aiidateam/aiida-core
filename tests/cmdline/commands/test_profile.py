# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for ``verdi profile``."""
from pgtest.pgtest import PGTest
import pytest

from aiida.cmdline.commands import cmd_profile, cmd_verdi
from aiida.manage import configuration


@pytest.fixture(scope='module')
def pg_test_cluster():
    """Create a standalone Postgres cluster, for setup tests."""
    pg_test = PGTest()
    yield pg_test
    pg_test.close()


@pytest.fixture
def mock_profiles(empty_config, profile_factory):
    """Create mock profiles and a runner object to invoke the CLI commands.

    Note: this cannot be done in the `setUp` or `setUpClass` methods, because the temporary configuration instance
    is not generated until the test function is entered, which calls the `config_with_profile` test fixture.
    """

    def _factory(**kwargs):
        config = empty_config
        profile_list = ['mock_profile1', 'mock_profile2', 'mock_profile3', 'mock_profile4']

        for profile_name in profile_list:
            profile = profile_factory(profile_name, **kwargs)
            config.add_profile(profile)

        config.set_default_profile(profile_list[0], overwrite=True).store()

        return profile_list

    return _factory


@pytest.mark.parametrize(
    'command',
    (cmd_profile.profile_list, cmd_profile.profile_setdefault, cmd_profile.profile_delete, cmd_profile.profile_show)
)
def test_help(run_cli_command, command):
    """Tests help text for all ``verdi profile`` commands."""
    result = run_cli_command(command, ['--help'])
    assert 'Usage' in result.output


def test_list(run_cli_command, mock_profiles):
    """Test the ``verdi profile list`` command."""
    profile_list = mock_profiles()
    result = run_cli_command(cmd_profile.profile_list)
    assert 'Report: configuration folder:' in result.output
    assert f'* {profile_list[0]}' in result.output
    assert profile_list[1] in result.output


def test_setdefault(run_cli_command, mock_profiles):
    """Test the ``verdi profile setdefault`` command."""
    profile_list = mock_profiles()
    run_cli_command(cmd_profile.profile_setdefault, [profile_list[1]])
    result = run_cli_command(cmd_profile.profile_list)

    assert 'Report: configuration folder:' in result.output
    assert f'* {profile_list[1]}' in result.output


def test_show(run_cli_command, mock_profiles):
    """Test the ``verdi profile show`` command."""
    config = configuration.get_config()
    profile_list = mock_profiles()
    profile_name = profile_list[0]
    profile = config.get_profile(profile_name)

    result = run_cli_command(cmd_profile.profile_show, [profile_name])
    for key, value in profile.dictionary.items():
        if isinstance(value, str):
            assert key in result.output
            assert value in result.output


def test_show_with_profile_option(run_cli_command, mock_profiles):
    """Test the ``verdi profile show`` command in combination with ``-p/--profile``."""
    profile_list = mock_profiles()
    profile_name_non_default = profile_list[1]

    # Specifying the non-default profile as argument should override the default
    result = run_cli_command(cmd_profile.profile_show, [profile_name_non_default])
    assert profile_name_non_default in result.output

    # Specifying ``-p/--profile`` should not override the argument default (which should be the default profile)
    result = run_cli_command(cmd_verdi.verdi, ['-p', profile_name_non_default, 'profile', 'show'])
    assert profile_name_non_default not in result.output


def test_delete_partial(run_cli_command, mock_profiles):
    """Test the ``verdi profile delete`` command.

    .. note:: we skip deleting the database as this might require sudo rights and this is tested in the CI tests
        defined in the file ``.github/system_tests/test_profile.py``
    """
    profile_list = mock_profiles()
    run_cli_command(cmd_profile.profile_delete, ['--force', '--skip-db', profile_list[1]])
    result = run_cli_command(cmd_profile.profile_list)
    assert profile_list[1] not in result.output


def test_delete(run_cli_command, mock_profiles, pg_test_cluster):
    """Test for verdi profile delete command."""
    kwargs = {'database_port': pg_test_cluster.dsn['port']}
    profile_list = mock_profiles(**kwargs)

    # Delete single profile
    run_cli_command(cmd_profile.profile_delete, ['--force', profile_list[1]])
    result = run_cli_command(cmd_profile.profile_list)
    assert profile_list[1] not in result.output

    # Delete multiple profiles
    run_cli_command(cmd_profile.profile_delete, ['--force', profile_list[2], profile_list[3]])
    result = run_cli_command(cmd_profile.profile_list)
    assert profile_list[2] not in result.output
    assert profile_list[3] not in result.output
