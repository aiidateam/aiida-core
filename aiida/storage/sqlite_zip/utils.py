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
from pathlib import Path
import tarfile
from typing import Any, Dict, Optional, Union
import zipfile

from archive_path import read_file_in_tar, read_file_in_zip
from sqlalchemy import event
from sqlalchemy.future.engine import Engine, create_engine

from aiida.common import json
from aiida.common.exceptions import CorruptStorage, UnreachableStorage

META_FILENAME = 'metadata.json'
"""The filename containing meta information about the storage instance."""

DB_FILENAME = 'db.sqlite3'
"""The filename of the SQLite database."""

REPO_FOLDER = 'repo'
"""The name of the folder containing the repository files."""


def sqlite_enforce_foreign_keys(dbapi_connection, _):
    """Enforce foreign key constraints, when using sqlite backend (off by default)"""
    cursor = dbapi_connection.cursor()
    cursor.execute('PRAGMA foreign_keys=ON;')
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
    if enforce_foreign_keys:
        event.listen(engine, 'connect', sqlite_enforce_foreign_keys)
    return engine


def extract_metadata(path: Union[str, Path], search_limit: Optional[int] = 10) -> Dict[str, Any]:
    """Extract the metadata dictionary from the archive"""
    # we fail if not one of the first record in central directory (as expected)
    # so we don't have to iter all repo files to fail
    return json.loads(read_file_in_zip(path, META_FILENAME, 'utf8', search_limit=search_limit))


def read_version(path: Union[str, Path]) -> str:
    """Read the version of the storage instance from the file.

    This is intended to work for all versions of the storage format.

    :param path: path to storage instance

    :raises: ``UnreachableStorage`` if a version cannot be read from the file
    """
    path = Path(path)
    if not path.is_file():
        raise UnreachableStorage('archive file not found')

    if zipfile.is_zipfile(path):
        try:
            metadata = extract_metadata(path, search_limit=None)
        except Exception as exc:
            raise CorruptStorage(f'Could not read metadata for version: {exc}') from exc
    elif tarfile.is_tarfile(path):
        try:
            metadata = json.loads(read_file_in_tar(path, META_FILENAME))
        except Exception as exc:
            raise CorruptStorage(f'Could not read metadata for version: {exc}') from exc
    else:
        raise CorruptStorage('Not a zip or tar file')

    if 'export_version' in metadata:
        return metadata['export_version']

    raise CorruptStorage("Metadata does not contain 'export_version' key")
