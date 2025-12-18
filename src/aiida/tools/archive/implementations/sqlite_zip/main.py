###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The file format implementation"""

from pathlib import Path
from typing import Any, Literal, Union, overload

from aiida.storage.sqlite_zip.migrator import get_schema_version_head, migrate
from aiida.storage.sqlite_zip.utils import read_version
from aiida.tools.archive.abstract import ArchiveFormatAbstract

from .reader import ArchiveReaderSqlZip
from .writer import ArchiveAppenderSqlZip, ArchiveWriterSqlZip


class ArchiveFormatSqlZip(ArchiveFormatAbstract):
    """Archive format, which uses a zip file, containing an SQLite database.

    The content of the zip file is::

        |- archive.zip
            |- metadata.json
            |- db.sqlite3
            |- repo/
                |- hashkey

    Repository files are named by their SHA256 content hash.

    """

    @property
    def latest_version(self) -> str:
        return get_schema_version_head()

    def read_version(self, path: Union[str, Path]) -> str:
        return read_version(path)

    @property
    def key_format(self) -> str:
        return 'sha256'

    @overload
    def open(
        self, path: Union[str, Path], mode: Literal['r'], *, compression: int = 6, **kwargs: Any
    ) -> ArchiveReaderSqlZip: ...

    @overload
    def open(
        self, path: Union[str, Path], mode: Literal['x', 'w'], *, compression: int = 6, **kwargs: Any
    ) -> ArchiveWriterSqlZip: ...

    @overload
    def open(
        self, path: Union[str, Path], mode: Literal['a'], *, compression: int = 6, **kwargs: Any
    ) -> ArchiveAppenderSqlZip: ...

    def open(
        self, path: Union[str, Path], mode: Literal['r', 'x', 'w', 'a'] = 'r', *, compression: int = 6, **kwargs: Any
    ) -> Union[ArchiveReaderSqlZip, ArchiveWriterSqlZip, ArchiveAppenderSqlZip]:
        if mode == 'r':
            return ArchiveReaderSqlZip(path, **kwargs)
        if mode == 'a':
            return ArchiveAppenderSqlZip(path, self, mode=mode, compression=compression, **kwargs)
        return ArchiveWriterSqlZip(path, self, mode=mode, compression=compression, **kwargs)

    def migrate(
        self,
        inpath: Union[str, Path],
        outpath: Union[str, Path],
        version: str,
        *,
        force: bool = False,
        compression: int = 6,
    ) -> None:
        """Migrate an archive to a specific version.

        :param path: archive path
        """
        return migrate(inpath, outpath, version, force=force, compression=compression)
