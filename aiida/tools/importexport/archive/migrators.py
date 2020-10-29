# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Archive migration classes, for migrating an archive to different versions."""
from abc import ABC, abstractmethod
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from typing import Any, cast, Dict, List, Optional, Type
import zipfile

from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter
from aiida.tools.importexport.common.exceptions import (
    ArchiveMigrationError, CorruptArchive, DanglingLinkError, IncompatibleArchiveVersionError
)
from aiida.tools.importexport.common.config import ExportFileFormat
from aiida.tools.importexport.archive.common import read_file_in_tar, read_file_in_zip
from aiida.tools.importexport.archive.migrations import MIGRATE_FUNCTIONS

__all__ = (
    'ArchiveMigratorAbstract', 'ArchiveMigratorJsonBase', 'ArchiveMigratorJsonZip', 'ArchiveMigratorJsonTar',
    'MIGRATE_LOGGER', 'get_migrator'
)

MIGRATE_LOGGER = AIIDA_LOGGER.getChild('migrate')


def get_migrator(file_format: str) -> Type['ArchiveMigratorAbstract']:
    """Return the available archive migrator classes."""
    migrators = {
        ExportFileFormat.ZIP: ArchiveMigratorJsonZip,
        ExportFileFormat.TAR_GZIPPED: ArchiveMigratorJsonTar,
    }

    if file_format not in migrators:
        raise ValueError(
            f'Can only migrate in the formats: {tuple(migrators.keys())}, please specify one for "file_format".'
        )

    return cast(Type[ArchiveMigratorAbstract], migrators[file_format])


class ArchiveMigratorAbstract(ABC):
    """An abstract base class to define an archive migrator."""

    def __init__(self, filepath: str):
        """Initialise the migrator

        :param filepath: the path to the archive file
        :param version: the version of the archive file or, if None, the version will be auto-retrieved.

        """
        self._filepath = filepath

    @property
    def filepath(self) -> str:
        """Return the input file path."""
        return self._filepath

    @abstractmethod
    def migrate(self, version: str, filename: Optional[str], *, force: bool = False, **kwargs: Any):
        """Migrate the archive to another version

        :param version: the version to migrate to
        :param filename: the file path to migrate to or, if None, migrate in-place
        :param force: overwrite output file if it already exists
        :param kwargs: key-word arguments specific to the concrete migrator implementation

        :raises: :class:`~aiida.tools.importexport.common.exceptions.CorruptArchive`:
            if the archive cannot be read
        :raises: :class:`~aiida.tools.importexport.common.exceptions.IncompatibleArchiveVersionError`:
            if the archive cannot migrated to the requested version
        :raises: :class:`~aiida.tools.importexport.common.exceptions.ArchiveMigrationError`:
            for other known errors occurring during the migration

        """


class ArchiveMigratorJsonBase(ArchiveMigratorAbstract):
    """A migrator base for the JSON compressed formats."""

    def migrate(
        self,
        version: str,
        filename: Optional[str],
        *,
        force: bool = False,
        out_compression: str = 'zip',
        **kwargs
    ):  # pylint: disable=arguments-differ
        # pylint: disable=too-many-branches

        if filename and Path(filename).exists() and not force:
            raise IOError('the output file already exists')

        allowed_compressions = ['zip', 'zip-uncompressed', 'tar.gz']
        if out_compression not in allowed_compressions:
            raise ValueError(f'Output compression must be in: {allowed_compressions}')

        current_version = self._retrieve_version()

        # compute the migration pathway
        prev_version = current_version
        pathway: List[str] = []
        while prev_version != version:
            if prev_version not in MIGRATE_FUNCTIONS:
                raise IncompatibleArchiveVersionError(
                    f"No migration pathway available for '{current_version}' to '{version}'"
                )
            if prev_version in pathway:
                raise ArchiveMigrationError(
                    f'cyclic migration pathway encountered: {" -> ".join(pathway + [prev_version])}'
                )
            pathway.append(prev_version)
            prev_version = MIGRATE_FUNCTIONS[prev_version][0]

        if not pathway:
            MIGRATE_LOGGER.info('No migration required')
            return

        MIGRATE_LOGGER.info('Migration pathway: %s', ' -> '.join(pathway + [version]))

        # perform migrations
        with tempfile.TemporaryDirectory() as tmpdirname:

            MIGRATE_LOGGER.info('Extracting archive to temporary folder')
            extracted = Path(tmpdirname) / 'extracted'
            extracted.mkdir()
            self._extract_archive(extracted)
            # cache of read data to parse between migration steps (to minimize re-reading data)
            cache: Dict[str, Any] = {}

            with get_progress_reporter()(total=len(pathway), desc='Performing migrations: ') as progress:
                for from_version in pathway:
                    to_version = MIGRATE_FUNCTIONS[from_version][0]
                    progress.set_description_str(
                        f'Performing migrations: {from_version} -> {to_version}', refresh=False
                    )
                    progress.update()
                    try:
                        cache = MIGRATE_FUNCTIONS[from_version][1](extracted, cache)
                    except DanglingLinkError:
                        raise ArchiveMigrationError('Archive file is invalid because it contains dangling links')

            # re-compress archive
            MIGRATE_LOGGER.info(f"Re-compressing archive as '{out_compression}'")
            compressed = Path(tmpdirname) / 'compressed'
            if out_compression == 'zip':
                self._compress_archive_zip(extracted, compressed, zipfile.ZIP_DEFLATED)
            elif out_compression == 'zip-uncompressed':
                self._compress_archive_zip(extracted, compressed, zipfile.ZIP_STORED)
            else:
                self._compress_archive_tar(extracted, compressed)

            # move to final location
            MIGRATE_LOGGER.info('Moving archive to: %s', filename or self.filepath)
            out_path = Path(filename or self.filepath)
            if out_path.exists():
                if out_path.is_file():
                    out_path.unlink()
                else:
                    shutil.rmtree(out_path)
            shutil.move(compressed, out_path)  # type: ignore

    def _retrieve_version(self) -> str:
        """Retrieve the version of the input archive."""
        raise NotImplementedError()

    def _extract_archive(self, filepath: Path):
        """Extract the archive to a filepath."""
        raise NotImplementedError()

    @staticmethod
    def _compress_archive_zip(in_path: Path, out_path: Path, compression: int):
        """Create a new zip compressed zip from a folder."""
        with zipfile.ZipFile(out_path, mode='w', compression=compression, allowZip64=True) as archive:
            for dirpath, dirnames, filenames in os.walk(in_path):
                relpath = os.path.relpath(dirpath, in_path)
                for filename in dirnames + filenames:
                    real_src = os.path.join(dirpath, filename)
                    real_dest = os.path.join(relpath, filename)
                    archive.write(real_src, real_dest)

    @staticmethod
    def _compress_archive_tar(in_path: Path, out_path: Path):
        """Create a new zip compressed tar from a folder."""
        with tarfile.open(os.path.abspath(out_path), 'w:gz', format=tarfile.PAX_FORMAT, dereference=True) as archive:
            archive.add(os.path.abspath(in_path), arcname='')


class ArchiveMigratorJsonZip(ArchiveMigratorJsonBase):
    """A migrator for a JSON zip compressed format."""

    def _retrieve_version(self) -> str:
        metadata = json.loads(read_file_in_zip(self.filepath, 'metadata.json'))
        if 'export_version' not in metadata:
            raise CorruptArchive("metadata.json doest not contain an 'export_version' key")
        return metadata['export_version']

    def _extract_archive(self, filepath: Path):
        with zipfile.ZipFile(self.filepath, 'r', allowZip64=True) as handle:
            handle.extractall(filepath)


class ArchiveMigratorJsonTar(ArchiveMigratorJsonBase):
    """A migrator for a JSON tar compressed format."""

    def _retrieve_version(self) -> str:
        metadata = json.loads(read_file_in_tar(self.filepath, 'metadata.json'))
        if 'export_version' not in metadata:
            raise CorruptArchive("metadata.json doest not contain an 'export_version' key")
        return metadata['export_version']
