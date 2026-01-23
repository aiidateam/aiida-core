###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi profile``."""

from unittest.mock import patch

import pytest
from pgtest.pgtest import PGTest

from aiida import orm
from aiida.cmdline.commands import cmd_profile, cmd_verdi
from aiida.manage import configuration
from aiida.plugins import StorageFactory
from aiida.tools.archive.create import create_archive

# NOTE: Most of these tests would work with sqlite_dos,
# but would require generalizing a bunch of fixtures ('profile_factory' et al) in tests/conftest.py
pytestmark = pytest.mark.requires_psql


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
    (
        cmd_profile.profile_list,
        cmd_profile.profile_set_default,
        cmd_profile.profile_delete,
        cmd_profile.profile_show,
        cmd_profile.profile_rename,
    ),
)
def test_help(run_cli_command, command):
    """Tests help text for all ``verdi profile`` commands."""
    result = run_cli_command(command, ['--help'], use_subprocess=False)
    assert 'Usage' in result.output


def test_list(run_cli_command, mock_profiles):
    """Test the ``verdi profile list`` command."""
    profile_list = mock_profiles()
    result = run_cli_command(cmd_profile.profile_list, use_subprocess=False)
    assert 'Report: configuration folder:' in result.output
    assert f'* {profile_list[0]}' in result.output
    assert profile_list[1] in result.output


def test_setdefault(run_cli_command, mock_profiles):
    """Test the ``verdi profile setdefault`` command."""
    profile_list = mock_profiles()
    setdefault_result = run_cli_command(cmd_profile.profile_setdefault, [profile_list[1]], use_subprocess=False)
    result = run_cli_command(cmd_profile.profile_list, use_subprocess=False)

    assert 'Report: configuration folder:' in result.output
    assert f'* {profile_list[1]}' in result.output

    # test if deprecation warning is printed
    assert 'Deprecated:' in setdefault_result.output
    assert 'Deprecated:' in setdefault_result.stderr


def test_set_default(run_cli_command, mock_profiles):
    """Test the ``verdi profile set-default`` command."""
    profile_list = mock_profiles()
    run_cli_command(cmd_profile.profile_set_default, [profile_list[1]], use_subprocess=False)
    result = run_cli_command(cmd_profile.profile_list, use_subprocess=False)

    assert 'Report: configuration folder:' in result.output
    assert f'* {profile_list[1]}' in result.output


def test_show(run_cli_command, mock_profiles):
    """Test the ``verdi profile show`` command."""
    config = configuration.get_config()
    profile_list = mock_profiles()
    profile_name = profile_list[0]
    profile = config.get_profile(profile_name)

    result = run_cli_command(cmd_profile.profile_show, [profile_name], use_subprocess=False)
    for key, value in profile.dictionary.items():
        if isinstance(value, str):
            assert key in result.output
            assert value in result.output


def test_show_with_profile_option(run_cli_command, mock_profiles):
    """Test the ``verdi profile show`` command in combination with ``-p/--profile``."""
    profile_list = mock_profiles()
    profile_name_non_default = profile_list[1]

    # Specifying the non-default profile as argument should override the default
    result = run_cli_command(cmd_profile.profile_show, [profile_name_non_default], use_subprocess=False)
    assert profile_name_non_default in result.output

    # Specifying ``-p/--profile`` should not override the argument default (which should be the default profile)
    result = run_cli_command(cmd_verdi.verdi, ['-p', profile_name_non_default, 'profile', 'show'], use_subprocess=False)
    assert profile_name_non_default not in result.output


def test_delete(run_cli_command, mock_profiles, pg_test_cluster):
    """Test for verdi profile delete command."""
    kwargs = {'database_port': pg_test_cluster.dsn['port']}
    profile_list = mock_profiles(**kwargs)
    config = configuration.get_config()

    # Delete single profile
    result = run_cli_command(
        cmd_profile.profile_delete, ['--force', '--keep-data', profile_list[0]], use_subprocess=False
    )
    output = result.output
    assert f'`{profile_list[0]}` was the default profile, setting `{profile_list[1]}` as the new default.' in output
    result = run_cli_command(cmd_profile.profile_list, use_subprocess=False)
    assert profile_list[0] not in result.output
    assert config.default_profile_name == profile_list[1]

    # Delete multiple profiles
    result = run_cli_command(
        cmd_profile.profile_delete,
        ['--force', '--keep-data', profile_list[1], profile_list[2], profile_list[3]],
        use_subprocess=False,
    )
    assert 'was the default profile, no profiles remain to set as default.' in result.output
    result = run_cli_command(cmd_profile.profile_list, use_subprocess=False)
    assert profile_list[1] not in result.output
    assert profile_list[2] not in result.output
    assert profile_list[3] not in result.output


def test_delete_force(run_cli_command, mock_profiles, pg_test_cluster):
    """Test that if force is specified the ``--delete-data`` or ``--keep-data`` has to be explicitly specified."""
    kwargs = {'database_port': pg_test_cluster.dsn['port']}
    profile_list = mock_profiles(**kwargs)

    result = run_cli_command(
        cmd_profile.profile_delete, ['--force', profile_list[0]], use_subprocess=False, raises=True
    )
    assert 'When the `-f/--force` flag is used either `--delete-data` or `--keep-data`' in result.output


@pytest.mark.parametrize('entry_point', ('core.sqlite_dos', 'core.sqlite_zip'))
def test_setup_with_validating_sqlite_version(run_cli_command, isolated_config, tmp_path, entry_point, monkeypatch):
    """Test the ``verdi profile setup`` command.
    Same as `test_setup`, here we test the functionality to check sqlite versions, before setting up profiles.
    """

    if entry_point == 'core.sqlite_zip':
        tmp_path = tmp_path / 'archive.aiida'
        create_archive([], filename=tmp_path)

    profile_name = 'temp-profile'
    options = [entry_point, '-n', '--profile-name', profile_name, '--email', 'email@host', '--filepath', str(tmp_path)]

    # Should raise if installed version is lower than the supported one.
    monkeypatch.setattr('aiida.storage.sqlite_zip.backend.SUPPORTED_VERSION', '100.0.0')
    result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False, raises=True)
    assert 'Storage backend requires sqlite 100.0.0 or higher. But you have' in result.stderr
    assert profile_name not in isolated_config.profile_names

    # Should not raise if installed version is higher than the supported one.
    monkeypatch.setattr('aiida.storage.sqlite_zip.backend.SUPPORTED_VERSION', '0.0.0')
    result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
    assert profile_name in isolated_config.profile_names
    assert f'Created new profile `{profile_name}`.' in result.output


@pytest.mark.parametrize('entry_point', ('core.sqlite_dos', 'core.sqlite_zip'))
def test_delete_storage(run_cli_command, isolated_config, tmp_path, entry_point):
    """Test the ``verdi profile delete`` command with the ``--delete-storage`` option."""
    profile_name = 'temp-profile'

    if entry_point == 'core.sqlite_zip':
        filepath = tmp_path / 'archive.aiida'
        create_archive([], filename=filepath)
    else:
        filepath = tmp_path / 'storage'

    options = [entry_point, '-n', '--filepath', str(filepath), '--profile-name', profile_name, '--email', 'email@host']
    result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
    assert filepath.exists()
    assert profile_name in isolated_config.profile_names

    run_cli_command(cmd_profile.profile_delete, ['--force', '--delete-data', profile_name], use_subprocess=False)
    result = run_cli_command(cmd_profile.profile_list, use_subprocess=False)
    assert profile_name not in result.output
    assert not filepath.exists()
    assert profile_name not in isolated_config.profile_names


@pytest.mark.parametrize('entry_point', ('core.psql_dos', 'core.sqlite_temp', 'core.sqlite_dos', 'core.sqlite_zip'))
def test_setup(config_psql_dos, run_cli_command, isolated_config, tmp_path, entry_point):
    """Test the ``verdi profile setup`` command.

    Note that the options for user name and institution are not given on purpose as these should not be required.
    """
    if entry_point == 'core.sqlite_zip':
        tmp_path = tmp_path / 'archive.aiida'
        create_archive([], filename=tmp_path)

    if entry_point == 'core.psql_dos':
        options = []
        for key, value in config_psql_dos().items():
            options.append(f'--{key.replace("_", "-")}')
            options.append(str(value))
    else:
        options = ['--filepath', str(tmp_path)]

    profile_name = 'temp-profile'
    options = [entry_point, '-n', '--profile-name', profile_name, '--email', 'email@host', *options]
    result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
    assert f'Created new profile `{profile_name}`.' in result.output
    assert profile_name in isolated_config.profile_names
    assert isolated_config.default_profile_name == profile_name


@pytest.mark.parametrize('set_as_default', (True, False))
def test_setup_set_as_default(run_cli_command, isolated_config, tmp_path, set_as_default):
    """Test the ``--set-as-default`` flag of the ``verdi profile setup`` command."""
    profile_name = 'temp-profile'
    flag = '--set-as-default' if set_as_default else '--no-set-as-default'
    options = [
        'core.sqlite_dos',
        '-n',
        '--filepath',
        str(tmp_path),
        '--profile-name',
        profile_name,
        '--email',
        'email@host',
        flag,
    ]
    result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
    assert f'Created new profile `{profile_name}`.' in result.output
    if set_as_default:
        assert isolated_config.default_profile_name == profile_name
    else:
        assert isolated_config.default_profile_name != profile_name


@pytest.mark.parametrize('entry_point', ('core.sqlite_zip', 'core.sqlite_dos'))
def test_setup_email_required(run_cli_command, isolated_config, tmp_path, entry_point):
    """Test the ``--email`` option is not required for read-only storage plugins."""
    storage_cls = StorageFactory(entry_point)
    profile_name = f'profile_{entry_point}'

    if entry_point == 'core.sqlite_zip':
        tmp_path = tmp_path / 'archive.aiida'
        create_archive([], filename=tmp_path)

    isolated_config.unset_option('autofill.user.email')

    options = [entry_point, '-n', '--filepath', str(tmp_path), '--profile-name', profile_name]

    if storage_cls.read_only:
        result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
        assert f'Created new profile `{profile_name}`.' in result.output
        assert profile_name in isolated_config.profile_names
    else:
        result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False, raises=True)
        assert 'Invalid value for --email: The option is required for storages that are not read-only.' in result.output


def test_setup_no_use_rabbitmq(run_cli_command, isolated_config):
    """Test the ``--no-use-rabbitmq`` option."""
    profile_name = 'profile-no-broker'
    options = ['core.sqlite_dos', '-n', '--email', 'a@a', '--profile-name', profile_name, '--no-use-rabbitmq']

    result = run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
    assert f'Created new profile `{profile_name}`.' in result.output
    assert profile_name in isolated_config.profile_names
    profile = isolated_config.get_profile(profile_name)
    assert profile.process_control_backend is None
    assert profile.process_control_config == {}


def test_configure_rabbitmq(run_cli_command, isolated_config):
    """Test the ``verdi profile configure-rabbitmq`` command."""
    profile_name = 'profile'

    # First setup a profile without a broker configured
    options = ['core.sqlite_dos', '-n', '--email', 'a@a', '--profile-name', profile_name, '--no-use-rabbitmq']
    run_cli_command(cmd_profile.profile_setup, options, use_subprocess=False)
    profile = isolated_config.get_profile(profile_name)
    assert profile.process_control_backend is None
    assert profile.process_control_config == {}

    # Now run the command to configure the broker
    options = [profile_name, '-n']
    cli_result = run_cli_command(cmd_profile.profile_configure_rabbitmq, options, use_subprocess=False)
    assert profile.process_control_backend == 'core.rabbitmq'
    assert 'Connected to RabbitMQ with the provided connection parameters' in cli_result.stdout

    # Verify that running in non-interactive mode is the default
    options = [
        profile_name,
    ]
    run_cli_command(cmd_profile.profile_configure_rabbitmq, options, use_subprocess=True)
    assert profile.process_control_backend == 'core.rabbitmq'
    assert 'Connected to RabbitMQ with the provided connection parameters' in cli_result.stdout

    # Verify that configuring with incorrect options and `--force` raises a warning but still configures the broker
    options = [profile_name, '-f', '--broker-port', '1234']
    cli_result = run_cli_command(cmd_profile.profile_configure_rabbitmq, options, use_subprocess=False)
    assert 'Unable to connect to RabbitMQ server: Failed to connect' in cli_result.stdout
    assert profile.process_control_config['broker_port'] == 1234

    # Call it again to check it works to reconfigure existing broker connection parameters
    options = [profile_name, '-n', '--broker-port', '5672']
    cli_result = run_cli_command(cmd_profile.profile_configure_rabbitmq, options, use_subprocess=False)
    assert 'Connected to RabbitMQ with the provided connection parameters' in cli_result.stdout
    assert profile.process_control_config['broker_port'] == 5672


class TestVerdiProfileDumpCLI:
    """CLI-focused tests for `verdi profile dump` command."""

    def test_dump_help(self, run_cli_command):
        """Test help text for verdi profile dump."""
        result = run_cli_command(cmd_profile.profile_dump, ['--help'])
        assert 'Usage' in result.output
        assert 'Dump all data in an AiiDA profile' in result.output

    def test_dump_warning_message_displayed(self, run_cli_command, tmp_path):
        """Test that warning message about new feature is displayed."""
        test_path = tmp_path / 'warning-message'
        options = ['--all', '--path', str(test_path)]

        result = run_cli_command(cmd_profile.profile_dump, options)
        assert 'Warning: This is a new feature which is still in its testing phase' in result.output

    def test_dump_no_scope_handling(self, tmp_path, run_cli_command):
        """Test CLI behavior when no scope is specified."""
        test_path = tmp_path / 'specified-path'
        options = ['--path', str(test_path)]
        result = run_cli_command(cmd_profile.profile_dump, options)
        # Should handle gracefully without error
        assert result.exception is None, result.output
        # No entities selected, returns before directory creation
        assert not test_path.exists()

    def test_dump_path_message(self, run_cli_command, tmp_path):
        """Test path-related CLI messages."""

        # Test specified path message
        test_path = tmp_path / 'specified-path'
        options = ['--path', str(test_path), '--all']
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert f'Using specified output path: `{test_path}`' in result.output

    def test_dump_conflicting_options_warnings(self, tmp_path, run_cli_command):
        """Test CLI warnings for conflicting options."""

        # Test dry-run + overwrite conflict
        test_path = tmp_path / 'conflicting-options'
        options = ['--all', '--dry-run', '--overwrite', '--path', str(test_path)]
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert 'Overwrite operation will NOT be performed' in result.output

        # Test relabel without organize conflict
        options = ['--all', '--relabel-groups', '--no-organize-by-groups', '--path', str(test_path)]
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert '`relabel_groups` is True, but `organize_by_groups` is False' in result.output

    def test_dump_success_and_dry_run_messages(self, run_cli_command, tmp_path):
        """Test CLI success and dry run message formats."""

        # Test success message
        test_path = tmp_path / 'success-test'
        options = ['--path', str(test_path), '--all']
        result = run_cli_command(cmd_profile.profile_dump, options)

        from aiida.manage.configuration import get_config

        profile_name = get_config().get_profile().name
        expected_msg = f'Raw files for profile `{profile_name}` dumped into folder `{test_path.name}`'
        assert expected_msg in result.output

        # Test dry run message
        options = ['--all', '--dry-run']
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert 'Dry run completed' in result.output

    @patch('aiida.manage.configuration.profile.Profile.dump')
    def test_dump_cli_to_api_mapping(self, mock_dump, run_cli_command, tmp_path):
        """Test that CLI arguments are correctly passed to the Python API."""
        group = orm.Group(label='test_args_group').store()
        test_path = tmp_path / 'test-args'

        options = [
            '--path',
            str(test_path),
            '--all',
            '--groups',
            group.label,
            '--past-days',
            '7',
            '--include-inputs',
            '--include-outputs',
            '--organize-by-groups',
            '--also-ungrouped',
            '--flat',
        ]
        run_cli_command(cmd_profile.profile_dump, options)

        # Verify the dump method was called with expected arguments
        args, kwargs = mock_dump.call_args
        assert kwargs['output_path'] == test_path.resolve()
        assert kwargs['all_entries'] is True
        assert kwargs['groups'] == [group]  # Converted to `orm.Group`
        assert kwargs['past_days'] == 7
        assert kwargs['include_inputs'] is True
        assert kwargs['include_outputs'] is True
        assert kwargs['organize_by_groups'] is True
        assert kwargs['also_ungrouped'] is True
        assert kwargs['flat'] is True

    def test_dump_multiple_groups_parsing(self, run_cli_command, tmp_path):
        """Test that multiple groups are parsed correctly."""
        group1 = orm.Group(label='test_multi_group1').store()
        group2 = orm.Group(label='test_multi_group2').store()
        test_path = tmp_path / 'multi-groups-test'

        options = ['--path', str(test_path), '--groups', group1.label, group2.label]
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert result.exception is None, result.output

    def test_dump_boolean_flag_parsing(self, run_cli_command, tmp_path):
        """Test that boolean flags (positive and negative) are parsed correctly."""
        test_path = tmp_path / 'boolean-test'

        # Test mix of positive and negative flags
        options = [
            '--path',
            str(test_path),
            '--all',
            '--exclude-inputs',
            '--include-outputs',
            '--organize-by-groups',
            '--no-also-ungrouped',
        ]
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert result.exception is None, result.output

    @patch('aiida.manage.configuration.profile.Profile.dump')
    def test_dump_error_handling(self, mock_dump, run_cli_command, tmp_path):
        """Test CLI error handling and message formatting."""
        test_path = tmp_path / 'error-test'

        # Mock dump to raise an exception
        mock_dump.side_effect = RuntimeError('Test error')

        options = ['--path', str(test_path), '--all']
        result = run_cli_command(cmd_profile.profile_dump, options, raises=True)

        from aiida.manage.configuration import get_config

        profile_name = get_config().get_profile().name

        assert f'Unexpected error during dump of {profile_name}:' in result.output
        assert 'RuntimeError: Test error' in result.output
        assert 'Traceback' in result.output

    def test_dump_date_parsing(self, run_cli_command, tmp_path):
        """Test that date arguments are parsed correctly."""
        group = orm.Group(label='test_date_group').store()
        node = orm.CalculationNode().store()
        group.add_nodes([node])
        test_path = tmp_path / 'date-test'

        options = [
            '--path',
            str(test_path),
            '--all',
            '--start-date',
            '2024-01-01',
            '--end-date',
            '2024-12-31',
        ]
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert result.exception is None, result.output

    def test_dump_user_parsing(self, run_cli_command, tmp_path):
        """Test that user argument is parsed correctly."""
        from typing import cast

        group = orm.Group(label='test_user_group').store()
        node = orm.CalculationNode().store()
        group.add_nodes([node])
        test_path = tmp_path / 'user-test'

        default_user = orm.User.collection.get_default()
        cast(orm.User, default_user)

        options = ['--path', str(test_path), '--user', default_user.email]
        result = run_cli_command(cmd_profile.profile_dump, options)
        assert result.exception is None, result.output


def test_rename(run_cli_command, mock_profiles):
    """Test the ``verdi profile rename`` command."""
    from pathlib import Path

    from aiida.manage.configuration.settings import AiiDAConfigPathResolver

    profile_list = mock_profiles()
    old_name = profile_list[0]
    new_name = 'renamed_profile'
    config = configuration.get_config()

    # Create access directory for the profile
    path_resolver = AiiDAConfigPathResolver()
    old_access_dir = path_resolver.access_control_dir / old_name
    old_access_dir.mkdir(parents=True, exist_ok=True)

    # Create daemon log files
    daemon_log_dir = Path(path_resolver.daemon_dir) / 'log'
    daemon_log_dir.mkdir(parents=True, exist_ok=True)
    old_circus_log = daemon_log_dir / f'circus-{old_name}.log'
    old_circus_log.write_text('test circus log')
    old_aiida_log = daemon_log_dir / f'aiida-{old_name}.log'
    old_aiida_log.write_text('test aiida log')

    # Rename the profile
    result = run_cli_command(cmd_profile.profile_rename, [old_name, new_name, '--force'], use_subprocess=False)
    assert f'Profile `{old_name}` successfully renamed to `{new_name}`' in result.output

    # Verify profile was renamed in config
    assert new_name in config.profile_names
    assert old_name not in config.profile_names

    # Verify the default profile was updated (since we renamed the default)
    assert config.default_profile_name == new_name

    # Verify access directory was moved
    new_access_dir = path_resolver.access_control_dir / new_name
    assert new_access_dir.exists()
    assert not old_access_dir.exists()

    # Verify log files were moved
    new_circus_log = daemon_log_dir / f'circus-{new_name}.log'
    new_aiida_log = daemon_log_dir / f'aiida-{new_name}.log'
    assert new_circus_log.exists()
    assert new_aiida_log.exists()
    assert not old_circus_log.exists()
    assert not old_aiida_log.exists()


def test_rename_non_default(run_cli_command, mock_profiles):
    """Test renaming a non-default profile."""
    profile_list = mock_profiles()
    old_name = profile_list[1]  # Not the default
    new_name = 'renamed_non_default'
    config = configuration.get_config()

    # Rename the profile
    result = run_cli_command(cmd_profile.profile_rename, [old_name, new_name, '--force'], use_subprocess=False)
    assert f'Profile `{old_name}` successfully renamed to `{new_name}`' in result.output

    # Verify profile was renamed in config
    assert new_name in config.profile_names
    assert old_name not in config.profile_names

    # Verify the default profile was NOT changed (it should still be profile_list[0])
    assert config.default_profile_name == profile_list[0]


def test_rename_existing_name(run_cli_command, mock_profiles):
    """Test that renaming to an existing profile name fails."""
    profile_list = mock_profiles()
    old_name = profile_list[0]
    new_name = profile_list[1]  # This already exists

    # Try to rename to existing name
    result = run_cli_command(
        cmd_profile.profile_rename, [old_name, new_name, '--force'], use_subprocess=False, raises=True
    )
    assert f'Profile `{new_name}` already exists' in result.output


def test_rename_help(run_cli_command):
    """Test help text for ``verdi profile rename`` command."""
    result = run_cli_command(cmd_profile.profile_rename, ['--help'], use_subprocess=False)
    assert 'Usage' in result.output
    assert 'Rename a profile' in result.output


def test_rename_no_broker(run_cli_command, empty_config, profile_factory):
    """Test renaming a profile that has no broker configured."""
    config = empty_config
    old_name = 'profile_no_broker'
    new_name = 'renamed_no_broker'

    # Create a profile without a broker (process_control_backend=None)
    profile = profile_factory(old_name, process_control_backend=None)
    config.add_profile(profile)
    config.set_default_profile(old_name, overwrite=True).store()

    # Rename the profile - this should succeed without trying to check daemon status
    result = run_cli_command(cmd_profile.profile_rename, [old_name, new_name, '--force'], use_subprocess=False)
    assert f'Profile `{old_name}` successfully renamed to `{new_name}`' in result.output

    # Verify profile was renamed in config
    assert new_name in config.profile_names
    assert old_name not in config.profile_names
