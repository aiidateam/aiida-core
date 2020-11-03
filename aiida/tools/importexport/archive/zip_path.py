
import os
from pathlib import Path
from types import TracebackType
from typing import cast, Optional, Type, Union
import zipfile


class ZipPath:
    """A wrapper around ``zipfile.ZipFile``, to provide an interface equivalent to ``pathlib.Path``"""

    def __init__(
        self,
        path: Union[str, Path, 'ZipPath'],
        *,
        internal_path: Optional[str] = None,
        mode: str = 'r',
        allowZip64: bool = True,
        compression: int = zipfile.ZIP_DEFLATED
    ):
        """Initialise a zip path item.

        :param path: the path to the zip file, or another instance of a ZipPath
        :param internal_path: the base path within the zipfile
        :param mode: the mode with which to open the zipfile,
            either read 'r', write 'w', exclusive create 'x', or append 'a'
        :param allowZip64:  if True, the ZipFile will create files with ZIP64 extensions when needed
        :param compression: ``zipfile.ZIP_STORED`` (no compression), ``zipfile.ZIP_DEFLATED`` (requires zlib),
                            ``zipfile.ZIP_BZIP2`` (requires bz2) or ``zipfile.ZIP_LZMA`` (requires lzma)

        """
        internal_path = cast(str, internal_path or '')
        assert not os.path.isabs(internal_path), 'internal_path must be relative'

        if isinstance(path, (str, Path)):
            self._filepath = Path(path)
            self._zippath = os.path.normpath(internal_path or '.')
            self._zipfile = zipfile.ZipFile(path, mode=mode, compression=compression, allowZip64=allowZip64)
        else:
            self._filepath = path._filepath
            self._zippath = os.path.normpath(os.path.join(path._zippath, internal_path))
            self._zipfile = path._zipfile

    def __repr__(self) -> str:
        """Return the string representation of the zip path."""
        return f'ZipPath({self._filepath}::{self._zippath})'

    @property
    def filepath(self) -> Path:
        """Return the path to the zip file."""
        return self._filepath

    @property
    def zippath(self) -> str:
        """Return the current internal path within the zip file."""
        return self._zippath

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
        return os.path.basename(self._zippath)

    def exists(self) -> bool:
        """Whether this path exists."""
        if self.zippath in ('', '.'):
            return True
        try:
            self._zipfile.getinfo(self.zippath)
        except KeyError:
            return False
        return True

    def is_dir(self):
        """Whether this path is a directory."""
        if self.zippath in ('', '.'):
            return True
        try:
            info = self._zipfile.getinfo(self.zippath)
        except KeyError:
            return False
        return info.is_dir()

    def is_file(self):
        """Whether this path is a regular file."""
        if self.zippath in ('', '.'):
            return False
        try:
            info = self._zipfile.getinfo(self.zippath)
        except KeyError:
            return False
        return not info.is_dir()

    def joinpath(self, *args) -> 'ZipPath':
        """Combine this path with one or several arguments, and return a new path."""
        path = os.path.join(*args)
        return self.__class__(self, internal_path=path)

    def __truediv__(self, path: str) -> 'ZipFolder':
        """Combine this path with another, and return a new path."""
        return self.__class__(self, internal_path=path)

    def _write(self, content: Union[str, bytes]):
        """Write content to the zip path."""
        if self.exists():
            raise FileExistsError(f"cannot write to an existing path: '{self.zippath}'")
        if self._zipfile.mode == 'r':
            with self._zipfile.open(self.zippath, 'w') as handle:
                handle.write(content)
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

    def iterdir(self):
        """Iterate over the files in this directory."""
        if not self.is_dir:
            return
        for info in self._zipfile.infolist():
            if info.is_dir():
                continue
            if os.path.normpath(os.path.dirname(info.filename)) == self.zippath:
                yield self.__class__(self, internal_path=os.path.basename(info.filename))

    # shutil like interface

    def copyfile(self, source: Union[str, Path]):
        """Create a file with the bytes from source as its content."""
        if self._zipfile.mode == 'r':
            raise IOError("Cannot write a file in read ('r') mode")
        if self.exists():
            raise FileExistsError(f"cannot copy to an existing path: '{self.zippath}'")
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        if not source.is_file():
            raise IOError(f"Source is not a file: {source}")

        self._zipfile.write(source, self.zippath)

    def copytree(self, source: Union[str, Path], pattern: str = '*', symlinks: bool = False):
        """Recursively copy a directory tree to this path.
        
        :param pattern: the rglob pattern used to iterate through the source directory.
            Use this to filter files to copy.
        :param symlinks: whether to copy symbolic links

        """
        if self._zipfile.mode == 'r':
            raise IOError("Cannot write a directory in read ('r') mode")
        if self.exists():
            raise FileExistsError(f"cannot copy to an existing path: '{self.zippath}'")
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")
        if not source.is_dir():
            raise IOError(f"Source is not a directory: {source}")
        for path in source.rglob(pattern):
            if path.is_dir():
                self._zipfile.write(source, os.path.join(self.zippath, path.relative_to(source)))
            elif path.is_file() and (symlinks or not path.is_symlink()):
                self._zipfile.write(source, os.path.join(self.zippath, path.relative_to(source)))
