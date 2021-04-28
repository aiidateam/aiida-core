# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name,invalid-name
"""Tests for the :mod:`aiida.repository.backend.abstract` module."""
import io
import tempfile

import pytest

from aiida.repository.backend import AbstractRepositoryBackend


class RepositoryBackend(AbstractRepositoryBackend):
    """Concrete implementation of ``AbstractRepositoryBackend``."""

    def has_object(self, key):
        return True


@pytest.fixture(scope='function')
def repository():
    """Return a `RepositoryBackend`."""
    yield RepositoryBackend()


def test_put_object_from_filelike_raises(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method raises for invalid handle type."""
    directory = generate_directory({'file_a': None})

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(directory / 'file_a')  # Path-like object

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(str(directory / 'file_a'))  # String

    with pytest.raises(TypeError):
        with open(directory / 'file_a') as handle:
            repository.put_object_from_filelike(handle)  # Not in binary mode

    with pytest.raises(TypeError):
        repository.put_object_from_filelike(io.StringIO('content'))  # Not a binary stream

    with pytest.raises(TypeError):
        with tempfile.TemporaryFile(mode='r') as handle:
            repository.put_object_from_filelike(handle)  # Not in binary mode


def test_put_object_from_filelike(repository, generate_directory):
    """Test the ``Repository.put_object_from_filelike`` method for valid handle types."""
    directory = generate_directory({'file_a': b'content'})

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle)

    repository.put_object_from_filelike(io.BytesIO(b'content'))

    with tempfile.TemporaryFile('rb') as handle:
        repository.put_object_from_filelike(handle)


def test_put_object_from_file(repository, generate_directory):
    """Test the ``Repository.put_object_from_file`` method for valid filepath types."""
    directory = generate_directory({'file_a': b'content'})

    with open(directory / 'file_a', 'rb') as handle:
        repository.put_object_from_filelike(handle)

    repository.put_object_from_file(directory / 'file_a')
    repository.put_object_from_file(str(directory / 'file_a'))
