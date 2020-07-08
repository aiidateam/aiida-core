# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Tests for the :mod:`aiida.repository.common` module."""
import pytest

from aiida.repository import File, FileType


@pytest.fixture
def file_object() -> File:
    """Test fixture to create and return a ``File`` instance."""
    name = 'relative'
    file_type = FileType.FILE
    key = 'abcdef'
    objects = {'sub': File()}
    return File(name, file_type, key, objects)


def test_constructor():
    """Test the constructor defaults."""
    file_object = File()
    assert file_object.name == ''
    assert file_object.file_type == FileType.DIRECTORY
    assert file_object.key is None
    assert file_object.objects == {}


def test_constructor_kwargs(file_object: File):
    """Test the constructor specifying specific keyword arguments."""
    name = 'relative'
    file_type = FileType.FILE
    key = 'abcdef'
    objects = {'sub': File()}
    file_object = File(name, file_type, key, objects)

    assert file_object.name == 'relative'
    assert file_object.file_type == FileType.FILE
    assert file_object.key == 'abcdef'
    assert file_object.objects == objects


def test_constructor_kwargs_invalid():
    """Test the constructor specifying invalid keyword arguments."""
    name = 'relative'
    file_type = FileType.FILE
    key = 'abcdef'
    objects = {'sub': File()}

    with pytest.raises(TypeError):
        File(None, file_type, key, objects)

    with pytest.raises(TypeError):
        File(name, None, key, objects)

    with pytest.raises(TypeError):
        File(name, file_type, 123, objects)

    with pytest.raises(TypeError):
        File(name, file_type, key, {'sub': File, 'wrong': 'type'})


def test_serialize(file_object: File):
    """Test the ``File.serialize`` method."""
    expected = {
        'name': file_object.name,
        'file_type': file_object.file_type.value,
        'key': file_object.key,
        'objects': {
            'sub': {
                'name': '',
                'file_type': FileType.DIRECTORY.value,
                'key': None,
                'objects': {},
            }
        }
    }

    assert file_object.serialize() == expected


def test_serialize_roundtrip(file_object: File):
    """Test the serialization round trip."""
    serialized = file_object.serialize()
    reconstructed = File.from_serialized(serialized)

    assert isinstance(reconstructed, File)
    assert file_object == reconstructed


def test_eq():
    """Test the ``File.__eq__`` method."""
    file_object = File()

    # Identity operation
    assert file_object == file_object  # pylint: disable=comparison-with-itself

    # Identical default copy
    assert file_object == File()

    # Identical copy with different arguments
    assert File(name='custom', file_type=FileType.FILE) == File(name='custom', file_type=FileType.FILE)

    # Identical copies with nested objects
    assert File(objects={'sub': File()}) == File(objects={'sub': File()})

    assert file_object != File(name='custom')
    assert file_object != File(file_type=FileType.FILE)
    assert file_object != File(key='123456')
    assert file_object != File(objects={'sub': File()})
