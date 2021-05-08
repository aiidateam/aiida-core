# -*- coding: utf-8 -*-
"""Module for the implementation of a repository file-system."""
import collections.abc
import contextlib
import io
import os
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Iterable, TextIO, Dict, Iterator, Optional, Set, Tuple, Union

from aiida.common import exceptions
from aiida.common.hashing import make_hash
from aiida.common.lang import type_check
from aiida.repository.backend import AbstractRepositoryBackend, SandboxRepositoryBackend


PATH_TYPE = Union[str, bytes, os.PathLike]

__all__ = ('BaseRepoFileSystem', 'MutableRepoFileSystem', 'FrozenRepoFileSystem', 'RepoPath')


def flatten(d, parent_key=(), last_key = None):
    """Return flattened dict of repository: path tuple -> key string if file else None.
    
    Note: All sub-folders will be included,
    and we assume a file/folder cannot exist with the same name (true for all OS)
    """
    items = []
    for k, v in d.items():
        if last_key:
            new_key = parent_key + (k,) if parent_key else (k,)
        else:
            new_key = parent_key
        if isinstance(v, collections.abc.MutableMapping):
            if last_key == 'o':
                items.append((new_key, None))
            items.extend(flatten(v, new_key, None if last_key else k).items())
        else:
            # assert k == 'k'
            items.append((new_key, v))
    return dict(items)


def unflatten(dct: Dict[Tuple[str, ...], Optional[str]]) -> Dict[str, Any]:
    output = {'o': {}}
    for path, value in dct.items():
        suboutput = output['o']
        for key in path[:-1]:
            suboutput.setdefault(key, {'o': {}})
            suboutput = suboutput[key]['o']
        if value is None:
            suboutput.setdefault(path[-1], {'o': {}})
        else:
            suboutput.setdefault(path[-1], {})
            suboutput[path[-1]]['k'] = value

    return output


class BaseRepoFileSystem:
    """Class to represent the node repository file system."""

    def __init__(self, file_tree: Union[None, Dict[str, Any]] = None, backend: Optional[AbstractRepositoryBackend] = None) -> None:
        """Initialise the file system.

        :param file_tree: A serialized representation of the file system.
            directory keys are 'o' and file keys are 'k', for example:
            ``{'o': 'folder': {'o': 'subfolder': {'o': {'file': {'k': 'filekey'}}}}}``
        :param backend: A key/value store for reading/writing file contents,
            this must be initialised (defaults to ``SandboxRepositoryBackend``)

        """
        self._set_file_tree(file_tree)
        if backend is None:
            backend = SandboxRepositoryBackend()
            backend.initialise()
        self._set_backend(backend)

    def _set_backend(self, backend: AbstractRepositoryBackend) -> None:
        type_check(backend, AbstractRepositoryBackend)
        # assert backend.is_initialised, 'backend must be initialised'
        self._backend = backend

    @property
    def backend(self):
        if not self._backend.is_initialised:
            from aiida.manage.configuration import get_profile
            profile = get_profile()
            self._backend.initialise(**profile.defaults['repository'])
        return self._backend

    def _set_file_tree(self, file_tree: Union[None, Dict[str, Any]]) -> None:
        type_check(file_tree, dict, allow_none=True)
        file_tree = file_tree or {'o': {}}
        assert 'o' in file_tree, "Serialized file system must begin with 'o' key"
        self._file_tree: Dict[Tuple[str, ...], Optional[str]] = flatten(file_tree)

    def __str__(self) -> str:
        return f'{type(self).__name__}()'

    def pretty(self) -> str:
        dct = {PurePosixPath(*k).as_posix(): v for k, v in self._file_tree.items()}
        print("\n".join(f"{key}: {dct[key] or ''}" for key in sorted(dct)))

    def serialize(self) -> Dict[str, Any]:
        """Serialize the metadata into a JSON-serializable format.

        :return: dictionary with the content metadata.
        """
        return unflatten(self._file_tree)

    @property
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository or ``None`` if it doesn't have one."""
        return self.backend.uuid

    def hash(self) -> str:
        """Generate a hash of the repository's contents.

        :return: the hash representing the contents of the repository.
        """
        hashes = {}
        for key in sorted(self._file_tree):
            value = self._file_tree[key]
            value = self.backend.get_object_hash(value) if value else value
            hashes[PurePosixPath(*key).as_posix()] = value
        return make_hash(hashes)

    def path_exists(self, path: PATH_TYPE) -> bool:
        posix_path = PurePosixPath(path or '')
        return tuple(posix_path.parts) in self._file_tree

    def file_exists(self, path: PATH_TYPE) -> bool:
        posix_path = PurePosixPath(path or '')
        try:
            return self._file_tree[tuple(posix_path.parts)] is not None
        except KeyError:
            return False

    def dir_exists(self, path: PATH_TYPE) -> bool:
        posix_path = PurePosixPath(path or '')
        try:
            return self._file_tree[tuple(posix_path.parts)] is None
        except KeyError:
            return False

    def _get_file_key(self, path: PATH_TYPE) -> str:
        posix_path = PurePosixPath(path or '')
        try:
            key = self._file_tree[tuple(posix_path.parts)]
        except KeyError:
            raise FileNotFoundError(posix_path)
        if key is None:
            raise IsADirectoryError(posix_path)
        return key

    def dir_walk(self, path: PATH_TYPE) -> Iterable[Tuple[PurePosixPath, Optional[str]]]:
        posix_path = PurePosixPath(path or '')
        parts = tuple(posix_path.parts)
        if parts and parts not in self._file_tree:
            raise FileNotFoundError(posix_path)
        if parts and self._file_tree[parts] is not None:
             raise NotADirectoryError(posix_path)
        len_parts = len(parts)
        for key, value in self._file_tree.items():
            if key[:len_parts] == parts:
                yield (PurePosixPath(*key), value)

    def dir_children(self, path: PATH_TYPE) -> Set[str]:
        posix_path = PurePosixPath(path or '')
        parts = tuple(posix_path.parts)
        if parts and parts not in self._file_tree:
            raise FileNotFoundError(posix_path)
        if parts and self._file_tree[parts] is not None:
            raise NotADirectoryError(posix_path)
        children = set()
        len_parts = len(parts)
        for key in self._file_tree:
            if key[:len_parts] == parts:
                try:
                    children.add(key[len_parts])
                except IndexError:
                    pass
        return children
    
    @contextlib.contextmanager
    def file_open(self, path: PATH_TYPE, mode: str = 'r', encoding: str = 'utf8') -> Iterator[Union[BinaryIO, TextIO]]:
        if mode not in ['r', 'rb']:
            raise ValueError(f'the mode {mode} is not supported.')
        key = self._get_file_key(path)
        with self.backend.open(key) as handle:
            if 'b' not in mode:
                yield io.StringIO(handle.read().decode(encoding))
            else:
                yield handle

    def file_read(self, path: PATH_TYPE) -> bytes:
        key = self._get_file_key(path)
        return self.backend.get_object_content(key)

    def file_write_handle(self, path: PATH_TYPE, handle: BinaryIO) -> None:
        posix_path = PurePosixPath(path or '')
        parts = tuple(posix_path.parts)
        if parts in self._file_tree:
            raise FileExistsError(path)
        key = self.backend.put_object_from_filelike(handle)
        self._file_tree[parts] = key
        while parts[:-1]:
            self._file_tree[parts[:-1]] = None
            parts = parts[:-1]

    def file_write_binary(self, path: PATH_TYPE, content: bytes) -> None:
        self.file_write_handle(path, io.BytesIO(content))

    def file_write_text(self, path: PATH_TYPE, content: str, encoding :str = "utf-8") -> None:
        self.file_write_handle(path, io.BytesIO(content.encode(encoding)))

    def file_write_path(self, path: PATH_TYPE, os_path: Union[str, Path]) -> None:
        with open(os_path, 'rb') as handle:
            self.file_write_handle(path, handle)

    def dir_create(self, path: PATH_TYPE, exists_ok: bool = True) -> None:
        posix_path = PurePosixPath(path or '')
        parts = tuple(posix_path.parts)
        if parts in self._file_tree:
            if not exists_ok:
                raise FileExistsError(posix_path)
            return
        while parts[:-1]:
            self._file_tree[parts[:-1]] = None
            parts = parts[:-1]

    def dir_write(self, path: PATH_TYPE, os_path: Union[str, Path]) -> None:
        type_check(os_path, (str, Path))
        posix_path = PurePosixPath(path or '')
        os_path = Path(os_path)
        if not os_path.is_absolute():
            raise TypeError(f'filepath `{os_path}` is not an absolute path.')

        # Explicitly create the base directory if specified by `path`, just in case `filepath` contains no file objects.
        if posix_path.parts:
            self.dir_create(path)

        for root_str, dirnames, filenames in os.walk(os_path):
            root = Path(root_str)
            for dirname in dirnames:
                self.dir_create(path / root.relative_to(os_path) / dirname)
            for filename in filenames:
                self.file_write_path(path / root.relative_to(os_path) / filename, root / filename)

    def file_remove(self, path: PATH_TYPE) -> None:
        posix_path = PurePosixPath(path or '')
        parts = tuple(posix_path.parts)
        if parts not in self._file_tree:
            raise FileNotFoundError(posix_path)
        if self._file_tree[parts] is None:
             raise IsADirectoryError(posix_path)
        self._file_tree.pop(parts)

    def dir_remove(self, path: PATH_TYPE) -> None:
        posix_path = PurePosixPath(path or '')
        parts = tuple(posix_path.parts)
        if parts not in self._file_tree:
            raise FileNotFoundError(posix_path)
        if self._file_tree[parts] is not None:
             raise NotADirectoryError(posix_path)
        self._file_tree.pop(parts)
        len_parts = len(parts)
        for key in self._file_tree:
            if key[:len_parts] == parts:
                self._file_tree.pop(key)


class FrozenRepoFileSystem(BaseRepoFileSystem):
    """A file system which does not allow any mutations."""

    _exception_msg = 'the node is stored and therefore the repository is immutable.'

    def file_write_handle(self, path: PATH_TYPE, handle: BinaryIO) -> None:
        raise exceptions.ModificationNotAllowed(self._exception_msg)

    def dir_create(self, path: PATH_TYPE, exists_ok: bool = True) -> Dict[str, Any]:
        raise exceptions.ModificationNotAllowed(self._exception_msg)

    def file_remove(self, path: PATH_TYPE) -> None:
        raise exceptions.ModificationNotAllowed(self._exception_msg)

    def dir_remove(self, path: PATH_TYPE) -> None:
        raise exceptions.ModificationNotAllowed(self._exception_msg)


class MutableRepoFileSystem(BaseRepoFileSystem):
    """A file system which allows mutations."""

    def clone(self, source: 'BaseRepoFileSystem') -> None:
        """Clone the contents of another repository instance."""
        if not isinstance(source, BaseRepoFileSystem):
            raise TypeError('source is not an instance of `BaseRepoFileSystem`.')
        self._file_tree = source._file_tree
        for path, file_key in source._file_tree.items():
            if file_key is not None:
                with source.backend.open(file_key) as handle:
                    new_key = self.backend.put_object_from_filelike(handle)
                    source._file_tree[path] = new_key

    def reset(self) -> None:
        self._file_tree = {}

    def delete(self) -> None:
        """Delete the repository.

        .. important:: This will not just delete the contents of the repository but also the repository itself and all
            of its assets. For example, if the repository is stored inside a folder on disk, the folder may be deleted.

        """
        self.backend.erase()
        self.reset()

    def erase(self) -> None:
        """Delete all objects from the repository.

        .. important: this intentionally does not call through to any ``erase`` method of the backend, because unlike
            this class, the backend does not just store the objects of a single node, but potentially of a lot of other
            nodes. Therefore, we manually delete all file objects and then simply reset the internal file hierarchy.

        """
        for file_key in self._file_tree.values():
            if file_key is not None:
                self.backend.delete_object(file_key)
        self.reset()


class RepoPath(os.PathLike):
    """Representation of a path in the repository.
    
    This an implementation of the file system path protocol (PEP 519),
    and mimics the ``pathlib.Path`` API.
    """
    def __init__(self, path: PATH_TYPE, file_system: BaseRepoFileSystem):
        self._current_path = PurePosixPath(path or '')
        if self._current_path.is_absolute():
            raise TypeError(f'path `{self._current_path}` is not a relative path.')
        type_check(file_system, BaseRepoFileSystem)
        self._file_system = file_system

    def __fspath__(self) -> str:
        return os.fspath(self._current_path)

    def __str__(self) -> str:
        return str(self._current_path)

    def __repr__(self) -> str:
        return f"RepoPath('{self._current_path}', {self._file_system})"

    def __eq__(self, other) -> bool:
        """Return whether this instance is equal to another path."""
        if not isinstance(other, self.__class__):
            return False
        return self._current_path == other._current_path

    def _copy(self, path = None) -> 'RepoPath':
        return RepoPath(path=(path or self._current_path), file_system=self._file_system)

    @property
    def parent(self) -> 'RepoPath':
        return self._copy(PurePosixPath(self._current_path).parent)

    @property
    def name(self) -> str:
        return self._current_path.name
    
    @property
    def otype(self) -> str:
        if not self.exists():
            return 'UNKNOWN'
        return 'FILE' if self.is_file() else 'DIRECTORY'

    def exists(self) -> bool:
        return self._file_system.path_exists(self._current_path)

    def is_file(self) -> bool:
        return self._file_system.file_exists(self._current_path)

    def is_dir(self) -> bool:
        return self._file_system.dir_exists(self._current_path)

    def iterdir(self) -> Iterator['RepoPath']:
        """Yield direct children of a directory."""
        for name in self._file_system.dir_children(self._current_path):
            yield self.joinpath(name)
    
    def walk(self, files_only: bool = False) -> Iterator['RepoPath']:
        """Yield recursive children of a directory."""
        for path, key in self._file_system.dir_walk(self._current_path):
            if (not files_only) or key:
                yield self._copy(path)

    def joinpath(self, *args: str) -> 'RepoPath':
        path = PurePosixPath(self._current_path, *args)
        return self._copy(path)

    def __truediv__(self, path: str) -> 'RepoPath':
        return self.joinpath(path)

    def mkdir(self, exists_ok: bool = True) -> None:
        self._file_system.dir_create(self._current_path, exists_ok=exists_ok)
    
    def write_bytes(self, content: bytes) -> None:
        self._file_system.file_write_binary(self._current_path, content)

    def write_text(self, content: str, encoding: str = "utf8") -> None:
        self._file_system.file_write_text(self._current_path, content, encoding)

    def read_bytes(self) -> bytes:
        return self._file_system.file_read(self._current_path)

    def read_text(self, encoding: str = 'utf8') -> str:
        return self._file_system.file_read(self._current_path).decode(encoding)

    @contextlib.contextmanager
    def open(self, mode: str = 'r', encoding: str = 'utf8') -> Iterator[Union[BinaryIO, TextIO]]:
        with self._file_system.file_open(self._current_path, mode, encoding) as handle:
            yield handle

    def unlink(self) -> None:
        """Soft delete this file from the repository."""
        self._file_system.file_remove(self._current_path)

    def rmtree(self) -> None:
        """Soft delete this directory and its children."""
        self._file_system.dir_remove(self._current_path)
