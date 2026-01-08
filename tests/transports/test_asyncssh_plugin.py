import asyncio
import os
import stat
from unittest.mock import MagicMock

import pytest

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
