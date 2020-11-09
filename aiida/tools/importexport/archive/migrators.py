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
from typing import Any, Callable, cast, List, Optional, Type, Union
import zipfile

from archive_path import TarPath, ZipPath, read_file_in_tar, read_file_in_zip

from aiida.common.log import AIIDA_LOGGER
from aiida.common.progress_reporter import get_progress_reporter, create_callback
from aiida.tools.importexport.common.exceptions import (ArchiveMigrationError, CorruptArchive, DanglingLinkError)
from aiida.tools.importexport.common.config import ExportFileFormat
from aiida.tools.importexport.archive.common import CacheFolder
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
    def migrate(
        self,
        version: str,
        filename: Optional[Union[str, Path]],
        *,
        force: bool = False,
        work_dir: Optional[Path] = None,
        **kwargs: Any
    ) -> Optional[Path]:
        """Migrate the archive to another version

        :param version: the version to migrate to
        :param filename: the file path to migrate to.
            If None, the migrated archive will not be copied from the work_dir.
        :param force: overwrite output file if it already exists
        :param work_dir: The directory in which to perform the migration.
            If None, a temporary folder will be created and destroyed at the end of the process.
        :param kwargs: key-word arguments specific to the concrete migrator implementation

        :returns: path to the migrated archive or None if no migration performed
            (if filename is None, this will point to a path in the work_dir)

        :raises: :class:`~aiida.tools.importexport.common.exceptions.CorruptArchive`:
            if the archive cannot be read
        :raises: :class:`~aiida.tools.importexport.common.exceptions.ArchiveMigrationError`:
            if the archive cannot migrated to the requested version

        """


class ArchiveMigratorJsonBase(ArchiveMigratorAbstract):
    """A migrator base for the JSON compressed formats."""

    # pylint: disable=arguments-differ
    def migrate(
        self,
        version: str,
        filename: Optional[Union[str, Path]],
        *,
        force: bool = False,
        work_dir: Optional[Path] = None,
        out_compression: str = 'zip',
        **kwargs
    ) -> Optional[Path]:
        # pylint: disable=too-many-branches

        if not isinstance(version, str):
            raise TypeError('version must be a string')

        if filename and Path(filename).exists() and not force:
            raise IOError(f'the output path already exists and force=False: {filename}')

        allowed_compressions = ['zip', 'zip-uncompressed', 'tar.gz', 'none']
        if out_compression not in allowed_compressions:
            raise ValueError(f'Output compression must be in: {allowed_compressions}')

        MIGRATE_LOGGER.info('Reading archive version')
        current_version = self._retrieve_version()

        # compute the migration pathway
        prev_version = current_version
        pathway: List[str] = []
        while prev_version != version:
            if prev_version not in MIGRATE_FUNCTIONS:
                raise ArchiveMigrationError(f"No migration pathway available for '{current_version}' to '{version}'")
            if prev_version in pathway:
                raise ArchiveMigrationError(
                    f'cyclic migration pathway encountered: {" -> ".join(pathway + [prev_version])}'
                )
            pathway.append(prev_version)
            prev_version = MIGRATE_FUNCTIONS[prev_version][0]

        if not pathway:
            MIGRATE_LOGGER.info('No migration required')
            return None

        MIGRATE_LOGGER.info('Migration pathway: %s', ' -> '.join(pathway + [version]))

        # perform migrations
        if work_dir is not None:
            migrated_path = self._perform_migration(Path(work_dir), pathway, out_compression, filename)
        else:
            with tempfile.TemporaryDirectory() as tmpdirname:
                migrated_path = self._perform_migration(Path(tmpdirname), pathway, out_compression, filename)
                MIGRATE_LOGGER.debug('Cleaning temporary folder')

        return migrated_path

    def _perform_migration(
        self, work_dir: Path, pathway: List[str], out_compression: str, out_path: Optional[Union[str, Path]]
    ) -> Path:
        """Perform the migration(s) in the work directory, compress (if necessary),
        then move to the out_path (if not None).
        """
        MIGRATE_LOGGER.info('Extracting archive to work directory')

        extracted = Path(work_dir) / 'extracted'
        extracted.mkdir(parents=True)

        with get_progress_reporter()(total=1) as progress:
            callback = create_callback(progress)
            self._extract_archive(extracted, callback)

        with CacheFolder(extracted) as folder:
            with get_progress_reporter()(total=len(pathway), desc='Performing migrations: ') as progress:
                for from_version in pathway:
                    to_version = MIGRATE_FUNCTIONS[from_version][0]
                    progress.set_description_str(f'Performing migrations: {from_version} -> {to_version}', refresh=True)
                    try:
                        MIGRATE_FUNCTIONS[from_version][1](folder)
                    except DanglingLinkError:
                        raise ArchiveMigrationError('Archive file is invalid because it contains dangling links')
                    progress.update()
            MIGRATE_LOGGER.debug('Flushing cache')

        # re-compress archive
        if out_compression != 'none':
            MIGRATE_LOGGER.info(f"Re-compressing archive as '{out_compression}'")
            migrated = work_dir / 'compressed'
        else:
            migrated = extracted

        if out_compression == 'zip':
            self._compress_archive_zip(extracted, migrated, zipfile.ZIP_DEFLATED)
        elif out_compression == 'zip-uncompressed':
            self._compress_archive_zip(extracted, migrated, zipfile.ZIP_STORED)
        elif out_compression == 'tar.gz':
            self._compress_archive_tar(extracted, migrated)

        if out_path is not None:
            # move to final location
            MIGRATE_LOGGER.info('Moving archive to: %s', out_path)
            self._move_file(migrated, Path(out_path))

        return Path(out_path) if out_path else migrated

    @staticmethod
    def _move_file(in_path: Path, out_path: Path):
        """Move a file to a another path, deleting the target path first if it exists."""
        if out_path.exists():
            if os.path.samefile(str(in_path), str(out_path)):
                return
            if out_path.is_file():
                out_path.unlink()
            else:
                shutil.rmtree(out_path)
        shutil.move(in_path, out_path)  # type: ignore

    def _retrieve_version(self) -> str:
        """Retrieve the version of the input archive."""
        raise NotImplementedError()

    def _extract_archive(self, filepath: Path, callback: Callable[[str, Any], None]):
        """Extract the archive to a filepath."""
        raise NotImplementedError()

    @staticmethod
    def _compress_archive_zip(in_path: Path, out_path: Path, compression: int):
        """Create a new zip compressed zip from a folder."""
        with get_progress_reporter()(total=1, desc='Compressing to zip') as progress:
            _callback = create_callback(progress)
            with ZipPath(out_path, mode='w', compression=compression, allow_zip64=True) as path:
                path.puttree(in_path, check_exists=False, callback=_callback, cb_descript='Compressing to zip')

    @staticmethod
    def _compress_archive_tar(in_path: Path, out_path: Path):
        """Create a new zip compressed tar from a folder."""
        with get_progress_reporter()(total=1, desc='Compressing to tar') as progress:
            _callback = create_callback(progress)
            with TarPath(out_path, mode='w:gz', dereference=True) as path:
                path.puttree(in_path, check_exists=False, callback=_callback, cb_descript='Compressing to tar')


class ArchiveMigratorJsonZip(ArchiveMigratorJsonBase):
    """A migrator for a JSON zip compressed format."""

    def _retrieve_version(self) -> str:
        try:
            metadata = json.loads(read_file_in_zip(self.filepath, 'metadata.json'))
        except (IOError, FileNotFoundError) as error:
            raise CorruptArchive(str(error))
        if 'export_version' not in metadata:
            raise CorruptArchive("metadata.json doest not contain an 'export_version' key")
        return metadata['export_version']

    def _extract_archive(self, filepath: Path, callback: Callable[[str, Any], None]):
        try:
            ZipPath(self.filepath, mode='r', allow_zip64=True).extract_tree(filepath, callback=callback)
        except zipfile.BadZipfile as error:
            raise CorruptArchive(f'The input file cannot be read: {error}')


class ArchiveMigratorJsonTar(ArchiveMigratorJsonBase):
    """A migrator for a JSON tar compressed format."""

    def _retrieve_version(self) -> str:
        try:
            metadata = json.loads(read_file_in_tar(self.filepath, 'metadata.json'))
        except (IOError, FileNotFoundError) as error:
            raise CorruptArchive(str(error))
        if 'export_version' not in metadata:
            raise CorruptArchive("metadata.json doest not contain an 'export_version' key")
        return metadata['export_version']

    def _extract_archive(self, filepath: Path, callback: Callable[[str, Any], None]):
        try:
            TarPath(self.filepath, mode='r:*', pax_format=tarfile.PAX_FORMAT
                    ).extract_tree(filepath, allow_dev=False, allow_symlink=False, callback=callback)
        except tarfile.ReadError as error:
            raise CorruptArchive(f'The input file cannot be read: {error}')
