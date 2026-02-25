"""Tests for the :mod:`aiida.repository.backend.abstract` module."""

import contextlib
import io
import tempfile
from typing import BinaryIO, Iterable, List, Optional

import pytest

from aiida.repository.backend import AbstractRepositoryBackend


class RepositoryBackend(AbstractRepositoryBackend):
    """Concrete implementation of ``AbstractRepositoryBackend``."""

    @property
    def key_format(self) -> Optional[str]:
        return None

    @property
    def uuid(self) -> Optional[str]:
        return None

    def initialise(self, **kwargs) -> None:
        return

    def erase(self):
        raise NotImplementedError

    @property
    def is_initialised(self) -> bool:
        return True

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        return 'key'

    def delete_objects(self, keys: List[str]) -> None:
        super().delete_objects(keys)

    def has_objects(self, keys: List[str]) -> List[bool]:
        return [True]

    def list_objects(self) -> Iterable[str]:
        raise NotImplementedError

    def iter_object_streams(self, keys: Iterable[str]):
        raise NotImplementedError

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        raise NotImplementedError

    def get_info(self, detailed: bool = False, **kwargs) -> dict:
        raise NotImplementedError

    def open(self, key: str) -> contextlib.AbstractContextManager[BinaryIO]:
        """Minimal implementation required because open() is now abstract."""
        if not self.has_object(key):
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
        return contextlib.nullcontext(io.BytesIO(b'test'))


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
        with open(directory / 'file_a', encoding='utf8') as handle:
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


def test_passes_to_batch(repository, monkeypatch):
    """Checks that the single object operations call the batch operations."""

    def mock_batch_operation(self, keys):
        raise NotImplementedError('this method was intentionally not implemented')

    monkeypatch.setattr(RepositoryBackend, 'has_objects', mock_batch_operation)
    with pytest.raises(NotImplementedError) as execinfo:
        repository.has_object('object_key')
    assert str(execinfo.value) == 'this method was intentionally not implemented'

    monkeypatch.undo()

    monkeypatch.setattr(RepositoryBackend, 'delete_objects', mock_batch_operation)
    with pytest.raises(NotImplementedError) as execinfo:
        repository.delete_object('object_key')
    assert str(execinfo.value) == 'this method was intentionally not implemented'


def test_delete_objects_test(repository, monkeypatch):
    """Checks that the super of delete_objects will check for existence of the files."""

    def has_objects_mock(self, keys):
        return [False for key in keys]

    monkeypatch.setattr(RepositoryBackend, 'has_objects', has_objects_mock)
    with pytest.raises(FileNotFoundError) as execinfo:
        repository.delete_objects(['object_key'])
    assert 'exist' in str(execinfo.value)
    assert 'object_key' in str(execinfo.value)
