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
from aiida.orm import RemoteStashData, RemoteStashFolderData


def test_base_class():
    """Verify that base class cannot be stored."""
    node = RemoteStashData(stash_mode=StashMode.COPY)

    with pytest.raises(StoringNotAllowed):
        node.store()


@pytest.mark.parametrize('store', (False, True))
def test_constructor(store):
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
def test_constructor_invalid(argument, value):
    """Test the constructor for invalid argument types."""
    kwargs = {
        'stash_mode': StashMode.COPY,
        'target_basepath': '/absolute/path',
        'source_list': ('relative/folder', 'relative/file'),
    }

    with pytest.raises(TypeError):
        kwargs[argument] = value
        RemoteStashFolderData(**kwargs)
