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
import pathlib
import shutil
import tempfile
import typing as t

from aiida.common import exceptions
from aiida.common.lang import override, type_check
from aiida.common.typing import FilePath
from aiida.orm.cli import CliFieldInfo
from aiida.orm.decorators import attribute
from aiida.orm.decorators.repo import RepoFiles, RepoSourceCliInput, file_to_repo_files, repo_source
from aiida.orm.nodes.data.data import Data, DataInterface

__all__ = ('SinglefileData', 'SinglefileInterface')

_DEFAULT_FILENAME = 'file.txt'


def _singlefile_to_repo_files(filepath: pathlib.Path, context: t.Mapping[str, t.Any]) -> RepoFiles:
    """Map a local file to the path selected for its repository entry."""
    attributes = context.get('attributes') or {}
    filename = attributes.get('filename') or filepath.name or _DEFAULT_FILENAME
    return file_to_repo_files(filepath, context, destination=filename)


def _singlefile_string_to_repo_files(
    value: tuple[str, str],
    context: t.Mapping[str, t.Any],
) -> RepoFiles:
    """Map inline text to a repository file."""
    filename, content = value
    attributes = context.get('attributes') or {}
    filename = attributes.get('filename') or filename or _DEFAULT_FILENAME
    content_bytes = content.encode('utf-8')

    def opener() -> t.BinaryIO:
        return io.BytesIO(content_bytes)

    return {filename: opener}


def _collect_singlefile_cli_input() -> dict[str, t.Any]:
    """Interactively choose a file or inline string as SinglefileData content."""
    import click

    source = click.prompt(
        'Singlefile input',
        type=click.Choice(('file', 'string')),
        default='file',
    )

    if source == 'file':
        filepath = click.prompt(
            'File to store',
            type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=pathlib.Path),
        )
        return {'filepath': filepath}

    filename = click.prompt(
        'File name',
        type=str,
        default=_DEFAULT_FILENAME,
    )
    content = click.prompt('File content', type=str, default='', show_default=False)
    return {'string': (filename, content)}


class SinglefileData(Data):
    """ORM representation of a single file in the node repository."""

    @attribute(
        required_once_stored=True,
        cli_field_info=CliFieldInfo(
            prompt=False,
            help='Optional. Defaults to the input file name, or `file.txt` if no name is available.',
            priority=1,
        ),
    )
    def filename(self) -> str | None:
        """The name of the file stored in the repository."""
        return self.base.attributes.get('filename')

    @filename.setter
    def filename(self, value: str | None) -> None:
        type_check(value, str)
        self.base.attributes.set('filename', value)

    @repo_source(
        cli_inputs=(
            RepoSourceCliInput(
                name='string',
                annotation=str,
                nargs=2,
                mapper=_singlefile_string_to_repo_files,
                cli_field_info=CliFieldInfo(
                    prompt=False,
                    help='Provide inline content as NAME and a string. `--filename` will override the name.',
                    short_name='-s',
                ),
            ),
            RepoSourceCliInput(
                name='filepath',
                annotation=pathlib.Path,
                mapper=_singlefile_to_repo_files,
                cli_field_info=CliFieldInfo(
                    prompt=False,
                    help='Use a local file as the source content.',
                    short_name='-f',
                ),
            ),
        ),
        min_files=1,
        max_files=1,
        interactive_collector=_collect_singlefile_cli_input,
    )
    def _singlefile(self) -> pathlib.PurePath | None:
        """The path of the file stored in the node repository."""
        if self.filename is None:
            return None

        return pathlib.PurePath(self.filename)

    def _validate(self) -> None:
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


class SinglefileInterface(DataInterface[SinglefileData]):
    """Detached, file-backed value interface for `SinglefileData`."""

    _orm_cls = SinglefileData

    filename: str
    file: pathlib.Path

    DEFAULT_FILENAME = _DEFAULT_FILENAME

    def __init__(
        self,
        file: FilePath | t.IO | None = None,
        *,
        filename: FilePath | None = None,
        content: str | bytes | None = None,
    ) -> None:
        """Initialize the interface from a path, file-like object, or inline content.

        :param file: local file path or file-like object to copy.
        :param filename: optional filename to store on the node.
        :param content: optional string or byte content to store.
        """
        self._tempdir = tempfile.TemporaryDirectory()

        if file is not None and content is not None:
            raise ValueError('cannot specify both `file` and `content`.')

        if content is not None:
            if isinstance(content, str):
                file = io.BytesIO(content.encode('utf-8'))
            else:
                file = io.BytesIO(content)

        if file is None:
            raise ValueError('a file or content must be provided.')

        self.set_file(file, filename=filename)

    @property
    def content(self) -> bytes:
        """Return the content of the file as bytes."""
        return self.file.read_bytes()

    @t.overload
    @contextlib.contextmanager
    def open(self, mode: t.Literal['r'] = ...) -> t.Generator[t.TextIO, None, None]: ...

    @t.overload
    @contextlib.contextmanager
    def open(self, mode: t.Literal['rb'] = ...) -> t.Generator[t.BinaryIO, None, None]: ...

    @contextlib.contextmanager
    def open(self, mode: t.Literal['r', 'rb'] = 'r') -> t.Generator[t.BinaryIO | t.TextIO, None, None]:
        """Open the file content.

        :param mode: the mode with which to open the file handle (default: read mode)
        :return: a file handle
        """
        if mode == 'rb':
            with self.file.open('rb') as handle:
                yield handle
        else:
            with self.file.open('r', encoding='utf-8') as handle:
                yield handle

    @contextlib.contextmanager
    def as_path(self) -> t.Generator[pathlib.Path, None, None]:
        """Yield a local path to the file.

        The path remains available while this interface is alive.

        :return: path to the file.
        """
        yield self.file

    @t.overload
    def get_content(self, mode: t.Literal['rb']) -> bytes: ...

    @t.overload
    def get_content(self, mode: t.Literal['r'] = 'r') -> str: ...

    @t.overload
    def get_content(self, mode: t.Literal['r', 'rb']) -> str | bytes: ...

    def get_content(self, mode: t.Literal['r', 'rb'] = 'r') -> str | bytes:
        """Return the content as text or bytes, depending on ``mode``.

        :param mode: the mode with which to read the content (default: text mode).
        :return: the content as text or bytes.
        """
        with self.open(mode=mode) as handle:  # type: ignore[call-overload]
            return handle.read()

    def set_file(self, file: FilePath | t.IO, *, filename: FilePath | None = None) -> None:
        """Replace the interface content with a copy of a path or file-like object.

        :param file: local file path or file-like object to copy.
        :param filename: optional filename to store on the node.
        """
        if isinstance(file, (str, pathlib.PurePath)):
            source = pathlib.Path(file)
            source_filename = source.name
        else:
            source = None
            try:
                source_filename = pathlib.Path(file.name).name
            except (AttributeError, TypeError):
                source_filename = ''

        filename = str(filename) if filename is not None else source_filename or self.DEFAULT_FILENAME
        basename = pathlib.PurePath(filename).name
        if basename in ('', '.', '..'):
            basename = 'content'
        destination = pathlib.Path(self._tempdir.name) / basename

        with tempfile.NamedTemporaryFile(dir=self._tempdir.name, delete=False) as temporary:
            temporary_path = pathlib.Path(temporary.name)
            if source is not None:
                with source.open('rb') as source_handle:
                    shutil.copyfileobj(source_handle, temporary)
            else:
                chunk = file.read(1024 * 1024)
                if isinstance(chunk, str):
                    while chunk:
                        temporary.write(chunk.encode('utf-8'))
                        chunk = file.read(1024 * 1024)
                else:
                    temporary.write(chunk)
                    shutil.copyfileobj(file, temporary)

        temporary_path.replace(destination)

        old_file = getattr(self, '_file', None)
        self.file = destination
        self.filename = filename

        if old_file is not None and old_file != destination:
            old_file.unlink(missing_ok=True)

    @override
    def _get_files(self) -> dict[str, t.Callable[[], t.BinaryIO | None]]:
        """Return the file opener for conversion to a node."""
        return {self.filename: lambda: self.file.open('rb')}

    @override
    def _set_files(self, entity: SinglefileData) -> None:
        """Copy the node's repository file into the interface-owned temporary directory."""
        self._tempdir = tempfile.TemporaryDirectory()

        filename = entity.filename
        if filename is None:
            raise ValueError('The entity does not have a filename.')

        basename = pathlib.PurePath(filename).name
        if basename in ('', '.', '..'):
            basename = 'content'
        destination = pathlib.Path(self._tempdir.name) / basename
        entity.base.repository.copy_file(destination, filename)

        self.file = destination
        self.filename = filename
