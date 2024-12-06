###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.utils.serialize` module."""

import types
import uuid
from dataclasses import dataclass

import numpy as np
import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.orm.utils import serialize


def test_serialize_round_trip():
    """Test the serialization of a dictionary with Nodes in various data structure
    Also make sure that the serialized data is json-serializable
    """
    node_a = orm.Data().store()
    node_b = orm.Data().store()

    data = {'test': 1, 'list': [1, 2, 3, node_a], 'dict': {('Si',): node_b, 'foo': 'bar'}, 'baz': 'aar'}

    serialized_data = serialize.serialize(data)
    deserialized_data = serialize.deserialize_unsafe(serialized_data)

    # For now manual element-for-element comparison until we come up with general
    # purpose function that can equate two node instances properly
    assert data['test'] == deserialized_data['test']
    assert data['baz'] == deserialized_data['baz']
    assert data['list'][:3] == deserialized_data['list'][:3]
    assert data['list'][3].uuid == deserialized_data['list'][3].uuid
    assert data['dict'][('Si',)].uuid == deserialized_data['dict'][('Si',)].uuid


def test_serialize_group():
    """Test that serialization and deserialization of Groups works.
    Also make sure that the serialized data is json-serializable
    """
    group_a = orm.Group(label=uuid.uuid4().hex).store()

    data = {'group': group_a}

    serialized_data = serialize.serialize(data)
    deserialized_data = serialize.deserialize_unsafe(serialized_data)

    assert data['group'].uuid == deserialized_data['group'].uuid
    assert data['group'].label == deserialized_data['group'].label


def test_serialize_node_round_trip():
    """Test you can serialize and deserialize a node"""
    node = orm.Data().store()
    deserialized = serialize.deserialize_unsafe(serialize.serialize(node))
    assert node.uuid == deserialized.uuid


def test_serialize_group_round_trip():
    """Test you can serialize and deserialize a group"""
    group = orm.Group(label='test_serialize_group_round_trip').store()
    deserialized = serialize.deserialize_unsafe(serialize.serialize(group))

    assert group.uuid == deserialized.uuid
    assert group.label == deserialized.label


def test_serialize_computer_round_trip(aiida_localhost):
    """Test you can serialize and deserialize a computer"""
    deserialized = serialize.deserialize_unsafe(serialize.serialize(aiida_localhost))

    assert aiida_localhost.uuid == deserialized.uuid
    assert aiida_localhost.label == deserialized.label


def test_serialize_unstored_node():
    """Test that you can't serialize an unstored node"""
    node = orm.Data()

    with pytest.raises(ValueError):
        serialize.serialize(node)


def test_serialize_unstored_group():
    """Test that you can't serialize an unstored group"""
    group = orm.Group(label='test_serialize_unstored_group')

    with pytest.raises(ValueError):
        serialize.serialize(group)


def test_serialize_unstored_computer():
    """Test that you can't serialize an unstored node"""
    computer = orm.Computer('test_computer', 'test_host')

    with pytest.raises(ValueError):
        serialize.serialize(computer)


def test_mixed_attribute_normal_dict():
    """Regression test for #3092.

    The yaml mapping constructor in `aiida.orm.utils.serialize` was not properly "deeply" reconstructing nested
    mappings, causing a mix of attribute dictionaries and normal dictionaries to lose information in a round-trip.

    If a nested `AttributeDict` contained a normal dictionary, the content of the latter would be lost during the
    deserialization, despite the information being present in the serialized yaml dump.
    """
    from aiida.common.extendeddicts import AttributeDict

    # Construct a nested `AttributeDict`, which should make all nested dictionaries `AttributeDicts` recursively
    dictionary = {'nested': AttributeDict({'dict': 'string', 'value': 1})}
    attribute_dict = AttributeDict(dictionary)

    # Now add a normal dictionary in the attribute dictionary
    attribute_dict['nested']['normal'] = {'a': 2}

    serialized = serialize.serialize(attribute_dict)
    deserialized = serialize.deserialize_unsafe(serialized)

    assert attribute_dict, deserialized


def test_serialize_numpy():
    """Regression test for #3709

    Check that numpy arrays can be serialized.
    """
    data = np.array([1, 2, 3])

    serialized = serialize.serialize(data)
    deserialized = serialize.deserialize_unsafe(serialized)
    assert np.all(data == deserialized)


def test_serialize_simplenamespace():
    """Regression test for #3709

    Check that `types.SimpleNamespace` can be serialized.
    """
    data = types.SimpleNamespace(a=1, b=2.1)

    serialized = serialize.serialize(data)
    deserialized = serialize.deserialize_unsafe(serialized)
    assert data == deserialized


def test_enum():
    """Test serialization and deserialization of an ``Enum``."""
    enum = LinkType.RETURN
    serialized = serialize.serialize(enum)
    assert isinstance(serialized, str)

    deserialized = serialize.deserialize_unsafe(serialized)
    assert deserialized == enum


@dataclass
class DataClass:
    """A dataclass for testing."""

    my_value: int


def test_dataclass():
    """Test serialization and deserialization of a ``dataclass``."""
    obj = DataClass(1)
    serialized = serialize.serialize(obj)
    assert isinstance(serialized, str)

    deserialized = serialize.deserialize_unsafe(serialized)
    assert deserialized == obj


def test_serialize_node_links_manager():
    """Test you can serialize and deserialize a NodeLinksManager"""
    from aiida.orm.utils.managers import NodeLinksManager

    node = orm.Data().store()
    node_links_manager = NodeLinksManager(node=node, link_type=LinkType.CREATE, incoming=False)
    deserialized = serialize.deserialize_unsafe(serialize.serialize(node_links_manager))
    assert isinstance(deserialized, NodeLinksManager)
    assert deserialized._node.uuid == node.uuid
    assert deserialized._link_type == LinkType.CREATE
    assert deserialized._incoming is False
