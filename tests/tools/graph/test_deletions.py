###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.tools.graph.deletions`."""

import pytest

from aiida import get_profile, orm
from aiida.tools.collab.config import OPTION_ENABLED
from aiida.tools.collab.state import CollabState
from aiida.tools.graph.deletions import delete_nodes


@pytest.fixture
def collab_filepath(monkeypatch, tmp_path):
    """Redirect the state of the collab to a temporary file and return its path."""
    filepath = tmp_path / 'collab.json'
    monkeypatch.setattr(CollabState, 'get_filepath', staticmethod(lambda profile: filepath))
    return filepath


@pytest.mark.usefixtures('aiida_profile_clean')
def test_delete_nodes_records_tombstones(monkeypatch, collab_filepath):
    """Test that deleted nodes are tombstoned when the profile takes part in a collab."""
    monkeypatch.setitem(get_profile().options, OPTION_ENABLED, True)
    node = orm.Data().store()
    uuid = node.uuid

    delete_nodes([node.pk], dry_run=False)

    assert CollabState.load(get_profile()).tombstones == {uuid}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_delete_nodes_without_collab(collab_filepath):
    """Test that no tombstones are recorded when the profile does not take part in a collab."""
    node = orm.Data().store()

    delete_nodes([node.pk], dry_run=False)

    assert not collab_filepath.exists()
