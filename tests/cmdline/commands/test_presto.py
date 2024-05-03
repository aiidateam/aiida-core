"""Tests for ``verdi presto``."""

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
@pytest.mark.parametrize('with_broker', (True, False))
def test_presto(run_cli_command, with_broker, monkeypatch):
    """Test the ``verdi presto``."""
    from aiida.brokers.rabbitmq import defaults

    if not with_broker:
        # Patch the RabbitMQ detection function to pretend it could not find the service
        monkeypatch.setattr(defaults, 'detect_rabbitmq_config', lambda: None)

    result = run_cli_command(verdi_presto)
    assert 'Created new profile `presto`.' in result.output

    with profile_context('presto', allow_switch=True) as profile:
        assert profile.name == 'presto'
        localhost = Computer.collection.get(label='localhost')
        assert localhost.is_configured
        if with_broker:
            assert profile.process_control_backend == 'core.rabbitmq'
        else:
            assert profile.process_control_backend is None
