"""Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""

from __future__ import annotations

import contextlib
import os
import pathlib
import shutil
import typing as t
import uuid

from aiida.common.folders import SandboxFolder

from .abstract import AbstractRepositoryBackend

__all__ = ('SandboxRepositoryBackend',)


class SandboxRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""

    def __init__(self, filepath: str | None = None):
        """Construct a new instance.

        :param filepath: The path to the directory in which the sandbox folder should be created.
        """
        self._sandbox: SandboxFolder | None = None
        self._filepath: str | None = filepath

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            return f'SandboxRepository: {self._sandbox.abspath if self._sandbox else "null"}'
        return 'SandboxRepository: <uninitialised>'

    def __del__(self) -> None:
        """Delete the entire sandbox folder if it was instantiated and still exists."""
        self.erase()

    @property
    def uuid(self) -> str | None:
        """Return the unique identifier of the repository.

        .. note:: A sandbox folder does not have the concept of a unique identifier and so always returns ``None``.
        """
        return None

    @property
    def key_format(self) -> str | None:
        return 'uuid4'

    def initialise(self, **kwargs: t.Any) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """
        # Merely calling the property will cause the sandbox folder to be initialised.
        self.sandbox

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""
        return isinstance(self._sandbox, SandboxFolder)

    @property
    def sandbox(self) -> SandboxFolder:
        """Return the sandbox instance of this repository."""
        if self._sandbox is None:
            self._sandbox = SandboxFolder(filepath=pathlib.Path(self._filepath) if self._filepath is not None else None)

        return self._sandbox

    def erase(self) -> None:
        """Delete the repository itself and all its contents."""
        if getattr(self, '_sandbox', None) is not None:
            try:
                shutil.rmtree(self.sandbox.abspath)
            except FileNotFoundError:
                pass
            finally:
                self._sandbox = None

    def _put_object_from_filelike(self, handle: t.BinaryIO) -> str:
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

    def has_objects(self, keys: list[str]) -> list[bool]:
        result = []
        dirlist = os.listdir(self.sandbox.abspath)
        for key in keys:
            result.append(key in dirlist)
        return result

    @contextlib.contextmanager
    def open(self, key: str) -> t.Iterator[t.BinaryIO]:
        super().open(key)

        with self.sandbox.open(key, mode='rb') as handle:
            yield handle

    def iter_object_streams(self, keys: t.Iterable[str]) -> t.Iterator[tuple[str, t.BinaryIO]]:
        for key in keys:
            with self.open(key) as handle:
                yield key, handle

    def delete_objects(self, keys: list[str]) -> None:
        super().delete_objects(keys)
        for key in keys:
            os.remove(os.path.join(self.sandbox.abspath, key))

    def list_objects(self) -> t.Iterable[str]:
        return self.sandbox.get_content_list()

    def get_info(self, detailed: bool = False) -> t.NoReturn:
        raise NotImplementedError
