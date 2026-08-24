###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for `verdi status`."""

import sys

import pytest

from aiida import __version__, get_profile
from aiida.brokers.zeromq.broker import ZeromqBroker
from aiida.cmdline.commands import cmd_status
from aiida.cmdline.utils.echo import ExitCode
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.engine.daemon.client import DaemonClient, DaemonException
from aiida.manage import get_manager
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


def test_status_no_broker(run_cli_command, monkeypatch):
    """Test `verdi status` reports when a brokerless profile still has a running daemon."""
    from aiida.manage.manager import get_manager

    manager = get_manager()
    profile = manager.get_profile()
    assert profile is not None

    old_backend = profile.process_control_backend
    old_config = profile.process_control_config

    try:
        profile.set_process_controller(None, None)
        manager.reset_broker()
        monkeypatch.setattr(DaemonClient, 'is_daemon_running', property(lambda self: True))
        result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    finally:
        profile.set_process_controller(old_backend, old_config)
        manager.reset_broker()

    assert result.exit_code is ExitCode.SUCCESS.value
    assert 'Daemon appears to be running but no broker is defined for this profile' in result.output


def test_status_daemon_exception(run_cli_command, monkeypatch):
    """Test `verdi status` returns a critical exit code on daemon errors."""

    def raise_daemon_exception(self):
        raise DaemonException('Connection failed.')

    monkeypatch.setattr(DaemonClient, 'get_status', raise_daemon_exception)

    result = run_cli_command(cmd_status.verdi_status, raises=True, use_subprocess=False)
    assert 'Connection failed.' in result.output
    assert result.exit_code is ExitCode.CRITICAL


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
def test_status_surfaces_zeromq_probe_error(run_cli_command, monkeypatch, tmp_path):
    """Test ``verdi status`` surfaces ZeroMQ probe errors even when the broker is reachable."""
    broker = ZeromqBroker.__new__(ZeromqBroker)
    broker._service_dir = tmp_path
    broker._service_log_file = tmp_path / 'broker.log'
    broker._service_status_file = tmp_path / 'broker.status'
    broker._service_status_file.write_text('{INVALID JSON')
    broker.check_service_reachable = lambda: True
    monkeypatch.setattr(get_manager(), 'get_broker', lambda: broker)
    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(DaemonClient, '_get_daemon_env_info', lambda self: None)

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    assert 'Failed to probe broker status: JSONDecodeError' in result.output
    assert 'Broker is running as PID ? [? pending, ? processing]' not in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_version_mismatch_warning(run_cli_command, monkeypatch, tmp_path):
    """Test that ``verdi status`` warns about version mismatches."""
    daemon_path = tmp_path / 'old-checkout'
    current_path = tmp_path / 'new-checkout'

    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(
        DaemonClient,
        '_get_daemon_env_info',
        lambda self: {
            'packages': {'aiida-core': {'version': '2.8.0.post0', 'editable_path': str(daemon_path)}},
            'python_binary': sys.executable,
        },
    )
    monkeypatch.setattr(
        DaemonClient,
        '_get_package_version_snapshot',
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
    ('daemon_packages', 'current_packages', 'expected_section', 'expected_change'),
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
    run_cli_command, monkeypatch, daemon_packages, current_packages, expected_section, expected_change
):
    """Test that ``verdi status`` warns when plugins were added or removed since daemon startup."""
    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(
        DaemonClient,
        '_get_daemon_env_info',
        lambda self: {'packages': daemon_packages, 'python_binary': sys.executable},
    )
    monkeypatch.setattr(DaemonClient, '_get_package_version_snapshot', staticmethod(lambda: current_packages))

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
    monkeypatch.setattr(
        DaemonClient,
        '_get_daemon_env_info',
        lambda self: {'packages': {'aiida-core': pkg_info}, 'python_binary': sys.executable},
    )
    monkeypatch.setattr(DaemonClient, '_get_package_version_snapshot', staticmethod(lambda: {'aiida-core': pkg_info}))

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
    monkeypatch.setattr(
        DaemonClient,
        '_get_daemon_env_info',
        lambda self: {'packages': {'aiida-core': daemon_info}, 'python_binary': sys.executable},
    )
    monkeypatch.setattr(
        DaemonClient, '_get_package_version_snapshot', staticmethod(lambda: {'aiida-core': current_info})
    )

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' in result.output
    assert 'Changed packages:' in result.output


@pytest.mark.usefixtures('stopped_daemon_client')
def test_no_warning_when_version_file_missing(run_cli_command, monkeypatch):
    """Test that ``verdi status`` shows no warning when version file is missing."""
    monkeypatch.setattr(DaemonClient, 'get_status', lambda self, timeout=None: {'pid': 12345})
    monkeypatch.setattr(DaemonClient, '_get_daemon_env_info', lambda self: None)

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    assert 'different package versions' not in result.output


@pytest.fixture
def brokerless_profile():
    """Unset the process controller of the loaded profile, so the status of the broker cannot fail the command."""
    manager = get_manager()
    profile = manager.get_profile()
    old_backend = profile.process_control_backend
    old_config = profile.process_control_config

    profile.set_process_controller(None, None)
    manager.reset_broker()

    yield profile

    profile.set_process_controller(old_backend, old_config)
    manager.reset_broker()


def peer_entry(url, nickname, **overrides):
    """Return a roster entry of a collab peer, as a completed contact leaves it."""
    return {
        'url': url,
        'nickname': nickname,
        'name': nickname,
        'stamp': 1,
        'seen': True,
        'active': True,
        'signalled': False,
        **overrides,
    }


def decodable_codes(output):
    """Return every whitespace-separated word of ``output`` that parses as a join code.

    Asserted on rather than on the redaction text: what matters is that no rendering of the code reaches the
    output, and matching a string would keep passing if a later change printed it in another shape.
    """
    from aiida.tools.collab.protocol import JoinCode

    found = []

    for word in output.split():
        try:
            found.append(JoinCode.decode(word))
        except ValueError:
            continue

    return found


def test_status_collab(run_cli_command, brokerless_profile, monkeypatch):
    """Test that the collab section lists each peer, reports the last sync and withholds the join code.

    A peer that never answered is called apart from one that is merely down: a wrong address announced at join
    cannot be detected any other way, since a joiner's endpoint only starts with its daemon.
    """
    from datetime import datetime
    from pathlib import Path

    from aiida import __version__
    from aiida.tools.archive.abstract import get_format
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError, PeerInfo
    from aiida.tools.collab.state import CollabEvent, CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(brokerless_profile.options, 'collab.uuid', 'uuid-of-the-collab')
    monkeypatch.setitem(brokerless_profile.options, 'collab.token', 'the-token')
    monkeypatch.setitem(brokerless_profile.options, 'collab.bind', '100.64.0.1')
    monkeypatch.setitem(brokerless_profile.options, 'collab.port', 9137)
    monkeypatch.setitem(brokerless_profile.options, 'collab.policy', {'extras_mode': 'sync', 'groups_mode': 'grow'})
    monkeypatch.setitem(
        brokerless_profile.options,
        'collab.peers',
        {
            'uuid-of-alice': peer_entry('http://one:9137', 'alice'),
            'uuid-of-bob': peer_entry('http://two:9137', 'bob'),
            'uuid-of-carol': peer_entry('http://x:9137', 'carol', seen=False),
            # A member that has not rekeyed since the last rotation is left out of the section entirely.
            'uuid-of-dave': peer_entry('http://y:9137', 'dave', active=False),
        },
    )

    def info(self):
        if 'one' not in self._base_url:
            raise CollabRequestError('offline')

        return PeerInfo(
            version=__version__,
            backend='core.sqlite_dos',
            storage_schema=brokerless_profile.storage_cls.version_head(),
            archive_schema=get_format().latest_version,
            pending_count=0,
            accept_push=True,
            extras_mode='local',
            groups_mode='local',
        )

    event = CollabEvent(time=datetime(2026, 8, 1, 12, 0, 0), direction='pull', peer='uuid-of-alice', uuids=[], size=0)

    monkeypatch.setattr(CollabClient, 'info', info)
    monkeypatch.setattr(
        CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'), events=[event]))
    )

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    alice = next(line for line in result.output_lines if 'peer alice' in line)
    bob = next(line for line in result.output_lines if 'peer bob' in line)
    carol = next(line for line in result.output_lines if 'peer carol' in line)

    assert 'online' in alice
    assert 'offline' in bob
    assert 'has never answered' in carol
    assert '1/3 peer(s) reachable' in result.output
    assert 'dave' not in result.output, 'a dormant member leaves no trace: neither a line nor a count'
    assert 'last sync 2026-08-01T12:00:00' in result.output

    assert 'join code' not in result.output, 'obtaining a code is an act of its own; `init` and the docs say so'
    assert not decodable_codes(result.output), (
        'the code embeds the token of the collab, and this output is what users paste into bug reports'
    )

    policy = next(line for line in result.output_lines if 'collab policy' in line)

    assert 'extras `sync`, groups `grow`' in policy, 'the policy is shown here because `verdi config` does not'
    assert 'fixed at creation' in policy


@pytest.mark.parametrize('own_event, expected', ((True, 'last sync 2026-08-01T12:00:00'), (False, 'no syncs yet')))
def test_status_collab_last_sync_ignores_what_peers_drove(
    run_cli_command, brokerless_profile, monkeypatch, own_event, expected
):
    """Test that a peer pulling from this profile does not pass for this profile having synced.

    The line is read to find out whether one is behind, and a `served` row answers a different question: it says a
    peer came and took, which says nothing about what this profile has taken since.
    """
    from datetime import datetime
    from pathlib import Path

    from aiida.tools.collab.state import CollabEvent, CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(brokerless_profile.options, 'collab.token', 'the-token')

    events = [
        CollabEvent(time=datetime(2026, 8, 5, 12, 0, 0), direction='served', peer='uuid-of-alice', uuids=[], size=0)
    ]

    if own_event:
        events.insert(
            0,
            CollabEvent(time=datetime(2026, 8, 1, 12, 0, 0), direction='pull', peer='uuid-of-alice', uuids=[], size=0),
        )

    monkeypatch.setattr(
        CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'), events=events))
    )

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    assert expected in result.output
    assert '2026-08-05' not in result.output


def test_status_collab_warns_when_offline(run_cli_command, brokerless_profile, monkeypatch):
    """Test that a profile taken out of service says so, and names the command that puts it back.

    The peer probes are outbound and prove nothing about being reachable oneself, so without this line an
    endpoint that is not serving looks exactly like one that is: the peers simply see a member that is down.
    """
    from pathlib import Path

    from aiida.tools.collab.state import CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(brokerless_profile.options, 'collab.online', False)
    monkeypatch.setattr(CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'))))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    offline = next(line for line in result.output_lines if 'collab offline' in line)

    assert 'peers cannot reach this profile' in offline
    assert 'verdi collab online' in offline


def test_status_collab_says_nothing_when_online(run_cli_command, brokerless_profile, monkeypatch):
    """Test that serving is the normal state and gets no line of its own: the warning is about the exception."""
    from pathlib import Path

    from aiida.tools.collab.state import CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setattr(CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'))))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    assert 'collab offline' not in result.output


def test_status_collab_reports_a_signalled_rotation(run_cli_command, brokerless_profile, monkeypatch):
    """Test that a peer's rotation signal surfaces as the one thing it may do: tell the user to rekey.

    It cannot do more. The signal is authenticated by the token being retired, which an excluded member still
    holds, so anything automatic would hand that member a way to paralyse the collab.
    """
    from pathlib import Path

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import CollabRequestError
    from aiida.tools.collab.state import CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(
        brokerless_profile.options,
        'collab.peers',
        {'uuid-of-alice': peer_entry('http://one:9137', 'alice', signalled=True)},
    )
    monkeypatch.setattr(CollabClient, 'info', lambda self: (_ for _ in ()).throw(CollabRequestError('offline')))
    monkeypatch.setattr(CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'))))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    rotation = next(line for line in result.output_lines if 'collab rotation' in line)

    assert 'signalled by alice' in rotation
    assert 'verdi collab rekey' in rotation


def test_status_collab_reports_a_peer_refusing_the_key(run_cli_command, brokerless_profile, monkeypatch):
    """Test that a peer which answered 401 is reported as refusing the key, not as absent.

    After a rotation that is the steady state of every member that has not rekeyed, and of every member whose
    daemon was down when the advisory signal went out this is the only thing that tells them to.
    """
    from http import HTTPStatus
    from pathlib import Path

    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import UNAUTHORIZED_DETAIL, CollabRequestError
    from aiida.tools.collab.state import CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(
        brokerless_profile.options, 'collab.peers', {'uuid-of-alice': peer_entry('http://one:9137', 'alice')}
    )

    def refused(self):
        raise CollabRequestError(UNAUTHORIZED_DETAIL, status=HTTPStatus.UNAUTHORIZED)

    monkeypatch.setattr(CollabClient, 'info', refused)
    monkeypatch.setattr(CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'))))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    alice = next(line for line in result.output_lines if 'peer alice' in line)

    assert 'refuses the current key' in alice
    assert 'verdi collab rekey' in alice
    assert 'offline' not in alice


def test_status_collab_probe_timeout(run_cli_command, brokerless_profile, monkeypatch):
    """Test that unreachable peers are probed concurrently, each bounded by the probe timeout.

    The peers are sockets that accept connections but never answer, so every probe has to run into the timeout;
    the wall-time bound fails if the probes serialize or the timeout stops being passed to the client.
    """
    import socket
    import time

    sockets, peers = [], {}

    for index in range(6):
        sock = socket.socket()
        sock.bind(('127.0.0.1', 0))
        sock.listen(1)
        sockets.append(sock)
        peers[f'uuid-of-peer-{index}'] = peer_entry(f'http://127.0.0.1:{sock.getsockname()[1]}', f'peer-{index}')

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(brokerless_profile.options, 'collab.peers', peers)
    monkeypatch.setattr(cmd_status, 'COLLAB_PROBE_TIMEOUT', 0.5)

    try:
        start = time.monotonic()
        result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
        elapsed = time.monotonic() - start

        # Matched at the end of the line, because the `collab offline` warning contains `peer` and `offline` too.
        assert sum(line.strip().endswith('offline') for line in result.output_lines) == 6
        assert '0/6 peer(s) reachable' in result.output
        # Six serialized probes would take at least 3 s; concurrency bounds the whole command well below that.
        assert elapsed < 2.5, f'probes did not run concurrently or ignored the timeout: {elapsed:.1f}s'
    finally:
        for sock in sockets:
            sock.close()


def test_status_collab_skew_is_archive_only(run_cli_command, brokerless_profile, monkeypatch):
    """Test that a peer is flagged as skewed on its archive format alone, since that is what a delta travels as.

    The storage schema of either side is its own business — that is what makes a mixed-backend collab work.
    """
    from pathlib import Path

    from aiida import __version__
    from aiida.tools.archive.abstract import get_format
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.protocol import PeerInfo
    from aiida.tools.collab.state import CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setitem(
        brokerless_profile.options,
        'collab.peers',
        {
            'uuid-of-storage': peer_entry('http://storage:9137', 'storage'),
            'uuid-of-archive': peer_entry('http://archive:9137', 'archive'),
        },
    )

    def info(self):
        newer = 'archive' in self._base_url

        return PeerInfo(
            version=__version__,
            backend='core.psql_dos',
            storage_schema='main_0099',
            archive_schema='main_0099' if newer else get_format().latest_version,
            pending_count=0,
            accept_push=True,
            extras_mode='local',
            groups_mode='local',
        )

    monkeypatch.setattr(CollabClient, 'info', info)
    monkeypatch.setattr(CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'))))

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    storage_line = next(line for line in result.output_lines if 'peer storage' in line)

    assert storage_line.endswith(f'online (aiida-core {__version__})'), 'a newer storage schema is no obstacle'
    assert 'newer archive format' in next(line for line in result.output_lines if 'peer archive' in line)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_status_collab_reports_withheld_seeds(run_cli_command, brokerless_profile, monkeypatch):
    """Test that sealed processes no delta can carry are reported, and that nothing is said when there are none.

    A workchain that excepted over a child the daemon never finished stops travelling for good, and this is the
    only place that says so: to its peers it looks like provenance that was simply never produced.
    """
    from pathlib import Path

    from aiida import orm
    from aiida.common.links import LinkType
    from aiida.tools.collab.state import CollabState

    monkeypatch.setitem(brokerless_profile.options, 'collab.enabled', True)
    monkeypatch.setattr(CollabState, 'load', classmethod(lambda cls, profile: cls(filepath=Path('unused'))))

    # A profile whose sealed processes all travel, so that the silent half cannot be passed by a report that
    # simply counts sealed processes.
    orm.CalcJobNode().store().seal()
    quiet = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    assert 'collab held' not in quiet.output

    excepted = orm.WorkChainNode().store()
    running = orm.CalcJobNode()
    running.base.links.add_incoming(excepted, link_type=LinkType.CALL_CALC, link_label='child')
    running.store()
    excepted.seal()

    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)
    held = next(line for line in result.output_lines if 'collab held' in line)

    assert '1 sealed process(es)' in held
    assert 'has not sealed' in held
    assert 'oldest' in held


def test_status_no_collab(run_cli_command, brokerless_profile):
    """Test that no collab row is printed when the profile is not part of a collab."""
    result = run_cli_command(cmd_status.verdi_status, use_subprocess=False)

    assert 'collab:' not in result.output
