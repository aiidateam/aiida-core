# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A implementation of the ``pathlib.Path`` interface for ``zipfile.ZipFile``.

The implementation is partially based on back-porting ``zipfile.Path`` (new in python 3.8)
"""
from contextlib import contextmanager
import itertools
from pathlib import Path
import posixpath
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
        assert sub_path.at == 'folder/file.txt'
        assert sub_path.exists() and sub_path.is_file()
        assert sub_path.parent.is_dir()
        content = sub_path.read_text()

    For writing zip files, you should use within a context manager, or directly call the ``close`` method::

        with ZipPath('path/to/file.zip', mode='w', compression=zipfile.ZIP_DEFLATED) as path:
            (path / 'new_file.txt').write_text('hallo world')
            # there are also some features equivalent to shutil
            (path / 'other_file.txt').copyfile('path/to/external_file.txt')
            (path / 'other_folder').copytree('path/to/external_folder', pattern='*')

    Note that ``zipfile`` does not allow to overwrite existing files (it will raise a ``FileExistsError``).

    """

    __repr = '{self.__class__.__name__}({self.root.filename!r}, {self.at!r})'

    def __init__(
        self,
        path: Union[str, Path, 'ZipPath'],
        *,
        mode: str = 'r',
        at: str = '',  # pylint: disable=invalid-name
        allow_zip64: bool = True,
        compression: int = zipfile.ZIP_DEFLATED
    ):
        """Initialise a zip path item.

        :param path: the path to the zip file, or another instance of a ZipPath
        :param at: the path within the zipfile (always use posixpath `/` separators)
        :param mode: the mode with which to open the zipfile,
            either read 'r', write 'w', exclusive create 'x', or append 'a'
        :param allow_zip64:  if True, the ZipFile will create files with ZIP64 extensions when needed
        :param compression: ``zipfile.ZIP_STORED`` (no compression), ``zipfile.ZIP_DEFLATED`` (requires zlib),
                            ``zipfile.ZIP_BZIP2`` (requires bz2) or ``zipfile.ZIP_LZMA`` (requires lzma)

        """
        if posixpath.isabs(at):
            raise ValueError(f"'at' cannot be an absolute path: {at}")
        assert not any(p == '..' for p in at.split(posixpath.sep)), ("'at' should not contain any '..'")
        self._at = at.rstrip('/')

        if isinstance(path, (str, Path)):
            self._filepath = Path(path)
            self._zipfile = zipfile.ZipFile(path, mode=mode, compression=compression, allowZip64=allow_zip64)
        else:
            self._filepath = path._filepath
            self._zipfile = path._zipfile

    def __str__(self):
        return posixpath.join(self.root.filename, self.at)

    def __repr__(self):
        return self.__repr.format(self=self)

    def __eq__(self, item: object) -> bool:
        """Return whether the external and internal path are equal"""
        if not isinstance(item, ZipPath):
            return False
        if item._at != self._at:
            return False
        return item._filepath.resolve(strict=False) == self._filepath.resolve(strict=False)

    @property
    def filepath(self) -> Path:
        """Return the path to the zip file."""
        return self._filepath

    @property
    def root(self) -> zipfile.ZipFile:
        """Return the root zip file."""
        return self._zipfile

    @property
    def at(self) -> str:  # pylint: disable=invalid-name
        """Return the current internal path within the zip file."""
        return self._at

    def _all_at_set(self) -> Set[str]:
        """Iterate through all file and directory paths in the zip file.

        Note: this is necessary, since the zipfile does not strictly store all directories in the namelist.
        """
        names = self._zipfile.namelist()
        parents = itertools.chain.from_iterable(map(_parents, names))
        return set(p.rstrip('/') for p in itertools.chain([''], names, parents))

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
    def name(self):
        """Return the basename of the current internal path within the zip file."""
        return posixpath.basename(self.at)

    @property
    def parent(self) -> 'ZipPath':
        """Return the parent of the current internal path within the zip file."""
        parent_at = posixpath.dirname(self.at)
        return self.__class__(self, at=parent_at)

    def is_dir(self):
        """Whether this path is an existing directory."""
        return self.exists() and not self.is_file()

    def is_file(self):
        """Whether this path is an existing regular file."""
        try:
            info = self._zipfile.getinfo(self.at)
        except KeyError:
            return False
        return not info.is_dir()

    def exists(self) -> bool:
        """Whether this path exists."""
        if self.at == '':
            return True
        try:
            self._zipfile.getinfo(self.at)
            return True
        except KeyError:
            pass
        try:
            self._zipfile.getinfo(self.at + '/')
            return True
        except KeyError:
            pass
        # note, we could just check this, but it takes time/memory to construct
        return self.at in self._all_at_set()

    def joinpath(self, *paths) -> 'ZipPath':
        """Combine this path with one or several arguments, and return a new path."""
        return self.__class__(self, at=posixpath.join(self.at, *paths))

    def __truediv__(self, path: str) -> 'ZipPath':
        """Combine this path with another, and return a new path."""
        return self.__class__(self, at=posixpath.join(self.at, path))

    @contextmanager
    def open(self, mode: str = 'rb'):
        """Open the file pointed by this path and return a file object."""
        # zip file open misleading signals 'r', 'w', when actually they are byte mode
        if mode not in {'rb', 'wb'}:
            raise ValueError('open() requires mode "rb" or "wb"')
        with self.root.open(self.at, mode=mode[0]) as handle:
            yield handle

    def _write(self, content: Union[str, bytes]):
        """Write content to the zip path."""
        if self.is_file():
            raise FileExistsError(f"cannot write to an existing path: '{self.at}'")
        self._zipfile.writestr(self.at, content)

    def write_bytes(self, content: bytes):
        """Create the file and write bytes to it."""
        self._write(content)

    def write_text(self, content: str, encoding='utf8'):
        """Create the file and write text to it."""
        self._write(content.encode(encoding=encoding))

    def read_bytes(self) -> bytes:
        """Read bytes from the file."""
        try:
            content = self._zipfile.read(self.at)
        except KeyError:
            raise FileNotFoundError(f"No such file: '{self.at}'")
        return content

    def read_text(self, encoding='utf8') -> str:
        """Read text from the file."""
        content = self.read_bytes()
        return content.decode(encoding=encoding)

    def iterdir(self) -> Iterable['ZipPath']:
        """Iterate over the files and folders in this directory (non-recursive)."""
        if self.is_file():
            raise NotADirectoryError(f"Not a directory: '{self.at}'")

        found_name = False
        for name in self._all_at_set():
            if name == self.at:
                found_name = True
            elif posixpath.dirname(name) == self.at:
                yield self.__class__(self, at=name)

        if not found_name:
            raise FileNotFoundError(f"No such file or directory: '{self.at}'")

    # shutil like interface

    def copyfile(self, path: Union[str, Path]):
        """Create a file with the bytes from path as its content."""
        if 'r' in self.root.mode:  # type: ignore
            raise IOError("Cannot write a file in read ('r') mode")

        path = cast(Path, Path(path))
        if not path.exists():
            raise FileNotFoundError(f'Source file not found: {path}')
        if not path.is_file():
            raise IOError(f'Source is not a file: {path}')

        if self.exists():
            raise FileExistsError(f"cannot copy to an existing path: '{self.at}'")

        self._zipfile.write(path, self.at)

    def copytree(
        self, path: Union[str, Path], pattern: str = '**/*', symlinks: bool = False, check_exists: bool = True
    ):
        """Recursively copy a directory tree to this path.

        :param pattern: the glob pattern used to iterate through the path directory.
            Use this to filter files to copy.
        :param symlinks: whether to copy symbolic links
        :param check_exists: whether to check if the ZipPath already exists (this can be time consuming for a large zip)

        """
        if 'r' in self.root.mode:  # type: ignore
            raise IOError("Cannot write a directory in read ('r') mode")

        path = cast(Path, Path(path))
        if not path.exists():
            raise FileNotFoundError(f'Source file not found: {path}')
        if not path.is_dir():
            raise IOError(f'Source is not a directory: {path}')

        if check_exists and self.exists():
            raise FileExistsError(f"cannot copy to an existing path: '{self.at}'")

        # always write the base folder
        self._zipfile.write(path, self.at)

        for subpath in path.glob(pattern):
            if subpath.is_dir() or (subpath.is_file() and (symlinks or not subpath.is_symlink())):
                zippath = posixpath.normpath(posixpath.join(self.at, subpath.relative_to(path).as_posix()))
                self._zipfile.write(subpath, zippath)


def _parents(path: str) -> Iterable[str]:
    """
    Given a path with elements separated by
    posixpath.sep, generate all parents of that path.

    >>> list(_parents('b/d'))
    ['b']
    >>> list(_parents('/b/d/'))
    ['/b']
    >>> list(_parents('b/d/f/'))
    ['b/d', 'b']
    >>> list(_parents('b'))
    []
    >>> list(_parents(''))
    []
    """
    return itertools.islice(_ancestry(path), 1, None)


def _ancestry(path: str) -> Iterable[str]:
    """
    Given a path with elements separated by
    posixpath.sep, generate all elements of that path

    >>> list(_ancestry('b/d'))
    ['b/d', 'b']
    >>> list(_ancestry('/b/d/'))
    ['/b/d', '/b']
    >>> list(_ancestry('b/d/f/'))
    ['b/d/f', 'b/d', 'b']
    >>> list(_ancestry('b'))
    ['b']
    >>> list(_ancestry(''))
    []
    """
    path = path.rstrip(posixpath.sep)
    while path and path != posixpath.sep:
        yield path
        path, _ = posixpath.split(path)
