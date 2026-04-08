"""Interface to the file repository of a node instance."""

from __future__ import annotations

import contextlib
import copy
import io
import pathlib
import shutil
import tempfile
import typing as t
import zipfile

from aiida.common import exceptions
from aiida.manage import get_config_option

if t.TYPE_CHECKING:
    from aiida.common.typing import FilePath
    from aiida.repository import File, Repository

    from .node import Node

__all__ = ('NodeRepository',)


class NodeRepository:
    """Interface to the file repository of a node instance.

    This is the compatibility layer between the `Node` class and the `Repository` class. The repository in principle has
    no concept of immutability, so it is implemented here. Any mutating operations will raise a `ModificationNotAllowed`
    exception if the node is stored. Otherwise the operation is just forwarded to the repository instance.

    The repository instance keeps an internal mapping of the file hierarchy that it maintains, starting from an empty
    hierarchy if the instance was constructed normally, or from a specific hierarchy if reconstructed through the
    ``Repository.from_serialized`` classmethod. This is only the case for stored nodes, because unstored nodes do not
    have any files yet when they are constructed. Once the node get's stored, the repository is asked to serialize its
    metadata contents which is then stored in the ``repository_metadata`` field of the backend node. This layer
    explicitly does not update the metadata of the node on a mutation action. The reason is that for stored nodes these
    actions are anyway forbidden and for unstored nodes, the final metadata will be stored in one go, once the node is
    stored, so there is no need to keep updating the node metadata intermediately. Note that this does mean that
    ``repository_metadata`` does not give accurate information, as long as the node is not yet stored.
    """

    def __init__(self, node: 'Node') -> None:
        """Construct a new instance of the repository interface."""
        self._node: 'Node' = node
        self._repository_instance: Repository | None = None

    @property
    def metadata(self) -> dict[str, t.Any]:
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
        from aiida.repository import Repository
        from aiida.repository.backend import SandboxRepositoryBackend

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
        from aiida.repository import Repository
        from aiida.repository.backend import SandboxRepositoryBackend

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
        self._repository = copy.copy(repo._repository)

    def _clone(self, repo: 'NodeRepository') -> None:
        """Clone the repository from another instance.

        This is used when cloning a node.

        :param repo: the repository to clone.
        """
        self._repository.clone(repo._repository)

    def serialize_content(self) -> dict[str, bytes]:
        """Serialize the content of the repository content into a JSON-serializable format.

        :return: dictionary with the content metadata.
        """
        serialized = {}

        for dirpath, _, filenames in self.walk():
            for filename in filenames:
                filepath = dirpath / filename
                serialized[str(filepath)] = self.get_object_content(str(filepath), mode='rb')

        return serialized

    def serialize(self) -> dict:
        """Serialize the metadata of the repository content into a JSON-serializable format.

        :return: dictionary with the content metadata.
        """
        return self._repository.serialize()

    def hash(self) -> str:
        """Generate a hash of the repository's contents.

        :return: the hash representing the contents of the repository.
        """
        return self._repository.hash()

    def list_objects(self, path: str | None = None) -> list[File]:
        """Return a list of the objects contained in this repository sorted by name, optionally in given sub directory.

        :param path: optional relative path inside the repository whose objects to list.
        :return: a list of `File` named tuples representing the objects present in directory with the given key.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return self._repository.list_objects(path)

    def list_object_names(self, path: str | None = None) -> list[str]:
        """Return a sorted list of the object names contained in this repository, optionally in the given sub directory.

        :param path: optional relative path inside the repository whose objects to list.
        :return: a list of `File` named tuples representing the objects present in directory with the given key.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return self._repository.list_object_names(path)

    @t.overload
    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['r']) -> t.Iterator[t.TextIO]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['rb']) -> t.Iterator[t.BinaryIO]: ...

    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['r', 'rb'] = 'r') -> t.Iterator[t.BinaryIO] | t.Iterator[t.TextIO]:
        """Open a file handle to an object stored under the given key.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param path: the relative path of the object within the repository.
        :param mode: (str) the type of stream object to be returned, 'r' for text handler, 'rb' for byte handler.
        :return: yield a stream object, (byte or text)
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        if mode not in ['r', 'rb']:
            raise ValueError(f'the mode {mode} is not supported.')

        with self._repository.open(path) as handle:
            if 'b' not in mode:
                with io.TextIOWrapper(handle, encoding='utf-8') as text_stream:
                    yield text_stream
            else:
                yield handle

    @contextlib.contextmanager
    def as_path(self, path: FilePath | None = None) -> t.Iterator[pathlib.Path]:
        """Make the contents of the repository available as a normal filepath on the local file system.

        :param path: optional relative path of the object within the repository.
        :return: the filepath of the content of the repository or object if ``path`` is specified.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        obj = self.get_object(path)

        with tempfile.TemporaryDirectory() as tmp_path:
            dirpath = pathlib.Path(tmp_path)

            if obj.is_dir():
                self.copy_tree(dirpath, path)
                yield dirpath
            else:
                filepath = dirpath / obj.name
                assert path is not None
                with self.open(path, mode='rb') as source:
                    with filepath.open('wb') as target:
                        shutil.copyfileobj(source, target)
                yield filepath

    def get_object(self, path: FilePath | None = None) -> File:
        """Return the object at the given path.

        :param path: the relative path of the object within the repository.
        :return: the `File` representing the object located at the given relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        return self._repository.get_object(path)

    @t.overload
    def get_object_content(self, path: str, mode: t.Literal['r']) -> str: ...

    @t.overload
    def get_object_content(self, path: str, mode: t.Literal['rb']) -> bytes: ...

    def get_object_content(self, path: str, mode: t.Literal['r', 'rb'] = 'r') -> str | bytes:
        """Return the content of a object identified by key.

        :param path: the relative path of the object within the repository.
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

    def get_object_size(self, path: str) -> int:
        """Return the size of the object located at the given path.

        :param path: the relative path of the object within the repository.
        :return: the size of the object in bytes.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        with self.open(path, mode='rb') as handle:
            handle.seek(0, io.SEEK_END)
            size = handle.tell()
        return size

    def get_zipped_objects(self, compression: int = zipfile.ZIP_DEFLATED) -> bytes:
        """Return the zipped content of the repository or a sub path within it.

        :param compression: the compression method to use. Defaults to `zipfile.ZIP_DEFLATED` (8).
        :return: the zipped content as bytes.
        """

        zip_bytes_io = io.BytesIO()

        with zipfile.ZipFile(zip_bytes_io, mode='w', compression=compression) as zip_file:
            for dirpath, _, filenames in self.walk():
                for filename in filenames:
                    filepath = dirpath / filename
                    file_content = self.get_object_content(str(filepath), mode='rb')
                    zip_file.writestr(str(filepath), file_content)

        return zip_bytes_io.getvalue()

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

        if isinstance(handle, io.StringIO):  # type: ignore[unreachable]
            handle = io.BytesIO(handle.read().encode('utf-8'))  # type: ignore[unreachable]

        if isinstance(handle, tempfile._TemporaryFileWrapper):  # type: ignore[unreachable]
            if 'b' in handle.file.mode:  # type: ignore[unreachable]
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

    def put_object_from_tree(self, filepath: str, path: str | None = None):
        """Store the entire contents of `filepath` on the local file system in the repository with under given `path`.

        :param filepath: absolute path of the directory whose contents to copy to the repository.
        :param path: the relative path where to store the objects in the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self._check_mutability()
        self._repository.put_object_from_tree(filepath, path)
        self._update_repository_metadata()

    def walk(self, path: FilePath | None = None) -> t.Iterable[tuple[pathlib.PurePath, list[str], list[str]]]:
        """Walk over the directories and files contained within this repository.

        .. note:: the order of the dirname and filename lists that are returned is not necessarily sorted. This is in
            line with the ``os.walk`` implementation where the order depends on the underlying file system used.

        :param path: the relative path of the directory within the repository whose contents to walk.
        :return: tuples of root, dirnames and filenames just like ``os.walk``, with the exception that the root path is
            always relative with respect to the repository root, instead of an absolute path and it is an instance of
            ``pathlib.PurePath`` instead of a normal string
        """
        yield from self._repository.walk(path)

    def glob(self) -> t.Iterable[pathlib.PurePath]:
        """Yield a recursive list of all paths (files and directories)."""
        for dirpath, dirnames, filenames in self.walk():
            for dirname in dirnames:
                yield dirpath / dirname
            for filename in filenames:
                yield dirpath / filename

    def copy_tree(self, target: str | pathlib.Path, path: FilePath | None = None) -> None:
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
