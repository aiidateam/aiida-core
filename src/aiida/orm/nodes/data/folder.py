###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a folder on a file system."""

from __future__ import annotations

import contextlib
import io
import pathlib
import typing as t

from .data import Data

if t.TYPE_CHECKING:
    from aiida.common.typing import FilePath
    from aiida.repository import File


__all__ = ('FolderData',)


class FolderData(Data):
    """`Data` sub class to represent a folder on a file system."""

    def __init__(self, **kwargs):
        """Construct a new `FolderData` to which any files and folders can be added.

        Use the `tree` keyword to simply wrap a directory:

            folder = FolderData(tree='/absolute/path/to/directory')

        Alternatively, one can construct the node first and then use the various repository methods to add objects:

            folder = FolderData()
            folder.put_object_from_tree('/absolute/path/to/directory')
            folder.put_object_from_filepath('/absolute/path/to/file.txt')
            folder.put_object_from_filelike(filelike_object)

        :param tree: absolute path to a folder to wrap
        :type tree: str
        """
        tree = kwargs.pop('tree', None)
        super().__init__(**kwargs)
        if tree:
            self.base.repository.put_object_from_tree(tree)

    def list_objects(self, path: str | None = None) -> list[File]:
        """Return a list of the objects contained in this repository sorted by name, optionally in given sub directory.

        :param path: optional relative path inside the repository whose objects to list.
        :return: a list of `File` named tuples representing the objects present in directory with the given key.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return self.base.repository.list_objects(path)

    def list_object_names(self, path: str | None = None) -> list[str]:
        """Return a sorted list of the object names contained in this repository, optionally in the given sub directory.

        :param path: optional relative path inside the repository whose objects to list.
        :return: a list of `File` named tuples representing the objects present in directory with the given key.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if no object exists for the given path.
        :raises NotADirectoryError: if the object at the given path is not a directory.
        """
        return self.base.repository.list_object_names(path)

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
        :return: yield a byte stream object.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be opened.
        """
        with self.base.repository.open(path, mode) as handle:
            yield handle

    @contextlib.contextmanager
    def as_path(self, path: FilePath | None = None) -> t.Iterator[pathlib.Path]:
        """Make the contents of the repository available as a normal filepath on the local file system.

        :param path: optional relative path of the object within the repository.
        :return: the filepath of the content of the repository or object if ``path`` is specified.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        with self.base.repository.as_path(path) as filepath:
            yield filepath

    def get_object(self, path: FilePath | None = None) -> File:
        """Return the object at the given path.

        :param path: the relative path of the object within the repository.
        :return: the `File` representing the object located at the given relative path.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        return self.base.repository.get_object(path)

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
        return self.base.repository.get_object_content(path, mode)

    def put_object_from_bytes(self, content: bytes, path: str) -> None:
        """Store the given content in the repository at the given path.

        :param path: the relative path where to store the object in the repository.
        :param content: the content to store.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileExistsError: if an object already exists at the given path.
        """
        return self.base.repository.put_object_from_bytes(content, path)

    def put_object_from_filelike(self, handle: io.BufferedReader, path: str) -> None:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :param path: the relative path where to store the object in the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        return self.base.repository.put_object_from_filelike(handle, path)

    def put_object_from_file(self, filepath: str, path: str) -> None:
        """Store a new object under `path` with contents of the file located at `filepath` on the local file system.

        :param filepath: absolute path of file whose contents to copy to the repository
        :param path: the relative path where to store the object in the repository.
        :raises TypeError: if the path is not a string and relative path, or the handle is not a byte stream.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        return self.base.repository.put_object_from_file(filepath, path)

    def put_object_from_tree(self, filepath: str, path: str | None = None) -> None:
        """Store the entire contents of `filepath` on the local file system in the repository with under given `path`.

        :param filepath: absolute path of the directory whose contents to copy to the repository.
        :param path: the relative path where to store the objects in the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        return self.base.repository.put_object_from_tree(filepath, path)

    def walk(self, path: FilePath | None = None) -> t.Iterable[tuple[pathlib.PurePath, list[str], list[str]]]:
        """Walk over the directories and files contained within this repository.

        .. note:: the order of the dirname and filename lists that are returned is not necessarily sorted. This is in
            line with the ``os.walk`` implementation where the order depends on the underlying file system used.

        :param path: the relative path of the directory within the repository whose contents to walk.
        :return: tuples of root, dirnames and filenames just like ``os.walk``, with the exception that the root path is
            always relative with respect to the repository root, instead of an absolute path and it is an instance of
            ``pathlib.PurePath`` instead of a normal string
        """
        yield from self.base.repository.walk(path)

    def glob(self) -> t.Iterable[pathlib.PurePath]:
        """Yield a recursive list of all paths (files and directories)."""
        yield from self.base.repository.glob()

    def copy_tree(self, target: str | pathlib.Path, path: FilePath | None = None) -> None:
        """Copy the contents of the entire node repository to another location on the local file system.

        :param target: absolute path of the directory where to copy the contents to.
        :param path: optional relative path whose contents to copy.
        """
        self.base.repository.copy_tree(target, path)

    def delete_object(self, path: str) -> None:
        """Delete the object from the repository.

        :param key: fully qualified identifier for the object within the repository.
        :raises TypeError: if the path is not a string and relative path.
        :raises FileNotFoundError: if the file does not exist.
        :raises IsADirectoryError: if the object is a directory and not a file.
        :raises OSError: if the file could not be deleted.
        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self.base.repository.delete_object(path)

    def erase(self) -> None:
        """Delete all objects from the repository.

        :raises `~aiida.common.exceptions.ModificationNotAllowed`: when the node is stored and therefore immutable.
        """
        self.base.repository.erase()
