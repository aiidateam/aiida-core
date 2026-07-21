"""Tests for the :class:`aiida.orm.nodes.data.jsonable.JsonableData` data type."""

import dataclasses
import datetime
import math

import numpy
import pytest
from pydantic import BaseModel
from pymatgen.core.structure import Molecule

from aiida.orm import load_node
from aiida.orm.nodes.data.jsonable import JsonableData


class JsonableClass:
    """Dummy class that implements the required interface."""

    def __init__(self, data):
        """Construct a new object."""
        self._data = data

    @property
    def data(self):
        """Return the data of this instance."""
        return self._data

    def as_dict(self):
        """Represent the object as a JSON-serializable dictionary."""
        return {
            'data': self._data,
        }

    @classmethod
    def from_dict(cls, dictionary):
        """Reconstruct an instance from a serialized version."""
        return cls(dictionary['data'])


def test_construct():
    """Test the ``JsonableData`` constructor."""
    data = {'a': 1}
    obj = JsonableClass(data)
    node = JsonableData(obj)

    assert isinstance(node, JsonableData)
    assert not node.is_stored


def test_invalid_class_no_as_dict():
    """Test the ``JsonableData`` constructor raises if object implements no supported serialization method."""

    class InvalidClass:
        pass

    with pytest.raises(TypeError, match=r'does not implement any of the supported serialization methods'):
        JsonableData(InvalidClass())


def test_invalid_class_not_serializable():
    """Test the ``JsonableData`` constructor raises if object ."""
    obj = JsonableClass({'datetime': datetime.datetime.now()})

    with pytest.raises(TypeError, match=r'the object `.*` is not JSON-serializable and therefore cannot be stored.'):
        JsonableData(obj)


def test_store():
    """Test storing a ``JsonableData`` instance."""
    data = {'a': 1}
    obj = JsonableClass(data)
    node = JsonableData(obj)
    assert not node.is_stored

    node.store()
    assert node.is_stored


def test_load():
    """Test loading a ``JsonableData`` instance."""
    data = {'a': 1}
    obj = JsonableClass(data)
    node = JsonableData(obj)
    node.store()

    loaded = load_node(node.pk)
    assert isinstance(node, JsonableData)
    assert loaded == node


def test_obj():
    """Test the ``JsonableData.obj`` property."""
    data = [1, float('inf'), float('-inf'), float('nan')]
    obj = JsonableClass(data)
    node = JsonableData(obj)
    node.store()

    assert isinstance(node.obj, JsonableClass)
    assert node.obj.data == data

    loaded = load_node(node.pk)
    assert isinstance(node.obj, JsonableClass)

    for left, right in zip(loaded.obj.data, data):
        # Need this explicit case to compare NaN because of the peculiarity in Python where ``float(nan) != float(nan)``
        if isinstance(left, float) and math.isnan(left):
            assert math.isnan(right)
            continue

        assert left == right


def test_unimportable_module():
    """Test the ``JsonableData.obj`` property if the associated module cannot be loaded."""
    obj = Molecule(['H'], [[0, 0, 0]])
    node = JsonableData(obj)

    # Artificially change the ``@module`` in the attributes so it becomes unloadable
    node.base.attributes.set('@module', 'not.existing')
    node.store()

    loaded = load_node(node.pk)

    with pytest.raises(ImportError, match='the objects module `not.existing` can not be imported.'):
        _ = loaded.obj


def test_unimportable_class():
    """Test the ``JsonableData.obj`` property if the associated class cannot be loaded."""
    obj = Molecule(['H'], [[0, 0, 0]])
    node = JsonableData(obj)

    # Artificially change the ``@class`` in the attributes so it becomes unloadable
    node.base.attributes.set('@class', 'NonExistingClass')
    node.store()

    loaded = load_node(node.pk)

    with pytest.raises(ImportError, match=r'the objects module `.*` does not contain the class `NonExistingClass`.'):
        _ = loaded.obj


def test_msonable():
    """Test that an ``MSONAble`` object can be wrapped, stored and loaded again."""
    obj = Molecule(['H'], [[0, 0, 0]])
    node = JsonableData(obj)
    node.store()
    assert node.is_stored

    loaded = load_node(node.pk)
    assert loaded is not node
    assert loaded.obj == obj


class ToDictClass:
    """Object that follows the ``to_dict`` / ``from_dict`` convention instead of ``as_dict``."""

    def __init__(self, value):
        self.value = value

    def to_dict(self):
        return {'value': self.value}

    @classmethod
    def from_dict(cls, dictionary):
        return cls(dictionary['value'])


@dataclasses.dataclass
class DataclassObj:
    """A plain dataclass, wrapped via ``dataclasses.asdict`` and rebuilt through its constructor."""

    x: int
    y: str


class PydanticObj(BaseModel):
    """A pydantic model, wrapped via ``model_dump`` and rebuilt through ``model_validate``."""

    a: int
    b: str


def test_wrap_object_with_to_dict():
    """An object exposing ``to_dict`` (not ``as_dict``) round-trips."""
    node = JsonableData(ToDictClass(7)).store()
    loaded = load_node(node.pk)
    assert isinstance(loaded.obj, ToDictClass)
    assert loaded.obj.value == 7


def test_wrap_dataclass():
    """A dataclass instance round-trips through ``asdict`` and its constructor."""
    node = JsonableData(DataclassObj(x=1, y='a')).store()
    loaded = load_node(node.pk)
    assert loaded.obj == DataclassObj(x=1, y='a')


def test_wrap_pydantic_model():
    """A pydantic model round-trips through ``model_dump`` and ``model_validate``."""
    node = JsonableData(PydanticObj(a=2, b='b')).store()
    loaded = load_node(node.pk)
    assert loaded.obj == PydanticObj(a=2, b='b')


def test_numpy_values_are_coerced():
    """Numpy scalars and arrays in the serialized dictionary are stored as JSON-native types."""
    obj = JsonableClass({'arr': numpy.array([1, 2, 3]), 'scalar': numpy.int64(5)})
    node = JsonableData(obj).store()
    loaded = load_node(node.pk)
    assert loaded.obj.data == {'arr': [1, 2, 3], 'scalar': 5}
