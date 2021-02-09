# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi config`."""
import traceback

from click.testing import CliRunner
import pytest

from aiida.cmdline.commands import cmd_verdi
from aiida.manage.configuration import get_config


@pytest.mark.usefixtures('temporary_config_instance')  # pylint: disable=not-callable
class TestVerdiConfigDeprecated:
    """Tests for `verdi config`."""

    def setup_method(self):
        self.cli_runner = CliRunner()  # pylint: disable=attribute-defined-outside-init

    def assertClickSuccess(self, cli_result):  # pylint: disable=invalid-name,no-self-use
        assert cli_result.exit_code == 0, cli_result.output
        assert cli_result.exception is None, ''.join(traceback.format_exception(*cli_result.exc_info))

    def test_config_set_option(self):
        """Test the `verdi config` command when setting an option."""
        config = get_config()

        option_name = 'daemon.timeout'
        option_values = [str(10), str(20)]

        for option_value in option_values:
            options = ['config', option_name, str(option_value)]
            result = self.cli_runner.invoke(cmd_verdi.verdi, options)

            self.assertClickSuccess(result)
            assert str(config.get_option(option_name, scope=config.current_profile.name)) == option_value

    def test_config_get_option(self):
        """Test the `verdi config` command when getting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', option_name, option_value]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)

        self.assertClickSuccess(result)

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert option_value in result.output.strip()

    def test_config_unset_option(self):
        """Test the `verdi config` command when unsetting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', option_name, str(option_value)]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert option_value in result.output.strip()

        options = ['config', option_name, '--unset']
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert f"'{option_name}' unset" in result.output.strip()

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        # assert result.output == ''  #  now has deprecation warning

    def test_config_set_option_global_only(self):
        """Test that `global_only` options are only set globally even if the `--global` flag is not set."""
        config = get_config()
        option_name = 'autofill.user.email'
        option_value = 'some@email.com'

        options = ['config', option_name, str(option_value)]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        options = ['config', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)

        # Check that the current profile name is not in the output
        self.assertClickSuccess(result)
        assert option_value in result.output.strip()
        assert config.current_profile.name not in result.output.strip()


@pytest.mark.usefixtures('temporary_config_instance')  # pylint: disable=not-callable
class TestVerdiConfig:
    """Tests for `verdi config`."""

    def setup_method(self):
        self.cli_runner = CliRunner()  # pylint: disable=attribute-defined-outside-init

    def assertClickSuccess(self, cli_result):  # pylint: disable=invalid-name,no-self-use
        assert cli_result.exit_code == 0, cli_result.output
        assert cli_result.exception is None, ''.join(traceback.format_exception(*cli_result.exc_info))

    def test_config_set_option(self):
        """Test the `verdi config set` command when setting an option."""
        config = get_config()

        option_name = 'daemon.timeout'
        option_values = [str(10), str(20)]

        for option_value in option_values:
            options = ['config', 'set', option_name, str(option_value)]
            result = self.cli_runner.invoke(cmd_verdi.verdi, options)

            self.assertClickSuccess(result)
            assert str(config.get_option(option_name, scope=config.current_profile.name)) == option_value

    def test_config_get_option(self):
        """Test the `verdi config show` command when getting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', 'set', option_name, option_value]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)

        self.assertClickSuccess(result)

        options = ['config', 'get', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert option_value in result.output.strip()

    def test_config_unset_option(self):
        """Test the `verdi config` command when unsetting an option."""
        option_name = 'daemon.timeout'
        option_value = str(30)

        options = ['config', 'set', option_name, str(option_value)]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        options = ['config', 'get', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert option_value in result.output.strip()

        options = ['config', 'unset', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert f"'{option_name}' unset" in result.output.strip()

        options = ['config', 'get', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert result.output.strip() == str(20)  # back to the default

    def test_config_set_option_global_only(self):
        """Test that `global_only` options are only set globally even if the `--global` flag is not set."""
        config = get_config()
        option_name = 'autofill.user.email'
        option_value = 'some@email.com'

        options = ['config', 'set', option_name, str(option_value)]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        options = ['config', 'get', option_name]
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)

        # Check that the current profile name is not in the output
        self.assertClickSuccess(result)
        assert option_value in result.output.strip()
        assert config.current_profile.name not in result.output.strip()

    def test_config_list(self):
        """Test `verdi config list`"""
        options = ['config', 'list']
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)

        assert 'daemon.timeout' in result.output
        assert 'The timeout in seconds' not in result.output

    def test_config_list_description(self):
        """Test `verdi config list --description`"""
        for flag in ['-d', '--description']:
            options = ['config', 'list', flag]
            result = self.cli_runner.invoke(cmd_verdi.verdi, options)
            self.assertClickSuccess(result)

            assert 'daemon.timeout' in result.output
            assert 'The timeout in seconds' in result.output

    def test_config_show(self):
        """Test `verdi config show`"""
        options = ['config', 'show', 'daemon.timeout']
        result = self.cli_runner.invoke(cmd_verdi.verdi, options)
        self.assertClickSuccess(result)
        assert 'schema' in result.output
