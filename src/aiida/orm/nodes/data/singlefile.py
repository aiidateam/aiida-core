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

from aiida.common import exceptions
from aiida.common.pydantic import MetadataField
from aiida.common.typing import FilePath

from .data import Data

__all__ = ('SinglefileData',)


class SinglefileData(Data):
    """Data class that can be used to store a single file in its repository."""

    DEFAULT_FILENAME = 'file.txt'

    class Model(Data.Model):
        content: bytes = MetadataField(
            description='The file content.',
            model_to_orm=lambda model: io.BytesIO(model.content),  # type: ignore[attr-defined]
        )
        filename: t.Optional[str] = MetadataField(None, description='The filename. Defaults to `file.txt`.')

    @classmethod
    def from_string(cls, content: str, filename: str | pathlib.Path | None = None, **kwargs: t.Any) -> 'SinglefileData':
        """Construct a new instance and set ``content`` as its contents.

        :param content: The content as a string.
        :param filename: Specify filename to use (defaults to ``file.txt``).
        """
        return cls(io.StringIO(content), filename, **kwargs)

    @classmethod
    def from_bytes(
        cls, content: bytes, filename: str | pathlib.Path | None = None, **kwargs: t.Any
    ) -> 'SinglefileData':
        """Construct a new instance and set ``content`` as its contents.

        :param content: The content as bytes.
        :param filename: Specify filename to use (defaults to ``file.txt``).
        """
        return cls(io.BytesIO(content), filename, **kwargs)

    def __init__(
        self,
        file: str | pathlib.Path | t.IO | None = None,
        filename: str | pathlib.Path | None = None,
        content: str | pathlib.Path | t.IO | None = None,
        **kwargs: t.Any,
    ) -> None:
        """Construct a new instance and set the contents to that of the file.

        :param file: an absolute filepath or filelike object whose contents to copy.
            Hint: Pass io.BytesIO(b"my string") to construct the SinglefileData directly from a string.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        super().__init__(**kwargs)

        if file is not None and content is not None:
            raise ValueError('cannot specify both `file` and `content`.')

        if content is not None:
            file = content

        if file is not None:
            self.set_file(file, filename=filename)

    @property
    def content(self) -> bytes:
        return self.get_content(mode='rb')

    @property
    def filename(self) -> str:
        """Return the name of the file stored.

        :return: the filename under which the file is stored in the repository
        """
        return self.base.attributes.get('filename')

    @t.overload
    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['r'] = ...) -> t.Iterator[t.TextIO]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: FilePath, mode: t.Literal['rb']) -> t.Iterator[t.BinaryIO]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: None = None, mode: t.Literal['r'] = ...) -> t.Iterator[t.TextIO]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, path: None = None, mode: t.Literal['rb'] = ...) -> t.Iterator[t.BinaryIO]: ...

    @contextlib.contextmanager
    def open(
        self, path: FilePath | None = None, mode: t.Literal['r', 'rb'] = 'r'
    ) -> t.Iterator[t.BinaryIO] | t.Iterator[t.TextIO]:
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
    def as_path(self) -> t.Iterator[pathlib.Path]:
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

    def set_file(self, file: str | pathlib.Path | t.IO, filename: str | pathlib.Path | None = None) -> None:
        """Store the content of the file in the node's repository, deleting any other existing objects.

        :param file: an absolute filepath or filelike object whose contents to copy
            Hint: Pass io.BytesIO(b"my string") to construct the file directly from a string.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        if isinstance(file, (str, pathlib.Path)):
            is_filelike = False

            key = os.path.basename(file)
            if not os.path.isabs(file):
                raise ValueError(f'path `{file}` is not absolute')

            if not os.path.isfile(file):
                raise ValueError(f'path `{file}` does not correspond to an existing file')
        else:
            is_filelike = True
            try:
                key = os.path.basename(file.name)
            except AttributeError:
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

        self.base.attributes.set('filename', key)

    def _validate(self) -> bool:
        """Ensure that there is one object stored in the repository, whose key matches value set for `filename` attr."""
        super()._validate()

        try:
            filename = self.filename
        except AttributeError:
            raise exceptions.ValidationError('the `filename` attribute is not set.')

        objects = self.base.repository.list_object_names()

        if [filename] != objects:
            raise exceptions.ValidationError(
                f'respository files {objects} do not match the `filename` attribute `{filename}`.'
            )

        return True
