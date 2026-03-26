###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``verdi bug-report``."""

import json
import pathlib
import sys
from types import SimpleNamespace

import pytest

import aiida
from aiida.cmdline.commands import cmd_bug_report


class DummyStorageBackend:
    """Dummy storage backend."""

    def __init__(self, _profile):
        self.closed = False

    def __str__(self):
        return 'DummyStorageBackend'

    def close(self):
        self.closed = True


class DummyBroker:
    """Dummy broker."""

    def __init__(self):
        self.closed = False

    def get_communicator(self):
        return object()

    def close(self):
        self.closed = True


class BrokenStorageBackend:
    """Broken storage backend."""

    def __init__(self, _profile):
        raise RuntimeError('storage unavailable')


def _patch_manager(monkeypatch, profile, broker, get_daemon_client):
    """Patch the global manager used by ``cmd_bug_report``."""
    manager = SimpleNamespace(
        get_profile=lambda: profile,
        get_broker=lambda: broker,
        get_daemon_client=get_daemon_client,
    )
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)


def _get_daemon_client_ok():
    """Return a daemon client with a running daemon status."""
    return SimpleNamespace(get_status=lambda: {'pid': 1234})


def _get_daemon_client_error():
    """Raise an error for an unavailable daemon client."""
    raise RuntimeError('daemon unavailable')


def _patch_config(monkeypatch, dirpath, client_log=None):
    """Patch the global config used by ``cmd_bug_report``."""
    client_log = client_log or pathlib.Path(dirpath) / 'client.log'
    monkeypatch.setattr(
        'aiida.manage.configuration.get_config',
        lambda: SimpleNamespace(
            dirpath=str(dirpath),
            filepaths=lambda _profile: {'client': {'log': str(client_log)}},
        ),
    )


def test_collect_diagnostics(monkeypatch, tmp_path):
    """Test ``_collect_diagnostics`` returns structured JSON-serializable data."""
    profile = SimpleNamespace(name='default', storage_cls=DummyStorageBackend)
    config_data = {'profiles': {'default': {'storage': {'backend': 'core.sqlite_dos'}}}}
    (tmp_path / 'config.json').write_text(json.dumps(config_data), encoding='utf-8')

    monkeypatch.setattr(aiida, '__version__', '1.2.3')
    _patch_manager(monkeypatch, profile, DummyBroker(), _get_daemon_client_ok)
    _patch_config(monkeypatch, tmp_path)

    diagnostics = cmd_bug_report._collect_diagnostics()

    assert diagnostics['aiida_version'] == '1.2.3'
    assert diagnostics['profile'] == {'name': 'default'}
    assert diagnostics['config'] == config_data
    assert {key: diagnostics['python'][key] for key in ('major', 'minor', 'micro')} == {
        'major': sys.version_info.major,
        'minor': sys.version_info.minor,
        'micro': sys.version_info.micro,
    }
    for key in ('version', 'implementation', 'compiler', 'executable'):
        assert diagnostics['python'][key]
    assert isinstance(diagnostics['python']['build'], list)


@pytest.mark.parametrize(
    ('storage_cls', 'broker', 'get_daemon_client', 'expected_services'),
    [
        pytest.param(
            DummyStorageBackend,
            DummyBroker(),
            _get_daemon_client_ok,
            {
                'storage': {'connected': True, 'message': 'DummyStorageBackend'},
                'broker': {'connected': True, 'message': 'DummyBroker'},
                'daemon': {
                    'connected': True,
                    'message': 'Daemon is running with PID 1234',
                    'status': {'pid': 1234},
                },
            },
            id='connected',
        ),
        pytest.param(
            BrokenStorageBackend,
            None,
            _get_daemon_client_error,
            {
                'storage': {'connected': False, 'message': 'RuntimeError: storage unavailable'},
                'broker': {'connected': False, 'message': 'No broker configured for this profile.'},
                'daemon': {'connected': False, 'message': 'RuntimeError: daemon unavailable'},
            },
            id='not-connected',
        ),
    ],
)
def test_collect_diagnostics_services(monkeypatch, tmp_path, storage_cls, broker, get_daemon_client, expected_services):
    """Test ``_collect_diagnostics`` reports service connection information."""
    profile = SimpleNamespace(name='default', dictionary={}, storage_cls=storage_cls)
    (tmp_path / 'config.json').write_text('{}', encoding='utf-8')
    _patch_manager(monkeypatch, profile, broker, get_daemon_client)
    _patch_config(monkeypatch, tmp_path)

    diagnostics = cmd_bug_report._collect_diagnostics()

    assert diagnostics['services'] == expected_services


def test_get_config_data(monkeypatch, tmp_path):
    """Test ``_get_config_data`` returns the contents of ``config.json``."""
    config_data = {'profiles': {'default': {'test_profile': False}}}
    (tmp_path / 'config.json').write_text(json.dumps(config_data), encoding='utf-8')

    _patch_config(monkeypatch, tmp_path)

    assert cmd_bug_report._get_config_data() == config_data


def test_get_log_files_uses_broker_interface(monkeypatch, tmp_path):
    """Test ``_get_log_files`` uses the configured client and broker log files."""
    client_log = tmp_path / 'client.log'
    client_log.write_text('client', encoding='utf-8')

    daemon_log = tmp_path / 'daemon.log'
    daemon_log.write_text('daemon', encoding='utf-8')

    circus_log = tmp_path / 'circus.log'
    circus_log.write_text('circus', encoding='utf-8')

    broker_log = tmp_path / 'rabbitmq.log'
    broker_log.write_text('broker', encoding='utf-8')

    daemon_client = SimpleNamespace(daemon_log_file=str(daemon_log), circus_log_file=str(circus_log))
    broker = SimpleNamespace(get_log_file=lambda: broker_log)
    profile = SimpleNamespace(name='default')
    manager = SimpleNamespace(get_profile=lambda: profile, get_broker=lambda: broker)

    _patch_config(monkeypatch, tmp_path, client_log=client_log)
    monkeypatch.setattr('aiida.engine.daemon.client.get_daemon_client', lambda: daemon_client)
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    assert cmd_bug_report._get_log_files() == [
        ('client.log', client_log),
        ('daemon.log', daemon_log),
        ('circus.log', circus_log),
        ('rabbitmq.log', broker_log),
    ]
