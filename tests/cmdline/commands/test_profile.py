###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi profile``."""

import pytest
from aiida.cmdline.commands import cmd_profile, cmd_verdi
from aiida.manage import configuration
from aiida.plugins import StorageFactory
from aiida.tools.archive.create import create_archive
from pgtest.pgtest import PGTest

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
    (cmd_profile.profile_list, cmd_profile.profile_set_default, cmd_profile.profile_delete, cmd_profile.profile_show),
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
