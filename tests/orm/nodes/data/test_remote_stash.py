###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.nodes.data.remote.stash` module."""

import pytest

from aiida.common.datastructures import StashMode
from aiida.common.exceptions import StoringNotAllowed
from aiida.orm import RemoteStashCompressedData, RemoteStashData, RemoteStashFolderData


def test_base_class():
    """Verify that base class cannot be stored."""

    node = RemoteStashData(stash_mode=StashMode.COPY)

    with pytest.raises(StoringNotAllowed):
        node.store()


@pytest.mark.parametrize('store', (False, True))
def test_constructor_folder(store):
    """Test the constructor and storing functionality."""

    stash_mode = StashMode.COPY
    target_basepath = '/absolute/path'
    source_list = ['relative/folder', 'relative/file']

    data = RemoteStashFolderData(stash_mode, target_basepath, source_list)

    assert data.stash_mode == stash_mode
    assert data.target_basepath == target_basepath
    assert data.source_list == source_list

    if store:
        data.store()
        assert data.is_stored
        assert data.stash_mode == stash_mode
        assert data.target_basepath == target_basepath
        assert data.source_list == source_list


@pytest.mark.parametrize(
    'argument, value',
    (
        ('stash_mode', 'copy'),
        ('target_basepath', ['list']),
        ('source_list', 'relative/path'),
        ('source_list', ('/absolute/path')),
    ),
)
def test_constructor_invalid_folder(argument, value):
    """Test the constructor for invalid argument types."""

    kwargs = {
        'stash_mode': StashMode.COPY,
        'target_basepath': '/absolute/path',
        'source_list': ('relative/folder', 'relative/file'),
    }

    with pytest.raises(TypeError):
        kwargs[argument] = value
        RemoteStashFolderData(**kwargs)


@pytest.mark.parametrize('store', (False, True))
@pytest.mark.parametrize(
    'stash_mode',
    [StashMode.COMPRESS_TAR, StashMode.COMPRESS_TARBZ2, StashMode.COMPRESS_TARGZ, StashMode.COMPRESS_TARXZ],
)
@pytest.mark.parametrize('dereference', (False, True))
def test_constructor_compressed(store, stash_mode, dereference):
    """Test the constructor and storing functionality."""

    target_basepath = '/absolute/path/foo.tar.gz'
    source_list = ['relative/folder', 'relative/file']

    data = RemoteStashCompressedData(stash_mode, target_basepath, source_list, dereference)

    assert data.stash_mode == stash_mode
    assert data.target_basepath == target_basepath
    assert data.source_list == source_list

    if store:
        data.store()
        assert data.is_stored
        assert data.stash_mode == stash_mode
        assert data.target_basepath == target_basepath
        assert data.source_list == source_list
        assert data.dereference == dereference


@pytest.mark.parametrize(
    'argument, value',
    (
        ('stash_mode', 'compress'),
        ('target_basepath', ['list']),
        ('source_list', 'relative/path'),
        ('source_list', ('/absolute/path')),
        ('dereference', 'False'),
    ),
)
def test_constructor_invalid_compressed(argument, value):
    """Test the constructor for invalid argument types."""

    kwargs = {
        'stash_mode': StashMode.COMPRESS_TAR,
        'target_basepath': '/absolute/path',
        'source_list': ('relative/folder', 'relative/file'),
        'dereference': False,
    }

    with pytest.raises(TypeError):
        kwargs[argument] = value
        RemoteStashCompressedData(**kwargs)


@pytest.mark.parametrize(
    'dataclass, valid_stash_modes',
    (
        (RemoteStashFolderData, [StashMode.COPY]),
        (
            RemoteStashCompressedData,
            [StashMode.COMPRESS_TAR, StashMode.COMPRESS_TARBZ2, StashMode.COMPRESS_TARGZ, StashMode.COMPRESS_TARXZ],
        ),
    ),
)
def test_constructor_invalid_stash_mode(dataclass, valid_stash_modes):
    """The constructor should raise if an invalid stash mode is passed."""

    all_modes = [mode for mode in StashMode.__members__.values()]

    for mode in all_modes:
        kwargs = {
            'stash_mode': mode,
            'target_basepath': '/absolute/path',
            'source_list': ('relative/folder', 'relative/file'),
        }

        if dataclass is RemoteStashCompressedData:
            kwargs['dereference'] = False

        if mode not in valid_stash_modes:
            with pytest.raises(ValueError):
                dataclass(**kwargs)
        else:
            dataclass(**kwargs)
