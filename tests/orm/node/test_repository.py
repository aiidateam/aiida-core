# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,protected-access
"""Tests for the :mod:`aiida.orm.nodes.repository` module."""
import io

import pytest

from aiida.engine import ProcessState
from aiida.manage.caching import enable_caching
from aiida.orm import load_node, CalcJobNode, Data
from aiida.repository.backend import DiskObjectStoreRepositoryBackend, SandboxRepositoryBackend


@pytest.fixture
def cacheable_node():
    """Return a node that can be cached from."""
    node = CalcJobNode(process_type='aiida.calculations:arithmetic.add')
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
    node = Data()
    node.put_object_from_filelike(io.BytesIO(b'content'), 'relative/path')
    node.store()

    loaded = load_node(node.uuid)
    assert loaded.get_object_content('relative/path', mode='rb') == b'new_content'


@pytest.mark.usefixtures('clear_database_before_test')
def test_caching(cacheable_node):
    """Test the repository after a node is stored from the cache."""

    with enable_caching():
        cached = CalcJobNode(process_type='aiida.calculations:arithmetic.add')
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
