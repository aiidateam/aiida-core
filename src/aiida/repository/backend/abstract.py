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
from collections.abc import Iterable, Iterator
from typing import Any, BinaryIO, List, Optional, Tuple, Union

from aiida.common.hashing import chunked_file_hash

__all__ = ('AbstractRepositoryBackend',)

InfoDictType = dict[str, Union[int, str, dict[str, int], dict[str, float]]]


class AbstractRepositoryBackend(metaclass=abc.ABCMeta):
    """Class that defines the abstract interface for an object repository.

    The repository backend only deals with raw bytes, both when creating new objects as well as when returning a stream
    or the content of an existing object. The encoding and decoding of the byte content should be done by the client
    upstream. The file repository backend is also not expected to keep any kind of file hierarchy but must be assumed
    to be a simple flat data store. When files are created in the file object repository, the implementation will return
    a string-based key with which the content of the stored object can be addressed. This key is guaranteed to be unique
    and persistent. Persisting the key or mapping it onto a virtual file hierarchy is again up to the client upstream.
    """

    @property
    @abc.abstractmethod
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository."""

    @property
    @abc.abstractmethod
    def key_format(self) -> Optional[str]:
        """Return the format for the keys of the repository.

        Important for when migrating between backends (e.g. archive -> main), as if they are not equal then it is
        necessary to re-compute all the `Node.base.repository.metadata` before importing (otherwise they will not match
        with the repository).
        """

    @abc.abstractmethod
    def initialise(self, **kwargs: Any) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """

    @property
    @abc.abstractmethod
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
    def is_readable_byte_stream(handle: Any) -> bool:
        return hasattr(handle, 'read') and hasattr(handle, 'mode') and 'b' in handle.mode

    def put_object_from_filelike(self, handle: BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        if not isinstance(handle, io.BufferedIOBase) and not self.is_readable_byte_stream(handle):
            raise TypeError(f'handle does not seem to be a byte stream: {type(handle)}.')
        return self._put_object_from_filelike(handle)

    @abc.abstractmethod
    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        raise NotImplementedError

    def put_object_from_file(self, filepath: Union[str, pathlib.Path]) -> str:
        """Store a new object with contents of the file located at `filepath` on this file system.

        :param filepath: absolute path of file whose contents to copy to the repository.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        with open(filepath, mode='rb') as handle:
            return self.put_object_from_filelike(handle)

    @abc.abstractmethod
    def has_objects(self, keys: List[str]) -> List[bool]:
        """Return whether the repository has an object with the given key.

        :param keys:
            list of fully qualified identifiers for objects within the repository.
        :return:
            list of logicals, in the same order as the keys provided, with value True if the respective
            object exists and False otherwise.
        """

    def has_object(self, key: str) -> bool:
        """Return whether the repository has an object with the given key.

        :param key: fully qualified identifier for the object within the repository.
        :return: True if the object exists, False otherwise.
        """
        return self.has_objects([key])[0]

    @abc.abstractmethod
    def list_objects(self) -> Iterable[str]:
        """Return iterable that yields all available objects by key.

        :return: An iterable for all the available object keys.
        """

    @abc.abstractmethod
    def get_info(self, detailed: bool = False) -> InfoDictType:
        """Returns relevant information about the content of the repository.

        :param detailed:
            flag to enable extra information (detailed=False by default, only returns basic information).

        :return: a dictionary with the information.
        """

    @abc.abstractmethod
    def open(self, key: str) -> contextlib.AbstractContextManager[BinaryIO]:
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

        # This method must be implemented by subclasses.
        raise NotImplementedError('Subclasses must implement open()')

    def get_object_content(self, key: str) -> bytes:
        """Return the content of a object identified by key.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        with self.open(key) as handle:
            return handle.read()

    @abc.abstractmethod
    def iter_object_streams(self, keys: Iterable[str]) -> Iterator[Tuple[str, BinaryIO]]:
        """Return an iterator over the (read-only) byte streams of objects identified by key.

        .. note:: handles should only be read within the context of this iterator.

        :param keys: fully qualified identifiers for the objects within the repository.
        :return: an iterator over the object byte streams.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if a file could not be opened.
        """
        raise NotImplementedError

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

    @abc.abstractmethod
    def delete_objects(self, keys: List[str]) -> None:
        """Delete the objects from the repository.

        :param keys: list of fully qualified identifiers for the objects within the repository.
        :raise FileNotFoundError: if any of the files does not exist.
        :raise OSError: if any of the files could not be deleted.
        """
        keys_exist = self.has_objects(keys)
        if not all(keys_exist):
            error_message = 'some of the keys provided do not correspond to any object in the repository:\n'
            for indx, key_exists in enumerate(keys_exist):
                if not key_exists:
                    error_message += f' > object with key `{keys[indx]}` does not exist.\n'
            raise FileNotFoundError(error_message)

    def delete_object(self, key: str) -> None:
        """Delete the object from the repository.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be deleted.
        """
        return self.delete_objects([key])
