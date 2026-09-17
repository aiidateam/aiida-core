"""Tests for the :class:`aiida.orm.nodes.data.jsonable.JsonableData` data type."""

import datetime
import math

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
    """Test the ``JsonableData`` constructor raises if object does not implement ``as_dict``."""

    class InvalidClass:
        pass

    with pytest.raises(
        TypeError, match=r'the `obj` argument does not have the required `as_dict` or `model_dump` method.'
    ):
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


class Point(BaseModel):
    """A model that says how it is written the way pydantic says it."""

    x: int
    y: int = 0


class Shape(BaseModel):
    """And one holding another, so that the nesting is carried too."""

    label: str
    origin: Point = Point(x=0)


def test_pydantic_model():
    """A pydantic model says `model_dump` and `model_validate` where this asks for `as_dict` and `from_dict`."""
    node = JsonableData(Shape(label='square')).store()
    loaded = load_node(node.pk)

    assert isinstance(loaded.obj, Shape)
    assert loaded.obj.label == 'square'
    assert isinstance(loaded.obj.origin, Point), 'the model it holds came back as well'
    assert (loaded.obj.origin.x, loaded.obj.origin.y) == (0, 0)


def test_pydantic_model_unstored():
    """An unstored node returns the very object it was given, as it does for anything else."""
    shape = Shape(label='circle')

    assert JsonableData(shape).obj is shape


def test_pydantic_model_in_a_node_model():
    """The node's own model carries what the object holds, which is read the same way as everything else."""
    node = JsonableData(Shape(label='square')).store()

    attributes = node.to_model().attributes

    assert (attributes.label, attributes.origin) == ('square', {'x': 0, 'y': 0})
