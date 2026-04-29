###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi status`."""

import pytest

from aiida import __version__, get_profile
from aiida.cmdline.commands import cmd_status
from aiida.cmdline.utils.echo import ExitCode
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.engine.daemon.client import DaemonClient
from aiida.storage.psql_dos import migrator


@pytest.mark.requires_broker
@pytest.mark.usefixtures('stopped_daemon_client')
def test_status(run_cli_command):
    """Test `verdi status`."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options)

    # Even though the daemon should not be running, the return value should still be 0 corresponding to success
    assert 'The daemon is not running' in result.output
    assert result.exit_code is ExitCode.SUCCESS.value

    for string in ['config', 'profile', 'storage', 'daemon']:
        assert string in result.output

    assert __version__ in result.output


@pytest.mark.usefixtures('empty_config')
def test_status_no_profile(run_cli_command):
    """Test `verdi status` when there is no profile."""
    options = []
    result = run_cli_command(cmd_status.verdi_status, options, use_subprocess=False)
    assert 'no profile configured yet' in result.output


def test_status_no_rmq(run_cli_command):
    """Test `verdi status` without a check for RabbitMQ."""
    options = ['--no-rmq']
    with pytest.warns(AiidaDeprecationWarning, match='The `--no-rmq` option is deprecated.'):
        result = run_cli_command(cmd_status.verdi_status, options)

    assert 'rabbitmq' not in result.output
    assert result.exit_code is ExitCode.SUCCESS.value

    for string in ['config', 'profile', 'storage', 'daemon']:
        assert string in result.output


@pytest.mark.requires_psql
def test_storage_unable_to_connect(run_cli_command):
    """Test `verdi status` when there is an unknown error while connecting to the storage."""
    profile = get_profile()

    old_port = profile._attributes['storage']['config']['database_port']
    profile._attributes['storage']['config']['database_port'] = 123

    try:
        result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
        assert "Unable to connect to profile's storage" in result.output
        assert result.exit_code is ExitCode.CRITICAL
    finally:
        profile._attributes['storage']['config']['database_port'] = old_port


@pytest.mark.requires_psql
def test_storage_incompatible(run_cli_command, monkeypatch):
    """Test `verdi status` when storage schema version is incompatible with that of the code."""

    def storage_cls(*args, **kwargs):
        from aiida.common.exceptions import IncompatibleStorageSchema

        raise IncompatibleStorageSchema()

    monkeypatch.setattr(migrator.PsqlDosMigrator, 'validate_storage', storage_cls)

    result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
    assert 'verdi storage migrate' in result.output
    assert result.exit_code is ExitCode.CRITICAL


@pytest.mark.requires_psql
def test_storage_corrupted(run_cli_command, monkeypatch):
    """Test `verdi status` when the storage is found to be corrupt (e.g. non-matching repository UUIDs)."""

    def storage_cls(*args, **kwargs):
        from aiida.common.exceptions import CorruptStorage

        raise CorruptStorage()

    monkeypatch.setattr(migrator.PsqlDosMigrator, 'validate_storage', storage_cls)

    result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
    assert 'Storage is corrupted' in result.output
    assert result.exit_code is ExitCode.CRITICAL


def test_sqlite_version(run_cli_command, monkeypatch):
    """Test `verdi status` when the sqlite version is incompatible with the required version.
    the main functionality of this test is triggered only by the pytest marker 'presto',
    through `pytest -m 'presto'`"""

    profile = get_profile()
    storage_backend = profile._attributes['storage']['backend']
    if storage_backend in ['core.sqlite_dos', 'core.sqlite_zip']:
        # Should raise if installed version is lower than the supported one.
        monkeypatch.setattr('aiida.storage.sqlite_zip.backend.SUPPORTED_VERSION', '100.0.0')
        result = run_cli_command(cmd_status.verdi_status, use_subprocess=False, raises=True)
        assert (
            'IncompatibleExternalDependencies: Storage backend requires sqlite 100.0.0 or higher. But you have'
            in result.stderr
        )

        # Should not raise if installed version is higher than the supported one.
        monkeypatch.setattr('aiida.storage.sqlite_zip.backend.SUPPORTED_VERSION', '0.0.0')
        result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    else:
        from unittest.mock import MagicMock

        mock_ = MagicMock()
        monkeypatch.setattr('aiida.storage.sqlite_zip.backend.validate_sqlite_version', mock_)
        result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
        assert mock_.call_count == 0


@pytest.mark.usefixtures('stopped_daemon_client')
def test_version_mismatch_warning(run_cli_command, monkeypatch, tmp_path):
    """Test that ``verdi status`` warns about version mismatches."""
    daemon_path = tmp_path / 'old-checkout'
    current_path = tmp_path / 'new-checkout'

    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(
        DaemonClient,
        'get_daemon_package_snapshot',
        lambda self: {'aiida-core': {'version': '2.8.0.post0', 'editable_path': str(daemon_path)}},
    )
    monkeypatch.setattr(
        DaemonClient,
        'get_package_version_snapshot',
        staticmethod(lambda: {'aiida-core': {'version': '2.8.0.post0', 'editable_path': str(current_path)}}),
    )

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' in result.output
    assert 'Changed packages:' in result.output
    assert 'aiida-core' in result.output
    assert result.output.count('daemon:') == 1
    assert str(daemon_path) in result.output
    assert str(current_path) in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
@pytest.mark.parametrize(
    ('daemon_versions', 'current_versions', 'expected_section', 'expected_change'),
    [
        (
            {'aiida-core': {'version': '2.8.0.post0'}},
            {'aiida-core': {'version': '2.8.0.post0'}, 'aiida-plugin': {'version': '1.2.3'}},
            'Added packages:',
            'aiida-plugin (1.2.3)',
        ),
        (
            {'aiida-core': {'version': '2.8.0.post0'}, 'aiida-plugin': {'version': '1.2.3'}},
            {'aiida-core': {'version': '2.8.0.post0'}},
            'Removed packages:',
            'aiida-plugin (1.2.3)',
        ),
    ],
)
def test_version_mismatch_warning_for_added_or_removed_plugin(
    run_cli_command, monkeypatch, daemon_versions, current_versions, expected_section, expected_change
):
    """Test that ``verdi status`` warns when plugins were added or removed since daemon startup."""
    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(DaemonClient, 'get_daemon_package_snapshot', lambda self: daemon_versions)
    monkeypatch.setattr(DaemonClient, 'get_package_version_snapshot', staticmethod(lambda: current_versions))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' in result.output
    assert expected_section in result.output
    assert expected_change in result.output
    assert result.output.count('daemon:') == 1


@pytest.mark.usefixtures('stopped_daemon_client')
@pytest.mark.parametrize(
    ('use_editable_path',),
    [(True,), (False,)],
)
def test_no_warning_when_versions_match(run_cli_command, monkeypatch, tmp_path, use_editable_path):
    """Test that ``verdi status`` shows no warning when versions match."""
    pkg_info: dict = {'version': '2.8.0.post0'}
    if use_editable_path:
        pkg_info['editable_path'] = str(tmp_path / 'aiida-core')

    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(DaemonClient, 'get_daemon_package_snapshot', lambda self: {'aiida-core': pkg_info})
    monkeypatch.setattr(DaemonClient, 'get_package_version_snapshot', staticmethod(lambda: {'aiida-core': pkg_info}))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' not in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
@pytest.mark.parametrize(
    ('daemon_has_path', 'current_has_path'),
    [(True, False), (False, True)],
)
def test_warning_when_editable_install_state_changes(
    run_cli_command, monkeypatch, tmp_path, daemon_has_path, current_has_path
):
    """Test that ``verdi status`` warns when editable-install state changes without a version change."""
    editable_path = str(tmp_path / 'aiida-core')
    daemon_info: dict = {'version': '2.8.0.post0'}
    current_info: dict = {'version': '2.8.0.post0'}
    if daemon_has_path:
        daemon_info['editable_path'] = editable_path
    if current_has_path:
        current_info['editable_path'] = editable_path

    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(DaemonClient, 'get_daemon_package_snapshot', lambda self: {'aiida-core': daemon_info})
    monkeypatch.setattr(
        DaemonClient, 'get_package_version_snapshot', staticmethod(lambda: {'aiida-core': current_info})
    )

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' in result.output
    assert 'Changed packages:' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_no_warning_when_version_file_missing(run_cli_command, monkeypatch):
    """Test that ``verdi status`` shows no warning when version file is missing."""
    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(DaemonClient, 'get_daemon_package_snapshot', lambda self: None)

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' not in result.output
