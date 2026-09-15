###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data class that can be used to store a single file in its repository."""

from __future__ import annotations

import contextlib
import io
import os
import pathlib
import typing as t

from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.typing import FilePath
from aiida.orm.decorators import attribute
from aiida.orm.nodes.data.data import Data

__all__ = ('SinglefileData',)


class SinglefileData(Data):
    """ORM representation of a single file in the node repository."""

    DEFAULT_FILENAME = 'file.txt'

    @classmethod
    def from_path(
        cls,
        filepath: FilePath,
        filename: FilePath | None = None,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance and set the contents to that of the file.

        :param filepath: an absolute filepath whose contents to copy.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        instance = cls(**kwargs)
        instance.set_file(filepath, filename=filename)
        return instance

    @classmethod
    def from_string(
        cls,
        content: str,
        filename: FilePath | None = None,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance and set ``content`` as its contents.

        :param content: The content as a string.
        :param filename: Specify filename to use (defaults to ``file.txt``).
        """
        instance = cls(**kwargs)
        instance.set_file(io.StringIO(content), filename=filename)
        return instance

    @classmethod
    def from_bytes(
        cls,
        content: bytes,
        filename: FilePath | None = None,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance and set ``content`` as its contents.

        :param content: The content as bytes.
        :param filename: Specify filename to use (defaults to ``file.txt``).
        """
        instance = cls(**kwargs)
        instance.set_file(io.BytesIO(content), filename=filename)
        return instance

    @classmethod
    def from_filelike(
        cls,
        handle: t.IO[t.Any],
        filename: FilePath | None = None,
        **kwargs: t.Any,
    ) -> Self:
        """Construct a new instance and set the contents from a file-like object.

        :param handle: A file-like object whose contents to copy.
        :param filename: Specify filename to use.
        """
        instance = cls(**kwargs)
        instance.set_file(handle, filename=filename)
        return instance

    @attribute(required_once_stored=True)
    def filename(self) -> str | None:
        """The name of the file stored in the repository."""
        return self.base.attributes.get('filename', None)

    @filename.setter
    def filename(self, value: str) -> None:
        self.base.attributes.set('filename', value)

    @property
    def content(self) -> bytes:
        """Return the content of the file as bytes."""
        return self.get_content(mode='rb')

    @t.overload
    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['r'] = ...) -> t.Generator[t.TextIO, None, None]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['rb']) -> t.Generator[t.BinaryIO, None, None]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: None = None, mode: t.Literal['r'] = ...) -> t.Generator[t.TextIO, None, None]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: None = None, mode: t.Literal['rb'] = ...) -> t.Generator[t.BinaryIO, None, None]: ...

    @contextlib.contextmanager
    def open(
        self,
        path: FilePath | None = None,
        mode: t.Literal['r', 'rb'] = 'r',
    ) -> t.Generator[t.BinaryIO, None, None] | t.Generator[t.TextIO, None, None]:
        """Return an open file handle to the content of this data node.

        :param path: the relative path of the object within the repository.
        :param mode: the mode with which to open the file handle (default: read mode)
        :return: a file handle
        """
        if path is None:
            path = self.filename

        with self.base.repository.open(path, mode=mode) as handle:
            yield handle

    @contextlib.contextmanager
    def as_path(self) -> t.Generator[pathlib.Path, None, None]:
        """Make the contents of the file available as a normal filepath on the local file system.

        :param path: optional relative path of the object within the repository.
        :return: the filepath of the content of the repository or object if ``path`` is specified.
        :raises TypeError: if the path is not a string or ``Path``, or is an absolute path.
        :raises FileNotFoundError: if no object exists for the given path.
        """
        with self.base.repository.as_path(self.filename) as filepath:
            yield filepath

    @t.overload
    def get_content(self, mode: t.Literal['rb']) -> bytes: ...

    @t.overload
    def get_content(self, mode: t.Literal['r']) -> str: ...

    def get_content(self, mode: str = 'r') -> str | bytes:
        """Return the content of the single file stored for this data node.

        :param mode: the mode with which to open the file handle (default: read mode)
        :return: the content of the file as a string or bytes, depending on ``mode``.
        """
        with self.open(mode=mode) as handle:  # type: ignore[call-overload]
            return handle.read()

    def set_file(self, file: FilePath | t.IO, filename: FilePath | None = None) -> None:
        """Store the content of the file in the node's repository, deleting any other existing objects.

        :param file: an absolute filepath or filelike object whose contents to copy
            Hint: Pass io.BytesIO(b"my string") to construct the file directly from a string.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        if isinstance(file, (str, pathlib.Path)):
            is_filelike = False

            key = os.path.basename(file)
            if not os.path.isabs(file):
                msg = f'path `{file}` is not absolute'
                raise ValueError(msg)

            if not os.path.isfile(file):
                msg = f'path `{file}` does not correspond to an existing file'
                raise ValueError(msg)
        else:
            is_filelike = True
            try:
                key = os.path.basename(file.name)
            except (AttributeError, TypeError):
                key = self.DEFAULT_FILENAME

        key = str(filename) if filename is not None else key
        existing_object_names = self.base.repository.list_object_names()

        try:
            # Remove the 'key' from the list of currently existing objects such that it is not deleted after storing
            existing_object_names.remove(key)
        except ValueError:
            pass

        if is_filelike:
            self.base.repository.put_object_from_filelike(file, key)  # type: ignore[arg-type]
        else:
            self.base.repository.put_object_from_file(file, key)  # type: ignore[arg-type]

        # Delete any other existing objects (minus the current `key` which was already removed from the list)
        for existing_key in existing_object_names:
            self.base.repository.delete_object(existing_key)

        self.filename = key

    def attach_file(self, filepath: str, fileobj: t.BinaryIO) -> None:
        self.set_file(fileobj, filepath)

    def _validate(self) -> None:
        """Validate the node before storing.

        This check ensures that there is exactly one file object stored in the repository,
        and that the filename attribute is set to the name of that object (forced).

        :return: True if the node is valid
        :raises ValidationError: if the node is not valid
        """
        super()._validate()

        objects = self.base.repository.list_object_names()

        if len(objects) != 1:
            msg = f'expected exactly one repository file, found {len(objects)}: {objects}'
            raise exceptions.ValidationError(msg)

        filename = objects[0]
        fileobj = self.base.repository.get_object(filename)
        if fileobj.is_dir():
            raise exceptions.ValidationError('expected a file, found a directory')

        self.filename = filename
