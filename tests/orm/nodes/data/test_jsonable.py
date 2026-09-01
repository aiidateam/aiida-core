"""Tests for the :class:`aiida.orm.nodes.data.jsonable.JsonableData` data type."""

import datetime
import math
from typing import Any

import pytest
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
    """Test the ``JsonableData`` constructor raises if object does not implement ``as_dict``."""

    class InvalidClass:
        pass

    with pytest.raises(TypeError, match=r'the `obj` argument does not have the required `as_dict` method.'):
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

    with pytest.raises(ImportError, match='the objects module `not\\.existing` can not be imported'):
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


class _MsonableWithRequiredKeys:
    """Class that requires @class and @module to be present in from_dict."""

    def __init__(self, data: Any) -> None:
        self._data = data

    @property
    def data(self) -> Any:
        return self._data

    def as_dict(self) -> dict[str, Any]:
        return {
            '@module': self.__class__.__module__,
            '@class': self.__class__.__name__,
            'data': self._data,
        }

    @classmethod
    def from_dict(cls, dictionary: dict[str, Any]) -> '_MsonableWithRequiredKeys':
        if '@module' not in dictionary or '@class' not in dictionary:
            msg = '`@module` and `@class` must be present in serialized dictionary'
            raise KeyError(msg)
        return cls(dictionary['data'])


def test_msonable_preserves_class_and_module():
    """Test that `@class` and `@module` are preserved in the dictionary passed to `from_dict`."""
    obj = _MsonableWithRequiredKeys('test_data')
    node = JsonableData(obj)
    node.store()

    loaded = load_node(node.pk)
    assert loaded.obj.data == 'test_data'


def test_invalid_reserved_key():
    """Test that @-prefixed keys other than MSONable reserved ones raise ValueError."""

    class BadClass:

        def as_dict(self) -> dict[str, Any]:
            return {'@custom': 'bad', 'value': 1}

        @classmethod
        def from_dict(cls, d: dict[str, Any]) -> 'BadClass':
            return cls()

    with pytest.raises(ValueError, match=r'invalid `@`-prefixed keys'):
        JsonableData(BadClass())




