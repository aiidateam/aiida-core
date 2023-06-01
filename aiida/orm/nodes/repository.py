# -*- coding: utf-8 -*-
"""Interface to the file repository of a node instance."""
import contextlib
import copy
import io
import pathlib
import tempfile
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, Iterable, Iterator, List, Optional, TextIO, Tuple, Union

from aiida.common import exceptions
from aiida.manage import get_config_option
from aiida.repository import File, Repository
from aiida.repository.backend import SandboxRepositoryBackend

if TYPE_CHECKING:
    from .node import Node

__all__ = ('NodeRepository',)

FilePath = Union[str, pathlib.PurePosixPath]


class NodeRepository:
    """Interface to the file repository of a node instance.

    This is the compatibility layer between the `Node` class and the `Repository` class. The repository in principle has
    no concept of immutability, so it is implemented here. Any mutating operations will raise a `ModificationNotAllowed`
    exception if the node is stored. Otherwise the operation is just forwarded to the repository instance.

    The repository instance keeps an internal mapping of the file hierarchy that it maintains, starting from an empty
    hierarchy if the instance was constructed normally, or from a specific hierarchy if reconstructred through the
    ``Repository.from_serialized`` classmethod. This is only the case for stored nodes, because unstored nodes do not
    have any files yet when they are constructed. Once the node get's stored, the repository is asked to serialize its
    metadata contents which is then stored in the ``repository_metadata`` field of the backend node.
    This layer explicitly does not update the metadata of the node on a mutation action.
    The reason is that for stored nodes these actions are anyway forbidden and for unstored nodes,
    the final metadata will be stored in one go, once the node is stored,
    so there is no need to keep updating the node metadata intermediately.
    Note that this does mean that ``repository_metadata`` does not give accurate information,
    as long as the node is not yet stored.
    """

    def __init__(self, node: 'Node') -> None:
        """Construct a new instance of the repository interface."""
        self._node: 'Node' = node
        self._repository_instance: Optional[Repository] = None

    @property
    def metadata(self) -> Dict[str, Any]:
        """Return the repository metadata, representing the virtual file hierarchy.

        Note, this is only accurate if the node is stored.

        :return: the repository metadata
        """
        return self._node.backend_entity.repository_metadata

    def _update_repository_metadata(self):
        """Refresh the repository metadata of the node if it is stored."""
        if self._node.is_stored:
            self._node.backend_entity.repository_metadata = self.serialize()

    def _check_mutability(self):
        """Check if the node is mutable.

        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        if self._node.is_stored:
            raise exceptions.ModificationNotAllowed('the node is stored and therefore the repository is immutable.')

    @property
    def _repository(self) -> Repository:
        """Return the repository instance, lazily constructing it if necessary.

        .. note:: this property is protected because a node's repository should not be accessed outside of its scope.

        :return: the file repository instance.
        """
        if self._repository_instance is None:
            if self._node.is_stored:
                backend = self._node.backend.get_repository()
                self._repository_instance = Repository.from_serialized(backend=backend, serialized=self.metadata)
            else:
                filepath = get_config_option('storage.sandbox') or None
                self._repository_instance = Repository(backend=SandboxRepositoryBackend(filepath))

        return self._repository_instance

    @_repository.setter
    def _repository(self, repository: Repository) -> None:
        """Set a new repository instance, deleting the current reference if it has been initialized.

        :param repository: the new repository instance to set.
        """
        if self._repository_instance is not None:
            del self._repository_instance

        self._repository_instance = repository

    def _store(self) -> None:
        """Store the repository in the backend."""
        if isinstance(self._repository.backend, SandboxRepositoryBackend):
            # Only if the backend repository is a sandbox do we have to clone its contents to the permanent repository.
            repository_backend = self._node.backend.get_repository()
            repository = Repository(backend=repository_backend)
            repository.clone(self._repository)
            # Swap the sandbox repository for the new permanent repository instance which should delete the sandbox
            self._repository_instance = repository
        # update the metadata on the node backend
        self._node.backend_entity.repository_metadata = self.serialize()

    def _copy(self, repo: 'NodeRepository') -> None:
        """Copy a repository from another instance.

        This is used when storing cached nodes.

        :param repo: the repository to clone.
        """
        self._repository = copy.copy(repo._repository)  # pylint: disable=protected-access

    def _clone(self, repo: 'NodeRepository') -> None:
        """Clone the repository from another instance.

        This is used when cloning a node.

        :param repo: the repository to clone.
        """
        self._repository.clone(repo._repository)  # pylint: disable=protected-access

    def serialize(self) -> Dict:
        """Serialize the metadata of the repository content into a JSON-serializable format.

        :return: dictionary with the content metadata.
        """
        return self._repository.serialize()

    def hash(self) -> str:
        """Generate a hash of the repository's contents.

        :return: the hash representing the contents of the repository.
        """
        return self._repository.hash()

    def list_objects(self, path: Optional[str] = None) -> List[File]:
        """Return a list of the objects contained in this repository sorted by name, optionally in given sub directory.

        :param path: the relative path where to store the object in the repository.
        :return: a list of `File` named tuples representing the objects present in directory with the given key.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return self._repository.list_objects(path)

    def list_object_names(self, path: Optional[str] = None) -> List[str]:
        """Return a sorted list of the object names contained in this repository, optionally in the given sub directory.

        :param path: the relative path where to store the object in the repository.
        :return: a list of `File` named tuples representing the objects present in directory with the given key.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return self._repository.list_object_names(path)

    @contextlib.contextmanager
    def open(self, path: str, mode='r') -> Iterator[Union[BinaryIO, TextIO]]:
        """Open a file handle to an object stored under the given key.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param path: the relative path of the object within the repository.
        :return: yield a byte stream object.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        if mode not in ['r', 'rb']:
            raise ValueError(f'the mode {mode} is not supported.')

        with self._repository.open(path) as handle:
            if 'b' not in mode:
                yield io.StringIO(handle.read().decode('utf-8'))
            else:
                yield handle

    def get_object(self, path: Optional[FilePath] = None) -> File:
        """Return the object at the given path.

        :param path: the relative path where to store the object in the repository.
        :return: the `File` representing the object located at the given relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        return self._repository.get_object(path)

    def get_object_content(self, path: str, mode='r') -> Union[str, bytes]:
        """Return the content of a object identified by key.

        :param key: fully qualified identifier for the object within the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        if mode not in ['r', 'rb']:
            raise ValueError(f'the mode {mode} is not supported.')

        if 'b' not in mode:
            return self._repository.get_object_content(path).decode('utf-8')

        return self._repository.get_object_content(path)

    def put_object_from_bytes(self, content: bytes, path: str) -> None:
        """Store the given content in the repository at the given path.

        :param path: the relative path where to store the object in the repository.
        :param content: the content to store.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileExistsError: if an object already exists at the given path.
        """
        self._check_mutability()
        self._repository.put_object_from_filelike(io.BytesIO(content), path)
        self._update_repository_metadata()

    def put_object_from_filelike(self, handle: io.BufferedReader, path: str):
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :param path: the relative path where to store the object in the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self._check_mutability()

        if isinstance(handle, io.StringIO):
            handle = io.BytesIO(handle.read().encode('utf-8'))

        if isinstance(handle, tempfile._TemporaryFileWrapper):  # pylint: disable=protected-access
            if 'b' in handle.file.mode:
                handle = io.BytesIO(handle.read())
            else:
                handle = io.BytesIO(handle.read().encode('utf-8'))

        self._repository.put_object_from_filelike(handle, path)
        self._update_repository_metadata()

    def put_object_from_file(self, filepath: str, path: str):
        """Store a new object under `path` with contents of the file located at `filepath` on the local file system.

        :param filepath: absolute path of file whose contents to copy to the repository
        :param path: the relative path where to store the object in the repository.
        :raises TypeError: if the path is not a string and relative path, or the handle is not a byte stream.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self._check_mutability()
        self._repository.put_object_from_file(filepath, path)
        self._update_repository_metadata()

    def put_object_from_tree(self, filepath: str, path: Optional[str] = None):
        """Store the entire contents of `filepath` on the local file system in the repository with under given `path`.

        :param filepath: absolute path of the directory whose contents to copy to the repository.
        :param path: the relative path where to store the objects in the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self._check_mutability()
        self._repository.put_object_from_tree(filepath, path)
        self._update_repository_metadata()

    def walk(self, path: Optional[FilePath] = None) -> Iterable[Tuple[pathlib.PurePosixPath, List[str], List[str]]]:
        """Walk over the directories and files contained within this repository.

        .. note:: the order of the dirname and filename lists that are returned is not necessarily sorted. This is in
            line with the ``os.walk`` implementation where the order depends on the underlying file system used.

        :param path: the relative path of the directory within the repository whose contents to walk.
        :return: tuples of root, dirnames and filenames just like ``os.walk``, with the exception that the root path is
            always relative with respect to the repository root, instead of an absolute path and it is an instance of
            ``pathlib.PurePosixPath`` instead of a normal string
        """
        yield from self._repository.walk(path)

    def glob(self) -> Iterable[pathlib.PurePosixPath]:
        """Yield a recursive list of all paths (files and directories)."""
        for dirpath, dirnames, filenames in self.walk():
            for dirname in dirnames:
                yield dirpath / dirname
            for filename in filenames:
                yield dirpath / filename

    def copy_tree(self, target: Union[str, pathlib.Path], path: Optional[FilePath] = None) -> None:
        """Copy the contents of the entire node repository to another location on the local file system.

        :param target: absolute path of the directory where to copy the contents to.
        :param path: optional relative path whose contents to copy.
        """
        self._repository.copy_tree(target, path)

    def delete_object(self, path: str):
        """Delete the object from the repository.

        :param key: fully qualified identifier for the object within the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be deleted.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self._check_mutability()
        self._repository.delete_object(path)
        self._update_repository_metadata()

    def erase(self):
        """Delete all objects from the repository.

        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self._check_mutability()
        self._repository.erase()
        self._update_repository_metadata()
