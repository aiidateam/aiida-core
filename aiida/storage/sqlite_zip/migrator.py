# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Versioning and migration implementation for the sqlite_zip format."""
import contextlib
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from typing import Any, Dict, Iterator, List, Optional, Union
import zipfile

from alembic.command import upgrade
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext, MigrationInfo
from alembic.script import ScriptDirectory
from archive_path import ZipPath, extract_file_in_zip, open_file_in_tar, open_file_in_zip

from aiida.common.exceptions import CorruptStorage, IncompatibleStorageSchema, StorageMigrationError
from aiida.common.progress_reporter import get_progress_reporter
from aiida.storage.log import MIGRATE_LOGGER

from .migrations.legacy import FINAL_LEGACY_VERSION, LEGACY_MIGRATE_FUNCTIONS
from .migrations.legacy_to_main import LEGACY_TO_MAIN_REVISION, perform_v1_migration
from .migrations.utils import copy_tar_to_zip, copy_zip_to_zip, update_metadata
from .utils import DB_FILENAME, META_FILENAME, REPO_FOLDER, create_sqla_engine, extract_metadata, read_version


def get_schema_version_head() -> str:
    """Return the head schema version for this storage, i.e. the latest schema this storage can be migrated to."""
    return _alembic_script().revision_map.get_current_head('main') or ''


def list_versions() -> List[str]:
    """Return all available schema versions (oldest to latest)."""
    legacy_versions = list(LEGACY_MIGRATE_FUNCTIONS) + [FINAL_LEGACY_VERSION]
    alembic_versions = [entry.revision for entry in reversed(list(_alembic_script().walk_revisions()))]
    return legacy_versions + alembic_versions


def validate_storage(inpath: Path) -> None:
    """Validate that the storage is at the head version.

    :raises: :class:`aiida.common.exceptions.UnreachableStorage` if the file does not exist
    :raises: :class:`aiida.common.exceptions.CorruptStorage`
        if the version cannot be read from the storage.
    :raises: :class:`aiida.common.exceptions.IncompatibleStorageSchema`
        if the storage is not compatible with the code API.
    """
    schema_version_code = get_schema_version_head()
    schema_version_archive = read_version(inpath)
    if schema_version_archive != schema_version_code:
        raise IncompatibleStorageSchema(
            f'Archive schema version `{schema_version_archive}` '
            f'is incompatible with the required schema version `{schema_version_code}`. '
            'To migrate the archive schema version to the current one, '
            f'run the following command: verdi archive migrate {str(inpath)!r}'
        )


def migrate(  # pylint: disable=too-many-branches,too-many-statements,too-many-locals
    inpath: Union[str, Path],
    outpath: Union[str, Path],
    version: str,
    *,
    force: bool = False,
    compression: int = 6
) -> None:
    """Migrate an `sqlite_zip` storage file to a specific version.

    Historically, this format could be a zip or a tar file,
    contained the database as a bespoke JSON format, and the repository files in the "legacy" per-node format.
    For these versions, we first migrate the JSON database to the final legacy schema,
    then we convert this file to the SQLite database, whilst sequentially migrating the repository files.

    Once any legacy migrations have been performed, we can then migrate the SQLite database to the final schema,
    using alembic.

    Note that, to minimise disk space usage, we never fully extract/uncompress the input file
    (except when migrating from a legacy tar file, whereby we cannot extract individual files):

    1. The sqlite database is extracted to a temporary location and migrated
    2. A new zip file is opened, within a temporary folder
    3. The repository files are "streamed" directly between the input file and the new zip file
    4. The sqlite database and metadata JSON are written to the new zip file
    5. The new zip file is closed (which writes its final central directory)
    6. The new zip file is moved to the output location, removing any existing file if `force=True`

    :param path: Path to the file
    :param outpath: Path to output the migrated file
    :param version: Target version
    :param force: If True, overwrite the output file if it exists
    :param compression: Compression level for the output file
    """
    inpath = Path(inpath)
    outpath = Path(outpath)

    # halt immediately, if we could not write to the output file
    if outpath.exists() and not force:
        raise StorageMigrationError('Output path already exists and force=False')
    if outpath.exists() and not outpath.is_file():
        raise StorageMigrationError('Existing output path is not a file')

    # the file should be either a tar (legacy only) or zip file
    if tarfile.is_tarfile(str(inpath)):
        is_tar = True
    elif zipfile.is_zipfile(str(inpath)):
        is_tar = False
    else:
        raise CorruptStorage(f'The input file is neither a tar nor a zip file: {inpath}')

    # read the metadata.json which should always be present
    metadata = extract_metadata(inpath, search_limit=None)

    # obtain the current version from the metadata
    if 'export_version' not in metadata:
        raise CorruptStorage('No export_version found in metadata')
    current_version = metadata['export_version']
    # update the modified time of the file and the compression
    metadata['mtime'] = datetime.now().isoformat()
    metadata['compression'] = compression

    # check versions are valid
    # versions 0.1, 0.2, 0.3 are no longer supported,
    # since 0.3 -> 0.4 requires costly migrations of repo files (you would need to unpack all of them)
    if current_version in ('0.1', '0.2', '0.3') or version in ('0.1', '0.2', '0.3'):
        raise StorageMigrationError(
            f"Legacy migration from '{current_version}' -> '{version}' is not supported in aiida-core v2. "
            'First migrate them to the latest version in aiida-core v1.'
        )
    all_versions = list_versions()
    if current_version not in all_versions:
        raise StorageMigrationError(f"Unknown current version '{current_version}'")
    if version not in all_versions:
        raise StorageMigrationError(f"Unknown target version '{version}'")

    # if we are already at the desired version, then no migration is required, so simply copy the file if necessary
    if current_version == version:
        if inpath != outpath:
            if outpath.exists() and force:
                outpath.unlink()
            shutil.copyfile(inpath, outpath)
        return

    # if the archive is a "legacy" format, i.e. has a data.json file, migrate it to the target/final legacy schema
    data: Optional[Dict[str, Any]] = None
    if current_version in LEGACY_MIGRATE_FUNCTIONS:
        MIGRATE_LOGGER.report(f'Legacy migrations required from {"tar" if is_tar else "zip"} format')
        MIGRATE_LOGGER.report('Extracting data.json ...')
        # read the data.json file
        data = _read_json(inpath, 'data.json', is_tar)
        to_version = FINAL_LEGACY_VERSION if version not in LEGACY_MIGRATE_FUNCTIONS else version
        current_version = _perform_legacy_migrations(current_version, to_version, metadata, data)

    # if we are now at the target version, then write the updated files to a new zip file and exit
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

    # open the temporary directory, to perform further migrations
    with tempfile.TemporaryDirectory() as tmpdirname:

        # open the new zip file, within which to write the migrated content
        new_zip_path = Path(tmpdirname) / 'new.zip'
        central_dir: Dict[str, Any] = {}
        with ZipPath(
            new_zip_path,
            mode='w',
            compresslevel=compression,
            name_to_info=central_dir,
            # this ensures that the metadata and database files are written above the repository files,
            # in in the central directory, so that they can be accessed easily
            info_order=(META_FILENAME, DB_FILENAME)
        ) as new_zip:

            written_repo = False
            if current_version == FINAL_LEGACY_VERSION:
                # migrate from the legacy format,
                # streaming the repository files directly to the new zip file
                MIGRATE_LOGGER.report(
                    f'legacy {FINAL_LEGACY_VERSION!r} -> {LEGACY_TO_MAIN_REVISION!r} conversion required'
                )
                if data is None:
                    MIGRATE_LOGGER.report('Extracting data.json ...')
                    data = _read_json(inpath, 'data.json', is_tar)
                db_path = perform_v1_migration(inpath, Path(tmpdirname), new_zip, central_dir, is_tar, metadata, data)
                # the migration includes adding the repository files to the new zip file
                written_repo = True
                current_version = LEGACY_TO_MAIN_REVISION
            else:
                if is_tar:
                    raise CorruptStorage('Tar files are not supported for this format')
                # extract the sqlite database, for alembic migrations
                db_path = Path(tmpdirname) / DB_FILENAME
                with db_path.open('wb') as handle:
                    try:
                        extract_file_in_zip(inpath, DB_FILENAME, handle)
                    except Exception as exc:
                        raise CorruptStorage(f'database could not be read: {exc}') from exc

            # perform alembic migrations
            # note, we do this before writing the repository files (unless a legacy migration),
            # so that we don't waste time doing that (which could be slow), only for alembic to fail
            if current_version != version:
                MIGRATE_LOGGER.report('Performing SQLite migrations:')
                with _migration_context(db_path) as context:
                    assert context.script is not None
                    context.stamp(context.script, current_version)
                    context.connection.commit()  # type: ignore
                # see https://alembic.sqlalchemy.org/en/latest/batch.html#dealing-with-referencing-foreign-keys
                # for why we do not enforce foreign keys here
                with _alembic_connect(db_path, enforce_foreign_keys=False) as config:
                    upgrade(config, version)
                update_metadata(metadata, version)

            if not written_repo:
                # stream the repository files directly to the new zip file
                with ZipPath(inpath, mode='r') as old_zip:
                    length = sum(1 for _ in old_zip.glob('**/*', include_virtual=False))
                    title = 'Copying repository files'
                    with get_progress_reporter()(desc=title, total=length) as progress:
                        for subpath in old_zip.glob('**/*', include_virtual=False):
                            new_path_sub = new_zip.joinpath(subpath.at)
                            if subpath.parts[0] == REPO_FOLDER:
                                if subpath.is_dir():
                                    new_path_sub.mkdir(exist_ok=True)
                                else:
                                    new_path_sub.putfile(subpath)
                            progress.update()

            MIGRATE_LOGGER.report('Finalising the migration ...')

            # write the final database file to the new zip file
            (new_zip / DB_FILENAME).putfile(db_path)

            # write the final metadata.json file to the new zip file
            (new_zip / META_FILENAME).write_text(json.dumps(metadata))

            # on exiting the the ZipPath context, the zip file is closed and the central directory written

        # move the new zip file to the final location
        if outpath.exists() and force:
            outpath.unlink()
        shutil.move(new_zip_path, outpath)  # type: ignore[arg-type]


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
            raise StorageMigrationError(f"No migration pathway available for '{current_version}' to '{to_version}'")
        if prev_version in pathway:
            raise StorageMigrationError(
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


def _alembic_config() -> Config:
    """Return an instance of an Alembic `Config`."""
    config = Config()
    config.set_main_option('script_location', str(Path(os.path.realpath(__file__)).parent / 'migrations'))
    return config


def _alembic_script() -> ScriptDirectory:
    """Return an instance of an Alembic `ScriptDirectory`."""
    return ScriptDirectory.from_config(_alembic_config())


@contextlib.contextmanager
def _alembic_connect(db_path: Path, enforce_foreign_keys=True) -> Iterator[Config]:
    """Context manager to return an instance of an Alembic configuration.

    The profiles's database connection is added in the `attributes` property, through which it can then also be
    retrieved, also in the `env.py` file, which is run when the database is migrated.
    """
    with create_sqla_engine(db_path, enforce_foreign_keys=enforce_foreign_keys).connect() as connection:
        config = _alembic_config()
        config.attributes['connection'] = connection  # pylint: disable=unsupported-assignment-operation

        def _callback(step: MigrationInfo, **kwargs):  # pylint: disable=unused-argument
            """Callback to be called after a migration step is executed."""
            from_rev = step.down_revision_ids[0] if step.down_revision_ids else '<base>'
            MIGRATE_LOGGER.report(f'- {from_rev} -> {step.up_revision_id}')

        config.attributes['on_version_apply'] = _callback  # pylint: disable=unsupported-assignment-operation

        yield config


@contextlib.contextmanager
def _migration_context(db_path: Path) -> Iterator[MigrationContext]:
    """Context manager to return an instance of an Alembic migration context.

    This migration context will have been configured with the current database connection, which allows this context
    to be used to inspect the contents of the database, such as the current revision.
    """
    with _alembic_connect(db_path) as config:
        script = ScriptDirectory.from_config(config)
        with EnvironmentContext(config, script) as context:
            context.configure(context.config.attributes['connection'])
            yield context.get_context()
