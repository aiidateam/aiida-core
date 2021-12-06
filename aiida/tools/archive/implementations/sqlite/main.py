# -*- coding: utf-8 -*-
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
from typing import Any, List, Union, overload

from aiida.tools.archive.abstract import ArchiveFormatAbstract

from .migrations.main import ALL_VERSIONS, migrate
from .reader import ArchiveReaderSqlZip, read_version
from .writer import ArchiveAppenderSqlZip, ArchiveWriterSqlZip

try:
    from typing import Literal  # pylint: disable=ungrouped-imports
except ImportError:
    # Python <3.8 backport
    from typing_extensions import Literal  # type: ignore

__all__ = ('ArchiveFormatSqlZip',)


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
    def versions(self) -> List[str]:
        return ALL_VERSIONS

    def read_version(self, path: Union[str, Path]) -> str:
        return read_version(path)

    @property
    def key_format(self) -> str:
        return 'sha256'

    @overload
    def open(
        self,
        path: Union[str, Path],
        mode: Literal['r'],
        *,
        compression: int = 6,
        **kwargs: Any
    ) -> ArchiveReaderSqlZip:
        ...

    @overload
    def open(
        self,
        path: Union[str, Path],
        mode: Literal['x', 'w'],
        *,
        compression: int = 6,
        **kwargs: Any
    ) -> ArchiveWriterSqlZip:
        ...

    @overload
    def open(
        self,
        path: Union[str, Path],
        mode: Literal['a'],
        *,
        compression: int = 6,
        **kwargs: Any
    ) -> ArchiveAppenderSqlZip:
        ...

    def open(
        self,
        path: Union[str, Path],
        mode: Literal['r', 'x', 'w', 'a'] = 'r',
        *,
        compression: int = 6,
        **kwargs: Any
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
        compression: int = 6
    ) -> None:
        """Migrate an archive to a specific version.

        :param path: archive path
        """
        current_version = self.read_version(inpath)
        return migrate(inpath, outpath, current_version, version, force=force, compression=compression)
