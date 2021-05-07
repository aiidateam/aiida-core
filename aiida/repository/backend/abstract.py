# -*- coding: utf-8 -*-
"""Class that defines the abstract interface for an object repository.

The scope of this class is intentionally very narrow. Any backend implementation should merely provide the methods to
store binary blobs, or "objects", and return a string-based key that unique identifies the object that was just created.
This key should then be able to be used to retrieve the bytes of the corresponding object or to delete it.
"""
import abc
import contextlib
import hashlib
import io
import pathlib
import typing

from aiida.common.hashing import chunked_file_hash

__all__ = ('AbstractRepositoryBackend',)


class AbstractRepositoryBackend(metaclass=abc.ABCMeta):
    """Class that defines the abstract interface for an object repository.

    The repository backend only deals with raw bytes, both when creating new objects as well as when returning a stream
    or the content of an existing object. The encoding and decoding of the byte content should be done by the client
    upstream. The file repository backend is also not expected to keep any kind of file hierarchy but must be assumed
    to be a simple flat data store. When files are created in the file object repository, the implementation will return
    a string-based key with which the content of the stored object can be addressed. This key is guaranteed to be unique
    and persistent. Persisting the key or mapping it onto a virtual file hierarchy is again up to the client upstream.
    """

    @abc.abstractproperty
    def uuid(self) -> typing.Optional[str]:
        """Return the unique identifier of the repository."""

    @abc.abstractmethod
    def initialise(self, **kwargs) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """

    @abc.abstractproperty
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""

    @abc.abstractmethod
    def erase(self) -> None:
        """Delete the repository itself and all its contents.

        .. note:: This should not merely delete the contents of the repository but any resources it created. For
            example, if the repository is essentially a folder on disk, the folder itself should also be deleted, not
            just its contents.
        """

    @staticmethod
    def is_readable_byte_stream(handle) -> bool:
        return hasattr(handle, 'read') and hasattr(handle, 'mode') and 'b' in handle.mode

    def put_object_from_filelike(self, handle: typing.BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        if not isinstance(handle, io.BytesIO) and not self.is_readable_byte_stream(handle):
            raise TypeError(f'handle does not seem to be a byte stream: {type(handle)}.')
        return self._put_object_from_filelike(handle)

    @abc.abstractmethod
    def _put_object_from_filelike(self, handle: typing.BinaryIO) -> str:
        pass

    def put_object_from_file(self, filepath: typing.Union[str, pathlib.Path]) -> str:
        """Store a new object with contents of the file located at `filepath` on this file system.

        :param filepath: absolute path of file whose contents to copy to the repository.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        with open(filepath, mode='rb') as handle:
            return self.put_object_from_filelike(handle)

    @abc.abstractmethod
    def has_object(self, key: str) -> bool:
        """Return whether the repository has an object with the given key.

        :param key: fully qualified identifier for the object within the repository.
        :return: True if the object exists, False otherwise.
        """

    @contextlib.contextmanager
    def open(self, key: str) -> typing.Iterator[typing.BinaryIO]:  # type: ignore[return]
        """Open a file handle to an object stored under the given key.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param key: fully qualified identifier for the object within the repository.
        :return: yield a byte stream object.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        if not self.has_object(key):
            raise FileNotFoundError(f'object with key `{key}` does not exist.')

    def get_object_content(self, key: str) -> bytes:
        """Return the content of a object identified by key.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        with self.open(key) as handle:
            return handle.read()

    def get_object_hash(self, key: str) -> str:
        """Return the SHA-256 hash of an object stored under the given key.

        .. important::
            A SHA-256 hash should always be returned,
            to ensure consistency across different repository implementations.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        with self.open(key) as handle:
            return chunked_file_hash(handle, hashlib.sha256)

    def delete_object(self, key: str):
        """Delete the object from the repository.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be deleted.
        """
        if not self.has_object(key):
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
