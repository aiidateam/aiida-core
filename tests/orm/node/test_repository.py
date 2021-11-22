# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,protected-access,no-member
"""Tests for the :mod:`aiida.orm.nodes.repository` module."""
import io
import pathlib

import pytest

from aiida.common import exceptions
from aiida.engine import ProcessState
from aiida.manage.caching import enable_caching
from aiida.orm import CalcJobNode, Data, load_node
from aiida.repository.backend import DiskObjectStoreRepositoryBackend, SandboxRepositoryBackend
from aiida.repository.common import File, FileType


@pytest.fixture
def cacheable_node():
    """Return a node that can be cached from."""
    node = CalcJobNode(process_type='aiida.calculations:core.arithmetic.add')
    node.set_process_state(ProcessState.FINISHED)
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    node.store()
    assert node.is_valid_cache

    return node


@pytest.mark.usefixtures('clear_database_before_test')
def test_initialization():
    """Test that the repository instance is lazily constructed."""
    node = Data()
    assert node.repository_metadata == {}
    assert node._repository_instance is None

    # Initialize just by calling the property
    assert isinstance(node._repository.backend, SandboxRepositoryBackend)


@pytest.mark.usefixtures('clear_database_before_test')
def test_unstored():
    """Test the repository for unstored nodes."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')

    assert isinstance(node._repository.backend, SandboxRepositoryBackend)
    assert node.repository_metadata == {}


@pytest.mark.usefixtures('clear_database_before_test')
def test_store():
    """Test the repository after storing."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    assert node.list_object_names() == ['relative']
    assert node.list_object_names('relative') == ['path']

    hash_unstored = node._repository.hash()
    metadata = node.repository_serialize()

    node.store()
    assert isinstance(node._repository.backend, DiskObjectStoreRepositoryBackend)
    assert node.repository_serialize() != metadata
    assert node._repository.hash() == hash_unstored


@pytest.mark.usefixtures('clear_database_before_test')
def test_load():
    """Test the repository after loading."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    node.store()

    hash_stored = node._repository.hash()
    metadata = node.repository_serialize()

    loaded = load_node(node.uuid)
    assert isinstance(node._repository.backend, DiskObjectStoreRepositoryBackend)
    assert node.repository_serialize() == metadata
    assert loaded._repository.hash() == hash_stored


@pytest.mark.usefixtures('clear_database_before_test')
def test_load_updated():
    """Test the repository after loading."""
    node = CalcJobNode()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    node.store()

    loaded = load_node(node.uuid)
    assert loaded.get_object_content('relative/path', mode='rb') == b'content'


@pytest.mark.usefixtures('clear_database_before_test')
def test_caching(cacheable_node):
    """Test the repository after a node is stored from the cache."""

    with enable_caching():
        cached = CalcJobNode(process_type='aiida.calculations:core.core.arithmetic.add')
        cached.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
        cached.store()

    assert cached.is_created_from_cache
    assert cached.get_cache_source() == cacheable_node.uuid
    assert cacheable_node.repository_metadata == cached.repository_metadata
    assert cacheable_node._repository.hash() == cached._repository.hash()


@pytest.mark.usefixtures('clear_database_before_test')
def test_clone():
    """Test the repository after a node is cloned from a stored node."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    node.store()

    clone = node.clone()
    assert clone.list_object_names('relative') == ['path']
    assert clone.get_object_content('relative/path', mode='rb') == b'content'

    clone.store()
    assert clone.list_object_names('relative') == ['path']
    assert clone.get_object_content('relative/path', mode='rb') == b'content'
    assert clone.repository_metadata == node.repository_metadata
    assert clone._repository.hash() == node._repository.hash()


@pytest.mark.usefixtures('clear_database_before_test')
def test_clone_unstored():
    """Test the repository after a node is cloned from an unstored node."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')

    clone = node.clone()
    assert clone.list_object_names('relative') == ['path']
    assert clone.get_object_content('relative/path', mode='rb') == b'content'

    clone.store()
    assert clone.list_object_names('relative') == ['path']
    assert clone.get_object_content('relative/path', mode='rb') == b'content'


@pytest.mark.usefixtures('clear_database_before_test')
def test_sealed():
    """Test the repository interface for a calculation node before and after it is sealed."""
    node = CalcJobNode()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    node.store()
    node.seal()

    with pytest.raises(exceptions.ModificationNotAllowed):
        node.put_object_from_filelike(io.BytesIO(b'content'), 'path')


@pytest.mark.usefixtures('clear_database_before_test')
def test_get_object_raises():
    """Test the ``NodeRepositoryMixin.get_object`` method when it is supposed to raise."""
    node = Data()

    with pytest.raises(TypeError, match=r'path `.*` is not a relative path.'):
        node.get_object('/absolute/path')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        node.get_object('non_existing_folder/file_a')

    with pytest.raises(FileNotFoundError, match=r'object with path `.*` does not exist.'):
        node.get_object('non_existant')


@pytest.mark.usefixtures('clear_database_before_test')
def test_get_object():
    """Test the ``NodeRepositoryMixin.get_object`` method."""
    node = CalcJobNode()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/file_b')

    file_object = node.get_object(None)
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.DIRECTORY

    file_object = node.get_object('relative')
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.DIRECTORY
    assert file_object.name == 'relative'

    file_object = node.get_object('relative/file_b')
    assert isinstance(file_object, File)
    assert file_object.file_type == FileType.FILE
    assert file_object.name == 'file_b'


@pytest.mark.usefixtures('clear_database_before_test')
def test_walk():
    """Test the ``NodeRepositoryMixin.walk`` method."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')

    results = []
    for root, dirnames, filenames in node.walk():
        results.append((root, sorted(dirnames), sorted(filenames)))

    assert sorted(results) == [
        (pathlib.Path('.'), ['relative'], []),
        (pathlib.Path('relative'), [], ['path']),
    ]

    # Check that the method still works after storing the node
    node.store()

    results = []
    for root, dirnames, filenames in node.walk():
        results.append((root, sorted(dirnames), sorted(filenames)))

    assert sorted(results) == [
        (pathlib.Path('.'), ['relative'], []),
        (pathlib.Path('relative'), [], ['path']),
    ]


@pytest.mark.usefixtures('clear_database_before_test')
def test_copy_tree(tmp_path):
    """Test the ``Repository.copy_tree`` method."""
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')

    node.copy_tree(tmp_path)
    dirpath = pathlib.Path(tmp_path / 'relative')
    filepath = dirpath / 'path'
    assert dirpath.is_dir()
    assert filepath.is_file()
    with node.open('relative/path', 'rb') as handle:
        assert filepath.read_bytes() == handle.read()
