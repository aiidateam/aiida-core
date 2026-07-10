import asyncio
import os
import stat
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import asyncssh
import pytest

from aiida.transports.plugins.async_backend import (
    _AcceptUnknownHostKey,
    _AsyncSSH,
    _OpenSSH,
    get_openssh_version,
)
from aiida.transports.plugins.async_backend import (
    build_asyncssh_connect_kwargs as _build_asyncssh_connect_kwargs,
)
from aiida.transports.plugins.ssh_async import _LEGACY_OPTION_NAMES, AsyncSshTransport


class TestAuthenticationScript:
    """Tests for authentication script (2FA) functionality."""

    @pytest.fixture
    def make_script(self, tmp_path):
        """Factory to create a script with given exit code."""

        def _make(exit_code=0):
            script = tmp_path / f'script_{exit_code}.sh'
            script.write_text(f'#!/bin/bash\necho "STDOUT"\necho "STDERR" >&2\nexit {exit_code}\n')
            os.chmod(script, 0o755)
            return script

        return _make

    def _make_transport(self, script_path=None, use_old_param=False):
        """Helper to create transport with mocked backend."""
        kwargs = {'machine': 'localhost', 'backend': 'asyncssh'}
        if script_path:
            key = 'script_before' if use_old_param else 'authentication_script'
            kwargs[key] = str(script_path)

        transport = AsyncSshTransport(**kwargs)
        transport.async_backend = MagicMock()
        transport.async_backend.open = AsyncMock()
        transport.async_backend.logger = MagicMock()
        return transport

    @pytest.mark.asyncio
    async def test_script_success(self, make_script):
        """Script returning 0 succeeds and logs info."""
        transport = self._make_transport(make_script(exit_code=0))

        await transport.open_async()

        transport.async_backend.logger.info.assert_called()
        assert 'executed successfully' in transport.async_backend.logger.info.call_args[0][0]

    @pytest.mark.asyncio
    async def test_script_failure_raises_and_logs(self, make_script):
        """Script returning non-zero raises OSError and logs stdout/stderr."""
        transport = self._make_transport(make_script(exit_code=1))

        with pytest.raises(OSError, match='failed with exit code 1'):
            await transport.open_async()

        error_msg = transport.async_backend.logger.error.call_args[0][0]
        assert 'stdout: STDOUT' in error_msg
        assert 'stderr: STDERR' in error_msg

    @pytest.mark.asyncio
    async def test_backward_compatibility_script_before(self, make_script):
        """Old 'script_before' parameter still works."""
        script = make_script(exit_code=0)
        transport = self._make_transport(script, use_old_param=True)
        assert transport.auth_script == str(script)

    @pytest.mark.asyncio
    async def test_no_script_configured(self):
        """Transport works without authentication script."""
        transport = self._make_transport()
        await transport.open_async()

        assert transport.auth_script == 'None'


class TestSemaphoreBehavior:
    """Tests for AsyncSshTransport semaphore/concurrency control."""

    @pytest.mark.asyncio
    async def test_semaphore_released_after_errors(self, tmp_path_factory):
        """Verify semaphore is properly released even when operations fail.

        This ensures that failed I/O operations don't cause semaphore leaks,
        which would eventually deadlock the transport.
        """
        local_dir = tmp_path_factory.mktemp('local')

        # Create a file without read permissions to trigger upload errors
        unreadable_file = local_dir / 'unreadable'
        unreadable_file.write_text('test file without read permissions\n')
        os.chmod(unreadable_file, stat.S_IWGRP | stat.S_IWUSR)  # chmod 220

        transport_params = {
            'machine': 'localhost',
            'backend': 'asyncssh',
            'max_io_allowed': 1,
        }
        async_transport = AsyncSshTransport(**transport_params)

        async with async_transport as transport:
            # Each operation should fail but release the semaphore
            with pytest.raises(OSError, match='Error while downloading file'):
                await transport.getfile_async('non_existing', local_dir)

            with pytest.raises(OSError, match='Error while uploading file'):
                await transport.puttree_async(local_dir, 'target_dir')

            # This would deadlock if semaphore wasn't released after previous errors
            with pytest.raises(OSError, match='Error while downloading file'):
                await transport.getfile_async('non_existing', local_dir)

        assert async_transport._semaphore._value == 1, 'Semaphore should be fully released'

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrent_operations(self):
        """Verify exec_command_wait_async respects max_io_allowed.

        This is particularly critical, because exec_command_wait_async opens subchannels on the SSH
        connection, and too many simultaneous subchannels can overwhelm the server.
        """
        max_allowed = 2
        transport = AsyncSshTransport(
            machine='localhost',
            backend='asyncssh',
            max_io_allowed=max_allowed,
        )

        concurrent_count = 0
        max_concurrent = 0

        async def mock_run(command, stdin=None, timeout=None):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)  # Simulate I/O latency
            concurrent_count -= 1
            return (0, 'output', '')

        mock_backend = MagicMock()
        mock_backend.run = mock_run
        transport.async_backend = mock_backend

        # Launch more tasks than the semaphore allows
        tasks = [transport.exec_command_wait_async(f'cmd{i}') for i in range(5)]
        await asyncio.gather(*tasks)

        assert (
            max_concurrent <= max_allowed
        ), f'Semaphore should limit to {max_allowed} concurrent ops, got {max_concurrent}'
        assert max_concurrent == max_allowed, f'Expected {max_allowed} concurrent ops to verify semaphore is being used'


def test_get_openssh_version():
    """Test that get_openssh_version() parses version correctly."""
    mock_result = MagicMock()
    mock_result.stdout = ''

    mock_result.stderr = 'OpenSSH_9.0p1, OpenSSL 3.0.2'
    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert get_openssh_version() == 9

    mock_result.stderr = 'OpenSSH_8.9p1, OpenSSL 3.0.2'
    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert get_openssh_version() == 8

    mock_result.stderr = ''
    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert get_openssh_version() is None


class _TestOpenSSH(_OpenSSH):
    """Minimal OpenSSH subclass for testing escape methods."""

    def __init__(self):
        self.machine = 'localhost'
        self.bash_command = 'bash -c '


class TestSshCommandGenerator:
    """Tests for ssh_command_generator escaping."""

    def test_escapes_shell_chars_and_paths(self):
        """Test $, `, " escaped and paths safely quoted."""

        openssh = _TestOpenSSH()

        """Test command structure and that $, `, " are escaped for the outer double-quote wrapper."""
        result = openssh.ssh_command_generator('echo $HOME `cmd` "test"')
        assert result[:2] == ['ssh', 'localhost']
        assert result[2].startswith('bash -c "') and result[2].endswith('"')
        assert r'\$HOME' in result[2]
        assert r'\`cmd\`' in result[2]
        assert r'\"test\"' in result[2]

        """Test $!, $?, $$ are escaped so they're interpreted by inner bash -c shell."""
        result = openssh.ssh_command_generator('script.sh & echo $!; echo $?; echo $$')
        assert r'\$!' in result[2]
        assert r'\$?' in result[2]
        assert r'\$\$' in result[2]

        """Test paths with special chars are safely quoted via escape_for_bash."""
        result = openssh.ssh_command_generator('cp {} {}', paths=['/path;rm -rf /', '/dst'])
        # Semicolon should be safely quoted, not interpreted as command separator
        assert "'/path;rm -rf /'" in result[2]
        assert "'/dst'" in result[2]


def test_escape_for_glob_preserves_wildcards_escapes_dangerous_chars():
    """Test wildcards (*, ?, []) preserved while dangerous chars escaped."""
    backend = _TestOpenSSH()
    # Wildcards preserved, dangerous chars escaped
    assert backend._escape_for_glob('/home/$USER/my files/[0-9]*.log') == '/home/\\$USER/my\\ files/[0-9]*.log'
    # Command injection attempt escaped
    assert backend._escape_for_glob('/path;rm -rf /*') == '/path\\;rm\\ -rf\\ /*'


def test_escape_for_rcp():
    """Test RCP mode escapes shell metacharacters but preserves globs."""
    backend = _TestOpenSSH()
    assert backend._escape_for_rcp('/path/with spaces/$VAR;cmd') == '/path/with\\ spaces/\\$VAR\\;cmd'
    # Glob characters pass through so the remote shell can expand them.
    assert backend._escape_for_rcp('/dir/*.[ch]') == '/dir/*.[ch]'


def test_escape_for_scp_version_aware():
    """Test _escape_for_scp behavior differs by OpenSSH version."""
    backend = _TestOpenSSH()
    path = '/path/with spaces'

    # SFTP mode (OpenSSH 9+): no escaping needed
    backend.is_openssh_9_or_higher = True
    assert backend._escape_for_scp(path) == path

    # RCP mode (OpenSSH < 9): escaping required
    backend.is_openssh_9_or_higher = False
    assert backend._escape_for_scp(path) == '/path/with\\ spaces'


def test_scp_with_special_chars(tmp_path):
    """Test scp in both SFTP and RCP modes with special characters."""
    backend = _TestOpenSSH()

    remote_dir = tmp_path / 'remote'
    local_dir = tmp_path / 'local'
    remote_dir.mkdir()
    local_dir.mkdir()

    special_files = ['file with spaces.txt', "file'quote.txt", 'file$dollar.txt']
    for f in special_files:
        (remote_dir / f).write_text(f'content of {f}')

    for filename in special_files:
        source = remote_dir / filename

        # SFTP mode (default on OpenSSH 9+)
        dest_sftp = local_dir / f'sftp_{filename}'
        result = subprocess.run(['scp', f'localhost:{source}', str(dest_sftp)], capture_output=True, check=False)
        assert result.returncode == 0 and dest_sftp.read_text() == f'content of {filename}'

        # RCP mode (forced with -O)
        dest_rcp = local_dir / f'rcp_{filename}'
        escaped = backend._escape_for_rcp(str(source))
        result = subprocess.run(['scp', '-O', f'localhost:{escaped}', str(dest_rcp)], capture_output=True, check=False)
        assert result.returncode == 0 and dest_rcp.read_text() == f'content of {filename}'


def build_asyncssh_connect_kwargs(host, params):
    """Call the translator with a dummy logger."""
    return _build_asyncssh_connect_kwargs(host, params, MagicMock())


class TestLegacyConnectionOptions:
    """Legacy ``core.ssh`` connection options, honored only for a migrated computer."""

    def test_asyncssh_translation(self):
        """Each legacy parameter maps to the correct ``asyncssh.connect()`` keyword."""
        params = {
            'username': 'alice',
            'port': 2222,
            'timeout': 30,
            'key_filename': '/home/alice/.ssh/id_ed25519',
            'proxy_jump': 'gw@bastion',
            'key_policy': 'AutoAddPolicy',
            'allow_agent': False,
            'compress': False,
            'gss_host': 'kdc.example',
            'gss_auth': False,
            'gss_kex': True,
            'gss_deleg_creds': False,
        }
        kwargs = build_asyncssh_connect_kwargs('target', params)
        assert kwargs.pop('client_factory').func is _AcceptUnknownHostKey
        assert kwargs == {
            'config': None,
            'username': 'alice',
            'port': 2222,
            'connect_timeout': 30,
            'client_keys': ['/home/alice/.ssh/id_ed25519'],
            'tunnel': 'gw@bastion',
            'agent_path': None,
            'compression_algs': None,
            'gss_host': 'kdc.example',
            'gss_auth': False,
            'gss_kex': True,
            'gss_delegate_creds': False,
        }

    def test_native_computer_returns_no_kwargs(self):
        """``params=None`` (native computer) yields no overrides: asyncssh reads ``~/.ssh/config``."""
        assert build_asyncssh_connect_kwargs('host', None) == {}

    def test_migrated_computer_ignores_ssh_config(self):
        """A migrated computer sets ``config=None`` so ``~/.ssh/config`` is never read."""
        assert build_asyncssh_connect_kwargs('host', {'username': 'alice'})['config'] is None

    def test_key_policy(self):
        """A permissive policy installs the client that accepts an unknown host but not a changed key."""
        for policy, warn in (('AutoAddPolicy', False), ('WarningPolicy', True)):
            kwargs = build_asyncssh_connect_kwargs('h', {'key_policy': policy})
            client_factory = kwargs.pop('client_factory')
            assert kwargs == {'config': None}
            assert client_factory.func is _AcceptUnknownHostKey
            assert client_factory.keywords['warn'] is warn
            # Host-key validation stays on: `known_hosts` is not disabled.
            assert 'known_hosts' not in kwargs

        # A strict policy keeps the asyncssh defaults, which already reject an unknown host.
        assert build_asyncssh_connect_kwargs('h', {'key_policy': 'RejectPolicy'}) == {'config': None}

    def test_look_for_keys(self):
        """``look_for_keys`` controls automatic discovery of ``~/.ssh/id_*`` keys."""
        # True is asyncssh's own default: nothing to pass.
        assert 'client_keys' not in build_asyncssh_connect_kwargs('h', {'look_for_keys': True})
        # An explicit key wins: only that key is offered, agent still used.
        assert build_asyncssh_connect_kwargs('h', {'look_for_keys': False, 'key_filename': '/k'})['client_keys'] == [
            '/k'
        ]
        # No discovery and no agent -> public-key auth disabled entirely.
        assert build_asyncssh_connect_kwargs('h', {'look_for_keys': False, 'allow_agent': False})['client_keys'] is None
        # No discovery but agent allowed: not expressible without killing the agent, so keep default.
        assert 'client_keys' not in build_asyncssh_connect_kwargs('h', {'look_for_keys': False, 'allow_agent': True})

    def test_allow_agent(self):
        """``allow_agent=False`` disables the ssh-agent but leaves key discovery alone."""
        kwargs = build_asyncssh_connect_kwargs('h', {'allow_agent': False})
        assert kwargs['agent_path'] is None
        assert 'client_keys' not in kwargs
        assert 'agent_path' not in build_asyncssh_connect_kwargs('h', {'allow_agent': True})

    def test_load_system_host_keys(self):
        """With no host keys loaded, a strict policy rejects every host and a permissive one accepts any."""
        assert 'known_hosts' not in build_asyncssh_connect_kwargs('h', {'load_system_host_keys': True})
        assert build_asyncssh_connect_kwargs('h', {'load_system_host_keys': False})['known_hosts'] == ([], [], [])
        # Nothing is known, so there is no key that could have changed: accept every host.
        kwargs = build_asyncssh_connect_kwargs('h', {'load_system_host_keys': False, 'key_policy': 'AutoAddPolicy'})
        assert kwargs['known_hosts'] is None
        assert 'client_factory' not in kwargs

    def test_compress(self):
        """``compress`` enables or disables the asyncssh compression algorithms."""
        assert build_asyncssh_connect_kwargs('h', {'compress': True}) == {
            'config': None,
            'compression_algs': ('zlib@openssh.com', 'zlib', 'none'),
        }
        assert build_asyncssh_connect_kwargs('h', {'compress': False}) == {'config': None, 'compression_algs': None}

    def test_proxy_command_token_expansion(self):
        """``%h``/``%p``/``%r``/``%%`` are expanded in a proxy command using the target host."""
        params = {'proxy_command': 'ssh -W %h:%p %r@gw # 100%%', 'port': 2222, 'username': 'alice'}
        assert (
            build_asyncssh_connect_kwargs('target.host', params)['proxy_command']
            == 'ssh -W target.host:2222 alice@gw # 100%'
        )
        # Without a port, ``%p`` falls back to the default SSH port.
        assert (
            build_asyncssh_connect_kwargs('target.host', {'proxy_command': 'nc %h %p'})['proxy_command']
            == 'nc target.host 22'
        )

    def test_legacy_options_are_hidden_on_the_cli(self):
        """The legacy options are valid auth params but hidden on ``verdi computer configure``."""
        from aiida.transports.cli import create_configure_cmd

        valid = set(AsyncSshTransport.get_valid_auth_params())
        assert valid.issuperset(_LEGACY_OPTION_NAMES)

        params = {p.name: p for p in create_configure_cmd('core.ssh_async').params}
        assert all(params[name].hidden for name in _LEGACY_OPTION_NAMES)
        assert params['host'].hidden is False

    def test_init_collects_legacy_params(self):
        """``__init__`` collects every legacy parameter present, even empty ones (a migration marker)."""
        transport = AsyncSshTransport(
            machine='remote.host', username='alice', port='2222', key_filename='', proxy_jump='gw@bastion'
        )
        assert transport._legacy_params == {
            'username': 'alice',
            'port': '2222',
            'key_filename': '',
            'proxy_jump': 'gw@bastion',
        }
        assert transport.machine == 'remote.host'

    def test_native_computer_has_no_legacy_params(self):
        """A computer with none of the legacy parameters is native: ``_legacy_params`` is ``None``."""
        assert AsyncSshTransport(machine='remote.host').async_backend.connection_params is None

    def test_host_alias_takes_precedence_over_machine(self):
        """When set, the ``host`` SSH-config alias is used instead of the machine hostname."""
        assert AsyncSshTransport(machine='real.host', host='myalias').machine == 'myalias'
        # An empty host falls back to the machine hostname.
        assert AsyncSshTransport(machine='real.host', host='').machine == 'real.host'

    def test_proxy_jump_and_command_are_mutually_exclusive(self):
        with pytest.raises(ValueError, match='mutually exclusive'):
            AsyncSshTransport(machine='h', proxy_jump='a', proxy_command='b')

    def test_migrated_computer_forces_the_asyncssh_backend(self):
        """A migrated computer always uses asyncssh: the openssh backend cannot honor its params."""
        transport = AsyncSshTransport(machine='remote.host', backend='openssh', username='alice')
        assert isinstance(transport.async_backend, _AsyncSSH)
        assert transport.async_backend.connection_params == {'username': 'alice'}

    def test_native_computer_keeps_the_requested_backend(self):
        """Without legacy parameters the ``openssh`` backend is honored as before."""
        assert isinstance(AsyncSshTransport(machine='remote.host', backend='openssh').async_backend, _OpenSSH)

    def test_asyncssh_backend_open_passes_kwargs(self):
        """The asyncssh backend forwards the translated options to ``asyncssh.connect()``."""
        backend = _AsyncSSH('remote.host', MagicMock(), 'bash ', {'username': 'alice', 'port': 2222})
        with patch('aiida.transports.plugins.async_backend.asyncssh') as mock_asyncssh:
            mock_conn = MagicMock()
            mock_conn.start_sftp_client = AsyncMock()
            mock_asyncssh.connect = AsyncMock(return_value=mock_conn)
            asyncio.run(backend.open())
        mock_asyncssh.connect.assert_awaited_once_with('remote.host', config=None, username='alice', port=2222)

    def test_asyncssh_backend_open_native_reads_ssh_config(self):
        """A native computer is opened exactly as before: host only, no overrides."""
        backend = _AsyncSSH('remote.host', MagicMock(), 'bash ', None)
        with patch('aiida.transports.plugins.async_backend.asyncssh') as mock_asyncssh:
            mock_conn = MagicMock()
            mock_conn.start_sftp_client = AsyncMock()
            mock_asyncssh.connect = AsyncMock(return_value=mock_conn)
            asyncio.run(backend.open())
        mock_asyncssh.connect.assert_awaited_once_with('remote.host')


class TestAcceptUnknownHostKey:
    """``_AcceptUnknownHostKey`` reproduces paramiko's permissive host-key policies.

    Both accept a host that is absent from ``known_hosts``; neither accepts a key that changed.
    Exercised against a real in-process ``asyncssh`` server.
    """

    @staticmethod
    def _connect(server_key, known_hosts_content, tmp_path, monkeypatch):
        """Connect to a throwaway server and return whether its host key was accepted."""
        monkeypatch.setenv('HOME', str(tmp_path))
        ssh_dir = tmp_path / '.ssh'
        ssh_dir.mkdir(exist_ok=True)
        (ssh_dir / 'known_hosts').write_text(known_hosts_content)

        async def run():
            server = await asyncssh.listen('127.0.0.1', 0, server_host_keys=[server_key])
            port = server.sockets[0].getsockname()[1]
            kwargs = build_asyncssh_connect_kwargs('127.0.0.1', {'key_policy': 'AutoAddPolicy'})
            kwargs.pop('config')
            try:
                connection = await asyncssh.connect('127.0.0.1', port=port, username='u', password='p', **kwargs)
                connection.close()
                return True, port
            except asyncssh.PermissionDenied:
                # The host key was accepted; only the (absent) user authentication failed.
                return True, port
            except asyncssh.HostKeyNotVerifiable:
                return False, port
            finally:
                server.close()

        return asyncio.run(run())

    def test_unknown_host_is_accepted(self, tmp_path, monkeypatch):
        key = asyncssh.generate_private_key('ssh-ed25519')
        accepted, _ = self._connect(key, '', tmp_path, monkeypatch)
        assert accepted

    def test_matching_host_key_is_accepted(self, tmp_path, monkeypatch):
        key = asyncssh.generate_private_key('ssh-ed25519')
        # The port is unknown before the server starts, so trust the key on every port of the host.
        entry = '127.0.0.1 ' + key.export_public_key().decode()
        accepted, _ = self._connect(key, entry, tmp_path, monkeypatch)
        assert accepted

    def test_changed_host_key_is_rejected(self, tmp_path, monkeypatch):
        """The security property that ``known_hosts=None`` would have silently dropped."""
        key = asyncssh.generate_private_key('ssh-ed25519')
        stale = asyncssh.generate_private_key('ssh-ed25519').export_public_key().decode()
        accepted, _ = self._connect(key, '127.0.0.1 ' + stale, tmp_path, monkeypatch)
        assert not accepted
