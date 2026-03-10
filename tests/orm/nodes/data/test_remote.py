###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.remote.base.RemoteData` module."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from aiida.orm import RemoteData


def _du_size(path: Path) -> int:
    """Return the disk usage of ``path`` in bytes using ``du -sk``, matching the implementation."""
    result = subprocess.run(['du', '-sk', str(path)], capture_output=True, text=True, check=True)
    return int(result.stdout.split('\t')[0]) * 1024


@pytest.fixture
def remote_data_factory(tmp_path, aiida_computer_local, aiida_computer_ssh):
    """Factory fixture to create RemoteData instances."""

    def _create_remote_data(mode: str, content: str | bytes = b'some content'):
        if mode == 'local':
            computer = aiida_computer_local(label='localhost')
        elif mode == 'ssh':
            computer = aiida_computer_ssh(label='localhost-ssh')
        else:
            raise ValueError(f'Unknown mode: {mode}')

        node = RemoteData(computer=computer)
        node.set_remote_path(str(tmp_path))
        node.store()
        (tmp_path / 'file.txt').write_bytes(content)
        return node

    return _create_remote_data


@pytest.mark.parametrize('mode', ('local', 'ssh'))
def test_clean(remote_data_factory, mode):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.clean` method."""

    remote_data = remote_data_factory(mode=mode)

    assert not remote_data.is_empty
    assert not remote_data.is_cleaned
    remote_data._clean()
    assert remote_data.is_empty
    assert remote_data.is_cleaned


@pytest.mark.parametrize('mode', ('local', 'ssh'))
@pytest.mark.parametrize(
    'setup, results',
    (
        (('stat', False), ('12.00 B', 'stat')),
        (('stat', True), (12, 'stat')),
    ),
)
def test_get_size_on_disk_params(remote_data_factory, mode, setup, results):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.get_size_on_disk` method."""

    remote_data = remote_data_factory(mode=mode)

    size_on_disk, method = remote_data.get_size_on_disk(method=setup[0], return_bytes=setup[1])
    assert (size_on_disk, method) == results


@pytest.mark.parametrize('mode', ('local', 'ssh'))
@pytest.mark.parametrize('return_bytes', (True, False))
def test_get_size_on_disk_params_du(remote_data_factory, tmp_path, mode, return_bytes):
    """Test ``get_size_on_disk`` with the ``du`` method.

    The expected ``du`` values are computed dynamically because disk block sizes differ across
    filesystems and operating systems (e.g. Linux ext4 vs macOS APFS).
    """
    remote_data = remote_data_factory(mode=mode)

    expected_bytes = _du_size(tmp_path)

    size_on_disk, method = remote_data.get_size_on_disk(method='du', return_bytes=return_bytes)
    assert method == 'du'
    if return_bytes:
        assert size_on_disk == expected_bytes
    else:
        from aiida.common.utils import format_directory_size

        assert size_on_disk == format_directory_size(size_in_bytes=expected_bytes)


@pytest.mark.parametrize('mode', ('local', 'ssh'))
@pytest.mark.parametrize(
    'content, stat_size',
    (
        (b'a', 1),
        (10 * b'a', 10),
        (1000 * b'a', 1000),
        (1000000 * b'a', int(1e6)),
    ),
    ids=['1-byte', '10-bytes', '1000-bytes', '1e6-bytes'],
)
def test_get_size_on_disk_sizes(remote_data_factory, tmp_path, mode, content, stat_size):
    """Test the different implementations to obtain the size of a ``RemoteData`` on disk.

    The expected ``du`` values are computed dynamically because disk block sizes differ across
    filesystems and operating systems (e.g. Linux ext4 vs macOS APFS).
    """
    from aiida.common.utils import format_directory_size

    remote_data = remote_data_factory(mode=mode, content=content)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    expected_du = _du_size(tmp_path)

    with authinfo.get_transport() as transport:
        size_on_disk_du = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
        size_on_disk_stat = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)
        size_on_disk_human, _ = remote_data.get_size_on_disk()

    assert size_on_disk_du == expected_du
    assert size_on_disk_stat == stat_size
    assert size_on_disk_human == format_directory_size(size_in_bytes=expected_du)


@pytest.mark.parametrize(
    'num_char, relpath',
    (
        (1, '.'),
        (100, '.'),
        (int(1e6), '.'),
        (1, 'subdir1'),
        (100, 'subdir1'),
        (int(1e6), 'subdir1'),
    ),
)
def test_get_size_on_disk_nested(aiida_localhost, tmp_path, num_char, relpath):
    """Test ``get_size_on_disk`` for nested directory structures.

    The expected ``du`` values are computed dynamically because disk block sizes differ across
    filesystems and operating systems (e.g. Linux ext4 vs macOS APFS).
    """
    from aiida.common.utils import format_directory_size

    sub_dir1 = tmp_path / 'subdir1'
    sub_dir1.mkdir()

    sub_dir2 = tmp_path / 'subdir1' / 'subdir2'
    sub_dir2.mkdir()

    # Create some files with known sizes
    file1 = sub_dir1 / 'file1.txt'
    file1.write_text('a' * num_char)

    file2 = sub_dir2 / 'file2.bin'
    file2.write_bytes(b'a' * num_char)

    file3 = tmp_path / 'file3.txt'
    file3.write_text('a' * num_char)

    remote_data = RemoteData(computer=aiida_localhost, remote_path=tmp_path)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path()) / relpath

    expected_du = _du_size(full_path)

    with authinfo.get_transport() as transport:
        size_on_disk_du = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
        size_on_disk_stat = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)

        size_on_disk_human, _ = remote_data.get_size_on_disk(relpath=relpath)

    assert size_on_disk_du == expected_du
    assert size_on_disk_stat > 0  # stat values depend on filesystem, just verify positive
    assert size_on_disk_human == format_directory_size(size_in_bytes=expected_du)


@pytest.mark.parametrize('mode', ('local', 'ssh'))
def test_get_size_on_disk_excs(remote_data_factory, mode):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.get_size_on_disk` method."""
    # Extra function to avoid unnecessary parametrization here
    remote_data = remote_data_factory(mode=mode)

    # Path/file non-existent
    with pytest.raises(FileNotFoundError, match='.*does not exist.*'):
        remote_data.get_size_on_disk(relpath=Path('non-existent'))

    # Non-valid method
    with pytest.raises(ValueError, match='.*is not an valid input. Please choose either.*.'):
        remote_data.get_size_on_disk(method='fake-du')


@pytest.mark.parametrize('mode', ('local', 'ssh'))
def test_get_size_on_disk_du(remote_data_factory, tmp_path, mode, monkeypatch):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_du` private method."""
    # No additional parametrization here, as already done in `test_get_size_on_disk_sizes`.

    remote_data = remote_data_factory(mode=mode)

    # Normal call
    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    expected_du = _du_size(tmp_path)

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
    assert size_on_disk == expected_du

    # Monkeypatch transport exec_command_wait command to simulate it not being implemented, e.g., for FirecREST plugin
    def mock_exec_command_wait(command):
        raise NotImplementedError('`exec_command_wait` not implemented for the current transport plugin.')

    monkeypatch.setattr(transport, 'exec_command_wait', mock_exec_command_wait)
    with pytest.raises(NotImplementedError, match='`exec_command_wait` not implemented.*'):
        remote_data._get_size_on_disk_du(full_path, transport)

    # Monkeypatch transport exec_command_wait command to simulate `du` failure
    def mock_exec_command_wait(command):
        return (1, '', 'Error executing `du` command')

    monkeypatch.setattr(transport, 'exec_command_wait', mock_exec_command_wait)
    with pytest.raises(RuntimeError, match='Error executing `du`.*'):
        remote_data._get_size_on_disk_du(full_path, transport)


@pytest.mark.parametrize('mode', ('local', 'ssh'))
def test_get_size_on_disk_stat(remote_data_factory, mode):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_stat` private method."""
    # No additional parametrization here, as already done in `test_get_size_on_disk_sizes`.

    remote_data = remote_data_factory(mode=mode)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)
        assert size_on_disk == 12

        # Raises OSError for non-existent directory
        with pytest.raises(OSError, match='The required remote folder.*'):
            remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path / 'non-existent')
