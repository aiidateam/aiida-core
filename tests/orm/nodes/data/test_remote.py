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
def remote_data_local(tmp_path, aiida_computer_local, num_char: int | None = None):
    """Return a non-empty ``RemoteData`` instance."""
    aiida_localhost = aiida_computer_local(label='localhost')
    node = RemoteData(computer=aiida_localhost)
    node.set_remote_path(str(tmp_path))
    node.store()

    if num_char is None:
        content = b'some content'
    else:
        content = b'a' * num_char
    (tmp_path / 'file.txt').write_bytes(content)
    return node


@pytest.fixture
def remote_data_ssh(tmp_path, aiida_computer_ssh, num_char: int | None = None):
    """Return a non-empty ``RemoteData`` instance."""
    aiida_localhost_ssh = aiida_computer_ssh(label='localhost-ssh')
    node = RemoteData(computer=aiida_localhost_ssh)
    node.set_remote_path(str(tmp_path))
    node.store()

    if num_char is None:
        content = b'some content'
    else:
        content = b'a' * num_char
    (tmp_path / 'file.txt').write_bytes(content)
    return node


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_clean(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.clean` method."""

    remote_data = request.getfixturevalue(fixture)

    assert not remote_data.is_empty
    assert not remote_data.is_cleaned
    remote_data._clean()
    assert remote_data.is_empty
    assert remote_data.is_cleaned


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.get_size_on_disk` method."""

    remote_data = request.getfixturevalue(fixture)

    # Check here for human-readable output string, as integer byte values are checked in
    # `test_get_size_on_disk_[du|lstat]`
    size_on_disk, method = remote_data.get_size_on_disk(method='du')
    assert size_on_disk == '4.01 KB'
    assert method == 'du'

    size_on_disk, method = remote_data.get_size_on_disk(method='lstat')
    assert size_on_disk == '12.00 B'
    assert method == 'lstat'

    # Path/file non-existent
    with pytest.raises(FileNotFoundError, match='.*does not exist, is not a directory.*'):
        remote_data.get_size_on_disk(relpath=Path('non-existent'))

@pytest.mark.parametrize(
    'num_char, relpath, sizes',
    (
        (1, '.', {'du': 12291, 'lstat': 8195, 'human': '12.00 KB'}),
        (100, '.', {'du': 12588, 'lstat': 8492, 'human': '12.29 KB'}),
        (int(1e6), '.', {'du': 3012288, 'lstat': 3008192, 'human': '2.87 MB'}),
        (1, 'subdir1', {'du': 8194, 'lstat': 4098, 'human': '8.00 KB'}),
        (100, 'subdir1', {'du': 8392, 'lstat': 4296, 'human': '8.20 KB'}),
        (int(1e6), 'subdir1', {'du': 2008192, 'lstat': 2004096, 'human': '1.92 MB'}),
    ),
)
def test_get_size_on_disk_nested(aiida_localhost, tmp_path, num_char, relpath, sizes):

    sub_dir1 = tmp_path / "subdir1"
    sub_dir1.mkdir()

    sub_dir2 = tmp_path / "subdir1" / "subdir2"
    sub_dir2.mkdir()

    # Create some files with known sizes
    file1 = sub_dir1 / "file1.txt"
    file1.write_text("a"*num_char)

    file2 = sub_dir2 / "file2.bin"
    file2.write_bytes(b"a" * num_char)

    file3 = tmp_path / "file3.txt"
    file3.write_text("a" * num_char)

    remote_data = RemoteData(computer=aiida_localhost, remote_path=tmp_path)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path()) / relpath

    with authinfo.get_transport() as transport:

        size_on_disk_du = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
        size_on_disk_lstat = remote_data._get_size_on_disk_lstat(transport=transport, full_path=full_path)

        size_on_disk_human, _ = remote_data.get_size_on_disk(relpath=relpath)

    print(f'du: {size_on_disk_du}, lstat: {size_on_disk_lstat}, human: {size_on_disk_human}')
    assert size_on_disk_du == sizes['du']
    assert size_on_disk_lstat == sizes['lstat']
    assert size_on_disk_human == sizes['human']

    # Do the same possibly for subtrees


@pytest.mark.parametrize(
    'num_char, sizes',
    (
        (1, {'du': 4097, 'lstat': 1, 'human': '4.00 KB'}),
        (10, {'du': 4106, 'lstat': 10, 'human': '4.01 KB'}),
        (100, {'du': 4196, 'lstat': 100, 'human': '4.10 KB'}),
        (1000, {'du': 5096, 'lstat': 1000, 'human': '4.98 KB'}),
        (int(1e6), {'du': 1004096, 'lstat': int(1e6), 'human': '980.56 KB'}),
    ),
)
@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk_sizes(tmp_path, num_char, sizes, request, fixture):
    """Test the different implementations implementations to obtain the size of a RemoteData on disk."""

    remote_data = request.getfixturevalue(fixture)  # (num_char=num_char)

    content = b'a' * num_char
    (tmp_path / 'file.txt').write_bytes(content)
    remote_data.store()

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk_du = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
        size_on_disk_lstat = remote_data._get_size_on_disk_lstat(transport=transport, full_path=full_path)
        size_on_disk_human, _ = remote_data.get_size_on_disk()

    assert size_on_disk_du == sizes['du']
    assert size_on_disk_lstat == sizes['lstat']
    assert size_on_disk_human == sizes['human']


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk_du(request, fixture, monkeypatch):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_du` private method."""

    remote_data = request.getfixturevalue(fixture)

    # Normal call
    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
    assert size_on_disk == 4108

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


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk_lstat(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_lstat` private method."""

    remote_data = request.getfixturevalue(fixture)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_lstat(transport=transport, full_path=full_path)
        assert size_on_disk == 12

        # Raises OSError for non-existent directory
        with pytest.raises(OSError, match='The required remote folder.*'):
            remote_data._get_size_on_disk_lstat(transport=transport, full_path=full_path / 'non-existent')
