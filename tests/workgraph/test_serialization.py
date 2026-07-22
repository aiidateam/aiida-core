###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :func:`aiida.workgraph.serialization.serialize_ports`."""

import pytest
from node_graph.socket_spec import SocketSpec, dynamic, namespace

from aiida import orm
from aiida.workgraph import serialize_ports


def test_leaf_spec_serializes_the_value():
    """A non-namespace spec serializes the value directly and does not store it."""
    node = serialize_ports(5, SocketSpec(identifier='node_graph.int'))
    assert isinstance(node, orm.Int)
    assert node.value == 5
    assert node.is_stored is False


def test_namespace_serializes_each_declared_field():
    result = serialize_ports({'x': 1, 'y': 'a'}, namespace(x=int, y=str))
    assert isinstance(result['x'], orm.Int)
    assert isinstance(result['y'], orm.Str)
    assert (result['x'].value, result['y'].value) == (1, 'a')


def test_nested_namespace_recurses():
    result = serialize_ports({'inner': {'x': 1}}, namespace(inner=namespace(x=int)))
    assert isinstance(result['inner']['x'], orm.Int)
    assert result['inner']['x'].value == 1


def test_dynamic_namespace_serializes_arbitrary_keys():
    result = serialize_ports({'a': 1, 'b': 2}, dynamic(int))
    assert set(result) == {'a', 'b'}
    assert all(isinstance(node, orm.Int) for node in result.values())


def test_non_mapping_for_namespace_raises():
    with pytest.raises(ValueError, match='expected a mapping'):
        serialize_ports(5, namespace(x=int))


def test_unexpected_key_in_static_namespace_raises():
    with pytest.raises(ValueError, match="unexpected key 'z'"):
        serialize_ports({'z': 1}, namespace(x=int))
