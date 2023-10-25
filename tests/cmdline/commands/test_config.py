# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi config``."""
import pytest

from aiida import get_profile
from aiida.cmdline.commands import cmd_verdi


@pytest.mark.usefixtures('empty_config')
def test_config_list_no_profile(run_cli_command):
    """Test the `verdi config list` command when no profile is present in the config, it should not except."""
    run_cli_command(cmd_verdi.verdi, ['config', 'list'], initialize_ctx_obj=False)


def test_config_set_option_no_profile(run_cli_command, empty_config):
    """Test the `verdi config set` command when no profile is present in the config."""
    config = empty_config

    option_name = 'daemon.timeout'
    option_value = str(10)

    options = ['config', 'set', option_name, str(option_value)]
    run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert str(config.get_option(option_name, scope=None)) == option_value


def test_config_set_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config set` command when setting an option."""
    config = config_with_profile_factory()

    option_name = 'daemon.timeout'
    option_values = [str(10), str(20)]

    for option_value in option_values:
        options = ['config', 'set', option_name, option_value]
        run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
        assert str(config.get_option(option_name, scope=get_profile().name)) == option_value


def test_config_append_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config set --append` command when appending an option value."""
    config = config_with_profile_factory()
    option_name = 'caching.enabled_for'
    for value in ['x', 'y', 'x', 'y']:
        options = ['config', 'set', '--append', option_name, value]
        run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert sorted(config.get_option(option_name, scope=get_profile().name)) == ['x', 'y']


def test_config_remove_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config set --remove` command when removing an option value."""
    config = config_with_profile_factory()

    option_name = 'caching.disabled_for'
    config.set_option(option_name, ['x', 'x', 'y', 'x'], scope=get_profile().name)

    options = ['config', 'set', '--remove', option_name, 'x']
    run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert config.get_option(option_name, scope=get_profile().name) == ['y']


def test_config_get_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config show` command when getting an option."""
    config_with_profile_factory()
    option_name = 'daemon.timeout'
    option_value = str(30)

    options = ['config', 'set', option_name, option_value]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    options = ['config', 'get', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert option_value in result.output.strip()


def test_config_unset_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config` command when unsetting an option."""
    from aiida.manage.configuration.options import get_option

    config_with_profile_factory()
    option_name = 'daemon.timeout'
    option_value = str(30)

    options = ['config', 'set', option_name, str(option_value)]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    options = ['config', 'get', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert option_value in result.output.strip()

    options = ['config', 'unset', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert f"'{option_name}' unset" in result.output.strip()

    options = ['config', 'get', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert result.output.strip() == str(get_option(option_name).default)  # back to the default


def test_config_set_option_global_only(run_cli_command, config_with_profile_factory):
    """Test that `global_only` options are only set globally even if the `--global` flag is not set."""
    config_with_profile_factory()
    option_name = 'autofill.user.email'
    option_value = 'some@email.com'

    options = ['config', 'set', option_name, str(option_value)]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    options = ['config', 'get', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    # Check that the current profile name is not in the output
    assert option_value in result.output.strip()
    assert get_profile().name not in result.output.strip()


def test_config_list(run_cli_command, config_with_profile_factory):
    """Test `verdi config list`"""
    config_with_profile_factory()
    options = ['config', 'list']
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    assert 'daemon.timeout' in result.output
    assert 'Timeout in seconds' not in result.output


def test_config_list_description(run_cli_command, config_with_profile_factory):
    """Test `verdi config list --description`"""
    config_with_profile_factory()
    for flag in ['-d', '--description']:
        options = ['config', 'list', flag]
        result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

        assert 'daemon.timeout' in result.output
        assert 'Timeout in seconds' in result.output


def test_config_show(run_cli_command, config_with_profile_factory):
    """Test `verdi config show`"""
    config_with_profile_factory()
    options = ['config', 'show', 'daemon.timeout']
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert 'schema' in result.output


def test_config_caching(run_cli_command, config_with_profile_factory):
    """Test `verdi config caching`"""
    config = config_with_profile_factory()

    result = run_cli_command(cmd_verdi.verdi, ['config', 'caching'], use_subprocess=False)
    assert result.output.strip() == ''

    result = run_cli_command(cmd_verdi.verdi, ['config', 'caching', '--disabled'], use_subprocess=False)
    assert 'core.arithmetic.add' in result.output.strip()

    config.set_option('caching.default_enabled', True, scope=get_profile().name)

    result = run_cli_command(cmd_verdi.verdi, ['config', 'caching'], use_subprocess=False)
    assert 'core.arithmetic.add' in result.output.strip()

    result = run_cli_command(cmd_verdi.verdi, ['config', 'caching', '--disabled'], use_subprocess=False)
    assert result.output.strip() == ''


def test_config_downgrade(run_cli_command, config_with_profile_factory):
    """Test `verdi config downgrade`"""
    config_with_profile_factory()
    options = ['config', 'downgrade', '1']
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert 'Success: Downgraded' in result.output.strip()
