# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA archive reader implementation."""
import json
from pathlib import Path
import tarfile
from typing import Any, Dict, Optional, Union
import zipfile

from archive_path import read_file_in_tar, read_file_in_zip

from aiida.manage import Profile
from aiida.tools.archive.abstract import ArchiveReaderAbstract
from aiida.tools.archive.exceptions import CorruptArchive, UnreadableArchiveError

from . import backend as db
from .common import META_FILENAME


class ArchiveReaderSqlZip(ArchiveReaderAbstract):
    """An archive reader for the SQLite format."""

    def __init__(self, path: Union[str, Path], **kwargs: Any):
        super().__init__(path, **kwargs)
        self._in_context = False
        # we lazily create the storage backend, then clean up on exit
        self._backend: Optional[db.ArchiveReadOnlyBackend] = None

    def __enter__(self) -> 'ArchiveReaderSqlZip':
        self._in_context = True
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Close the archive backend."""
        super().__exit__(*args, **kwargs)
        if self._backend:
            self._backend.close()
            self._backend = None
        self._in_context = False

    def get_metadata(self) -> Dict[str, Any]:
        try:
            return extract_metadata(self.path)
        except Exception as exc:
            raise CorruptArchive('metadata could not be read') from exc

    def get_backend(self) -> db.ArchiveReadOnlyBackend:
        if not self._in_context:
            raise AssertionError('Not in context')
        if self._backend is not None:
            return self._backend
        profile = Profile(
            'default', {
                'storage': {
                    'backend': 'archive.sqlite',
                    'config': {
                        'path': str(self.path)
                    }
                },
                'process_control': {
                    'backend': 'null',
                    'config': {}
                }
            }
        )
        self._backend = db.ArchiveReadOnlyBackend(profile)
        return self._backend


def extract_metadata(path: Union[str, Path], search_limit: Optional[int] = 10) -> Dict[str, Any]:
    """Extract the metadata dictionary from the archive"""
    # we fail if not one of the first record in central directory (as expected)
    # so we don't have to iter all repo files to fail
    return json.loads(read_file_in_zip(path, META_FILENAME, 'utf8', search_limit=search_limit))


def read_version(path: Union[str, Path]) -> str:
    """Read the version of the archive from the file.

    Intended to work for all versions of the archive format.

    :param path: archive path

    :raises: ``FileNotFoundError`` if the file does not exist
    :raises: ``UnreadableArchiveError`` if a version cannot be read from the archive
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError('archive file not found')
    # check the file is at least a zip or tar file
    if zipfile.is_zipfile(path):
        try:
            metadata = extract_metadata(path, search_limit=None)
        except Exception as exc:
            raise UnreadableArchiveError(f'Could not read metadata for version: {exc}') from exc
    elif tarfile.is_tarfile(path):
        try:
            metadata = json.loads(read_file_in_tar(path, META_FILENAME))
        except Exception as exc:
            raise UnreadableArchiveError(f'Could not read metadata for version: {exc}') from exc
    else:
        raise UnreadableArchiveError('Not a zip or tar file')
    if 'export_version' in metadata:
        return metadata['export_version']
    raise UnreadableArchiveError("Metadata does not contain 'export_version' key")
