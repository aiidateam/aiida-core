"""Tests for the :mod:`aiida.repository.common` module."""

import pytest

from aiida.repository import File, FileType


@pytest.fixture
def file_object() -> File:
    """Test fixture to create and return a ``File`` instance."""
    name = 'relative'
    file_type = FileType.DIRECTORY
    key = None
    objects = {'sub': File('sub', file_type=FileType.FILE, key='abcdef')}
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
    file_type = FileType.DIRECTORY
    key = None
    objects = {'sub': File()}
    file_object = File(name, file_type, key, objects)

    assert file_object.name == name
    assert file_object.file_type == file_type
    assert file_object.key == key
    assert file_object.objects == objects

    name = 'relative'
    file_type = FileType.FILE
    key = 'abcdef'
    file_object = File(name, file_type, key, None)

    assert file_object.name == name
    assert file_object.file_type == file_type
    assert file_object.key == key
    assert file_object.objects == {}


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

    with pytest.raises(ValueError, match=r'an object of type `FileType.FILE` cannot define any objects.'):
        File(name, FileType.FILE, key, {})

    with pytest.raises(ValueError, match=r'an object of type `FileType.DIRECTORY` cannot define a key.'):
        File(name, FileType.DIRECTORY, key, {})


def test_serialize():
    """Test the ``File.serialize`` method."""
    objects = {
        'empty': File('empty', file_type=FileType.DIRECTORY),
        'file.txt': File('file.txt', file_type=FileType.FILE, key='abcdef'),
    }
    file_object = File(file_type=FileType.DIRECTORY, objects=objects)

    expected = {
        'o': {
            'empty': {},
            'file.txt': {
                'k': 'abcdef',
            },
        }
    }

    assert file_object.serialize() == expected


def test_serialize_roundtrip(file_object: File):
    """Test the serialization round trip."""
    serialized = file_object.serialize()
    reconstructed = File.from_serialized(serialized, file_object.name)

    assert isinstance(reconstructed, File)
    assert file_object == reconstructed


def test_eq():
    """Test the ``File.__eq__`` method."""
    file_object = File()

    # Identity operation
    assert file_object == file_object  # noqa: PLR0124

    # Identical default copy
    assert file_object == File()

    # Identical copy with different arguments
    assert File(name='custom', file_type=FileType.FILE) == File(name='custom', file_type=FileType.FILE)

    # Identical copies with nested objects
    assert File(objects={'sub': File()}) == File(objects={'sub': File()})

    assert file_object != File(name='custom')
    assert file_object != File(file_type=FileType.FILE)
    assert file_object != File(key='123456', file_type=FileType.FILE)
    assert file_object != File(objects={'sub': File()})

    # Test ordering of nested files:
    objects = {
        'empty': File('empty', file_type=FileType.DIRECTORY),
        'file.txt': File('file.txt', file_type=FileType.FILE, key='abcdef'),
    }
    file_object_a = File(file_type=FileType.DIRECTORY, objects=objects)
    objects = {
        'file.txt': File('file.txt', file_type=FileType.FILE, key='abcdef'),
        'empty': File('empty', file_type=FileType.DIRECTORY),
    }
    file_object_b = File(file_type=FileType.DIRECTORY, objects=objects)

    assert file_object_a == file_object_b
