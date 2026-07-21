###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for :mod:`aiida.orm.nodes.data.serializer`."""

import numpy
import pytest

from aiida import orm
from aiida.common.extendeddicts import AttributeDict
from aiida.orm.nodes.data.serializer import general_serializer, get_serializers, serialize_to_aiida_nodes


@pytest.mark.parametrize(
    'value, expected_type',
    (
        (5, orm.Int),
        (5.0, orm.Float),
        ('x', orm.Str),
        (True, orm.Bool),
        ([1, 2], orm.List),
        ({'a': 1}, orm.Dict),
        (numpy.int64(3), orm.Int),
        (numpy.array([1, 2]), orm.ArrayData),
        (None, orm.NoneData),
    ),
)
def test_core_owned_types_go_through_to_aiida_type(value, expected_type):
    """Core-owned value types are dispatched by :func:`to_aiida_type` and stored."""
    node = general_serializer(value)
    assert isinstance(node, expected_type)
    assert node.is_stored is True


def test_existing_node_is_returned_unchanged():
    node = orm.Int(1).store()
    assert general_serializer(node) is node


def test_attribute_dict_is_returned_unchanged():
    namespace = AttributeDict({'a': 1})
    assert general_serializer(namespace) is namespace


def test_store_false_does_not_store():
    node = general_serializer(5, store=False)
    assert isinstance(node, orm.Int)
    assert node.is_stored is False


class JsonableClass:
    """Object exposing the ``as_dict`` / ``from_dict`` contract for the JSON fallback."""

    def __init__(self, value):
        self.value = value

    def as_dict(self):
        return {'value': self.value}

    @classmethod
    def from_dict(cls, dictionary):
        return cls(dictionary['value'])


def test_json_able_object_falls_back_to_jsonable_data():
    node = general_serializer(JsonableClass(7))
    assert isinstance(node, orm.JsonableData)
    assert node.obj.value == 7


def test_unserializable_object_raises_with_guidance():
    class Opaque:
        pass

    with pytest.raises(ValueError, match=r'cannot serialize the object of type `.*Opaque`'):
        general_serializer(Opaque())


def tuple_to_list(data, user=None):
    """A serializer following the ``serializer(value, user=...)`` calling convention, used by the registry test."""
    return orm.List(list=list(data))


def test_explicit_serializers_mapping_handles_foreign_type():
    """The registry branch: a type ``to_aiida_type`` does not own is resolved via the ``serializers`` mapping."""
    node = general_serializer((1, 2, 3), serializers={'builtins.tuple': f'{__name__}.tuple_to_list'})
    assert isinstance(node, orm.List)
    assert node.get_list() == [1, 2, 3]


def test_serialize_to_aiida_nodes_maps_each_value():
    result = serialize_to_aiida_nodes({'i': 1, 's': 'x'})
    assert isinstance(result['i'], orm.Int)
    assert isinstance(result['s'], orm.Str)


def test_get_serializers_is_cached_and_skips_non_type_keys():
    registry = get_serializers()
    assert get_serializers() is registry
    # ``core.dict`` yields the dot-less key ``dict`` and is skipped; only dotted (type-key-shaped) names are kept.
    assert 'dict' not in registry
    assert all('.' in key for key in registry)
