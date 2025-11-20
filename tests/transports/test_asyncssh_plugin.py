import os
import stat

import pytest

from aiida.transports.plugins.ssh_async import AsyncSshTransport


@pytest.mark.asyncio
async def test_locking_problem(tmp_path_factory):
    """Regression test for issue https://github.com/aiidateam/aiida-core/issues/7106"""

    local_dir = tmp_path_factory.mktemp('local')

    # Create a file and remove its read permissions from ourselves,
    # so that we cannot upload it through the transport
    unreadable_file = local_dir / 'unreadable'
    with open(unreadable_file, 'w') as f:
        f.write('test file without read permissions\n')
    # Grant write permissions (so we can remove the file after the test),
    # but not read permissions. Corresponds to `chmod 220`
    os.chmod(unreadable_file, stat.S_IWGRP | stat.S_IWUSR)

    transport_params = {
        'machine': 'localhost',
        'backend': 'asyncssh',
        'max_io_allowed': 1,
    }
    async_transport = AsyncSshTransport(**transport_params)

    assert async_transport.max_io_allowed == 1

    with async_transport as transport:
        with pytest.raises(OSError, match='Error while downloading file'):
            await transport.getfile_async('non_existing', local_dir)

        with pytest.raises(OSError, match='Error while uploading file'):
            await transport.puttree_async(local_dir, 'target_dir')

        with pytest.raises(OSError, match='Error while downloading file'):
            await transport.getfile_async('non_existing', local_dir)
