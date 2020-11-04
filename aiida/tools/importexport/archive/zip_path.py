# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A implementation of the ``pathlib.Path`` interface for ``zipfile.ZipFile``."""
# see also https://github.com/twisted/twisted/blob/trunk/src/twisted/python/zippath.py

from pathlib import Path, PosixPath
from types import TracebackType
from typing import cast, Iterable, Optional, Set, Type, Union
import zipfile

__all__ = ('ZipPath',)


class ZipPath:
    """A wrapper around ``zipfile.ZipFile``, to provide an interface equivalent to ``pathlib.Path``

    For reading zip files, you can use it directly::

        path = ZipPath('path/to/file.zip', mode='r')
        sub_path = path / 'folder' / 'file.txt'
        assert sub_path.filepath == 'path/to/file.zip'
        assert sub_path.zippath == 'folder/file.txt'
        assert sub_path.exists() and sub_path.is_file()
        assert sub_path.parent.is_dir()
        content = sub_path.read_text()

    For writing zip files, you should use within a context manager, or directly call the ``close`` method::

        with ZipPath('path/to/file.zip', mode='w', compression=zipfile.ZIP_DEFLATED) as path:
            (path / 'new_file.txt').write_text('hallo world')
            # there are also some features equivalent to shutil
            (path / 'other_file.txt').copyfile('path/to/external_file.txt')
            (path / 'other_folder').copytree('path/to/external_folder', pattern='*')

    Note with zipfile is not possible to overwrite existing files (it will raise a ``FileExistsError``).

    """

    ZIP_PATH_SEP: str = '/'  # In zipfiles, "/" is universally used as the path separator, regardless of platform.

    def __init__(
        self,
        path: Union[str, Path, 'ZipPath'],
        *,
        mode: str = 'r',
        internal_path: Optional[str] = None,
        allow_zip64: bool = True,
        compression: int = zipfile.ZIP_DEFLATED
    ):
        """Initialise a zip path item.

        :param path: the path to the zip file, or another instance of a ZipPath
        :param internal_path: the path within the zipfile (always use `/` separators)
        :param mode: the mode with which to open the zipfile,
            either read 'r', write 'w', exclusive create 'x', or append 'a'
        :param allow_zip64:  if True, the ZipFile will create files with ZIP64 extensions when needed
        :param compression: ``zipfile.ZIP_STORED`` (no compression), ``zipfile.ZIP_DEFLATED`` (requires zlib),
                            ``zipfile.ZIP_BZIP2`` (requires bz2) or ``zipfile.ZIP_LZMA`` (requires lzma)

        """
        internal_path = cast(str, internal_path or '')
        assert not internal_path.startswith(self.ZIP_PATH_SEP), 'internal_path must be relative'
        assert not any(p == '..' for p in internal_path.split(self.ZIP_PATH_SEP)
                       ), ("internal_path should not contain any '..'")

        if isinstance(path, (str, Path)):
            self._filepath = Path(path)
            self._zippath = self._normalize_zippath(internal_path)
            self._mode = mode
            self._zipfile = zipfile.ZipFile(path, mode=mode, compression=compression, allowZip64=allow_zip64)
        else:
            self._filepath = path._filepath
            self._zippath = self._normalize_zippath(internal_path)
            self._zipfile = path._zipfile
            self._mode = path._mode

    @staticmethod
    def _normalize_zippath(path: Union[str, Path]) -> str:
        path = PosixPath(path).as_posix()
        return path

    def __repr__(self) -> str:
        """Return the string representation of the zip path."""
        return f'ZipPath({self._filepath}::{self._zippath})'

    def __eq__(self, item: object) -> bool:
        """Return whether the external and internal path are equal"""
        if not isinstance(item, ZipPath):
            return False
        return (item._filepath, item._zippath) == (self._filepath, self._zippath)

    @property
    def filepath(self) -> Path:
        """Return the path to the zip file."""
        return self._filepath

    @property
    def zippath(self) -> str:
        """Return the current internal path within the zip file."""
        return self._zippath

    def iter_dirs(self) -> Iterable[str]:
        """Iterate through all directory paths.

        Note: this is necessary, since the zipfile does not strictly store all folders in the namelist.
        """
        yield self._normalize_zippath('')
        yielded: Set[str] = {self._normalize_zippath('')}
        for info in self._zipfile.infolist():
            parts = list(PosixPath(info.filename).parts) + ([''] if info.is_dir() else [])
            for i in range(len(parts)):
                parent = self._normalize_zippath(self.ZIP_PATH_SEP.join(parts[:-i]))
                if parent not in yielded:
                    yielded.add(parent)
                    yield parent

    def close(self):
        """Close the zipfile."""
        self._zipfile.close()

    def __enter__(self):
        """Enter the zipfile for reading/writing."""
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        """Exit the zipfile and close."""
        self.close()

    # pathlib like interface

    @property
    def name(self) -> str:
        """Return the basename of the current internal path within the zip file."""
        return PosixPath(self._zippath).name

    @property
    def parent(self) -> 'ZipPath':
        """Return the parent of the current internal path within the zip file."""
        path = PosixPath(self._zippath).parent.as_posix()
        return self.__class__(self, internal_path=path)

    def is_dir(self):
        """Whether this path is a directory."""
        try:
            info = self._zipfile.getinfo(self.zippath)
        except KeyError:
            info = None
        if info and info.is_dir():
            return True
        return any(self._zippath == p for p in self.iter_dirs())

    def is_file(self):
        """Whether this path is a regular file."""
        try:
            info = self._zipfile.getinfo(self.zippath)
        except KeyError:
            return False
        return not info.is_dir()

    def exists(self) -> bool:
        """Whether this path exists."""
        return self.is_file() or self.is_dir()

    def joinpath(self, *args) -> 'ZipPath':
        """Combine this path with one or several arguments, and return a new path."""
        path = PosixPath(self._zippath).joinpath(*args).as_posix()
        return self.__class__(self, internal_path=path)

    def __truediv__(self, path: str) -> 'ZipPath':
        """Combine this path with another, and return a new path."""
        path = PosixPath(self._zippath).joinpath(path).as_posix()
        return self.__class__(self, internal_path=path)

    def _write(self, content: Union[str, bytes]):
        """Write content to the zip path."""
        if self.exists():
            raise FileExistsError(f"cannot write to an existing path: '{self.zippath}'")
        if self._mode == 'r':
            with self._zipfile.open(self.zippath, 'w') as handle:
                handle.write(content)  # type: ignore
        else:
            self._zipfile.writestr(self.zippath, content)

    def write_bytes(self, content: bytes):
        """Create the file and write bytes to it."""
        self._write(content)

    def write_text(self, content: str):
        """Create the file and write text to it."""
        self._write(content)

    def read_bytes(self) -> bytes:
        """Read bytes from the file."""
        try:
            content = self._zipfile.read(self.zippath)
        except KeyError:
            raise FileNotFoundError(f"No such file: '{self.zippath}'")
        return content

    def read_text(self, encoding='utf8') -> str:
        """Read text from the file."""
        content = self.read_bytes()
        return content.decode(encoding=encoding)

    def iterdir(self) -> Iterable['ZipPath']:
        """Iterate over the files and folders in this directory (non-recursive)."""
        if self.is_file():
            raise NotADirectoryError(f"Not a directory: ;{self.zippath}'")

        cur_parts = PosixPath(self._zippath).parts
        cur_parts_len = len(cur_parts)

        yielded = set()

        # we also have to find folders that are not specifically stored in the namelist
        for info in self._zipfile.infolist():
            parts = PosixPath(info.filename).parts
            if parts[:cur_parts_len] == cur_parts:
                try:
                    item = parts[cur_parts_len]
                except IndexError:
                    continue
                if item not in yielded:
                    yielded.add(item)
                    yield self.__class__(self, internal_path=item)

        if not yielded:
            try:
                self._zipfile.getinfo(self.zippath)
            except KeyError:
                raise FileNotFoundError(f"No such file or directory: '{self.zippath}'")

    # shutil like interface

    def copyfile(self, path: Union[str, Path]):
        """Create a file with the bytes from path as its content."""
        if self._mode == 'r':
            raise IOError("Cannot write a file in read ('r') mode")
        if self.exists():
            raise FileExistsError(f"cannot copy to an existing path: '{self.zippath}'")
        path = cast(Path, Path(path))
        if not path.exists():
            raise FileNotFoundError(f'Source file not found: {path}')
        if not path.is_file():
            raise IOError(f'Source is not a file: {path}')

        self._zipfile.write(path, self.zippath)

    def copytree(self, path: Union[str, Path], pattern: str = '**/*', symlinks: bool = False):
        """Recursively copy a directory tree to this path.

        :param pattern: the glob pattern used to iterate through the path directory.
            Use this to filter files to copy.
        :param symlinks: whether to copy symbolic links

        """
        if self._mode == 'r':
            raise IOError("Cannot write a directory in read ('r') mode")
        if self.exists():
            raise FileExistsError(f"cannot copy to an existing path: '{self.zippath}'")
        path = cast(Path, Path(path))
        if not path.exists():
            raise FileNotFoundError(f'Source file not found: {path}')
        if not path.is_dir():
            raise IOError(f'Source is not a directory: {path}')
        self._zipfile.write(path, self.zippath)
        for subpath in path.glob(pattern):
            if subpath.is_dir() or (subpath.is_file() and (symlinks or not subpath.is_symlink())):
                zippath = self.ZIP_PATH_SEP.join([self.zippath, subpath.relative_to(path).as_posix()])
                self._zipfile.write(subpath, zippath)
