# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :mod:`aiida.orm.nodes.data.remote.base.RemoteData` module."""
import pytest

from aiida.orm import RemoteData


@pytest.fixture
def remote_data(tmp_path, aiida_localhost):
    """Return a non-empty ``RemoteData`` instance."""
    node = RemoteData(computer=aiida_localhost)
    node.set_remote_path(str(tmp_path))
    node.store()
    (tmp_path / 'file.txt').write_bytes(b'some content')
    return node


def test_clean(remote_data):
    """Test the :meth:`aiida.orm.nodes.data.remote.base.RemoteData.clean` method."""
    assert not remote_data.is_empty
    assert not remote_data.is_cleaned

    remote_data._clean()  #  pylint: disable=protected-access
    assert remote_data.is_empty
    assert remote_data.is_cleaned
