###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`aiida.orm.utils.serialize` module."""

import base64
import functools
import operator
import re
import sys
import types
import uuid
from dataclasses import dataclass

import numpy as np
import pytest

from aiida import orm
from aiida.common import callables
from aiida.common.links import LinkType
from aiida.engine.processes import persistence
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


def make_adder(offset):
    """Return a closure, which no name identifies, over the provided offset."""
    return lambda value: value + offset


class Adder:
    """A callable object, which a name reference resolves to its class rather than to this instance."""

    def __init__(self, offset):
        self.offset = offset

    def __call__(self, value):
        return value + self.offset


def test_importable_callable_stays_a_name_reference():
    """Test that a callable that can be imported is still represented by name, and not by its bytes."""
    serialized = serialize.serialize({'callable': serialize.serialize})

    assert serialized.strip() == "callable: !!python/name:aiida.orm.utils.serialize.serialize ''"
    assert serialize.deserialize_unsafe(serialized)['callable'] is serialize.serialize


def test_callable_representation():
    """Test what a callable no name refers to actually looks like in a checkpoint.

    The whole callable is written out under a tag of ours, base64 encoded so that it stays printable text, which is
    what someone reading a checkpoint by hand will find where a `!!python/name:` reference used to be.
    """
    offset = 10
    dumped = serialize.serialize({'callable': lambda value: value + offset})

    match = re.fullmatch(r"callable: !aiida_callable '([A-Za-z0-9+/=]+)'\n", dumped)
    assert match is not None, dumped

    payload = base64.b64decode(match.group(1))

    assert payload.startswith(b'\x80'), 'the payload should be a pickle stream'
    assert callables.loads(payload)(1) == 11


@pytest.mark.parametrize(
    'value',
    (
        pytest.param(make_adder(10), id='closure'),
        pytest.param(functools.partial(operator.add, 10), id='partial'),
        pytest.param(Adder(10), id='callable-object'),
    ),
)
def test_callable_round_trip(value):
    """Test that a callable no name identifies survives a round trip, including the state it carries."""
    deserialized = serialize.deserialize_unsafe(serialize.serialize({'callable': value}))['callable']

    assert deserialized(1) == 11


@pytest.fixture
def user_module(tmp_path):
    """Yield a module on this interpreter's path only, as a directory added after the daemon started would be."""
    (tmp_path / 'userlib.py').write_text('def parse(value):\n    return value * 2\n')
    sys.path.insert(0, str(tmp_path))

    try:
        import userlib

        yield userlib
    finally:
        sys.path.remove(str(tmp_path))
        del sys.modules['userlib']


@pytest.fixture
def reader_without(monkeypatch, tmp_path):
    """Make the reader's paths this interpreter's, minus the directory the user module lives in."""
    monkeypatch.setattr(
        persistence, 'reader_import_paths', lambda: tuple(entry for entry in sys.path if entry != str(tmp_path))
    )


def test_carried_modules_for_a_name_the_reader_resolves(monkeypatch):
    """Test that an importable callable the reader can import stays a name reference."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: tuple(sys.path))

    assert persistence.carried_modules(serialize.serialize) is None


def test_carried_modules_when_the_reader_is_unknown(monkeypatch):
    """Test that an importable callable stays a name reference when nothing is known about the reader.

    This is what happened before there was anything to go on: the cheap form, which fails loudly if it is wrong.
    """
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: None)

    assert persistence.carried_modules(serialize.serialize) is None


def test_carried_modules_for_a_name_the_reader_lacks(user_module, reader_without):
    """Test that a module only this interpreter can import travels inside the payload."""
    # ``__main__`` is in there too, and always is: no reader can import another interpreter's entry point.
    # Carrying a module the callable never touches costs nothing, since only what it reaches is written out.
    assert 'userlib' in persistence.carried_modules(user_module.parse)


def test_carried_modules_holds_nothing_the_reader_has(user_module, reader_without):
    """Test that an installed module stays a reference, since carrying it would pin the reader to this version."""
    needed = persistence.carried_modules(user_module.parse)

    assert 'yaml' not in needed
    assert not any(name.startswith('aiida') for name in needed)


def test_carried_modules_for_a_closure(monkeypatch):
    """Test that a callable no name identifies is written out whole however the reader is set up."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: tuple(sys.path))

    carried = persistence.carried_modules(lambda: None)

    assert carried is not None, 'a closure has no name to keep, so it has to be written out'
    assert set(carried) <= {'__main__'}, "a reader with this interpreter's paths lacks only its entry point"


def test_representation_follows_the_reader(user_module, monkeypatch, tmp_path):
    """Test that one callable is a name for a reader that can import it and a payload for one that cannot."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: tuple(sys.path))
    named = serialize.serialize({'callable': user_module.parse})

    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: tuple(e for e in sys.path if e != str(tmp_path)))
    carried = serialize.serialize({'callable': user_module.parse})

    assert named.strip() == "callable: !!python/name:userlib.parse ''"
    assert carried.startswith('callable: !aiida_callable')
    assert serialize.deserialize_unsafe(carried)['callable'](3) == 6


def test_carried_modules_skips_a_module_that_has_no_name_to_import(user_module, reader_without):
    """Test that a module object never registered in ``sys.modules`` is left alone.

    ``sys.monitoring`` and friends are attributes of a builtin rather than importable modules, so they can be neither
    carried nor missing, and treating them as either puts an unimportable name into the payload.
    """
    needed = persistence.carried_modules(user_module.parse)

    assert not any(name.startswith('sys.') for name in needed)
