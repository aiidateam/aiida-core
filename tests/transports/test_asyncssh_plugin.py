import pytest

from aiida.transports.plugins.ssh_async import AsyncSshTransport


@pytest.mark.asyncio
async def test_locking_problem(tmp_path_factory):
    """Regression test for issue https://github.com/aiidateam/aiida-core/issues/7106"""

    local_dir = tmp_path_factory.mktemp('local')

    transport_params = {
        'machine': 'localhost',
        'backend': 'asyncssh',
        'max_io_allowed': 1,
    }
    async_transport = AsyncSshTransport(**transport_params)

    assert async_transport.max_io_allowed == 1

    with async_transport as transport:
        with pytest.raises(OSError):
            await transport.getfile_async('non_existing', local_dir)

        with pytest.raises(OSError):
            await transport.getfile_async('non_existing', local_dir)
