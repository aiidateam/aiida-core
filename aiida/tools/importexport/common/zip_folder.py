# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Convenience class for interacting with a zipped folder."""
import io
import os
from pathlib import Path
from types import TracebackType
from typing import IO, Optional, Type, Union
import zipfile


class _ZipFileWriter:
    """An open zip file."""

    def __init__(self, zip_file: zipfile.ZipFile, fname: str):
        self._zipfile = zip_file
        self._fname = fname
        self._buffer: Optional[io.StringIO] = None

    def open(self):
        """Open the file for writing."""
        if self._buffer is not None:
            raise IOError('Cannot open again!')
        self._buffer = io.StringIO()

    def write(self, data: str):
        """Write to the file."""
        if self._buffer is None:
            raise IOError('The file writer is not open')
        self._buffer.write(data)

    def close(self):
        """Close to the file."""
        self._buffer.seek(0)
        self._zipfile.writestr(self._fname, self._buffer.read())
        self._buffer = None

    def __enter__(self):
        """Enter the file for writing."""
        self.open()
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        """Close the file."""
        self.close()


class ZipFolder:
    """A wrapper around ``zipfile.ZipFile``, to provide convenience methods for interacting with a zipped folder."""

    # To improve: if zipfile is closed, do something
    # (e.g. add explicit open method, rename open to openfile, set _zipfile to None, ...)

    def __init__(
        self,
        zipfolder_or_fname: Union[str, 'ZipFolder'],
        mode: Optional[str] = None,
        subfolder: str = '.',
        use_compression: bool = True,
        allowZip64: bool = True
    ):
        """Initialise the zip folder.

        :param zipfolder_or_fname: either another ZipFolder instance,
          of which you want to get a subfolder, or a filename to create.

        :param mode: the file mode; see the zipfile.ZipFile docs for valid strings.
            Note: can be specified only if zipfolder_or_fname is a string (the filename to generate)

        :param subfolder: the subfolder that specified the "current working
          directory" in the zip file. If zipfolder_or_fname is a ZipFolder,
          subfolder is a relative path from zipfolder_or_fname.subfolder

        :param use_compression: either True, to compress files in the Zip, or
          False if you just want to pack them together without compressing.
          It is ignored if zipfolder_or_fname is a ZipFolder instance.

        """
        if isinstance(zipfolder_or_fname, str):
            the_mode = mode
            if the_mode is None:
                the_mode = 'r'
            if use_compression:
                compression = zipfile.ZIP_DEFLATED
            else:
                compression = zipfile.ZIP_STORED
            self._zipfile = zipfile.ZipFile(
                zipfolder_or_fname, mode=the_mode, compression=compression, allowZip64=allowZip64
            )
            self._pwd = subfolder
        else:
            if mode is not None:
                raise ValueError("Cannot specify 'mode' when passing a ZipFolder")
            self._zipfile = zipfolder_or_fname._zipfile  # pylint: disable=protected-access
            self._pwd = os.path.join(zipfolder_or_fname.pwd, subfolder)

    def __enter__(self):
        """Enter the zipfile for reading/writing."""
        return self

    def __exit__(
        self, exctype: Optional[Type[BaseException]], excinst: Optional[BaseException], exctb: Optional[TracebackType]
    ):
        """Exit the zipfile and close."""
        self.close()

    def close(self):
        """Close the zipfile."""
        self._zipfile.close()

    @property
    def pwd(self) -> str:
        """Return the pathname working directory within the zipfile."""
        return self._pwd

    def open(self, fname: str, mode: str = 'r') -> Union['_ZipFileWriter', IO[bytes]]:
        """Open a path in the zipfile, for reading/writing

        :param fname: An internal path in the zipfile
        :param mode: mode should be 'r' to read a file already in the ZIP file,
            or 'w' to write to a file newly added to the archive.

        """
        if mode == 'w':
            return _ZipFileWriter(zip_file=self._zipfile, fname=self._get_internal_path(fname))
        return self._zipfile.open(self._get_internal_path(fname), mode=mode)

    def _get_internal_path(self, filename: str):
        """Return a path to the filename from the root of zip file."""
        return os.path.normpath(os.path.join(self.pwd, filename))

    # pylint: disable=unused-argument
    def get_subfolder(self, subfolder: str, create: bool = False, reset_limit: bool = False) -> 'ZipFolder':
        """Return a subfolder in the zipfile as a new zip folder."""
        return ZipFolder(self, subfolder=subfolder)

    def exists(self, path):
        """Check whether path already exists in the ZipFolder"""
        try:
            self._zipfile.getinfo(path)
            exists = True
        except KeyError:
            exists = False
        return exists

    def insert_path(self, src: Union[str, Path], dest_name: Optional[Union[str, Path]] = None, overwrite: bool = True):
        """Copy an external path into the zipfile

        :param src: the path to the file or folder
        :param dest_name: the path to write to in the zip file
            If None, use the basename of src
        :param overwrite: Overwrite any existing path in the zipfile

        :raises ValueError: If the src path is not absolute
        :raises IOError: If the destination already exists and overwrite is False
        """
        if dest_name is None:
            base_filename = str(os.path.basename(src))
        else:
            base_filename = str(dest_name)

        base_filename = self._get_internal_path(base_filename)

        src = str(src)

        if not os.path.isabs(src):
            raise ValueError('src must be an absolute path in insert_file')

        if not overwrite and self.exists(base_filename):
            raise IOError(f'destination already exists: {base_filename}')

        if os.path.isdir(src):
            for dirpath, dirnames, filenames in os.walk(src):
                relpath = os.path.relpath(dirpath, src)
                if not dirnames and not filenames:
                    real_src = dirpath
                    real_dest = os.path.join(base_filename, relpath) + os.path.sep
                    if not self.exists(real_dest):
                        self._zipfile.write(real_src, real_dest)
                else:
                    for fname in dirnames + filenames:
                        real_src = os.path.join(dirpath, fname)
                        real_dest = os.path.join(base_filename, relpath, fname)
                        if not self.exists(real_dest):
                            self._zipfile.write(real_src, real_dest)
        else:
            self._zipfile.write(src, base_filename)
