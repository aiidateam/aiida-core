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
@pytest.mark.parametrize(
    'setup, results',
    (
        (('du', False), ('4.01 KB', 'du')),
        (('du', True), (4108, 'du')),
        (('stat', False), ('12.00 B', 'stat')),
        (('stat', True), (12, 'stat')),
    ),
)
def test_get_size_on_disk_params(request, fixture, setup, results):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.get_size_on_disk` method."""

    remote_data = request.getfixturevalue(fixture)

    size_on_disk, method = remote_data.get_size_on_disk(method=setup[0], return_bytes=setup[1])
    assert (size_on_disk, method) == results


@pytest.mark.parametrize(
    'num_char, sizes',
    (
        (1, {'du': 4097, 'stat': 1, 'human': '4.00 KB'}),
        (10, {'du': 4106, 'stat': 10, 'human': '4.01 KB'}),
        (100, {'du': 4196, 'stat': 100, 'human': '4.10 KB'}),
        (1000, {'du': 5096, 'stat': 1000, 'human': '4.98 KB'}),
        (int(1e6), {'du': 1004096, 'stat': int(1e6), 'human': '980.56 KB'}),
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
        size_on_disk_stat = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)
        size_on_disk_human, _ = remote_data.get_size_on_disk()

    assert size_on_disk_du == sizes['du']
    assert size_on_disk_stat == sizes['stat']
    assert size_on_disk_human == sizes['human']


@pytest.mark.parametrize(
    'num_char, relpath, sizes',
    (
        (1, '.', {'du': 12291, 'stat': 8195, 'human': '12.00 KB'}),
        (100, '.', {'du': 12588, 'stat': 8492, 'human': '12.29 KB'}),
        (int(1e6), '.', {'du': 3012288, 'stat': 3008192, 'human': '2.87 MB'}),
        (1, 'subdir1', {'du': 8194, 'stat': 4098, 'human': '8.00 KB'}),
        (100, 'subdir1', {'du': 8392, 'stat': 4296, 'human': '8.20 KB'}),
        (int(1e6), 'subdir1', {'du': 2008192, 'stat': 2004096, 'human': '1.92 MB'}),
    ),
)
def test_get_size_on_disk_nested(aiida_localhost, tmp_path, num_char, relpath, sizes):
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


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk_excs(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.get_size_on_disk` method."""
    # Extra function to avoid unnecessary parametrization here
    remote_data = request.getfixturevalue(fixture)

    # Path/file non-existent
    with pytest.raises(FileNotFoundError, match='.*does not exist.*'):
        remote_data.get_size_on_disk(relpath=Path('non-existent'))

    # Non-valid method
    with pytest.raises(NotImplementedError, match='.*for evaluating the size on disk not implemented.'):
        remote_data.get_size_on_disk(method='fake-du')


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk_du(request, fixture, monkeypatch):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_du` private method."""
    # No additional parametrization here, as already done in `test_get_size_on_disk_sizes`.

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
def test_get_size_on_disk_stat(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData._get_size_on_disk_stat` private method."""
    # No additional parametrization here, as already done in `test_get_size_on_disk_sizes`.

    remote_data = request.getfixturevalue(fixture)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path)
        assert size_on_disk == 12

        # Raises OSError for non-existent directory
        with pytest.raises(OSError, match='The required remote folder.*'):
            remote_data._get_size_on_disk_stat(transport=transport, full_path=full_path / 'non-existent')
