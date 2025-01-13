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

from pathlib import Path

import pytest

from aiida.orm import RemoteData


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
        (('du', False), ('8.00 KB', 'du')),
        (('du', True), (8192, 'du')),
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
@pytest.mark.parametrize(
    'content, sizes',
    (
        (b'a', {'du': 8192, 'stat': 1, 'human': '8.00 KB'}),
        (10 * b'a', {'du': 8192, 'stat': 10, 'human': '8.00 KB'}),
        (1000 * b'a', {'du': 8192, 'stat': 1000, 'human': '8.00 KB'}),
        (1000000 * b'a', {'du': 1007616, 'stat': int(1e6), 'human': '984.00 KB'}),
    ),
    ids=['1-byte', '10-bytes', '1000-bytes', '1e6-bytes'],
)
def test_get_size_on_disk_sizes(remote_data_factory, mode, content, sizes):
    """Test the different implementations to obtain the size of a ``RemoteData`` on disk."""

    remote_data = remote_data_factory(mode=mode, content=content)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk_du = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
        size_on_disk_stat = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)
        size_on_disk_human, _ = remote_data.get_size_on_disk()

    assert size_on_disk_du == sizes['du']
    assert size_on_disk_stat == sizes['stat']
    assert size_on_disk_human == sizes['human']


@pytest.mark.parametrize(
    'num_char, relpath, sizes',
    (
        (1, '.', {'du': 24576, 'stat': 8195, 'human': '24.00 KB'}),
        (100, '.', {'du': 24576, 'stat': 8492, 'human': '24.00 KB'}),
        (int(1e6), '.', {'du': 3022848, 'stat': 3008192, 'human': '2.88 MB'}),
        (1, 'subdir1', {'du': 16384, 'stat': 4098, 'human': '16.00 KB'}),
        (100, 'subdir1', {'du': 16384, 'stat': 4296, 'human': '16.00 KB'}),
        (int(1e6), 'subdir1', {'du': 2015232, 'stat': 2004096, 'human': '1.92 MB'}),
    ),
)
def test_get_size_on_disk_nested(aiida_localhost, tmp_path, num_char, relpath, sizes):
    # TODO: Use create file hierarchy fixture from test_execmanager?
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

    with authinfo.get_transport() as transport:
        size_on_disk_du = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
        size_on_disk_stat = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)

        size_on_disk_human, _ = remote_data.get_size_on_disk(relpath=relpath)

    assert size_on_disk_du == sizes['du']
    assert size_on_disk_stat == sizes['stat']
    assert size_on_disk_human == sizes['human']


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
def test_get_size_on_disk_du(remote_data_factory, mode, monkeypatch):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_du` private method."""
    # No additional parametrization here, as already done in `test_get_size_on_disk_sizes`.

    remote_data = remote_data_factory(mode=mode)

    # Normal call
    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
    assert size_on_disk == 8192

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
