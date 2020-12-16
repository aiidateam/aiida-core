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
"""Module to test remote data."""
import pytest

from aiida.orm import RemoteData


@pytest.fixture
def remote_data(aiida_localhost, tmp_path):
    """Return an instance of a ``RemoteData`` instance containing a single file."""
    remote_data = RemoteData(computer=aiida_localhost)
    remote_data.set_remote_path(str(tmp_path))

    with open(tmp_path / 'file.txt', 'w') as handle:
        handle.write('content')
        handle.flush()

    return remote_data


@pytest.mark.usefixtures('clear_database_before_test')
def test_clean(remote_data):
    """Try the ``RemoteData._clean`` method."""
    with remote_data.computer.get_transport() as transport:
        assert not remote_data.is_empty(transport=transport)
        remote_data._clean(transport=transport)  # pylint: disable=protected-access
        assert remote_data.is_empty(transport=transport)

        # Second call should be a no-op
        remote_data._clean(transport=transport)  # pylint: disable=protected-access
