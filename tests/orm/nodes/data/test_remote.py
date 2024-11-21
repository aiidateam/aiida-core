###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.remote.base.RemoteData` module."""

from pathlib import Path

import pytest

from aiida.orm import RemoteData


@pytest.fixture
def remote_data_local(tmp_path, aiida_localhost):
    """Return a non-empty ``RemoteData`` instance."""
    node = RemoteData(computer=aiida_localhost)
    node.set_remote_path(str(tmp_path))
    node.store()
    (tmp_path / 'file.txt').write_bytes(b'some content')
    return node


@pytest.fixture
def remote_data_ssh(tmp_path, aiida_computer_ssh):
    """Return a non-empty ``RemoteData`` instance."""
    # Compared to `aiida_localhost`, `aiida_computer_ssh` doesn't return an actual `Computer`, but just a factory
    # Thus, we need to call the factory here passing the label to actually create the `Computer` instance
    localhost_ssh = aiida_computer_ssh(label='localhost-ssh')
    node = RemoteData(computer=localhost_ssh)
    node.set_remote_path(str(tmp_path))
    node.store()
    (tmp_path / 'file.txt').write_bytes(b'some content')
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
def test_get_size_on_disk_du(request, fixture, monkeypatch):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.clean` method."""

    remote_data = request.getfixturevalue(fixture)

    # Normal call
    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_du(transport=transport, full_path=full_path)
    assert size_on_disk == 4108

    # Monkeypatch transport exec_command_wait command to simulate `du` failure
    def mock_exec_command_wait(command):
        return (1, '', 'Error executing `du` command')

    monkeypatch.setattr(transport, 'exec_command_wait', mock_exec_command_wait)
    with pytest.raises(RuntimeError, match='Error executing `du`.*'):
        remote_data._get_size_on_disk_du(full_path, transport)


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk_lstat(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.clean` method."""

    remote_data = request.getfixturevalue(fixture)

    authinfo = remote_data.get_authinfo()
    full_path = Path(remote_data.get_remote_path())

    with authinfo.get_transport() as transport:
        size_on_disk = remote_data._get_size_on_disk_lstat(transport=transport, full_path=full_path)
    assert size_on_disk == 12


@pytest.mark.parametrize('fixture', ['remote_data_local', 'remote_data_ssh'])
def test_get_size_on_disk(request, fixture):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.clean` method."""

    remote_data = request.getfixturevalue(fixture)

    # Check here for human-readable output string, as integer byte values are checked in
    # `test_get_size_on_disk_[du|lstat]`
    size_on_disk = remote_data.get_size_on_disk()
    assert size_on_disk == '4.01 KB'

    # Path/file non-existent
    with pytest.raises(FileNotFoundError, match='.*does not exist, is not a directory.*'):
        remote_data.get_size_on_disk(relpath=Path('non-existent'))
