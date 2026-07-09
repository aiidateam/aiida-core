###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Local cache for the database files extracted from ``core.sqlite_zip`` archives.

The cache is content-addressed: entries are named after the CRC-32 checksum and size of the uncompressed database
file, as recorded in the central directory of the zip archive. This means that checking whether the database of an
archive is cached only requires reading the central directory of the archive (for archives served over HTTP, a range
request of the last few tens of kilobytes of the file), not the database itself. It also means that the same database
is shared between profiles and URLs pointing to the same archive, and that the cache requires no metadata: a changed
archive simply resolves to a different filename.

The cache is stored in the ``cache/sqlite_zip`` subdirectory of the AiiDA configuration folder. It can safely be
deleted at any time, at the cost of the databases being fetched anew on first access.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import IO
from zipfile import ZipInfo

__all__ = ('get_cache_dirpath', 'get_cache_filename', 'lookup_cache', 'store_in_cache')

CACHE_SUBFOLDER = Path('cache') / 'sqlite_zip'
"""Subfolder of the AiiDA configuration folder in which the extracted database files are cached."""


def get_cache_dirpath() -> Path:
    """Return the path of the directory in which the extracted database files are cached."""
    from aiida.manage.configuration.settings import AiiDAConfigDir

    return AiiDAConfigDir.get() / CACHE_SUBFOLDER


def get_cache_filename(info: ZipInfo) -> str:
    """Return the cache filename for the database with the given zip central directory record.

    The name is derived from the CRC-32 checksum and the size of the uncompressed database file, making the cache
    content-addressed: a changed archive resolves to a different filename, and identical archives available at
    different locations share a single cache entry.

    :param info: the central directory record of the database file inside the zip archive.
    """
    return f'{info.CRC:08x}-{info.file_size}.sqlite3'


def lookup_cache(filename: str) -> Path | None:
    """Return the path of the cached database file with the given name, or ``None`` if it is not cached.

    :param filename: the cache filename, as returned by :func:`get_cache_filename`.
    """
    filepath = get_cache_dirpath() / filename
    return filepath if filepath.is_file() else None


def store_in_cache(handle: IO[bytes], filename: str) -> Path:
    """Store the database read from the given handle in the cache and return the path of the cached file.

    The file is written to a temporary file in the cache directory first and moved in place atomically, such that
    concurrent processes caching the same database do not interfere and never observe a partially written file.

    :param handle: a file-like object from which the database can be read.
    :param filename: the cache filename, as returned by :func:`get_cache_filename`.
    """
    dirpath = get_cache_dirpath()
    dirpath.mkdir(parents=True, exist_ok=True)
    filepath = dirpath / filename

    with tempfile.NamedTemporaryFile(dir=dirpath, suffix='.tmp', delete=False) as tmp_handle:
        filepath_tmp = Path(tmp_handle.name)
        try:
            shutil.copyfileobj(handle, tmp_handle)
        except BaseException:
            filepath_tmp.unlink(missing_ok=True)
            raise

    try:
        filepath_tmp.replace(filepath)
    except BaseException:
        filepath_tmp.unlink(missing_ok=True)
        raise

    return filepath
