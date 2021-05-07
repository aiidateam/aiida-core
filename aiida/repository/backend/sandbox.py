# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""
import contextlib
import os
import shutil
import typing
import uuid

from .abstract import AbstractRepositoryBackend

__all__ = ('SandboxRepositoryBackend',)


class SandboxRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""

    def __init__(self):
        from aiida.common.folders import SandboxFolder
        self._sandbox: typing.Optional[SandboxFolder] = None

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            return f'SandboxRepository: {self._sandbox.abspath if self._sandbox else "null"}'
        return 'SandboxRepository: <uninitialised>'

    def __del__(self):
        """Delete the entire sandbox folder if it was instantiated and still exists."""
        self.erase()

    @property
    def uuid(self) -> typing.Optional[str]:
        """Return the unique identifier of the repository.

        .. note:: A sandbox folder does not have the concept of a unique identifier and so always returns ``None``.
        """
        return None

    def initialise(self, **kwargs) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """
        # Merely calling the property will cause the sandbox folder to be initialised.
        self.sandbox  # pylint: disable=pointless-statement

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""
        from aiida.common.folders import SandboxFolder
        return isinstance(self._sandbox, SandboxFolder)

    @property
    def sandbox(self):
        """Return the sandbox instance of this repository."""
        from aiida.common.folders import SandboxFolder

        if self._sandbox is None:
            self._sandbox = SandboxFolder()

        return self._sandbox

    def erase(self):
        """Delete the repository itself and all its contents."""
        if getattr(self, '_sandbox', None) is not None:
            try:
                shutil.rmtree(self.sandbox.abspath)
            except FileNotFoundError:
                pass
            finally:
                self._sandbox = None

    def _put_object_from_filelike(self, handle: typing.BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
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
    def open(self, key: str) -> typing.Iterator[typing.BinaryIO]:
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
