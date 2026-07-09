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
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from sqlalchemy import event
from sqlalchemy.future.engine import Engine, create_engine

from aiida.common.exceptions import AiidaException, CorruptStorage, UnreachableStorage

if TYPE_CHECKING:
    from remotezip import RemoteZip

META_FILENAME = 'metadata.json'
"""The filename containing meta information about the storage instance."""

DB_FILENAME = 'db.sqlite3'
"""The filename of the SQLite database."""

REPO_FOLDER = 'repo'
"""The name of the folder containing the repository files."""


def is_url(path: Union[str, Path]) -> bool:
    """Return whether the path is a remote URL (``http://`` or ``https://``).

    The scheme is compared case-insensitively, as URL schemes are case-insensitive per RFC 3986.
    """
    return isinstance(path, str) and path.lower().startswith(('http://', 'https://'))


def open_remote_zip(url: str, *, timeout: Optional[float] = None) -> 'RemoteZip':
    """Open a zip file over HTTP(S) using range requests, without downloading the whole file.

    :param url: the URL of the remote zip file.
    :param timeout: timeout in seconds for the HTTP requests. If ``None``, the value of the
        ``storage.remote_archive_timeout`` configuration option is used.
    :raises UnreachableStorage: if the URL cannot be reached or the server does not support range requests.
    :raises CorruptStorage: if the remote file is not a valid zip file.
    """
    import requests
    from remotezip import RangeNotSupported, RemoteZip, RemoteZipError

    if timeout is None:
        from aiida.manage.configuration import get_config_option

        timeout = get_config_option('storage.remote_archive_timeout')

    try:
        return RemoteZip(url, timeout=timeout)
    except zipfile.BadZipFile as exc:
        msg = f'The remote file is not a valid zip file: {url}'
        raise CorruptStorage(msg) from exc
    except RangeNotSupported as exc:
        msg = (
            f'The server hosting `{url}` does not support HTTP range requests, which are required to read a remote '
            'archive without downloading it in full. Download the file and use the local path instead.'
        )
        raise UnreachableStorage(msg) from exc
    except (RemoteZipError, requests.RequestException) as exc:
        msg = f'Could not reach remote archive `{url}`: {exc}'
        raise UnreachableStorage(msg) from exc


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


def _contains(lhs: Union[dict, list], rhs: Union[dict, list]):
    if isinstance(lhs, dict) and isinstance(rhs, dict):
        for key in rhs:
            if key not in lhs or not _contains(lhs[key], rhs[key]):
                return False
        return True

    elif isinstance(lhs, list) and isinstance(rhs, list):
        for item in rhs:
            if not any(_contains(e, item) for e in lhs):
                return False
        return True
    else:
        return lhs == rhs


def _json_contains(lhs: Union[str, bytes, bytearray, dict, list], rhs: Union[str, bytes, bytearray, dict, list]):
    try:
        if isinstance(lhs, (str, bytes, bytearray)):
            lhs = json.loads(lhs)
        if isinstance(rhs, (str, bytes, bytearray)):
            rhs = json.loads(rhs)
    except json.JSONDecodeError:
        return 0
    return int(_contains(lhs, rhs))  # type: ignore[arg-type]


def register_json_contains(dbapi_connection, _):
    dbapi_connection.create_function('json_contains', 2, _json_contains)


def create_sqla_engine(
    path: Union[str, Path], *, enforce_foreign_keys: bool = True, read_only: bool = False, **kwargs
) -> Engine:
    """Create a new engine instance.

    :param path: path of the database file.
    :param enforce_foreign_keys: whether to enforce foreign key constraints.
    :param read_only: open the database in read-only mode (sqlite URI options ``mode=ro&immutable=1``). The file must
        not be modified in place for the lifetime of the engine (atomically replacing it is fine).
    """
    if read_only:
        uri = f'sqlite:///file:{path}?mode=ro&immutable=1&uri=true'
    else:
        uri = f'sqlite:///{path}'
    engine = create_engine(uri, json_serializer=json.dumps, json_deserializer=json.loads, **kwargs)
    event.listen(engine, 'connect', sqlite_case_sensitive_like)
    if enforce_foreign_keys:
        event.listen(engine, 'connect', sqlite_enforce_foreign_keys)
    event.listen(engine, 'connect', register_json_contains)
    return engine


def _read_metadata_from_zip_handle(zip_handle: 'RemoteZip') -> Any:
    """Read and JSON-decode the metadata file from an open (remote) zip file handle."""
    try:
        return json.loads(zip_handle.read(META_FILENAME))
    except Exception as exc:
        msg = f'Could not read metadata: {exc}'
        raise CorruptStorage(msg) from exc


def extract_metadata(
    path: Union[str, Path], *, search_limit: Optional[int] = 10, zip_handle: Optional['RemoteZip'] = None
) -> Dict[str, Any]:
    """Extract the metadata dictionary from the archive.

    :param path: path to the archive: a folder, zip file, tar file, or URL (``http(s)://``) of a remote zip file.
    :param search_limit: the maximum number of records to search for the metadata file in a zip file.
    :param zip_handle: for a remote URL ``path``, optionally an already-open handle of the remote zip file, which is
        reused (and not closed) instead of opening a new connection.
    """
    import tarfile

    from archive_path import read_file_in_tar, read_file_in_zip

    if is_url(path):
        if zip_handle is not None:
            metadata = _read_metadata_from_zip_handle(zip_handle)
        else:
            with open_remote_zip(str(path)) as handle:
                metadata = _read_metadata_from_zip_handle(handle)
    else:
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


def read_version(
    path: Union[str, Path], *, search_limit: Optional[int] = None, zip_handle: Optional['RemoteZip'] = None
) -> str:
    """Read the version of the storage instance from the path.

    This is intended to work for all versions of the storage format.

    :param path: path to storage instance: a folder, zip file, tar file, or URL of a remote zip file.
    :param search_limit: the maximum number of records to search for the metadata file in a zip file.
    :param zip_handle: for a remote URL ``path``, optionally an already-open handle of the remote zip file, which is
        reused (and not closed) instead of opening a new connection.

    :raises: ``UnreachableStorage`` if a version cannot be read from the file
    """
    metadata = extract_metadata(path, search_limit=search_limit, zip_handle=zip_handle)
    if 'export_version' in metadata:
        return metadata['export_version']

    raise CorruptStorage("Metadata does not contain 'export_version' key")


class ReadOnlyError(AiidaException):
    """Raised when a write operation is called on a read-only archive."""

    def __init__(self, msg: str = 'sqlite_zip storage is read-only'):
        super().__init__(msg)
