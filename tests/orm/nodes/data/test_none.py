###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :class:`aiida.orm.nodes.data.none.NoneData` data type."""

from aiida import orm
from aiida.orm import NoneData, load_node


def test_value_and_obj_are_none():
    """Both accessors report the represented value."""
    node = NoneData()
    assert node.value is None
    assert node.obj is None


def test_repr_and_str():
    assert repr(NoneData()) == 'NoneData()'
    assert str(NoneData()) == 'NoneData()'


def test_to_aiida_type_dispatches_none():
    """``to_aiida_type(None)`` returns an (unstored) ``NoneData``."""
    node = orm.to_aiida_type(None)
    assert isinstance(node, NoneData)
    assert node.is_stored is False


def test_stores_without_attributes():
    """A ``None`` carries no state, so the stored node has no attributes."""
    node = NoneData().store()
    assert node.is_stored is True
    assert node.base.attributes.all == {}


def test_identical_content_hash():
    """Every ``None`` is the same value, so all instances hash identically."""
    assert NoneData().store().base.caching.compute_hash() == NoneData().store().base.caching.compute_hash()


def test_roundtrip_through_entry_point():
    """A stored node reloads as ``NoneData`` via its registered ``node_type``."""
    pk = NoneData().store().pk
    loaded = load_node(pk)
    assert isinstance(loaded, NoneData)
    assert loaded.value is None
