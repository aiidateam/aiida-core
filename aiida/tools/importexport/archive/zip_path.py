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
from collections.abc import Sequence, MutableMapping
from contextlib import contextmanager, suppress
import io
import itertools
import os
from pathlib import Path
import posixpath
import threading
from types import TracebackType
from typing import Any, cast, Dict, IO, Iterable, List, Optional, Set, Type, Union
import zipfile

__all__ = ('ZipPath', 'ZipFileExtra', 'FilteredZipInfo', 'StopZipIndexRead')


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
        compression: int = zipfile.ZIP_DEFLATED,
        name_to_info: Optional[Dict[str, zipfile.ZipInfo]] = None
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

        # Note ``zipfile.ZipInfo.filename`` of directories always end `/`
        # but we store without, to e.g. correctly compute parent/file names
        self._at = at.rstrip('/')

        if isinstance(path, (str, Path)):
            self._filepath = Path(path)
            self._zipfile = ZipFileExtra(
                path, mode=mode, compression=compression, allowZip64=allow_zip64, name_to_info=name_to_info
            )
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

        It is cached on the zipfile instance if it is in read mode ('r'), since then the name list cannot change.

        """
        read_mode = (self._zipfile.mode == 'r')  # type: ignore
        if read_mode:
            with suppress(AttributeError):
                return self._zipfile.__all_at  # type: ignore # pylint: disable=protected-access
        names = self._zipfile.namelist()
        parents = itertools.chain.from_iterable(map(_parents, names))
        all_set = set(p.rstrip('/') for p in itertools.chain([''], names, parents))
        if read_mode:
            self._zipfile.__all_at = all_set  # type: ignore # pylint: disable=protected-access,attribute-defined-outside-init
        return all_set

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
        with suppress(KeyError):
            self._zipfile.getinfo(self.at)
            return True
        with suppress(KeyError):
            self._zipfile.getinfo(self.at + '/')
            return True
        # note, we could just check this, but it can takes time/memory to construct
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


class FileList(Sequence):
    """A list of ``zipfile.ZipInfo`` which mirrors the ``zipfile.ZipFile.NameToInfo`` mapping.

    For indexing, assumes that ``NameToInfo`` is an ordered dict.
    """

    def __init__(self, name_to_info: Dict[str, zipfile.ZipInfo]):
        self._name_to_info = name_to_info

    def __getitem__(self, item):
        key = list(self._name_to_info)[item]
        return self._name_to_info[key]

    def __len__(self):
        return self._name_to_info.__len__()

    def __contains__(self, item: Any):
        if not isinstance(item, zipfile.ZipInfo):
            return False
        key = item.filename
        return key in self._name_to_info

    def __iter__(self):
        for value in self._name_to_info.values():
            yield value

    def __reversed__(self):
        return reversed(list(self._name_to_info.values()))

    def append(self, item: zipfile.ZipInfo):
        """Add a ``ZipInfo`` object."""
        assert isinstance(item, zipfile.ZipInfo)
        assert item.filename not in self._name_to_info, 'cannot append an existing ZipInfo'
        self._name_to_info[item.filename] = item


class StopZipIndexRead(Exception):
    """An exception to signal that the reading of the index should be stopped."""


class FilteredZipInfo(MutableMapping):
    """A mapping which only stores pre-defined ``ZipInfo``s.

    Once all required filenames are set, ``__setitem__`` will raise ``StopZipIndexRead``.

    """

    def __init__(self, filenames: Set[str]):
        self._dict: Dict[str, zipfile.ZipInfo] = {}
        self._filenames = set(filenames)

    def __getitem__(self, name):
        return self._dict.__getitem__(name)

    def __setitem__(self, name, item):
        if name in self._filenames:
            self._dict.__setitem__(name, item)
        if set(self._dict) == self._filenames:
            raise StopZipIndexRead

    def __delitem__(self, name):
        self._dict.__delitem__(name)

    def __iter__(self):
        return self._dict.__iter__()

    def __len__(self):
        return self._dict.__len__()


class ZipFileExtra(zipfile.ZipFile):
    """A subclass of ``zipfile.ZipFile``, which allows for specifying the name_to_info mapping.

    This mapping holds the zip file object index, which is fully generated on initiation.
    An example of its use, is when reading zip files with large amounts of objects in a memory light manner::

        import shelve
        with shelve.open('name_to_info') as db:
            zipfile = ZipFileExtra('path/to/file.zip', name_to_info=db)

    Additionally, in read mode, the name_to_info object can raise a ``StopZipIndexRead`` on ``__setitem__``.
    This will break the index generation and can be useful,
    for example to efficiently find/read a single object in the zip file::

        zipfile = ZipFileExtra('path/to/file.zip', name_to_info=FilteredZipInfo({'file.txt'}))
        zipfile.read('file.txt')

    """

    def __init__(
        self,
        file: Union[str, Path, IO],
        mode: str = 'r',
        compression: int = zipfile.ZIP_STORED,
        allowZip64: bool = True,
        compresslevel: Optional[int] = None,
        *,
        strict_timestamps: bool = True,
        name_to_info: Optional[MutableMapping] = None
    ):
        """Open the ZIP file with mode read 'r', write 'w', exclusive create 'x', or append 'a'.

        :param file: The zip file to use
        :param mode: The mode in which to open the zip file
        :param compression: the ZIP compression method to use when writing the archive
        :param allowZip64: If True, zipfile will create ZIP files that use the ZIP64 extensions,
            when the zipfile is larger than 4 GiB
        :param compresslevel: controls the compression level to use when writing files to the archive
        :param strict_timestamps: when set to False, allows to zip files older than 1980-01-01

        :param name_to_info: The dictionary for storing mappings of filename -> ``ZipInfo``,
            if ``None``, defaults to ``{}``

        """
        # pylint: disable=super-init-not-called,invalid-name,too-many-branches,too-many-statements
        if mode not in ('r', 'w', 'x', 'a'):
            raise ValueError("ZipFile requires mode 'r', 'w', 'x', or 'a'")

        zipfile._check_compression(compression)  # type: ignore

        self._allowZip64: bool = allowZip64
        self._didModify: bool = False
        self.debug: int = 0  # Level of printing: 0 through 3
        # Find file info given name
        self.NameToInfo: Dict[str, zipfile.ZipInfo] = name_to_info if name_to_info is not None else {}  # type: ignore
        # List of ZipInfo instances for archive
        self.filelist: List[zipfile.ZipInfo] = FileList(self.NameToInfo)  # type: ignore
        self.compression: int = compression  # Method of compression
        self.compresslevel: Optional[int] = compresslevel
        self.mode: str = mode
        self.pwd: Optional[str] = None
        self._comment: bytes = b''
        self._strict_timestamps: bool = strict_timestamps

        self.filename: str
        self._filePassed: int
        self.fp: IO

        # Check if we were passed a file-like object
        if isinstance(file, os.PathLike):
            file = os.fspath(file)
        if isinstance(file, str):
            # No, it's a filename
            self._filePassed = 0
            self.filename = file
            modeDict = {'r': 'rb', 'w': 'w+b', 'x': 'x+b', 'a': 'r+b', 'r+b': 'w+b', 'w+b': 'wb', 'x+b': 'xb'}
            filemode = modeDict[mode]
            while True:
                try:
                    self.fp = io.open(file, filemode)
                except OSError:
                    if filemode in modeDict:
                        filemode = modeDict[filemode]
                        continue
                    raise
                break
        else:
            self._filePassed = 1
            self.fp = cast(IO, file)
            self.filename = getattr(file, 'name', None)
        self._fileRefCnt = 1
        self._lock = threading.RLock()
        self._seekable = True
        self._writing = False

        try:
            if mode == 'r':
                with suppress(StopZipIndexRead):
                    self._RealGetContents()  # type: ignore
            elif mode in ('w', 'x'):
                # set the modified flag so central directory gets written
                # even if no files are added to the archive
                self._didModify = True
                try:
                    self.start_dir = self.fp.tell()
                except (AttributeError, OSError):
                    self.fp = zipfile._Tellable(self.fp)  # type: ignore
                    self.start_dir = 0
                    self._seekable = False
                else:
                    # Some file-like objects can provide tell() but not seek()
                    try:
                        self.fp.seek(self.start_dir)
                    except (AttributeError, OSError):
                        self._seekable = False
            elif mode == 'a':
                try:
                    # See if file is a zip file
                    self._RealGetContents()  # type: ignore
                    # seek to start of directory and overwrite
                    self.fp.seek(self.start_dir)
                except zipfile.BadZipFile:
                    # file is not a zip file, just append
                    self.fp.seek(0, 2)

                    # set the modified flag so central directory gets written
                    # even if no files are added to the archive
                    self._didModify = True
                    self.start_dir = self.fp.tell()
            else:
                raise ValueError("Mode must be 'r', 'w', 'x', or 'a'")
        except:
            fp = self.fp
            self.fp = None  # type: ignore
            self._fpclose(fp)  # type: ignore
            raise

    def namelist(self):
        """Return a list of file names in the archive."""
        return list(self.NameToInfo)
