# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""
import contextlib
import io
import os
import shutil
import uuid

from .abstract import AbstractRepositoryBackend

__all__ = ('SandboxRepositoryBackend',)


class SandboxRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""

    def __init__(self):
        self._sandbox = None

    def __del__(self):
        """Delete the entire sandbox folder if it was instantiated and still exists."""
        if getattr(self, '_sandbox', None) is not None:
            try:
                shutil.rmtree(self.sandbox.abspath)
            except FileNotFoundError:
                pass

    @property
    def sandbox(self):
        """Return the sandbox instance of this repository."""
        from aiida.common.folders import SandboxFolder

        if self._sandbox is None:
            self._sandbox = SandboxFolder()

        return self._sandbox

    def put_object_from_filelike(self, handle: io.BufferedIOBase) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        super().put_object_from_filelike(handle)

        key = str(uuid.uuid4())
        filepath = os.path.join(self.sandbox.abspath, key)

        with open(filepath, 'wb') as target:
            shutil.copyfileobj(handle, target)

        return key

    def has_object(self, key: str) -> bool:
        """Return whether the repository has an object with the given key.

        :param key: fully qualified identifier for the object within the repository.
        :return: True if the object exists, False otherwise.
        """
        return key in os.listdir(self.sandbox.abspath)

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

        with self.sandbox.open(key, mode='rb') as handle:
            yield handle

    def delete_object(self, key: str):
        """Delete the object from the repository.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be deleted.
        """
        super().delete_object(key)
        os.remove(os.path.join(self.sandbox.abspath, key))
