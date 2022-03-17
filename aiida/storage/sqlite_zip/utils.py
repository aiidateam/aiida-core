# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for this backend."""
import json
from pathlib import Path
import tarfile
from typing import Any, Dict, Optional, Union
import zipfile

from archive_path import read_file_in_tar, read_file_in_zip
from sqlalchemy import event
from sqlalchemy.future.engine import Engine, create_engine

from aiida.common.exceptions import AiidaException, CorruptStorage, UnreachableStorage

META_FILENAME = 'metadata.json'
"""The filename containing meta information about the storage instance."""

DB_FILENAME = 'db.sqlite3'
"""The filename of the SQLite database."""

REPO_FOLDER = 'repo'
"""The name of the folder containing the repository files."""


def sqlite_enforce_foreign_keys(dbapi_connection, _):
    """Enforce foreign key constraints, when using sqlite backend (off by default).

    See: https://www.sqlite.org/pragma.html#pragma_foreign_keys
    """
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON;')
    cursor.close()


def sqlite_case_sensitive_like(dbapi_connection, _):
    """Enforce case sensitive like operations (off by default).

    See: https://www.sqlite.org/pragma.html#pragma_case_sensitive_like
    """
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA case_sensitive_like=ON;')
    cursor.close()


def create_sqla_engine(path: Union[str, Path], *, enforce_foreign_keys: bool = True, **kwargs) -> Engine:
    """Create a new engine instance."""
    engine = create_engine(
        f'sqlite:///{path}',
        json_serializer=json.dumps,
        json_deserializer=json.loads,
        encoding='utf-8',
        future=True,
        **kwargs
    )
    event.listen(engine, 'connect', sqlite_case_sensitive_like)
    if enforce_foreign_keys:
        event.listen(engine, 'connect', sqlite_enforce_foreign_keys)
    return engine


def extract_metadata(path: Union[str, Path], *, search_limit: Optional[int] = 10) -> Dict[str, Any]:
    """Extract the metadata dictionary from the archive.

    :param search_limit: the maximum number of records to search for the metadata file in a zip file.
    """
    path = Path(path)
    if not path.exists():
        raise UnreachableStorage(f'path not found: {path}')

    if path.is_dir():
        if not path.joinpath(META_FILENAME).is_file():
            raise CorruptStorage('Could not find metadata file')
        try:
            metadata = json.loads(path.joinpath(META_FILENAME).read_text(encoding='utf8'))
        except Exception as exc:
            raise CorruptStorage(f'Could not read metadata: {exc}') from exc
    elif path.is_file() and zipfile.is_zipfile(path):
        try:
            metadata = json.loads(read_file_in_zip(path, META_FILENAME, search_limit=search_limit))
        except Exception as exc:
            raise CorruptStorage(f'Could not read metadata: {exc}') from exc
    elif path.is_file() and tarfile.is_tarfile(path):
        try:
            metadata = json.loads(read_file_in_tar(path, META_FILENAME))
        except Exception as exc:
            raise CorruptStorage(f'Could not read metadata: {exc}') from exc
    else:
        raise CorruptStorage('Path not a folder, zip or tar file')

    if not isinstance(metadata, dict):
        raise CorruptStorage(f'Metadata is not a dictionary: {type(metadata)}')

    return metadata


def read_version(path: Union[str, Path], *, search_limit: Optional[int] = None) -> str:
    """Read the version of the storage instance from the path.

    This is intended to work for all versions of the storage format.

    :param path: path to storage instance, either a folder, zip file or tar file.
    :param search_limit: the maximum number of records to search for the metadata file in a zip file.

    :raises: ``UnreachableStorage`` if a version cannot be read from the file
    """
    metadata = extract_metadata(path, search_limit=search_limit)
    if 'export_version' in metadata:
        return metadata['export_version']

    raise CorruptStorage("Metadata does not contain 'export_version' key")


class ReadOnlyError(AiidaException):
    """Raised when a write operation is called on a read-only archive."""

    def __init__(self, msg='sqlite_zip storage is read-only'):  # pylint: disable=useless-super-delegation
        super().__init__(msg)
