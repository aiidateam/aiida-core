# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA archive migrator implementation."""
from pathlib import Path
import shutil
import tarfile
import tempfile
from typing import Any, Dict, List, Optional, Union
import zipfile

from archive_path import open_file_in_tar, open_file_in_zip

from aiida.common import json
from aiida.common.progress_reporter import get_progress_reporter
from aiida.tools.archive.common import MIGRATE_LOGGER
from aiida.tools.archive.exceptions import ArchiveMigrationError, CorruptArchive

from ..common import copy_tar_to_zip, copy_zip_to_zip
from .legacy import FINAL_LEGACY_VERSION, LEGACY_MIGRATE_FUNCTIONS
from .legacy_to_new import perform_v1_migration

ALL_VERSIONS = ['0.4', '0.5', '0.6', '0.7', '0.8', '0.9', '0.10', '0.11', '0.12', '1.0']


def migrate(  # pylint: disable=too-many-branches,too-many-statements
    inpath: Union[str, Path],
    outpath: Union[str, Path],
    current_version: str,
    version: str,
    *,
    force: bool = False,
    compression: int = 6
) -> None:
    """Migrate an archive to a specific version.

    :param path: archive path
    """
    inpath = Path(inpath)
    outpath = Path(outpath)

    if outpath.exists() and not force:
        raise IOError('Output path already exists and force=False')
    if outpath.exists() and not outpath.is_file():
        raise IOError('Existing output path is not a file')

    # check versions are valid
    # versions 0.1, 0.2, 0.3 are no longer supported,
    # since 0.3 -> 0.4 requires costly migrations of repo files (you would need to unpack all of them)
    if current_version in ('0.1', '0.2', '0.3') or version in ('0.1', '0.2', '0.3'):
        raise ArchiveMigrationError(
            f"Migration from '{current_version}' -> '{version}' is not supported in aiida-core v2"
        )
    if current_version not in ALL_VERSIONS:
        raise ArchiveMigrationError(f"Unknown current version '{current_version}'")
    if version not in ALL_VERSIONS:
        raise ArchiveMigrationError(f"Unknown target version '{version}'")

    # if we are already at the desired version, then no migration is required
    if current_version == version:
        if inpath != outpath:
            if outpath.exists() and force:
                outpath.unlink()
            shutil.copyfile(inpath, outpath)
        return

    # the file should be either a tar (legacy only) or zip file
    if tarfile.is_tarfile(str(inpath)):
        is_tar = True
    elif zipfile.is_zipfile(str(inpath)):
        is_tar = False
    else:
        raise CorruptArchive(f'The input file is neither a tar nor a zip file: {inpath}')

    # read the metadata.json which should always be present
    metadata = _read_json(inpath, 'metadata.json', is_tar)
    # data.json will only be read from legacy archives
    data: Optional[Dict[str, Any]] = None

    # if the archive is a "legacy" format, i.e. has a data.json file, migrate to latest one
    if current_version in LEGACY_MIGRATE_FUNCTIONS:
        MIGRATE_LOGGER.report('Legacy migrations required')
        MIGRATE_LOGGER.report('Extracting data.json ...')
        # read the data.json file
        data = _read_json(inpath, 'data.json', is_tar)
        to_version = FINAL_LEGACY_VERSION if version not in LEGACY_MIGRATE_FUNCTIONS else version
        current_version = _perform_legacy_migrations(current_version, to_version, metadata, data)

    if current_version == version:
        # create new legacy archive with updated metadata & data
        def path_callback(inpath, outpath) -> bool:
            if inpath.name == 'metadata.json':
                outpath.write_text(json.dumps(metadata))
                return True
            if inpath.name == 'data.json':
                outpath.write_text(json.dumps(data))
                return True
            return False

        func = copy_tar_to_zip if is_tar else copy_zip_to_zip

        func(
            inpath,
            outpath,
            path_callback,
            overwrite=force,
            compression=compression,
            title='Writing migrated legacy archive',
            info_order=('metadata.json', 'data.json')
        )
        return

    with tempfile.TemporaryDirectory() as tmpdirname:

        if current_version == FINAL_LEGACY_VERSION:
            MIGRATE_LOGGER.report('aiida-core v1 -> v2 migration required')
            if data is None:
                MIGRATE_LOGGER.report('Extracting data.json ...')
                data = _read_json(inpath, 'data.json', is_tar)
            current_version = perform_v1_migration(
                inpath, Path(tmpdirname), 'new.zip', is_tar, metadata, data, compression
            )

        if not current_version == version:
            raise ArchiveMigrationError(f"Migration from '{current_version}' -> '{version}' failed")

        if outpath.exists() and force:
            outpath.unlink()
        shutil.move(Path(tmpdirname) / 'new.zip', outpath)  # type: ignore[arg-type]


def _read_json(inpath: Path, filename: str, is_tar: bool) -> Dict[str, Any]:
    """Read a JSON file from the archive."""
    if is_tar:
        with open_file_in_tar(inpath, filename) as handle:
            data = json.load(handle)
    else:
        with open_file_in_zip(inpath, filename) as handle:
            data = json.load(handle)
    return data


def _perform_legacy_migrations(current_version: str, to_version: str, metadata: dict, data: dict) -> str:
    """Perform legacy migrations from the current version to the desired version.

    Legacy archives use the old ``data.json`` format for storing the database.
    These migrations simply manipulate the metadata and data in-place.

    :param current_version: current version of the archive
    :param to_version: version to migrate to
    :param metadata: the metadata to migrate
    :param data: the data to migrate
    :return: the new version of the archive
    """
    # compute the migration pathway
    prev_version = current_version
    pathway: List[str] = []
    while prev_version != to_version:
        if prev_version not in LEGACY_MIGRATE_FUNCTIONS:
            raise ArchiveMigrationError(f"No migration pathway available for '{current_version}' to '{to_version}'")
        if prev_version in pathway:
            raise ArchiveMigrationError(
                f'cyclic migration pathway encountered: {" -> ".join(pathway + [prev_version])}'
            )
        pathway.append(prev_version)
        prev_version = LEGACY_MIGRATE_FUNCTIONS[prev_version][0]

    if not pathway:
        MIGRATE_LOGGER.report('No migration required')
        return to_version

    MIGRATE_LOGGER.report('Legacy migration pathway: %s', ' -> '.join(pathway + [to_version]))

    with get_progress_reporter()(total=len(pathway), desc='Performing migrations: ') as progress:
        for from_version in pathway:
            to_version = LEGACY_MIGRATE_FUNCTIONS[from_version][0]
            progress.set_description_str(f'Performing migrations: {from_version} -> {to_version}', refresh=True)
            LEGACY_MIGRATE_FUNCTIONS[from_version][1](metadata, data)
            progress.update()

    return to_version
