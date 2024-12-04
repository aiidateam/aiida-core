"""Tests for ``verdi presto``."""

import textwrap

import pytest

from aiida.cmdline.commands.cmd_presto import get_default_presto_profile_name, verdi_presto
from aiida.manage.configuration import profile_context
from aiida.manage.configuration.config import Config
from aiida.orm import Computer


@pytest.mark.parametrize(
    'profile_names, expected',
    (
        ([], 'presto'),
        (['main', 'sqlite'], 'presto'),
        (['presto'], 'presto-1'),
        (['presto', 'presto-5', 'presto-2'], 'presto-6'),
        (['presto', 'main', 'presto-2', 'sqlite'], 'presto-3'),
    ),
)
def test_get_default_presto_profile_name(monkeypatch, profile_names, expected):
    """Test the dynamic default profile function."""

    def get_profile_names(self):
        return profile_names

    monkeypatch.setattr(Config, 'profile_names', property(get_profile_names))
    assert get_default_presto_profile_name() == expected


@pytest.mark.usefixtures('empty_config')
def test_presto_without_rmq(pytestconfig, run_cli_command, monkeypatch):
    """Test the ``verdi presto`` without RabbitMQ."""
    from aiida.brokers.rabbitmq import defaults

    def detect_rabbitmq_config(**kwargs):
        raise ConnectionError()

    # Patch the RabbitMQ detection function to pretend it could not find the service
    monkeypatch.setattr(defaults, 'detect_rabbitmq_config', lambda: detect_rabbitmq_config())

    result = run_cli_command(verdi_presto, ['--non-interactive'])
    assert 'Created new profile `presto`.' in result.output

    with profile_context('presto', allow_switch=True) as profile:
        assert profile.name == 'presto'
        localhost = Computer.collection.get(label='localhost')
        assert localhost.is_configured
        assert profile.process_control_backend is None


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('empty_config')
def test_presto_with_rmq(pytestconfig, run_cli_command):
    """Test the ``verdi presto``."""
    result = run_cli_command(verdi_presto, ['--non-interactive'])
    assert 'Created new profile `presto`.' in result.output

    with profile_context('presto', allow_switch=True) as profile:
        assert profile.name == 'presto'
        localhost = Computer.collection.get(label='localhost')
        assert localhost.is_configured
        assert profile.process_control_backend == 'core.rabbitmq'


@pytest.mark.requires_psql
@pytest.mark.usefixtures('empty_config')
def test_presto_use_postgres(run_cli_command, manager):
    """Test the ``verdi presto`` with the ``--use-postgres`` flag."""
    result = run_cli_command(verdi_presto, ['--non-interactive', '--use-postgres'])
    assert 'Created new profile `presto`.' in result.output

    with profile_context('presto', allow_switch=True) as profile:
        assert profile.name == 'presto'
        localhost = Computer.collection.get(label='localhost')
        assert localhost.is_configured
        assert profile.storage_backend == 'core.psql_dos'
        assert manager.get_profile_storage()


@pytest.mark.usefixtures('empty_config')
def test_presto_use_postgres_fail(run_cli_command):
    """Test the ``verdi presto`` with the ``-use-postgres`` flag specifying an incorrect option."""
    options = ['--non-interactive', '--use-postgres', '--postgres-port', str(5000)]
    result = run_cli_command(verdi_presto, options, raises=True)
    assert 'Failed to connect to the PostgreSQL server' in result.output


@pytest.mark.usefixtures('empty_config')
def test_presto_overdose(run_cli_command, config_with_profile_factory):
    """Test that ``verdi presto`` still works for users that have over 10 presto profiles."""
    config_with_profile_factory(name='presto-10')
    result = run_cli_command(verdi_presto)
    assert 'Created new profile `presto-11`.' in result.output


@pytest.mark.requires_psql
@pytest.mark.usefixtures('empty_config')
def test_presto_profile_name_exists(run_cli_command, config_with_profile_factory):
    """Test ``verdi presto`` fails early if the specified profile name already exists."""
    profile_name = 'custom-presto'
    config_with_profile_factory(name=profile_name)
    options = ['--non-interactive', '--use-postgres', '--profile-name', profile_name]
    result = run_cli_command(verdi_presto, options, raises=True)
    # Matching for the complete literal output as a way to test that nothing else of the command was run, such as
    # configuring the broker or creating a database for PostgreSQL
    assert result.output == textwrap.dedent("""\
        Usage: presto [OPTIONS]
        Try 'presto --help' for help.

        Error: Invalid value for --profile-name: The profile `custom-presto` already exists.
        """)
