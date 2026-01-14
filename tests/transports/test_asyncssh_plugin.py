import asyncio
import os
import stat
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from aiida.transports.plugins.async_backend import _OpenSSH, get_openssh_version, is_openssh_9_or_higher
from aiida.transports.plugins.ssh_async import AsyncSshTransport


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

        with async_transport as transport:
            # Each operation should fail but release the semaphore
            with pytest.raises(OSError, match='Error while downloading file'):
                await transport.getfile_async('non_existing', local_dir)

            with pytest.raises(OSError, match='Error while uploading file'):
                await transport.puttree_async(local_dir, 'target_dir')

            # This would deadlock if semaphore wasn't released after previous errors
            with pytest.raises(OSError, match='Error while downloading file'):
                await transport.getfile_async('non_existing', local_dir)

        assert transport._semaphore._value == 1, 'Semaphore should be fully released'

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
    """Test that get_openssh_version() parses version correctly and caches results."""
    # Clear the cache before testing
    get_openssh_version.cache_clear()

    mock_result = MagicMock()
    mock_result.stderr = 'OpenSSH_9.0p1, OpenSSL 3.0.2'
    mock_result.stdout = ''

    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert get_openssh_version() == 9

    # Clear cache to test other version
    get_openssh_version.cache_clear()

    mock_result.stderr = 'OpenSSH_8.9p1, OpenSSL 3.0.2'

    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert get_openssh_version() == 8

    # Clear cache after test
    get_openssh_version.cache_clear()


def test_is_openssh_9_or_higher():
    """Test that is_openssh_9_or_higher() correctly identifies version thresholds."""
    # Clear the cache before testing
    get_openssh_version.cache_clear()

    mock_result = MagicMock()
    mock_result.stderr = 'OpenSSH_9.0p1, OpenSSL 3.0.2'
    mock_result.stdout = ''

    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert is_openssh_9_or_higher() is True

    # Clear cache to test older version
    get_openssh_version.cache_clear()

    mock_result.stderr = 'OpenSSH_8.9p1, OpenSSL 3.0.2'

    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result):
        assert is_openssh_9_or_higher() is False

    # Clear cache after test
    get_openssh_version.cache_clear()


def test_openssh_version_caching():
    """Test that get_openssh_version() caches its result."""
    get_openssh_version.cache_clear()

    mock_result = MagicMock()
    mock_result.stderr = 'OpenSSH_9.0p1, OpenSSL 3.0.2'
    mock_result.stdout = ''

    with patch('aiida.transports.plugins.async_backend.subprocess.run', return_value=mock_result) as mock_run:
        # First call should invoke subprocess.run
        version1 = get_openssh_version()
        assert version1 == 9
        assert mock_run.call_count == 1

        # Second call should use cached value
        version2 = get_openssh_version()
        assert version2 == 9
        assert mock_run.call_count == 1  # Still 1, not 2

    get_openssh_version.cache_clear()


class TestSshCommandGenerator:
    """Tests for ssh_command_generator escaping."""

    def test_escapes_shell_chars_and_paths(self):
        """Test $, `, " escaped and paths safely quoted."""

        class TestOpenSSH(_OpenSSH):
            def __init__(self):
                self.machine = 'localhost'
                self.bash_command = 'bash -c '

        openssh = TestOpenSSH()

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


class TestEscapeForGlob:
    """Tests for glob path escaping that preserves wildcards while escaping dangerous chars."""

    @pytest.fixture
    def openssh_backend(self):
        class TestOpenSSH(_OpenSSH):
            def __init__(self):
                self.machine = 'localhost'

        return TestOpenSSH()

    def test_preserves_wildcards_escapes_dangerous_chars(self, openssh_backend):
        """Test wildcards (*, ?, []) preserved while dangerous chars escaped."""
        # Wildcards preserved, dangerous chars escaped
        assert (
            openssh_backend._escape_for_glob('/home/$USER/my files/[0-9]*.log') == '/home/\\$USER/my\\ files/[0-9]*.log'
        )
        # Command injection attempt escaped
        assert openssh_backend._escape_for_glob('/path;rm -rf /*') == '/path\\;rm\\ -rf\\ /*'


class TestScpEscaping:
    """Tests for scp path escaping for OpenSSH 9+ (SFTP) vs <9 (RCP)."""

    @pytest.fixture
    def openssh_backend(self):
        class TestOpenSSH(_OpenSSH):
            def __init__(self):
                self.machine = 'localhost'

        return TestOpenSSH()

    def test_escape_for_rcp(self, openssh_backend):
        """Test RCP mode escapes shell metacharacters."""
        assert openssh_backend._escape_for_rcp('/path/with spaces/$VAR;cmd') == '/path/with\\ spaces/\\$VAR\\;cmd'

    def test_escape_for_scp_version_aware(self, openssh_backend):
        """Test _escape_for_scp behavior differs by OpenSSH version."""
        get_openssh_version.cache_clear()
        path = '/path/with spaces'

        with patch('aiida.transports.plugins.async_backend.is_openssh_9_or_higher', return_value=True):
            assert openssh_backend._escape_for_scp(path) == path  # SFTP: no escaping

        with patch('aiida.transports.plugins.async_backend.is_openssh_9_or_higher', return_value=False):
            assert openssh_backend._escape_for_scp(path) == '/path/with\\ spaces'  # RCP: escaped


class TestScpIntegration:
    """Integration tests for scp with special characters in filenames."""

    @pytest.fixture
    def test_files(self, tmp_path):
        remote_dir = tmp_path / 'remote'
        local_dir = tmp_path / 'local'
        remote_dir.mkdir()
        local_dir.mkdir()
        special_files = ['file with spaces.txt', "file'quote.txt", 'file$dollar.txt']
        for f in special_files:
            (remote_dir / f).write_text(f'content of {f}')
        return {'remote': remote_dir, 'local': local_dir, 'files': special_files}

    @pytest.fixture
    def openssh_backend(self):
        class TestOpenSSH(_OpenSSH):
            def __init__(self):
                self.machine = 'localhost'

        return TestOpenSSH()

    def test_scp_with_special_chars(self, test_files, openssh_backend):
        """Test scp in both SFTP and RCP modes with special characters."""
        for filename in test_files['files']:
            source = test_files['remote'] / filename

            # SFTP mode (default on OpenSSH 9+)
            dest_sftp = test_files['local'] / f'sftp_{filename}'
            result = subprocess.run(['scp', f'localhost:{source}', str(dest_sftp)], capture_output=True, check=False)
            assert result.returncode == 0 and dest_sftp.read_text() == f'content of {filename}'

            # RCP mode (forced with -O)
            dest_rcp = test_files['local'] / f'rcp_{filename}'
            escaped = openssh_backend._escape_for_rcp(str(source))
            result = subprocess.run(
                ['scp', '-O', f'localhost:{escaped}', str(dest_rcp)], capture_output=True, check=False
            )
            assert result.returncode == 0 and dest_rcp.read_text() == f'content of {filename}'
