# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""
import contextlib
import os
import shutil
from typing import BinaryIO, Iterable, Iterator, List, Optional, Tuple
import uuid

from aiida.common.folders import SandboxFolder

from .abstract import AbstractRepositoryBackend

__all__ = ('SandboxRepositoryBackend',)


class SandboxRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using a sandbox folder on disk as the backend."""

    def __init__(self):
        self._sandbox: Optional[SandboxFolder] = None

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            return f'SandboxRepository: {self._sandbox.abspath if self._sandbox else "null"}'
        return 'SandboxRepository: <uninitialised>'

    def __del__(self):
        """Delete the entire sandbox folder if it was instantiated and still exists."""
        self.erase()

    @property
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository.

        .. note:: A sandbox folder does not have the concept of a unique identifier and so always returns ``None``.
        """
        return None

    @property
    def key_format(self) -> Optional[str]:
        return 'uuid4'

    def initialise(self, **kwargs) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """
        # Merely calling the property will cause the sandbox folder to be initialised.
        self.sandbox  # pylint: disable=pointless-statement

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""
        return isinstance(self._sandbox, SandboxFolder)

    @property
    def sandbox(self):
        """Return the sandbox instance of this repository."""
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

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
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

    def has_objects(self, keys: List[str]) -> List[bool]:
        result = []
        dirlist = os.listdir(self.sandbox.abspath)
        for key in keys:
            result.append(key in dirlist)
        return result

    @contextlib.contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        super().open(key)

        with self.sandbox.open(key, mode='rb') as handle:
            yield handle

    def iter_object_streams(self, keys: List[str]) -> Iterator[Tuple[str, BinaryIO]]:
        for key in keys:
            with self.open(key) as handle:  # pylint: disable=not-context-manager
                yield key, handle

    def delete_objects(self, keys: List[str]) -> None:
        super().delete_objects(keys)
        for key in keys:
            os.remove(os.path.join(self.sandbox.abspath, key))

    def list_objects(self) -> Iterable[str]:
        return self.sandbox.get_content_list()

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        raise NotImplementedError

    def get_info(self, detailed: bool = False, **kwargs) -> dict:
        raise NotImplementedError
