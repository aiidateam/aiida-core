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
import zipfile
from types import SimpleNamespace

import pytest

import aiida
from aiida.brokers.zeromq.broker import ZeromqBroker
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

    def get_service_status(self):
        return {'product': 'RabbitMQ', 'version': '3.12.0'}

    def close(self):
        self.closed = True


class BrokenStorageBackend:
    """Broken storage backend."""

    def __init__(self, _profile):
        raise RuntimeError('storage unavailable')


class BrokenStorageStringBackend(DummyStorageBackend):
    """Storage backend whose string conversion fails."""

    def __str__(self):
        raise RuntimeError('storage string unavailable')


class BrokenStorageCloseBackend(DummyStorageBackend):
    """Storage backend whose close operation fails."""

    def close(self):
        raise RuntimeError('storage close unavailable')


def _make_zeromq_broker(service_dir: pathlib.Path, is_running: bool, status: dict | None) -> ZeromqBroker:
    """Create a ``ZeromqBroker`` instance without invoking its constructor."""
    broker = ZeromqBroker.__new__(ZeromqBroker)
    broker._service_dir = service_dir
    broker.is_service_reachable = lambda: is_running
    broker.get_service_status = lambda: status
    return broker


def _patch_manager(monkeypatch, profile, broker, get_daemon_client):
    """Patch the global manager used by ``cmd_bug_report``."""
    manager = SimpleNamespace(
        _broker=None,
        profile_storage_loaded=False,
        get_profile=lambda: profile,
        get_profile_storage=lambda: profile.storage_cls(profile),
        reset_profile_storage=lambda: None,
        get_broker=lambda: broker,
        reset_broker=lambda: None,
        get_daemon_client=get_daemon_client,
    )
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)


def _get_daemon_client_ok():
    """Return a daemon client with a running daemon status."""
    return SimpleNamespace(get_status=lambda: {'pid': 1234})


def _get_daemon_client_error():
    """Raise an error for an unavailable daemon client."""
    raise RuntimeError('daemon unavailable')


def _make_filepaths(dirpath: pathlib.Path) -> dict:
    """Return a profile filepaths dictionary rooted in the given directory."""
    return {
        'profile': {'log': str(dirpath / 'profile.log')},
        'daemon': {'log': str(dirpath / 'daemon.log')},
        'circus': {'log': str(dirpath / 'circus.log')},
        'zmq_broker_service': {'dir': str(dirpath / 'broker'), 'log': str(dirpath / 'broker' / 'broker.log')},
    }


def _patch_config(monkeypatch, dirpath):
    """Patch the global config used by ``cmd_bug_report``."""
    monkeypatch.setattr(
        'aiida.manage.configuration.get_config',
        lambda: SimpleNamespace(
            dirpath=str(dirpath),
            filepaths=lambda _profile: _make_filepaths(dirpath),
        ),
    )


def test_collect_diagnostics(monkeypatch, tmp_path):
    """Test ``_collect_diagnostics`` returns structured JSON-serializable data."""
    profile = SimpleNamespace(name='default', storage_cls=DummyStorageBackend)
    config_data = {
        'profiles': {
            'default': {
                'storage': {'backend': 'core.sqlite_dos', 'config': {'database_password': 'secret'}},
                'process_control': {'config': {'broker_password': 'guest'}},
                'AIIDADB_PASS': 'legacy-secret',
            }
        }
    }
    (tmp_path / 'config.json').write_text(json.dumps(config_data), encoding='utf-8')

    monkeypatch.setattr(aiida, '__version__', '1.2.3')
    _patch_manager(monkeypatch, profile, DummyBroker(), _get_daemon_client_ok)
    _patch_config(monkeypatch, tmp_path)

    diagnostics = cmd_bug_report._collect_diagnostics()

    assert diagnostics['aiida_version'] == '1.2.3'
    assert diagnostics['profile'] == {'name': 'default'}
    assert diagnostics['config']['profiles']['default']['storage']['config']['database_password'] == '***'
    assert diagnostics['config']['profiles']['default']['process_control']['config']['broker_password'] == '***'
    assert diagnostics['config']['profiles']['default']['AIIDADB_PASS'] == '***'
    assert {key: diagnostics['python'][key] for key in ('major', 'minor', 'micro')} == {
        'major': sys.version_info.major,
        'minor': sys.version_info.minor,
        'micro': sys.version_info.micro,
    }
    for key in ('version', 'implementation', 'compiler', 'executable'):
        assert diagnostics['python'][key]
    assert isinstance(diagnostics['python']['build'], list)


@pytest.mark.parametrize(
    ('storage_cls', 'broker_cls', 'get_daemon_client', 'expected_services'),
    [
        pytest.param(
            DummyStorageBackend,
            DummyBroker,
            _get_daemon_client_ok,
            {
                'storage': {'connected': True, 'status': 'DummyStorageBackend'},
                'broker': {'connected': True, 'status': {'product': 'RabbitMQ', 'version': '3.12.0'}},
                'daemon': {'connected': True, 'status': {'pid': 1234}},
            },
            id='connected',
        ),
        pytest.param(
            BrokenStorageBackend,
            None,
            _get_daemon_client_error,
            {
                'storage': {'connected': False, 'status': 'RuntimeError: storage unavailable'},
                'broker': {'connected': False, 'status': 'No broker configured for this profile.'},
                'daemon': {'connected': False, 'status': 'RuntimeError: daemon unavailable'},
            },
            id='not-connected',
        ),
    ],
)
def test_collect_diagnostics_services(
    monkeypatch, tmp_path, storage_cls, broker_cls, get_daemon_client, expected_services
):
    """Test ``_collect_diagnostics`` reports service connection information."""
    profile = SimpleNamespace(name='default', dictionary={}, storage_cls=storage_cls)
    broker = broker_cls() if broker_cls is not None else None
    (tmp_path / 'config.json').write_text('{}', encoding='utf-8')
    _patch_manager(monkeypatch, profile, broker, get_daemon_client)
    _patch_config(monkeypatch, tmp_path)

    diagnostics = cmd_bug_report._collect_diagnostics()

    assert diagnostics['services'] == expected_services


@pytest.mark.parametrize(
    ('is_running', 'status'),
    [
        (True, {'pid': 4321, 'pending_tasks': 0}),
        (False, None),
    ],
)
def test_check_broker_zeromq_status(monkeypatch, tmp_path, is_running, status):
    """Test ``_check_broker`` reports the ZeroMQ broker service status payload."""
    broker = _make_zeromq_broker(tmp_path, is_running=is_running, status=status)
    manager = SimpleNamespace(_broker=None, get_broker=lambda: broker, reset_broker=lambda: None)
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    result = cmd_bug_report._check_broker()

    assert result['connected'] is (status is not None)
    assert result['status'] == status


def test_get_config_data(monkeypatch, tmp_path):
    """Test ``_get_config_data`` returns the contents of ``config.json`` with secrets redacted."""
    config_data = {
        'profiles': {
            'default': {
                'test_profile': False,
                'storage': {'config': {'database_password': 'secret'}},
                'process_control': {'config': {'broker_password': 'guest'}},
                'AIIDADB_PASS': 'legacy-secret',
            }
        }
    }
    (tmp_path / 'config.json').write_text(json.dumps(config_data), encoding='utf-8')

    _patch_config(monkeypatch, tmp_path)

    assert cmd_bug_report._get_config_data() == {
        'profiles': {
            'default': {
                'test_profile': False,
                'storage': {'config': {'database_password': '***'}},
                'process_control': {'config': {'broker_password': '***'}},
                'AIIDADB_PASS': '***',
            }
        }
    }


def test_collect_diagnostics_invalid_config(monkeypatch, tmp_path):
    """Test invalid config data does not abort diagnostics collection."""
    profile = SimpleNamespace(name='default', storage_cls=DummyStorageBackend)
    (tmp_path / 'config.json').write_bytes(b'\x80')

    _patch_manager(monkeypatch, profile, DummyBroker(), _get_daemon_client_ok)
    _patch_config(monkeypatch, tmp_path)

    diagnostics = cmd_bug_report._collect_diagnostics()

    assert diagnostics['config'] is None
    assert (
        diagnostics['config_error']
        == "UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte"
    )


def test_get_log_files(monkeypatch, tmp_path):
    """Test ``_get_log_files`` returns the existing log files from the profile filepaths."""
    profile_log = tmp_path / 'profile.log'
    profile_log.write_text('profile', encoding='utf-8')

    daemon_log = tmp_path / 'daemon.log'
    daemon_log.write_text('daemon', encoding='utf-8')

    circus_log = tmp_path / 'circus.log'
    circus_log.write_text('circus', encoding='utf-8')

    broker_log = tmp_path / 'broker' / 'broker.log'
    broker_log.parent.mkdir()
    broker_log.write_text('broker', encoding='utf-8')

    profile = SimpleNamespace(name='default')
    manager = SimpleNamespace(get_profile=lambda: profile)

    _patch_config(monkeypatch, tmp_path)
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    assert cmd_bug_report._get_log_files() == [profile_log, circus_log, daemon_log, broker_log]


def test_get_log_files_skips_missing(monkeypatch, tmp_path):
    """Test ``_get_log_files`` skips log files that do not exist."""
    daemon_log = tmp_path / 'daemon.log'
    daemon_log.write_text('daemon', encoding='utf-8')

    profile = SimpleNamespace(name='default')
    manager = SimpleNamespace(get_profile=lambda: profile)

    _patch_config(monkeypatch, tmp_path)
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    assert cmd_bug_report._get_log_files() == [daemon_log]


def test_read_log_tail(tmp_path):
    """Test ``_read_log_tail`` truncates long log files to their tail."""
    log_file = tmp_path / 'test.log'
    log_file.write_bytes(b'a' * 10 + b'b' * 30)

    assert cmd_bug_report._read_log_tail(log_file, max_bytes=100) == b'a' * 10 + b'b' * 30

    truncated = cmd_bug_report._read_log_tail(log_file, max_bytes=35)
    assert truncated == b'... (truncated from 40 bytes)\n' + b'b' * 5
    assert len(truncated) <= 35


def test_read_log_tail_handles_partial_utf8(tmp_path):
    """Test ``_read_log_tail`` drops incomplete UTF-8 bytes at the truncation boundary."""
    log_file = tmp_path / 'test.log'
    log_file.write_bytes(b'a' * 30 + '🙂'.encode('utf-8') + b'b' * 2)

    truncated = cmd_bug_report._read_log_tail(log_file, max_bytes=34)

    assert truncated == b'... (truncated from 36 bytes)\n' + b'b' * 2


def test_check_storage_failure_after_instantiation(monkeypatch):
    """Test storage string conversion failures are reported instead of escaping."""
    profile = SimpleNamespace(storage_cls=BrokenStorageStringBackend)

    def reset_profile_storage():
        return None

    manager = SimpleNamespace(
        profile_storage_loaded=False,
        get_profile_storage=lambda: profile.storage_cls(profile),
        reset_profile_storage=reset_profile_storage,
    )
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    assert cmd_bug_report._check_storage() == {
        'connected': False,
        'status': 'RuntimeError: storage string unavailable',
    }


def test_check_storage_close_failure_is_logged(monkeypatch, caplog):
    """Test storage reset failures are logged without changing the connection result."""
    profile = SimpleNamespace(storage_cls=DummyStorageBackend)
    manager = SimpleNamespace(
        profile_storage_loaded=False,
        get_profile_storage=lambda: profile.storage_cls(profile),
        reset_profile_storage=lambda: (_ for _ in ()).throw(RuntimeError('storage close unavailable')),
    )
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    result = cmd_bug_report._check_storage()

    assert result == {'connected': True, 'status': 'DummyStorageBackend'}
    assert 'Failed to reset storage while collecting bug report diagnostics' in caplog.text


def test_check_broker_reset_failure_is_logged(monkeypatch, caplog):
    """Test broker reset failures are logged without changing the connection result."""
    broker = DummyBroker()
    manager = SimpleNamespace(
        _broker=None,
        get_broker=lambda: broker,
        reset_broker=lambda: (_ for _ in ()).throw(RuntimeError('broker close unavailable')),
    )
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    result = cmd_bug_report._check_broker()

    assert result == {'connected': True, 'status': {'product': 'RabbitMQ', 'version': '3.12.0'}}
    assert 'Failed to reset broker while collecting bug report diagnostics' in caplog.text


def test_check_broker_does_not_reset_preloaded_broker(monkeypatch):
    """Test preloaded broker is not reset by the diagnostics check."""
    broker = DummyBroker()
    reset_called = False

    def reset_broker():
        nonlocal reset_called
        reset_called = True

    manager = SimpleNamespace(_broker=broker, get_broker=lambda: broker, reset_broker=reset_broker)
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    result = cmd_bug_report._check_broker()

    assert result == {'connected': True, 'status': {'product': 'RabbitMQ', 'version': '3.12.0'}}
    assert reset_called is False
    assert broker.closed is False


def test_check_storage_does_not_reset_preloaded_storage(monkeypatch):
    """Test preloaded storage is not reset by the diagnostics check."""
    storage = DummyStorageBackend(None)
    reset_called = False

    def reset_profile_storage():
        nonlocal reset_called
        reset_called = True

    manager = SimpleNamespace(
        profile_storage_loaded=True,
        get_profile_storage=lambda: storage,
        reset_profile_storage=reset_profile_storage,
    )
    monkeypatch.setattr('aiida.manage.get_manager', lambda: manager)

    result = cmd_bug_report._check_storage()

    assert result == {'connected': True, 'status': 'DummyStorageBackend'}
    assert reset_called is False
    assert storage.closed is False


def test_bug_report_command(run_cli_command, tmp_path):
    """Test the ``verdi bug-report`` command creates a zip file with diagnostics."""
    output = tmp_path / 'report.zip'
    result = run_cli_command(cmd_bug_report.verdi_bug_report, ['-o', str(output)], use_subprocess=False)

    assert output.exists()
    assert 'Bug report written to' in result.output

    with zipfile.ZipFile(output) as zf:
        assert 'diagnostics.json' in zf.namelist()
        diagnostics = json.loads(zf.read('diagnostics.json'))

    assert diagnostics['aiida_version'] == aiida.__version__
    assert diagnostics['profile'] is not None
    assert diagnostics['services']['storage']['connected'] is True


def test_bug_report_command_default_output(run_cli_command, monkeypatch, tmp_path):
    """Test ``verdi bug-report`` uses a timestamped default output filename."""
    monkeypatch.chdir(tmp_path)

    result = run_cli_command(cmd_bug_report.verdi_bug_report, use_subprocess=False)

    output_files = list(tmp_path.glob('aiida-bug-report-*.zip'))

    assert len(output_files) == 1
    assert output_files[0].name != 'aiida-bug-report-{timestamp}.zip'
    assert 'Bug report written to' in result.output


def test_bug_report_command_output_directory(run_cli_command, tmp_path):
    """Test ``verdi bug-report`` writes into a target output directory."""
    output_directory = tmp_path / 'reports'
    output_directory.mkdir()

    result = run_cli_command(cmd_bug_report.verdi_bug_report, ['-o', str(output_directory)], use_subprocess=False)

    output_files = list(output_directory.glob('aiida-bug-report-*.zip'))

    assert len(output_files) == 1
    assert 'Bug report written to' in result.output


def test_bug_report_command_rejects_existing_output(run_cli_command, tmp_path):
    """Test ``verdi bug-report`` fails rather than overwriting an existing archive."""
    output = tmp_path / 'report.zip'
    output.write_text('existing', encoding='utf-8')

    result = run_cli_command(cmd_bug_report.verdi_bug_report, ['-o', str(output)], raises=True, use_subprocess=False)

    assert 'already exists' in result.output
    assert output.read_text(encoding='utf-8') == 'existing'
