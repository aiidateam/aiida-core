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
from pathlib import Path
from typing import Any, Dict, Optional, Union

from aiida.common.exceptions import CorruptStorage
from aiida.storage.sqlite_zip.backend import SqliteZipBackend
from aiida.storage.sqlite_zip.utils import extract_metadata
from aiida.tools.archive.abstract import ArchiveReaderAbstract


class ArchiveReaderSqlZip(ArchiveReaderAbstract):
    """An archive reader for the SQLite format."""

    def __init__(self, path: Union[str, Path], **kwargs: Any):
        super().__init__(path, **kwargs)
        self._in_context = False
        # we lazily create the storage backend, then clean up on exit
        self._backend: Optional[SqliteZipBackend] = None

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
            raise CorruptStorage('metadata could not be read') from exc

    def get_backend(self) -> SqliteZipBackend:
        if not self._in_context:
            raise AssertionError('Not in context')
        if self._backend is not None:
            return self._backend
        profile = SqliteZipBackend.create_profile(self.path)
        self._backend = SqliteZipBackend(profile)
        return self._backend
