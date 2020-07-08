# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,invalid-name
"""Tests for the :mod:`aiida.repository.backend.sandbox` module."""
import io
import os

import pytest

from aiida.repository.backend.sandbox import SandboxRepositoryBackend


@pytest.fixture(scope='function')
def repository():
    """Return a `SandboxRepositoryBackend`."""
    yield SandboxRepositoryBackend()


def test_put_object_from_filelike_raises(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method when it should raise."""
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # Path-like object

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # String

    with pytest.raises(TypeError):
        with open(directory / 'file_a') as handle:
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


def test_delete_object(repository, generate_directory):
    """Test the ``Repository.delete_object`` method."""
    directory = generate_directory({'file_a': None})

    with open(directory / 'file_a', 'rb') as handle:
        key = repository.put_object_from_filelike(handle)

    assert repository.has_object(key)

    repository.delete_object(key)
    assert not repository.has_object(key)


def test_cleanup():
    """Test that the contents of the repository are deleted when the object is deleted.

    .. note:: cannot use the repository fixture for this, because in that case the fixture will hold a reference and the
        del won't be effectuated until after the end of the scope of this test function, meaning that the final check
        will fail as the sandbox won't have been erased yet.
    """
    repository = SandboxRepositoryBackend()
    dirpath = repository.sandbox.abspath

    assert os.path.isdir(dirpath)
    del repository
    assert not os.path.isdir(dirpath)
