# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=no-self-use
"""Tests for `verdi config`."""
import pytest

from aiida.cmdline.commands import cmd_verdi
from aiida.manage.configuration import get_config


class TestVerdiConfigDeprecated:
    """Tests for deprecated `verdi config <OPTION_NAME>`."""

    @pytest.fixture(autouse=True)
    def setup_fixture(self, config_with_profile_factory):
        config_with_profile_factory()

    def test_config_set_option(self, run_cli_command):
        """Test the `verdi config` command when setting an option."""
        config = get_config()

        option_name = 'daemon.timeout'
        option_values = [str(10), str(20)]

        for option_value in option_values:
            options = ['config', option_name, str(option_value)]
            run_cli_command(cmd_verdi.verdi, options)

            assert str(config.get_option(option_name, scope=config.current_profile.name)) == option_value

    def test_config_get_option(self, run_cli_command):
        """Test the `verdi config` command when getting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', option_name, option_value]
        result = run_cli_command(cmd_verdi.verdi, options)

        options = ['config', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)

        assert option_value in result.output.strip()

    def test_config_unset_option(self, run_cli_command):
        """Test the `verdi config` command when unsetting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', option_name, str(option_value)]
        result = run_cli_command(cmd_verdi.verdi, options)

        options = ['config', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)

        assert option_value in result.output.strip()

        options = ['config', option_name, '--unset']
        result = run_cli_command(cmd_verdi.verdi, options)

        assert f"'{option_name}' unset" in result.output.strip()

        options = ['config', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)

        # assert result.output == ''  #  now has deprecation warning

    def test_config_set_option_global_only(self, run_cli_command):
        """Test that `global_only` options are only set globally even if the `--global` flag is not set."""
        config = get_config()
        option_name = 'autofill.user.email'
        option_value = 'some@email.com'

        options = ['config', option_name, str(option_value)]
        result = run_cli_command(cmd_verdi.verdi, options)

        options = ['config', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)

        # Check that the current profile name is not in the output

        assert option_value in result.output.strip()
        assert config.current_profile.name not in result.output.strip()


class TestVerdiConfig:
    """Tests for `verdi config`."""

    @pytest.fixture(autouse=True)
    def setup_fixture(self, config_with_profile_factory):
        config_with_profile_factory()

    def test_config_set_option(self, run_cli_command):
        """Test the `verdi config set` command when setting an option."""
        config = get_config()

        option_name = 'daemon.timeout'
        option_values = [str(10), str(20)]

        for option_value in option_values:
            options = ['config', 'set', option_name, str(option_value)]
            run_cli_command(cmd_verdi.verdi, options)
            assert str(config.get_option(option_name, scope=config.current_profile.name)) == option_value

    def test_config_append_option(self, run_cli_command):
        """Test the `verdi config set --append` command when appending an option value."""
        config = get_config()
        option_name = 'caching.enabled_for'
        for value in ['x', 'y']:
            options = ['config', 'set', '--append', option_name, value]
            run_cli_command(cmd_verdi.verdi, options)
        assert config.get_option(option_name, scope=config.current_profile.name) == ['x', 'y']

    def test_config_remove_option(self, run_cli_command):
        """Test the `verdi config set --remove` command when removing an option value."""
        config = get_config()

        option_name = 'caching.disabled_for'
        config.set_option(option_name, ['x', 'y'], scope=config.current_profile.name)

        options = ['config', 'set', '--remove', option_name, 'x']
        run_cli_command(cmd_verdi.verdi, options)
        assert config.get_option(option_name, scope=config.current_profile.name) == ['y']

    def test_config_get_option(self, run_cli_command):
        """Test the `verdi config show` command when getting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', 'set', option_name, option_value]
        result = run_cli_command(cmd_verdi.verdi, options)

        options = ['config', 'get', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)
        assert option_value in result.output.strip()

    def test_config_unset_option(self, run_cli_command):
        """Test the `verdi config` command when unsetting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', 'set', option_name, str(option_value)]
        result = run_cli_command(cmd_verdi.verdi, options)

        options = ['config', 'get', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)
        assert option_value in result.output.strip()

        options = ['config', 'unset', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)
        assert f"'{option_name}' unset" in result.output.strip()

        options = ['config', 'get', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)
        assert result.output.strip() == str(20)  # back to the default

    def test_config_set_option_global_only(self, run_cli_command):
        """Test that `global_only` options are only set globally even if the `--global` flag is not set."""
        config = get_config()
        option_name = 'autofill.user.email'
        option_value = 'some@email.com'

        options = ['config', 'set', option_name, str(option_value)]
        result = run_cli_command(cmd_verdi.verdi, options)

        options = ['config', 'get', option_name]
        result = run_cli_command(cmd_verdi.verdi, options)

        # Check that the current profile name is not in the output
        assert option_value in result.output.strip()
        assert config.current_profile.name not in result.output.strip()

    def test_config_list(self, run_cli_command):
        """Test `verdi config list`"""
        options = ['config', 'list']
        result = run_cli_command(cmd_verdi.verdi, options)

        assert 'daemon.timeout' in result.output
        assert 'Timeout in seconds' not in result.output

    def test_config_list_description(self, run_cli_command):
        """Test `verdi config list --description`"""
        for flag in ['-d', '--description']:
            options = ['config', 'list', flag]
            result = run_cli_command(cmd_verdi.verdi, options)

            assert 'daemon.timeout' in result.output
            assert 'Timeout in seconds' in result.output

    def test_config_show(self, run_cli_command):
        """Test `verdi config show`"""
        options = ['config', 'show', 'daemon.timeout']
        result = run_cli_command(cmd_verdi.verdi, options)
        assert 'schema' in result.output

    def test_config_caching(self, run_cli_command):
        """Test `verdi config caching`"""
        result = run_cli_command(cmd_verdi.verdi, ['config', 'caching'])
        assert result.output.strip() == ''

        result = run_cli_command(cmd_verdi.verdi, ['config', 'caching', '--disabled'])
        assert 'arithmetic.add' in result.output.strip()

        config = get_config()
        config.set_option('caching.default_enabled', True, scope=config.current_profile.name)

        result = run_cli_command(cmd_verdi.verdi, ['config', 'caching'])
        assert 'arithmetic.add' in result.output.strip()

        result = run_cli_command(cmd_verdi.verdi, ['config', 'caching', '--disabled'])
        assert result.output.strip() == ''
