###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi config``."""

import json
import pathlib

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


@pytest.mark.parametrize(
    'option_name, is_list',
    (
        ('storage.sandbox', False),
        ('caching.enabled_for', True),
    ),
)
def test_config_set_option(run_cli_command, config_with_profile_factory, option_name, is_list):
    """Test the `verdi config set` command when setting an option."""
    config = config_with_profile_factory()
    option_value = 'aiida.calculations:core.arithmetic.add'
    options = ['config', 'set', option_name, option_value]
    run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    if is_list:
        assert config.get_option(option_name, scope=get_profile().name) == [option_value]
    else:
        assert str(config.get_option(option_name, scope=get_profile().name)) == option_value


def test_config_append_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config set --append` command when appending an option value."""
    config = config_with_profile_factory()
    prefix = 'aiida.calculations:core.'
    option_name = 'caching.enabled_for'
    for value in ['transfer', 'arithmetic.add', 'transfer', 'arithmetic.add']:
        options = ['config', 'set', '--append', option_name, f'{prefix}{value}']
        run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert sorted(config.get_option(option_name, scope=get_profile().name)) == [
        f'{prefix}arithmetic.add',
        f'{prefix}transfer',
    ]


def test_config_remove_option(run_cli_command, config_with_profile_factory):
    """Test the `verdi config set --remove` command when removing an option value."""
    config = config_with_profile_factory()

    option_name = 'caching.disabled_for'
    prefix = 'aiida.calculations:core.'
    option_value = [f'{prefix}{value}' for value in ('transfer', 'transfer', 'arithmetic.add', 'transfer')]
    config.set_option(option_name, option_value, scope=get_profile().name)

    options = ['config', 'set', '--remove', option_name, f'{prefix}transfer']
    run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert config.get_option(option_name, scope=get_profile().name) == [f'{prefix}arithmetic.add']


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


@pytest.mark.parametrize(
    'option_name, option_value, requires_daemon_restart',
    (
        ('daemon.timeout', '30', False),
        ('daemon.default_workers', '2', True),
    ),
)
def test_config_unset_option(
    run_cli_command, config_with_profile_factory, option_name, option_value, requires_daemon_restart
):
    """Test the `verdi config` command when unsetting an option."""
    from aiida.manage.configuration.options import get_option

    config_with_profile_factory()

    options = ['config', 'set', option_name, str(option_value)]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    options = ['config', 'get', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert option_value in result.output.strip()

    options = ['config', 'unset', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert f"'{option_name}' unset" in result.output.strip()

    if requires_daemon_restart:
        assert 'verdi daemon restart' in result.output
    else:
        assert 'verdi daemon restart' not in result.output

    options = ['config', 'get', option_name]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert result.output.strip() == str(get_option(option_name).default)  # back to the default


def test_config_set_handler_warns_when_ineffective(run_cli_command, config_with_profile_factory):
    """`verdi config set` should warn when a handler filter is set more verbose than any logger level.

    ``logging.aiida_loglevel`` defaults to ``REPORT``, so setting ``terminal_handler`` to ``DEBUG`` cannot surface any
    additional messages until a logger level is lowered as well.
    """
    config_with_profile_factory()
    options = ['config', 'set', 'logging.terminal_handler', 'DEBUG']
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert 'Warning' in result.output
    assert 'no logger emits messages at that level' in result.output
    assert 'logging.aiida_loglevel' in result.output
    assert 'REPORT' in result.output


@pytest.mark.parametrize(
    'option_name, value, effective_option_name, requires_daemon_restart',
    (
        ('daemon.default_workers', '2', 'daemon.default_workers', True),
        ('daemon.timeout', '10', 'daemon.timeout', False),
        ('logging.aiida_loglevel', 'DEBUG', 'logging.aiida_loglevel', True),
        ('logging.db_loglevel', 'DEBUG', 'logging.database_handler', True),
        ('caching.default_enabled', 'True', 'caching.default_enabled', True),
        ('rmq.task_timeout', '5', 'broker.task_timeout', True),
    ),
)
def test_config_set_option_requires_daemon_restart(
    run_cli_command,
    config_with_profile_factory,
    option_name,
    value,
    effective_option_name,
    requires_daemon_restart,
):
    """Test that `verdi config set` reports when an option requires restarting the daemon."""
    config_with_profile_factory()
    options = ['config', 'set', option_name, value]
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)

    assert f"'{effective_option_name}' set to" in result.output

    if option_name != effective_option_name:
        assert 'deprecated using' in result.output

    if requires_daemon_restart:
        assert 'verdi daemon restart' in result.output
    else:
        assert 'verdi daemon restart' not in result.output


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
    assert 'logging.db_loglevel' not in result.output
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


@pytest.mark.parametrize(
    'value, raises',
    (
        ('aiida.calculations:core.arithmetic.add', False),
        ('aiida.calculations:core.arithmetic.invalid', True),
        ('core.arithmetic.invalid', True),
        ('aiida.calculations.arithmetic.add.ArithmeticAddCalculation', False),
        ('aiida.calculations.arithmetic.invalid.ArithmeticAddCalculation', True),
    ),
)
def test_config_set_caching_enabled(run_cli_command, config_with_profile_factory, value, raises):
    """Test `verdi config set caching.enabled_for`"""
    config_with_profile_factory()
    options = ['config', 'set', 'caching.enabled_for', value]
    result = run_cli_command(cmd_verdi.verdi, options, raises=raises, use_subprocess=False)
    if raises:
        assert 'Critical: Invalid identifier pattern' in result.output
    else:
        assert "Success: 'caching.enabled_for' set to" in result.output


def test_development_version_warning_option(run_cli_command, unacknowledged_config, monkeypatch):
    """The regular config commands can acknowledge the warning and turn it back on."""
    from aiida.manage import configuration

    monkeypatch.setattr('aiida.__version__', '3.0.0.dev0')
    option = 'warnings.development_version'
    command = ['config', 'upgrade']
    prompt = 'Continue with this development version? [y/N]'

    result = run_cli_command(cmd_verdi.verdi, ['config', 'list'])
    assert option in result.output

    run_cli_command(cmd_verdi.verdi, ['config', 'set', option, 'False'])
    configuration.reset_config()
    result = run_cli_command(cmd_verdi.verdi, command)
    assert prompt not in result.stderr

    run_cli_command(cmd_verdi.verdi, ['config', 'set', option, 'True'])
    result = run_cli_command(cmd_verdi.verdi, command, user_input='n\n', raises=True)
    assert prompt in result.stderr
    assert configuration.get_config().get_option(option) is True

    result = run_cli_command(cmd_verdi.verdi, command, user_input='y\n')
    assert prompt in result.stderr
    assert configuration.get_config().get_option(option) is False
    result = run_cli_command(cmd_verdi.verdi, command)
    assert prompt not in result.stderr


def test_config_help_schema_command_order(run_cli_command):
    """List upgrade immediately before downgrade in the config help."""
    result = run_cli_command(cmd_verdi.verdi, ['config', '--help'])
    lines = result.stdout.splitlines()
    upgrade = next(index for index, line in enumerate(lines) if line.lstrip().startswith('upgrade '))
    assert lines[upgrade + 1].lstrip().startswith('downgrade ')


@pytest.mark.parametrize('version', ['3.0.0', '3.0.0.dev0'])
def test_config_upgrade(run_cli_command, config_with_profile_factory, monkeypatch, version):
    """Upgrade an outdated file explicitly without loading a profile."""
    from aiida.manage import configuration, get_manager
    from aiida.manage.configuration.migrations import CURRENT_CONFIG_VERSION, downgrade_config

    monkeypatch.setattr('aiida.__version__', version)
    config = config_with_profile_factory()
    path = pathlib.Path(config.filepath)
    original = json.dumps(downgrade_config(config.dictionary, CURRENT_CONFIG_VERSION - 1))
    path.write_text(original, encoding='utf8')
    configuration.reset_config()
    get_manager().unload_profile()

    result = run_cli_command(cmd_verdi.verdi, ['profile', 'list'], raises=True, initialize_ctx_obj=False)
    assert 'verdi config upgrade' in result.stderr
    assert path.read_text(encoding='utf8') == original

    command = ['config', 'upgrade']
    prompt = 'Continue with this development version? [y/N]'
    user_input = None
    if version == '3.0.0.dev0':
        result = run_cli_command(cmd_verdi.verdi, command, user_input='n\n', raises=True, initialize_ctx_obj=False)
        assert prompt in result.stderr
        assert path.read_text(encoding='utf8') == original
        user_input = 'y\n'

    result = run_cli_command(cmd_verdi.verdi, command, user_input=user_input, initialize_ctx_obj=False)
    assert (prompt in result.stderr) == (version == '3.0.0.dev0')
    assert f'Configuration is up to date (schema v{CURRENT_CONFIG_VERSION})' in result.output
    assert configuration.get_config().version == CURRENT_CONFIG_VERSION
    assert configuration.get_config().profile_names == config.profile_names
    assert any(backup.read_text(encoding='utf8') == original for backup in path.parent.glob('config.json.*'))


def test_config_downgrade(run_cli_command, config_with_profile_factory):
    """Test `verdi config downgrade`"""
    config_with_profile_factory()
    options = ['config', 'downgrade', '1']
    result = run_cli_command(cmd_verdi.verdi, options, use_subprocess=False)
    assert 'Success: Downgraded' in result.output.strip()


def test_config_downgrade_incompatible_but_downgradeable(run_cli_command, config_with_profile_factory, monkeypatch):
    """Test `verdi config downgrade` can run even if the config cannot be loaded normally."""
    from aiida.manage import configuration
    from aiida.manage.configuration.migrations import migrations

    config = config_with_profile_factory()
    filepath = pathlib.Path(config.filepath)
    dictionary = config.dictionary
    dictionary['CONFIG_VERSION'] = {'CURRENT': 10, 'OLDEST_COMPATIBLE': 10}
    dictionary.setdefault('options', {})['broker.task_timeout'] = 12
    filepath.write_text(json.dumps(dictionary), encoding='utf8')

    configuration.CONFIG = None
    monkeypatch.setattr(migrations, 'CURRENT_CONFIG_VERSION', 9)
    monkeypatch.setattr(migrations, 'MAXIMUM_DOWNGRADE_CONFIG_VERSION', 10)

    result = run_cli_command(
        cmd_verdi.verdi, ['config', 'downgrade', '9'], initialize_ctx_obj=False, use_subprocess=False
    )

    assert 'Success: Downgraded' in result.output.strip()
    dictionary = json.loads(filepath.read_text(encoding='utf8'))
    assert dictionary['CONFIG_VERSION'] == {'CURRENT': 9, 'OLDEST_COMPATIBLE': 9}
    assert dictionary['options']['rmq.task_timeout'] == 12
    assert 'broker.task_timeout' not in dictionary['options']
