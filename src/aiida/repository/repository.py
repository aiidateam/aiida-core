"""Module for the implementation of a file repository."""

import contextlib
import pathlib
from typing import Any, BinaryIO, Dict, Iterable, Iterator, List, Optional, Tuple, Union

from aiida.common.hashing import make_hash
from aiida.common.lang import type_check
from aiida.common.typing import FilePath

from .backend import AbstractRepositoryBackend, SandboxRepositoryBackend
from .common import File, FileType

__all__ = ('Repository',)


class Repository:
    """File repository.

    This class provides an interface to a backend file repository instance, but unlike the backend repository, this
    class keeps a reference of the virtual file hierarchy. This means that through this interface, a client can create
    files and directories with a file hierarchy, just as they would on a local file system, except it is completely
    virtual as the files are stored by the backend which can store them in a completely flat structure. This also means
    that the internal virtual hierarchy of a ``Repository`` instance does not necessarily represent all the files that
    are stored by repository backend. The repository exposes a mere subset of all the file objects stored in the
    backend. This is why object deletion is also implemented as a soft delete, by default, where the files are just
    removed from the internal virtual hierarchy, but not in the actual backend. This is because those objects can be
    referenced by other instances.
    """

    _file_cls = File

    def __init__(self, backend: Optional[AbstractRepositoryBackend] = None):
        """Construct a new instance with empty metadata.

        :param backend: instance of repository backend to use to actually store the file objects. By default, an
            instance of the ``SandboxRepositoryBackend`` will be created.
        """
        if backend is None:
            backend = SandboxRepositoryBackend()

        self.set_backend(backend)
        self.reset()

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        return f'Repository<{self.backend!s}>'

    @property
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository backend or ``None`` if it doesn't have one."""
        return self.backend.uuid

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository backend has been initialised."""
        return self.backend.is_initialised

    @classmethod
    def from_serialized(cls, backend: AbstractRepositoryBackend, serialized: Dict[str, Any]) -> 'Repository':
        """Construct an instance where the metadata is initialized from the serialized content.

        :param backend: instance of repository backend to use to actually store the file objects.
        """
        instance = cls.__new__(cls)
        instance.__init__(backend)  # type: ignore[misc]

        if serialized:
            for name, obj in serialized['o'].items():
                instance.get_directory().objects[name] = cls._file_cls.from_serialized(obj, name)

        return instance

    def reset(self) -> None:
        self._directory = self._file_cls()

    def serialize(self) -> Dict[str, Any]:
        """Serialize the metadata into a JSON-serializable format.

        :return: dictionary with the content metadata.
        """
        return self._directory.serialize()

    @classmethod
    def flatten(cls, serialized=Optional[Dict[str, Any]], delimiter: str = '/') -> Dict[str, Optional[str]]:
        """Flatten the serialized content of a repository into a mapping of path -> key or None (if folder).

        Note, all folders are represented in the flattened output, and their path is suffixed with the delimiter.

        :param serialized: the serialized content of the repository.
        :param delimiter: the delimiter to use to separate the path elements.
        :return: dictionary with the flattened content.
        """
        if serialized is None:
            return {}
        items: Dict[str, Optional[str]] = {}
        stack = [('', serialized)]
        while stack:
            path, sub_dict = stack.pop()
            for name, obj in sub_dict.get('o', {}).items():
                sub_path = f'{path}{delimiter}{name}' if path else name
                if not obj:
                    items[f'{sub_path}{delimiter}'] = None
                elif 'k' in obj:
                    items[sub_path] = obj['k']
                else:
                    items[f'{sub_path}{delimiter}'] = None
                    stack.append((sub_path, obj))
        return items

    def hash(self) -> str:
        """Generate a hash of the repository's contents.

        .. warning:: this will read the content of all file objects contained within the virtual hierarchy into memory.

        :return: the hash representing the contents of the repository.
        """
        objects: Dict[str, Any] = {}
        for root, dirnames, filenames in self.walk():
            objects['__dirnames__'] = dirnames
            for filename in filenames:
                key = self.get_file(root / filename).key
                assert key is not None, 'Expected FileType.File to have a key'
                objects[str(root / filename)] = self.backend.get_object_hash(key)

        return make_hash(objects)

    @staticmethod
    def _pre_process_path(path: Optional[FilePath] = None) -> pathlib.PurePath:
        """Validate and convert the path to instance of ``pathlib.PurePath``.

        This should be called by every method of this class before doing anything, such that it can safely assume that
        the path is a ``pathlib.PurePath`` object, which makes path manipulation a lot easier.

        :param path: the path as a ``pathlib.PurePath`` object or `None`.
        :raises TypeError: if the type of path was not a str nor a ``pathlib.PurePath`` instance.
        """
        if path is None:
            return pathlib.PurePath()

        if isinstance(path, str):
            path = pathlib.PurePath(path)

        if not isinstance(path, pathlib.PurePath):
            raise TypeError('path is not of type `str` nor `pathlib.PurePath`.')

        if path.is_absolute():
            raise TypeError(f'path `{path}` is not a relative path.')

        return path

    @property
    def backend(self) -> AbstractRepositoryBackend:
        """Return the current repository backend.

        :return: the repository backend.
        """
        return self._backend

    def set_backend(self, backend: AbstractRepositoryBackend) -> None:
        """Set the backend for this repository.

        :param backend: the repository backend.
        :raises TypeError: if the type of the backend is invalid.
        """
        type_check(backend, AbstractRepositoryBackend)
        self._backend = backend

    def _insert_file(self, path: pathlib.PurePath, key: str) -> None:
        """Insert a new file object in the object mapping.

        .. note:: this assumes the path is a valid relative path, so should be checked by the caller.

        :param path: the relative path where to store the object in the repository.
        :param key: fully qualified identifier for the object within the repository.
        """
        directory = self.create_directory(path.parent)
        directory.objects[path.name] = self._file_cls(path.name, FileType.FILE, key)

    def create_directory(self, path: FilePath) -> File:
        """Create a new directory with the given path.

        :param path: the relative path of the directory.
        :return: the created directory.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        """
        if path is None:
            raise TypeError('path cannot be `None`.')

        path = self._pre_process_path(path)
        directory = self._directory

        for part in path.parts:
            if part not in directory.objects:
                directory.objects[part] = self._file_cls(part)

            directory = directory.objects[part]

        return directory

    def get_file_keys(self) -> List[str]:
        """Return the keys of all file objects contained within this repository.

        :return: list of keys, which map a file to its content in the backend repository.
        """
        file_keys: List[str] = []

        def _add_file_keys(keys, objects):
            """Recursively add keys of all file objects to the keys list."""
            for obj in objects.values():
                if obj.file_type == FileType.FILE and obj.key is not None:
                    keys.append(obj.key)
                elif obj.file_type == FileType.DIRECTORY:
                    _add_file_keys(keys, obj.objects)

        _add_file_keys(file_keys, self._directory.objects)

        return file_keys

    def get_object(self, path: Optional[FilePath] = None) -> File:
        """Return the object at the given path.

        :param path: the relative path where to store the object in the repository.
        :return: the `File` representing the object located at the given relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        path = self._pre_process_path(path)
        file_object = self._directory

        if not path.parts:
            return file_object

        for part in path.parts:
            if part not in file_object.objects:
                raise FileNotFoundError(f'object with path `{path}` does not exist.')

            file_object = file_object.objects[part]

        return file_object

    def get_directory(self, path: Optional[FilePath] = None) -> File:
        """Return the directory object at the given path.

        :param path: the relative path of the directory.
        :return: the `File` representing the object located at the given relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        file_object = self.get_object(path)

        if file_object.file_type != FileType.DIRECTORY:
            raise NotADirectoryError(f'object with path `{path}` is not a directory.')

        return file_object

    def get_file(self, path: FilePath) -> File:
        """Return the file object at the given path.

        :param path: the relative path of the file object.
        :return: the `File` representing the object located at the given relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises IsADirectoryError: if the object at the given path is not a directory.
        """
        if path is None:
            raise TypeError('path cannot be `None`.')

        path = self._pre_process_path(path)

        file_object = self.get_object(path)

        if file_object.file_type != FileType.FILE:
            raise IsADirectoryError(f'object with path `{path}` is not a file.')

        return file_object

    def list_objects(self, path: Optional[FilePath] = None) -> List[File]:
        """Return a list of the objects contained in this repository sorted by name, optionally in given sub directory.

        :param path: the relative path of the directory.
        :return: a list of `File` named tuples representing the objects present in directory with the given path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        directory = self.get_directory(path)
        return sorted(directory.objects.values(), key=lambda obj: obj.name)

    def list_object_names(self, path: Optional[FilePath] = None) -> List[str]:
        """Return a sorted list of the object names contained in this repository, optionally in the given sub directory.

        :param path: the relative path of the directory.
        :return: a list of `File` named tuples representing the objects present in directory with the given path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return [entry.name for entry in self.list_objects(path)]

    def put_object_from_filelike(self, handle: BinaryIO, path: FilePath) -> None:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :param path: the relative path where to store the object in the repository.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        """
        path = self._pre_process_path(path)
        key = self.backend.put_object_from_filelike(handle)
        self._insert_file(path, key)

    def put_object_from_file(self, filepath: FilePath, path: FilePath) -> None:
        """Store a new object under `path` with contents of the file located at `filepath` on the local file system.

        :param filepath: absolute path of file whose contents to copy to the repository
        :param path: the relative path where to store the object in the repository.
        :raises TypeError: if the path is not a string and relative path, or the handle is not a byte stream.
        """
        with open(filepath, 'rb') as handle:
            self.put_object_from_filelike(handle, path)

    def put_object_from_tree(self, filepath: FilePath, path: Optional[FilePath] = None) -> None:
        """Store the entire contents of `filepath` on the local file system in the repository with under given `path`.

        :param filepath: absolute path of the directory whose contents to copy to the repository.
        :param path: the relative path where to store the objects in the repository.
        :raises TypeError: if the filepath is not a string or ``Path``, or is a relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        """
        import os

        path = self._pre_process_path(path)

        if isinstance(filepath, str):
            filepath = pathlib.PurePath(filepath)

        if not isinstance(filepath, pathlib.PurePath):
            raise TypeError(f'filepath `{filepath}` is not of type `str` nor `pathlib.PurePath`.')

        if not filepath.is_absolute():
            raise TypeError(f'filepath `{filepath}` is not an absolute path.')

        # Explicitly create the base directory if specified by `path`, just in case `filepath` contains no file objects.
        if path.parts:
            self.create_directory(path)

        for root_str, dirnames, filenames in os.walk(filepath):
            root = pathlib.PurePath(root_str)

            for dirname in dirnames:
                self.create_directory(path / root.relative_to(filepath) / dirname)

            for filename in filenames:
                self.put_object_from_file(root / filename, path / root.relative_to(filepath) / filename)

    def is_empty(self) -> bool:
        """Return whether the repository is empty.

        :return: True if the repository contains no file objects.
        """
        return not self._directory.objects

    def has_object(self, path: FilePath) -> bool:
        """Return whether the repository has an object with the given path.

        :param path: the relative path of the object within the repository.
        :return: True if the object exists, False otherwise.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        """
        try:
            self.get_object(path)
        except FileNotFoundError:
            return False
        return True

    @contextlib.contextmanager
    def open(self, path: FilePath) -> Iterator[BinaryIO]:
        """Open a file handle to an object stored under the given path.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param path: the relative path of the object within the repository.
        :return: yield a byte stream object.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        key = self.get_file(path).key
        assert key is not None, 'Expected FileType.File to have a key'
        with self.backend.open(key) as handle:
            yield handle

    def get_object_content(self, path: FilePath) -> bytes:
        """Return the content of a object identified by path.

        :param path: the relative path of the object within the repository.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        key = self.get_file(path).key
        assert key is not None, 'Expected FileType.File to have a key'
        return self.backend.get_object_content(key)

    def delete_object(self, path: FilePath, hard_delete: bool = False) -> None:
        """Soft delete the object from the repository.

        .. note:: can only delete file objects, but not directories.

        :param path: the relative path of the object within the repository.
        :param hard_delete: when true, not only remove the file from the internal mapping but also call through to the
            ``delete_object`` method of the actual repository backend.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be deleted.
        """
        path = self._pre_process_path(path)
        file_object = self.get_object(path)

        if file_object.file_type == FileType.DIRECTORY:
            raise IsADirectoryError(f'object with path `{path}` is a directory.')

        if hard_delete:
            assert file_object.key is not None, 'Expected FileType.File to have a key'
            self.backend.delete_object(file_object.key)

        directory = self.get_directory(path.parent)
        directory.objects.pop(path.name)

    def erase(self) -> None:
        """Delete all objects from the repository.

        .. important: this intentionally does not call through to any ``erase`` method of the backend, because unlike
            this class, the backend does not just store the objects of a single node, but potentially of a lot of other
            nodes. Therefore, we manually delete all file objects and then simply reset the internal file hierarchy.

        """
        for file_key in self.get_file_keys():
            self.backend.delete_object(file_key)
        self.reset()

    def clone(self, source: 'Repository') -> None:
        """Clone the contents of another repository instance."""
        if not isinstance(source, Repository):
            raise TypeError('source is not an instance of `Repository`.')

        for root, dirnames, filenames in source.walk():
            for dirname in dirnames:
                self.create_directory(root / dirname)
            for filename in filenames:
                with source.open(root / filename) as handle:
                    self.put_object_from_filelike(handle, root / filename)

    def walk(self, path: Optional[FilePath] = None) -> Iterable[Tuple[pathlib.PurePath, List[str], List[str]]]:
        """Walk over the directories and files contained within this repository.

        .. note:: the order of the dirname and filename lists that are returned is not necessarily sorted. This is in
            line with the ``os.walk`` implementation where the order depends on the underlying file system used.

        :param path: the relative path of the directory within the repository whose contents to walk.
        :return: tuples of root, dirnames and filenames just like ``os.walk``, with the exception that the root path is
            always relative with respect to the repository root, instead of an absolute path and it is an instance of
            ``pathlib.PurePath`` instead of a normal string
        """
        path = self._pre_process_path(path)

        directory = self.get_directory(path)
        dirnames = [obj.name for obj in directory.objects.values() if obj.file_type == FileType.DIRECTORY]
        filenames = [obj.name for obj in directory.objects.values() if obj.file_type == FileType.FILE]

        if dirnames:
            for dirname in dirnames:
                yield from self.walk(path / dirname)

        yield path, dirnames, filenames

    def copy_tree(self, target: Union[str, pathlib.Path], path: Optional[FilePath] = None) -> None:
        """Copy the contents of the entire node repository to another location on the local file system.

        .. note:: If ``path`` is specified, only its contents are copied, and the relative path with respect to the
            root is discarded. For example, if ``path`` is ``relative/sub``, the contents of ``sub`` will be copied
            directly to the target, without the ``relative/sub`` directory.

        :param target: absolute path of the directory where to copy the contents to.
        :param path: optional relative path whose contents to copy.
        :raises TypeError: if ``target`` is of incorrect type or not absolute.
        :raises NotADirectoryError: if ``path`` does not reference a directory.
        """
        path = self._pre_process_path(path)
        file_object = self.get_object(path)

        if file_object.file_type != FileType.DIRECTORY:
            raise NotADirectoryError(f'object with path `{path}` is not a directory.')

        if isinstance(target, str):
            target = pathlib.Path(target)

        if not isinstance(target, pathlib.Path):
            raise TypeError(f'path `{path}` is not of type `str` nor `pathlib.Path`.')

        if not target.is_absolute():
            raise TypeError(f'provided target `{target}` is not an absolute path.')

        for root, dirnames, filenames in self.walk(path):
            for dirname in dirnames:
                dirpath = target / (root / dirname).relative_to(path)
                dirpath.mkdir(parents=True, exist_ok=True)

            for filename in filenames:
                dirpath = target / root.relative_to(path)
                filepath = dirpath / filename

                dirpath.mkdir(parents=True, exist_ok=True)

                with self.open(root / filename) as handle:
                    filepath.write_bytes(handle.read())

    # these methods are not actually used in aiida-core, but are here for completeness

    def initialise(self, **kwargs: Any) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: keyword argument that will be passed to the ``initialise`` call of the backend.
        """
        self.backend.initialise(**kwargs)

    def delete(self) -> None:
        """Delete the repository.

        .. important:: This will not just delete the contents of the repository but also the repository itself and all
            of its assets. For example, if the repository is stored inside a folder on disk, the folder may be deleted.
        """
        self.backend.erase()
        self.reset()
