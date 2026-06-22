###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Unit tests for the `DaemonClient` class."""

import json
import pathlib
from unittest.mock import patch

import pytest
import zmq

from aiida.engine.daemon.client import (
    DaemonClient,
    DaemonNotRunningException,
    DaemonTimeoutException,
    _get_dist_commit_hash,
    _get_dist_editable_path,
    get_daemon_client,
)

pytestmark = pytest.mark.requires_broker


def test_ipc_socket_file_length_limit():
    """The maximum length of socket filepaths is often limited by the operating system.
    For MacOS it is limited to 103 bytes, versus 107 bytes on Unix. This limit is
    exposed by the Zmq library which is used by Circus library that is used to
    daemonize the daemon runners. This test verifies that the three endpoints used
    for the Circus client have a filepath that does not exceed that path limit.

    See issue #1317 and pull request #1403 for the discussion
    """
    daemon_client = get_daemon_client()

    controller_endpoint = daemon_client.get_controller_endpoint()
    pubsub_endpoint = daemon_client.get_pubsub_endpoint()
    stats_endpoint = daemon_client.get_stats_endpoint()

    assert len(controller_endpoint) <= zmq.IPC_PATH_MAX_LEN
    assert len(pubsub_endpoint) <= zmq.IPC_PATH_MAX_LEN
    assert len(stats_endpoint) <= zmq.IPC_PATH_MAX_LEN


def test_get_daemon_client_non_default_profile(profile_factory, empty_config):
    """Test that ``get_daemon_client`` returns a client for the requested profile, not the default."""
    profile_default = profile_factory('default-profile')
    profile_other = profile_factory('other-profile')
    empty_config.add_profile(profile_default)
    empty_config.add_profile(profile_other)
    empty_config.set_default_profile('default-profile', overwrite=True).store()

    client = get_daemon_client('other-profile')
    assert client.profile.name == 'other-profile'


def test_get_daemon_client_does_not_switch_profile(empty_config, profile_factory):
    """Test that ``get_daemon_client`` does not switch the loaded profile."""
    from aiida.manage import get_manager

    profile_default = profile_factory(
        'default',
        storage_backend='core.sqlite_dos',
        process_control_backend='rabbitmq',
        repository_dirpath=empty_config.dirpath,
    )
    profile_other = profile_factory(
        'other',
        storage_backend='core.sqlite_dos',
        process_control_backend='rabbitmq',
        repository_dirpath=empty_config.dirpath,
    )

    empty_config.add_profile(profile_default)
    empty_config.add_profile(profile_other)
    empty_config.set_default_profile(profile_default.name, overwrite=True)
    empty_config.store()

    manager = get_manager()
    manager.load_profile(profile_other.name, allow_switch=True)

    assert manager.get_profile().name == profile_other.name
    assert get_daemon_client(profile_default.name).profile.name == profile_default.name
    assert manager.get_profile().name == profile_other.name


def test_get_status_daemon_not_running(stopped_daemon_client):
    """Test ``DaemonClient.get_status`` output when the daemon is not running."""
    with pytest.raises(DaemonNotRunningException, match='The daemon is not running.'):
        stopped_daemon_client.get_status()


def raise_daemon_timeout():
    """Raise a ``DaemonTimeoutException``."""
    raise DaemonTimeoutException('Connection to the daemon timed out.')


@patch.object(DaemonClient, 'get_status', lambda _: raise_daemon_timeout())
def test_get_status_timeout(stopped_daemon_client):
    """Test ``DaemonClient.get_status`` output when the circus daemon process cannot be reached."""
    with pytest.raises(DaemonTimeoutException, match='Connection to the daemon timed out.'):
        stopped_daemon_client.get_status()


@pytest.mark.usefixtures('aiida_profile_clean')
class TestDaemonVersionInfo:
    """Tests for the daemon version info methods."""

    @staticmethod
    def test_get_package_version_snapshot():
        """Test that ``get_package_version_snapshot`` returns at least ``aiida-core``."""
        from importlib.metadata import version as metadata_version

        versions = DaemonClient.get_package_version_snapshot()
        assert 'aiida-core' in versions
        assert versions['aiida-core']['version'].startswith(metadata_version('aiida-core'))

    @staticmethod
    def test_get_daemon_package_snapshot_no_file(stopped_daemon_client):
        """Test that ``get_daemon_package_snapshot`` returns None when no version file exists."""
        assert stopped_daemon_client.get_daemon_package_snapshot() is None

    @staticmethod
    def test_daemon_package_snapshot_file_missing_configuration(stopped_daemon_client, monkeypatch):
        """Test that ``daemon_package_snapshot_file`` raises ``ConfigurationError`` when the filepath is missing."""
        from aiida.common.exceptions import ConfigurationError

        filepaths = stopped_daemon_client._config.filepaths(stopped_daemon_client.profile)
        monkeypatch.setattr(
            stopped_daemon_client._config, 'filepaths', lambda profile: {'daemon': {'pid': filepaths['daemon']['pid']}}
        )

        with pytest.raises(ConfigurationError, match='daemon package snapshot file path is not configured'):
            _ = stopped_daemon_client.daemon_package_snapshot_file

    @staticmethod
    def test_get_daemon_package_snapshot_missing_configuration(stopped_daemon_client, monkeypatch):
        """Test that ``get_daemon_package_snapshot`` returns None when the filepath is missing."""
        filepaths = stopped_daemon_client._config.filepaths(stopped_daemon_client.profile)
        modified_filepaths = dict(filepaths)
        modified_filepaths['daemon'] = dict(filepaths['daemon'])
        modified_filepaths['daemon'].pop('package_snapshot', None)
        monkeypatch.setattr(stopped_daemon_client._config, 'filepaths', lambda profile: modified_filepaths)

        assert stopped_daemon_client.get_daemon_package_snapshot() is None

    @staticmethod
    def test_get_daemon_package_snapshot_corrupt_file(stopped_daemon_client):
        """Test that ``get_daemon_package_snapshot`` returns None for corrupt version file."""
        version_file = pathlib.Path(stopped_daemon_client.daemon_package_snapshot_file)
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text('not valid json {{{', encoding='utf8')
        assert stopped_daemon_client.get_daemon_package_snapshot() is None

    @staticmethod
    def test_daemon_version_info_roundtrip(stopped_daemon_client):
        """Test that version info can be written and read back."""
        version_file = pathlib.Path(stopped_daemon_client.daemon_package_snapshot_file)
        version_file.parent.mkdir(parents=True, exist_ok=True)
        expected = {
            'aiida-core': {'version': '2.6.0', 'editable_path': '/tmp/aiida-core'},
            'some-plugin': {'version': '1.0.0'},
        }
        version_file.write_text(json.dumps(expected), encoding='utf8')
        assert stopped_daemon_client.get_daemon_package_snapshot() == expected

    @staticmethod
    def test_get_dist_commit_hash_vcs_install():
        """Test that ``_get_dist_commit_hash`` extracts commit_id from VCS install metadata."""
        from unittest.mock import MagicMock

        dist = MagicMock()
        dist.read_text.return_value = json.dumps(
            {
                'url': 'https://github.com/aiidateam/aiida-core',
                'vcs_info': {'vcs': 'git', 'commit_id': 'abcdef1234567890', 'requested_revision': 'main'},
            }
        )
        assert _get_dist_commit_hash(dist) == 'abcdef1234567890'

    @staticmethod
    def test_get_dist_commit_hash_no_direct_url():
        """Test that ``_get_dist_commit_hash`` returns None when direct_url.json is absent."""
        from unittest.mock import MagicMock

        dist = MagicMock()
        dist.read_text.return_value = None
        assert _get_dist_commit_hash(dist) is None

    @staticmethod
    def test_get_dist_commit_hash_editable_install():
        """Test that ``_get_dist_commit_hash`` ignores editable installs from local directories."""
        from unittest.mock import MagicMock

        dist = MagicMock()
        dist.read_text.return_value = json.dumps(
            {
                'url': 'file:///tmp/aiida-core',
                'dir_info': {'editable': True},
            }
        )
        assert _get_dist_commit_hash(dist) is None

    @staticmethod
    def test_get_dist_editable_path():
        """Test that ``_get_dist_editable_path`` extracts a normalized local path for editable installs."""
        import tempfile
        from unittest.mock import MagicMock

        with tempfile.TemporaryDirectory() as tmpdir:
            dist = MagicMock()
            dist.read_text.return_value = json.dumps(
                {'url': pathlib.Path(tmpdir).as_uri(), 'dir_info': {'editable': True}}
            )
            assert _get_dist_editable_path(dist) == str(pathlib.Path(tmpdir).resolve())

    @staticmethod
    def test_get_package_version_snapshot_includes_editable_path():
        """Test that editable local installs record their source path in the package snapshot."""
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch

        with tempfile.TemporaryDirectory() as tmpdir:
            dist = MagicMock()
            dist.name = 'aiida-core'
            dist.version = '2.8.0.post0'
            dist.read_text.return_value = json.dumps(
                {'url': pathlib.Path(tmpdir).as_uri(), 'dir_info': {'editable': True}}
            )
            entry_point = SimpleNamespace(group='aiida.transports', dist=dist)

            with patch('aiida.plugins.entry_point.eps', return_value=[entry_point]):
                versions = DaemonClient.get_package_version_snapshot()

            assert versions == {
                'aiida-core': {'version': '2.8.0.post0', 'editable_path': str(pathlib.Path(tmpdir).resolve())}
            }

    @staticmethod
    def test_get_package_version_snapshot_parses_direct_url_once():
        """Test that ``get_package_version_snapshot`` reads ``direct_url.json`` at most once per distribution."""
        from types import SimpleNamespace
        from unittest.mock import MagicMock, patch

        dist = MagicMock()
        dist.name = 'aiida-core'
        dist.version = '2.8.0.post0'
        dist.read_text.return_value = json.dumps({'url': 'https://github.com/aiidateam/aiida-core'})
        entry_point = SimpleNamespace(group='aiida.transports', dist=dist)

        with patch('aiida.plugins.entry_point.eps', return_value=[entry_point]):
            DaemonClient.get_package_version_snapshot()

        dist.read_text.assert_called_once_with('direct_url.json')

    @staticmethod
    def test_stop_daemon_cleans_version_file(stopped_daemon_client):
        """Test that ``stop_daemon`` removes the version file."""
        version_file = pathlib.Path(stopped_daemon_client.daemon_package_snapshot_file)
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text('{"aiida-core": "2.6.0"}', encoding='utf8')
        assert version_file.exists()

        with (
            patch.object(DaemonClient, 'call_client', return_value={}),
            patch.object(DaemonClient, 'delete_circus_socket_directory'),
        ):
            stopped_daemon_client.stop_daemon()

        assert not version_file.exists()

    @staticmethod
    def test_stop_daemon_missing_version_file_configuration(stopped_daemon_client, monkeypatch):
        """Test that ``stop_daemon`` ignores a missing version-file configuration."""
        filepaths = stopped_daemon_client._config.filepaths(stopped_daemon_client.profile)
        modified_filepaths = dict(filepaths)
        modified_filepaths['daemon'] = dict(filepaths['daemon'])
        modified_filepaths['daemon'].pop('package_snapshot', None)
        monkeypatch.setattr(stopped_daemon_client._config, 'filepaths', lambda profile: modified_filepaths)

        with (
            patch.object(DaemonClient, 'call_client', return_value={}),
            patch.object(DaemonClient, 'delete_circus_socket_directory'),
        ):
            assert stopped_daemon_client.stop_daemon() == {}

    @staticmethod
    def test_start_daemon_writes_version_file(stopped_daemon_client):
        """Test that ``start_daemon`` writes the version file after a successful spawn."""
        version_file = pathlib.Path(stopped_daemon_client.daemon_package_snapshot_file)
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.unlink(missing_ok=True)

        with (
            patch('aiida.engine.daemon.client.subprocess.check_output', return_value=b''),
            patch.object(DaemonClient, '_await_condition'),
            patch.object(DaemonClient, '_clean_potentially_stale_pid_file'),
            patch.object(
                DaemonClient, 'get_package_version_snapshot', return_value={'aiida-core': {'version': '2.6.0'}}
            ),
        ):
            stopped_daemon_client.start_daemon()

        assert version_file.exists()
        assert json.loads(version_file.read_text(encoding='utf8')) == {'aiida-core': {'version': '2.6.0'}}

    @staticmethod
    def test_start_daemon_no_version_file_on_await_failure(stopped_daemon_client):
        """Test that ``start_daemon`` does not write the version file if ``_await_condition`` fails."""
        version_file = pathlib.Path(stopped_daemon_client.daemon_package_snapshot_file)
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.unlink(missing_ok=True)

        with (
            patch('aiida.engine.daemon.client.subprocess.check_output', return_value=b''),
            patch.object(
                DaemonClient,
                '_await_condition',
                side_effect=DaemonTimeoutException('timed out'),
            ),
            patch.object(DaemonClient, '_clean_potentially_stale_pid_file'),
            patch.object(
                DaemonClient, 'get_package_version_snapshot', return_value={'aiida-core': {'version': '2.6.0'}}
            ),
        ):
            with pytest.raises(DaemonTimeoutException):
                stopped_daemon_client.start_daemon()

        assert not version_file.exists()

    @staticmethod
    def test_start_daemon_missing_version_file_configuration(stopped_daemon_client, monkeypatch):
        """Test that ``start_daemon`` ignores a missing version-file configuration."""
        filepaths = stopped_daemon_client._config.filepaths(stopped_daemon_client.profile)
        modified_filepaths = dict(filepaths)
        modified_filepaths['daemon'] = dict(filepaths['daemon'])
        modified_filepaths['daemon'].pop('package_snapshot', None)
        monkeypatch.setattr(stopped_daemon_client._config, 'filepaths', lambda profile: modified_filepaths)

        with (
            patch('aiida.engine.daemon.client.subprocess.check_output', return_value=b''),
            patch.object(DaemonClient, '_await_condition'),
            patch.object(DaemonClient, '_clean_potentially_stale_pid_file'),
            patch.object(
                DaemonClient, 'get_package_version_snapshot', return_value={'aiida-core': {'version': '2.6.0'}}
            ),
        ):
            stopped_daemon_client.start_daemon()

    @staticmethod
    def test_restart_daemon_writes_version_file(stopped_daemon_client):
        """Test that ``restart_daemon`` updates the version file after a successful restart."""
        version_file = pathlib.Path(stopped_daemon_client.daemon_package_snapshot_file)
        version_file.parent.mkdir(parents=True, exist_ok=True)
        version_file.write_text('{"aiida-core": {"version": "1.0.0"}}', encoding='utf8')

        with (
            patch.object(DaemonClient, 'call_client', return_value={'status': 'ok'}),
            patch.object(
                DaemonClient, 'get_package_version_snapshot', return_value={'aiida-core': {'version': '2.6.0'}}
            ),
        ):
            stopped_daemon_client.restart_daemon()

        assert json.loads(version_file.read_text(encoding='utf8')) == {'aiida-core': {'version': '2.6.0'}}

    @staticmethod
    def test_restart_daemon_missing_version_file_configuration(stopped_daemon_client, monkeypatch):
        """Test that ``restart_daemon`` ignores a missing version-file configuration."""
        filepaths = stopped_daemon_client._config.filepaths(stopped_daemon_client.profile)
        modified_filepaths = dict(filepaths)
        modified_filepaths['daemon'] = dict(filepaths['daemon'])
        modified_filepaths['daemon'].pop('package_snapshot', None)
        monkeypatch.setattr(stopped_daemon_client._config, 'filepaths', lambda profile: modified_filepaths)

        with (
            patch.object(DaemonClient, 'call_client', return_value={'status': 'ok'}),
            patch.object(
                DaemonClient, 'get_package_version_snapshot', return_value={'aiida-core': {'version': '2.6.0'}}
            ),
        ):
            assert stopped_daemon_client.restart_daemon() == {'status': 'ok'}
