"""Tests for the :mod:`aiida.repository.backend.git` module."""

import io
import pathlib

import pytest

from aiida.repository.backend.git import GitRepositoryBackend


@pytest.fixture(scope='function')
def repository(tmp_path):
    """Return a GitRepositoryBackend instance.

    :param tmp_path: Temporary path fixture from pytest
    :return: An uninitialized GitRepositoryBackend instance
    """
    repo_path = tmp_path / 'git_repo'
    yield GitRepositoryBackend(repo_path)


@pytest.fixture(scope='function')
def initialized_repository(repository):
    """Return an initialized GitRepositoryBackend instance.

    :param repository: Uninitialized repository fixture
    :return: An initialized GitRepositoryBackend instance with some test data
    """
    repository.initialise()
    yield repository


def test_str(repository):
    """Test the ``__str__`` method."""
    # Before initialization
    str_repr = str(repository)
    assert 'GitRepository' in str_repr
    assert 'uninitialised' in str_repr

    # After initialization
    repository.initialise()
    str_repr = str(repository)
    assert 'GitRepository' in str_repr
    assert 'uninitialised' not in str_repr
    assert repository.uuid in str_repr


def test_uuid(repository):
    """Test the ``uuid`` property."""
    # Before initialization, UUID should be None
    assert repository.uuid is None

    # After initialization, UUID should be a string
    repository.initialise()
    assert isinstance(repository.uuid, str)
    assert len(repository.uuid) > 0

    # UUID should be persistent across repository instances
    uuid = repository.uuid
    new_instance = GitRepositoryBackend(repository._folder)
    assert new_instance.uuid == uuid


def test_key_format(repository):
    """Test the ``key_format`` property."""
    # Before initialization
    assert repository.key_format is None

    # After initialization, should return 'sha1'
    repository.initialise()
    assert repository.key_format == 'sha1'


def test_initialise(repository):
    """Test the ``initialise`` method and the ``is_initialised`` property."""
    # Should not be initialized initially
    assert not repository.is_initialised

    # Initialize the repository
    repository.initialise()
    assert repository.is_initialised

    # Re-initializing should be idempotent
    repository.initialise()
    assert repository.is_initialised


def test_put_object_from_filelike(initialized_repository):
    """Test the ``put_object_from_filelike`` method."""
    # Store a file
    content = b'Hello, World!'
    handle = io.BytesIO(content)
    key = initialized_repository.put_object_from_filelike(handle)

    # Key should be a SHA-1 hash (40 hex characters)
    assert isinstance(key, str)
    assert len(key) == 40
    assert all(c in '0123456789abcdef' for c in key)

    # Should be able to retrieve the object
    assert initialized_repository.has_object(key)


def test_put_object_from_filelike_raises(initialized_repository, generate_directory):
    """Test the ``put_object_from_filelike`` method when it should raise."""
    directory = generate_directory({'file_a': None})

    # Should raise TypeError for path-like object
    with pytest.raises(TypeError):
        initialized_repository.put_object_from_filelike(directory / 'file_a')

    # Should raise TypeError for string
    with pytest.raises(TypeError):
        initialized_repository.put_object_from_filelike(str(directory / 'file_a'))


def test_has_objects(initialized_repository):
    """Test the ``has_objects`` method."""
    # Store some objects
    keys = []
    for i in range(3):
        content = f'Content {i}'.encode()
        handle = io.BytesIO(content)
        key = initialized_repository.put_object_from_filelike(handle)
        keys.append(key)

    # Check that all objects exist
    exists = initialized_repository.has_objects(keys)
    assert exists == [True, True, True]

    # Check non-existent object
    fake_key = '0' * 40  # Valid SHA-1 format but non-existent
    exists = initialized_repository.has_objects([fake_key])
    assert exists == [False]

    # Mix of existing and non-existing
    mixed_keys = [keys[0], fake_key, keys[1]]
    exists = initialized_repository.has_objects(mixed_keys)
    assert exists == [True, False, True]


def test_open(initialized_repository):
    """Test the ``open`` method."""
    # Store an object
    content = b'Test content for reading'
    handle = io.BytesIO(content)
    key = initialized_repository.put_object_from_filelike(handle)

    # Read the object back
    with initialized_repository.open(key) as stream:
        assert isinstance(stream, io.BufferedIOBase)
        read_content = stream.read()
        assert read_content == content


def test_open_raises(initialized_repository):
    """Test the ``open`` method when it should raise."""
    # Non-existent object should raise FileNotFoundError
    fake_key = '0' * 40
    with pytest.raises(FileNotFoundError):
        with initialized_repository.open(fake_key):
            pass


def test_iter_object_streams(initialized_repository):
    """Test the ``iter_object_streams`` method."""
    # Store multiple objects
    test_data = {
        b'First file content',
        b'Second file content',
        b'Third file content',
    }

    keys = []
    for content in test_data:
        handle = io.BytesIO(content)
        key = initialized_repository.put_object_from_filelike(handle)
        keys.append(key)

    # Iterate over object streams
    retrieved_data = set()
    for key, stream in initialized_repository.iter_object_streams(keys):
        assert key in keys
        content = stream.read()
        retrieved_data.add(content)

    # Should have retrieved all data
    assert retrieved_data == test_data


def test_list_objects(initialized_repository):
    """Test the ``list_objects`` method."""
    # Empty repository
    objects = list(initialized_repository.list_objects())
    assert objects == []

    # Add some objects
    keys = []
    for i in range(5):
        content = f'Object {i}'.encode()
        handle = io.BytesIO(content)
        key = initialized_repository.put_object_from_filelike(handle)
        keys.append(key)

    # List should contain all added objects
    objects = list(initialized_repository.list_objects())
    assert len(objects) == 5
    assert set(objects) == set(keys)


def test_get_object_hash(initialized_repository):
    """Test the ``get_object_hash`` method."""
    import hashlib

    # Store an object
    content = b'Content for hashing'
    handle = io.BytesIO(content)
    key = initialized_repository.put_object_from_filelike(handle)

    # Get the SHA-256 hash
    sha256_hash = initialized_repository.get_object_hash(key)

    # Verify it's correct
    expected_hash = hashlib.sha256(content).hexdigest()
    assert sha256_hash == expected_hash


def test_get_object_hash_raises(initialized_repository):
    """Test the ``get_object_hash`` method when it should raise."""
    # Non-existent object should raise FileNotFoundError
    fake_key = '0' * 40
    with pytest.raises(FileNotFoundError):
        initialized_repository.get_object_hash(fake_key)


def test_delete_objects(initialized_repository):
    """Test the ``delete_objects`` method."""
    # Store some objects
    keys = []
    for i in range(3):
        content = f'Object {i}'.encode()
        handle = io.BytesIO(content)
        key = initialized_repository.put_object_from_filelike(handle)
        keys.append(key)

    # Delete objects
    initialized_repository.delete_objects(keys)

    # Objects still exist (Git limitation - no direct deletion)
    exists = initialized_repository.has_objects(keys)
    assert not any(exists)


def test_delete_objects_raises(initialized_repository):
    """Test the ``delete_objects`` method when it should raise."""
    # Deleting non-existent objects should raise FileNotFoundError
    fake_keys = ['0' * 40, '1' * 40]
    with pytest.raises(FileNotFoundError):
        initialized_repository.delete_objects(fake_keys)


def test_erase(repository):
    """Test the ``erase`` method."""
    # Initialize and add some data
    repository.initialise()
    content = io.BytesIO(b'Some content')
    repository.put_object_from_filelike(content)

    # Repository should exist
    assert repository._folder.exists()
    assert repository.is_initialised

    # Erase the repository
    repository.erase()

    # Repository should no longer exist
    assert not repository._folder.exists()
    assert not repository.is_initialised


def test_get_info(initialized_repository):
    """Test the ``get_info`` method."""
    # Empty repository
    info = initialized_repository.get_info()
    assert info['Backend'] == 'git'
    assert info['Hash algorithm (keys)'] == 'sha1'
    assert info['Hash algorithm (content)'] == 'sha256'
    assert info['Objects']['total'] == 0

    # Add some objects
    for i in range(3):
        content = f'Object {i}'.encode()
        handle = io.BytesIO(content)
        initialized_repository.put_object_from_filelike(handle)

    # Get info again
    info = initialized_repository.get_info(detailed=True)
    assert info['Objects']['total'] == 3


def test_deduplication(initialized_repository):
    """Test that identical content is deduplicated."""
    content = b'Duplicate content'

    # Store the same content twice
    handle1 = io.BytesIO(content)
    key1 = initialized_repository.put_object_from_filelike(handle1)

    handle2 = io.BytesIO(content)
    key2 = initialized_repository.put_object_from_filelike(handle2)

    # Keys should be identical (same content = same SHA-1)
    assert key1 == key2

    # Should only have one object in the repository
    objects = list(initialized_repository.list_objects())
    assert len(objects) == 1


def test_large_file(initialized_repository):
    """Test storing and retrieving a larger file."""
    # Create a 1MB file
    content = b'x' * (1024 * 1024)
    handle = io.BytesIO(content)
    key = initialized_repository.put_object_from_filelike(handle)

    # Verify it can be retrieved correctly
    with initialized_repository.open(key) as stream:
        retrieved = stream.read()
        assert len(retrieved) == len(content)
        assert retrieved == content


def test_binary_content(initialized_repository):
    """Test storing binary content (not just text)."""
    # Create binary content with all byte values
    content = bytes(range(256))
    handle = io.BytesIO(content)
    key = initialized_repository.put_object_from_filelike(handle)

    # Verify it's stored and retrieved correctly
    with initialized_repository.open(key) as stream:
        retrieved = stream.read()
        assert retrieved == content


def test_empty_file(initialized_repository):
    """Test storing an empty file."""
    content = b''
    handle = io.BytesIO(content)
    key = initialized_repository.put_object_from_filelike(handle)

    # Should still work
    assert initialized_repository.has_object(key)
    with initialized_repository.open(key) as stream:
        retrieved = stream.read()
        assert retrieved == content
