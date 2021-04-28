# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using the ``disk-objectstore`` as the backend."""
import contextlib
import io

from disk_objectstore import Container

from aiida.common.lang import type_check

from .abstract import AbstractRepositoryBackend

__all__ = ('DiskObjectStoreRepositoryBackend',)


class DiskObjectStoreRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using the ``disk-object-store`` as the backend."""

    def __init__(self, container):
        type_check(container, Container)
        self._container = container

    @property
    def container(self):
        return self._container

    def put_object_from_filelike(self, handle: io.BufferedIOBase) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        super().put_object_from_filelike(handle)
        return self.container.add_object(handle.read())

    def has_object(self, key: str) -> bool:
        """Return whether the repository has an object with the given key.

        :param key: fully qualified identifier for the object within the repository.
        :return: True if the object exists, False otherwise.
        """
        return self.container.has_object(key)

    @contextlib.contextmanager
    def open(self, key: str) -> io.BufferedIOBase:
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
            yield handle

    def delete_object(self, key: str):
        """Delete the object from the repository.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be deleted.
        """
        super().delete_object(key)
        self.container.delete_objects([key])
