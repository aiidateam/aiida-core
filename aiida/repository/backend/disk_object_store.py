# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using the ``disk-objectstore`` as the backend."""
import contextlib
import shutil
from typing import BinaryIO, Iterable, Iterator, List, Optional, Tuple

from disk_objectstore import Container

from aiida.common.lang import type_check

from .abstract import AbstractRepositoryBackend

__all__ = ('DiskObjectStoreRepositoryBackend',)


class DiskObjectStoreRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using the ``disk-object-store`` as the backend."""

    def __init__(self, container):
        type_check(container, Container)
        self._container = container

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            return f'DiskObjectStoreRepository: {self.container.container_id} | {self.container.get_folder()}'
        return 'DiskObjectStoreRepository: <uninitialised>'

    @property
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository."""
        if not self.is_initialised:
            return None
        return self.container.container_id

    @property
    def key_format(self) -> Optional[str]:
        return self.container.hash_type

    def initialise(self, **kwargs) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """
        self.container.init_container(**kwargs)

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""
        return self.container.is_initialised

    @property
    def container(self) -> Container:
        return self._container

    def erase(self):
        """Delete the repository itself and all its contents."""
        try:
            shutil.rmtree(self.container.get_folder())
        except FileNotFoundError:
            pass

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        return self.container.add_streamed_object(handle)

    def has_objects(self, keys: List[str]) -> List[bool]:
        return self.container.has_objects(keys)

    @contextlib.contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        """Open a file handle to an object stored under the given key.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param key: fully qualified identifier for the object within the repository.
        :return: yield a byte stream object.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        super().open(key)

        with self.container.get_object_stream(key) as handle:
            yield handle  # type: ignore[misc]

    def iter_object_streams(self, keys: List[str]) -> Iterator[Tuple[str, BinaryIO]]:
        with self.container.get_objects_stream_and_meta(keys) as triplets:
            for key, stream, _ in triplets:
                assert stream is not None
                yield key, stream  # type: ignore[misc]

    def delete_objects(self, keys: List[str]) -> None:
        super().delete_objects(keys)
        self.container.delete_objects(keys)

    def list_objects(self) -> Iterable[str]:
        return self.container.list_all_objects()

    def get_object_hash(self, key: str) -> str:
        """Return the SHA-256 hash of an object stored under the given key.

        .. important::
            A SHA-256 hash should always be returned,
            to ensure consistency across different repository implementations.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.

        """
        if not self.has_object(key):
            raise FileNotFoundError(key)
        if self.container.hash_type != 'sha256':
            return super().get_object_hash(key)
        return key
