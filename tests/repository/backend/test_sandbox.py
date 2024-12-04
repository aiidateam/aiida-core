"""Tests for the :mod:`aiida.repository.backend.sandbox` module."""

import io
import pathlib

import pytest

from aiida.repository.backend.sandbox import SandboxRepositoryBackend


@pytest.fixture(scope='function')
def repository():
    """Return a `SandboxRepositoryBackend`."""
    yield SandboxRepositoryBackend()


def test_str(repository):
    """Test the ``__str__`` method."""
    assert str(repository)
    repository.initialise()
    assert str(repository)


def test_uuid(repository):
    """Test the ``uuid`` property."""
    assert repository.uuid is None


def test_initialise(repository):
    """Test the ``initialise`` method and the ``is_initialised`` property."""
    assert not repository.is_initialised
    repository.initialise()
    assert repository.is_initialised


def test_put_object_from_filelike_raises(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method when it should raise."""
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # Path-like object

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # String

    with pytest.raises(TypeError):
        with open(directory / 'file_a', encoding='utf-8') as handle:
            repository.put_object_from_filelike(handle)  # Not in binary mode


def test_put_object_from_filelike(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method."""
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert isinstance(key, str)


def test_has_object(repository, generate_directory):
    """Test the ``Repository.has_object`` method."""
    directory = generate_directory({'file_a': None})

    assert not repository.has_object('non_existant')

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)


def test_open_raise(repository):
    """Test the ``Repository.open`` method when it should raise."""
    with pytest.raises(FileNotFoundError):
        with repository.open('non_existant'):
            pass


def test_open(repository, generate_directory):
    """Test the ``Repository.open`` method."""
    directory = generate_directory({'file_a': b'content_a', 'relative': {'file_b': b'content_b'}})

    with open(directory / 'file_a', 'rb') as handle:
        key_a = repository.put_object_from_filelike(handle)

    with open(directory / 'relative/file_b', 'rb') as handle:
        key_b = repository.put_object_from_filelike(handle)

    with repository.open(key_a) as handle:
        assert isinstance(handle, io.BufferedReader)

    with repository.open(key_a) as handle:
        assert handle.read() == b'content_a'

    with repository.open(key_b) as handle:
        assert handle.read() == b'content_b'


def test_iter_object_streams(repository):
    """Test the ``Repository.iter_object_streams`` method."""
    key = repository.put_object_from_filelike(io.BytesIO(b'content'))

    for _key, stream in repository.iter_object_streams([key]):
        assert _key == key
        assert stream.read() == b'content'


def test_delete_object(repository, generate_directory):
    """Test the ``Repository.delete_object`` method."""
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)

    repository.delete_object(key)
    assert not repository.has_object(key)


def test_erase(repository, generate_directory):
    """Test the ``Repository.erase`` method."""
    repository.initialise()
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)

    dirpath = repository.sandbox.abspath
    repository.erase()

    assert not pathlib.Path(dirpath).exists()
    assert not repository.is_initialised


def test_cleanup():
    """Test that the contents of the repository are deleted when the object is deleted.

    .. note:: cannot use the repository fixture for this, because in that case the fixture will hold a reference and the
        del won't be effectuated until after the end of the scope of this test function, meaning that the final check
        will fail as the sandbox won't have been erased yet.
    """
    repository = SandboxRepositoryBackend()
    dirpath = pathlib.Path(repository.sandbox.abspath)

    assert dirpath.exists()
    del repository
    assert not dirpath.exists()


def test_get_object_hash(repository, generate_directory):
    """Test the ``Repository.get_object_hash`` returns the expected value."""
    repository.initialise()
    directory = generate_directory({'file_a': b'content'})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.get_object_hash(key) == 'ed7002b439e9ac845f22357d822bac1444730fbdb6016d3ec9432297b9ec9f73'


def test_list_objects(repository, generate_directory):
    """Test the ``Repository.delete_object`` method."""
    repository.initialise()
    keylist = []

    directory = generate_directory({'file_a': b'content a'})
    with open(directory / 'file_a', 'rb') as handle:
        keylist.append(repository.put_object_from_filelike(handle))

    directory = generate_directory({'file_b': b'content b'})
    with open(directory / 'file_b', 'rb') as handle:
        keylist.append(repository.put_object_from_filelike(handle))

    assert sorted(list(repository.list_objects())) == sorted(keylist)


def test_key_format(repository):
    """Test the ``key_format`` property."""
    repository.initialise()
    assert repository.key_format == 'uuid4'
