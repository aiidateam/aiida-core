###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The table models are dynamically generated from the sqlalchemy backend models."""

from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import shutil
import tarfile
import tempfile
import weakref
import zipfile
from collections.abc import Iterable, Iterator
from contextlib import contextmanager, nullcontext
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, ContextManager, NoReturn, Optional, Tuple, Union, cast
from zipfile import ZipFile, is_zipfile

from pydantic import field_validator
from sqlalchemy.future.engine import Engine
from sqlalchemy.orm import Session

from aiida import __version__
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.common.exceptions import (
    ClosedStorage,
    ConfigurationError,
    CorruptStorage,
    IncompatibleExternalDependencies,
    IncompatibleStorageSchema,
    StorageMigrationError,
    UnreachableStorage,
)
from aiida.common.log import AIIDA_LOGGER
from aiida.common.pydantic import AiiDABaseModel, MetadataField
from aiida.manage import Profile
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import StorageBackend
from aiida.repository.backend.abstract import AbstractRepositoryBackend, InfoDictType

from . import orm
from .utils import (
    DB_FILENAME,
    META_FILENAME,
    REPO_FOLDER,
    ReadOnlyError,
    create_sqla_engine,
    extract_metadata,
    is_url,
    open_remote_zip,
    read_version,
)

if TYPE_CHECKING:
    from remotezip import RemoteZip

__all__ = ('SqliteZipBackend',)

LOGGER = AIIDA_LOGGER.getChild(__file__)
SUPPORTED_VERSION = '3.35.0'  # minimum supported version of sqlite

# Hardcoded zip compression level
COMPRESSION_LEVEL = 6


def validate_sqlite_version() -> None:
    import sqlite3

    from packaging.version import parse

    sqlite_installed_version = parse(sqlite3.sqlite_version)
    if sqlite_installed_version < parse(SUPPORTED_VERSION):
        message = (
            f'Storage backend requires sqlite {parse(SUPPORTED_VERSION)} or higher.'
            f' But you have {sqlite_installed_version} installed.'
        )
        raise IncompatibleExternalDependencies(message)


class _ArchiveResources:
    """Container for the resources opened by a :class:`SqliteZipBackend` instance.

    The container is registered with :func:`weakref.finalize`, such that the resources are released both when the
    backend is garbage collected and at interpreter exit. To that end, it must not hold a reference to the backend
    instance itself, as that would keep the backend alive until interpreter exit.
    """

    def __init__(self) -> None:
        self.db_file: Optional[Path] = None
        self.session: Optional[Session] = None
        self.repo: Optional['_RoBackendRepository'] = None
        self.remote_zip: Optional['RemoteZip'] = None

    def close(self) -> None:
        """Release all resources: close the session and any open zip handle, and delete the temporary database."""
        if self.session:
            self.session.close()
            bind = self.session.get_bind()
            if isinstance(bind, Engine):
                # Fully dispose of the connection pool, so the database file is no longer held open by a pooled
                # connection and can be deleted also on platforms that refuse to delete open files (Windows).
                bind.dispose()
        if self.db_file and self.db_file.exists():
            self.db_file.unlink()
        if self.repo:
            self.repo.close()
        if self.remote_zip:
            self.remote_zip.close()
        self.session = None
        self.db_file = None
        self.repo = None
        self.remote_zip = None


class SqliteZipBackend(StorageBackend):
    """A read-only backend for a sqlite/zip format.

    The storage format uses an SQLite database and repository files, within a folder or zipfile.

    The content of the folder/zipfile should be::

        |- metadata.json
        |- db.sqlite3
        |- repo/
            |- hashkey1
            |- hashkey2
            ...

    """

    read_only = True
    """This plugin is read only and data cannot be created or mutated."""

    class CliModel(AiiDABaseModel):
        """Model describing required information to configure an instance of the storage."""

        filepath: str = MetadataField(
            title='Filepath of the archive', description='Filepath or URL (http/https) of the archive.'
        )
        use_cache: bool = MetadataField(
            False,
            title='Use cache',
            description='Cache the extracted database file in the AiiDA configuration folder, such that subsequent '
            'loads of the profile do not need to extract (or for remote archives, download) it again.',
            # Do not prompt for this niche performance knob in interactive mode; it remains settable with the
            # explicit ``--use-cache`` option.
            option_cls=functools.partial(InteractiveOption, prompt_fn=lambda ctx: False),
        )

        @field_validator('filepath')
        @classmethod
        def filepath_exists_and_is_absolute(cls, value: str) -> str:
            """Validate the filepath exists and return the resolved and absolute filepath, unless it is a URL."""
            if is_url(value):
                return value
            filepath = Path(value)
            if not filepath.is_file():
                msg = f'The archive `{value}` does not exist.'
                raise ValueError(msg)
            return str(filepath.resolve().absolute())

    @classmethod
    def version_head(cls) -> str:
        from .migrator import get_schema_version_head

        return get_schema_version_head()

    @staticmethod
    def create_profile(filepath: str | Path, options: dict | None = None) -> Profile:
        """Create a new profile instance for this backend, from the path or URL of the zip file.

        The profile name is derived from the archive filename, with any character that is not alphanumeric or an
        underscore replaced by an underscore, followed by a short hash of the full location, such that distinct
        locations sharing the same filename map to distinct (but deterministic) profile names.
        """
        location = str(filepath)
        if is_url(filepath):
            from urllib.parse import urlsplit

            name = urlsplit(location).path.rstrip('/').rsplit('/', 1)[-1] or 'remote_archive'
        else:
            name = Path(filepath).name
        digest = hashlib.sha256(location.encode()).hexdigest()[:8]
        sanitized = re.sub(r'\W', '_', name)
        profile_name = f'{sanitized}_{digest}'
        return Profile(
            profile_name,
            {
                'storage': {'backend': 'core.sqlite_zip', 'config': {'filepath': str(filepath)}},
                'process_control': {'backend': None, 'config': {}},
                'options': options or {},
            },
        )

    @classmethod
    def version_profile(cls, profile: Profile) -> Optional[str]:
        return read_version(profile.storage_config['filepath'], search_limit=None)

    @classmethod
    def initialise(cls, profile: 'Profile', reset: bool = False) -> bool:
        """Initialise an instance of the ``SqliteZipBackend`` storage backend.

        :param reset: If ``true``, destroy the backend if it already exists including all of its data before recreating
            and initialising it. This is useful for example for test profiles that need to be reset before or after
            tests having run.
        :returns: ``True`` if the storage was initialised by the function call, ``False`` if it was already initialised.
        """
        validate_sqlite_version()
        from archive_path import ZipPath

        filepath = profile.storage_config['filepath']

        if is_url(filepath):
            # A remote archive cannot be created, reset or migrated in place: it can only be validated to already
            # be at the target schema version.
            if reset:
                msg = f'cannot reset a remote archive: {filepath}'
                raise ReadOnlyError(msg)
            target_version = cls.version_head()
            current_version = cls.get_current_archive_version(inpath=filepath)
            cls.validate_archive_versions(current_version=current_version, target_version=target_version)
            if current_version != target_version:
                msg = (
                    f'The remote archive at `{filepath}` has version {current_version} but version {target_version} '
                    'is required, and a remote archive cannot be migrated in place. Download the file and migrate it '
                    'locally with `verdi archive migrate`.'
                )
                raise StorageMigrationError(msg)
            LOGGER.report(f'Remote {cls.__name__} is already at target version {target_version}.')
            cls._refresh_cache_if_requested(profile)
            return False

        filepath_archive = Path(filepath)

        if filepath_archive.exists() and not reset:
            from .migrator import migrate

            # Check if migration is needed. If we are already at the desired version, then no migration is required
            target_version = cls.version_head()
            current_version = cls.get_current_archive_version(inpath=filepath_archive)
            cls.validate_archive_versions(current_version=current_version, target_version=target_version)
            if current_version == target_version:
                LOGGER.report(
                    f'Existing {cls.__name__} is already at target version {target_version}. No migration needed.'
                )
                cls._refresh_cache_if_requested(profile)
                return False

            # The archive exists but ``reset == False``, so we try to migrate to the latest schema version. If the
            # migration works, we replace the original archive with the migrated one.
            with tempfile.TemporaryDirectory() as dirpath:
                filepath_migrated = Path(dirpath) / 'migrated.zip'
                LOGGER.report(
                    f'Migrating existing {cls.__name__} from version {current_version} to version {target_version}'
                )
                migrate(filepath_archive, filepath_migrated, target_version)
                shutil.move(filepath_migrated, filepath_archive)
                cls._refresh_cache_if_requested(profile)
                return False

        # Here the original archive either doesn't exist or ``reset == True`` so we simply create an empty base archive
        # and move it to the path pointed to by the storage configuration of the profile.
        with tempfile.TemporaryDirectory() as dirpath:
            from .models import SqliteBase

            if reset:
                LOGGER.report(f'Resetting existing {cls.__name__} at {filepath_archive}')
            else:
                LOGGER.report(f'Initialising a new {cls.__name__} at {filepath_archive}')

            filepath_database = Path(dirpath) / DB_FILENAME
            filepath_zip = Path(dirpath) / 'profile.zip'

            metadata = {
                'export_version': cls.version_head(),
                'aiida_version': __version__,
                'key_format': 'sha256',
                'compression': COMPRESSION_LEVEL,
                'ctime': datetime.now().isoformat(),
            }

            # Create the database schema
            SqliteBase.metadata.create_all(create_sqla_engine(filepath_database))

            with ZipPath(
                filepath_zip, mode='w', compresslevel=COMPRESSION_LEVEL, info_order=(META_FILENAME, DB_FILENAME)
            ) as zip_handle:
                (zip_handle / META_FILENAME).write_text(json.dumps(metadata))
                (zip_handle / DB_FILENAME).putfile(filepath_database)

            shutil.move(filepath_zip, filepath_archive)

        cls._refresh_cache_if_requested(profile)

        return True

    @classmethod
    def refresh_cache(cls, profile: Profile) -> str:
        """Cache the database of the archive and record it under the ``cached_database`` storage configuration key.

        The archive schema version is recorded alongside, under the ``cached_database_version`` key, such that a
        cached database can be detected as stale after upgrading ``aiida-core`` even when the archive itself is not
        consulted (see the ``force_cache`` storage configuration key).

        Note that this only updates the profile instance; persisting the recorded keys to the configuration file,
        where applicable, is the responsibility of the caller.

        :param profile: the profile whose database to cache.
        :returns: the filename of the cached database.
        """
        from .cache import get_cache_filename, lookup_cache, store_in_cache

        filepath = profile.storage_config['filepath']

        with cls._open_zip(filepath) as zip_handle:
            try:
                info = zip_handle.getinfo(DB_FILENAME)
            except KeyError as exc:
                msg = f'database could not be read: no `{DB_FILENAME}` in the archive'
                raise CorruptStorage(msg) from exc

            filename = get_cache_filename(info)

            if lookup_cache(filename) is None:
                with zip_handle.open(DB_FILENAME) as source:
                    store_in_cache(source, filename)
                LOGGER.report(f'Cached the database of the archive as `{filename}`.')

            version = read_version(filepath, zip_handle=zip_handle if is_url(filepath) else None)

        profile.storage_config['cached_database'] = filename
        profile.storage_config['cached_database_version'] = version

        return filename

    @classmethod
    def _refresh_cache_if_requested(cls, profile: Profile) -> None:
        """Populate the database cache and record it in the storage configuration, if the profile requests caching."""
        if profile.storage_config.get('use_cache', False):
            cls.refresh_cache(profile)

    @classmethod
    def migrate(cls, profile: Profile) -> NoReturn:
        raise NotImplementedError('use the :func:`aiida.storage.sqlite_zip.migrator.migrate` function directly.')

    def __init__(self, profile: Profile):
        from .migrator import validate_storage

        validate_sqlite_version()
        super().__init__(profile)
        filepath = profile.storage_config['filepath']
        self._path: Union[Path, str] = filepath if is_url(filepath) else Path(filepath)
        # The resources (database session, temporary database file, repository, remote zip handle) are opened lazily
        # and kept in a separate container, registered with ``weakref.finalize``: this releases them both when the
        # backend is garbage collected and at interpreter exit, without keeping the backend instance alive (as e.g.
        # ``atexit.register(self.close)`` would) and without calling ``close`` during interpreter finalization (as
        # ``__del__`` would).
        self._resources = _ArchiveResources()
        self._finalizer = weakref.finalize(self, self._resources.close)
        if not profile.storage_config.get('force_cache', False):
            # With ``force_cache`` the archive is deliberately not accessed: the schema version was already validated
            # when the cached database was recorded for the profile.
            if is_url(filepath):
                # Open a single handle to the remote zip file, reused for the metadata, the database and the
                # repository: each new handle downloads the full central directory of the zip file, which can be
                # expensive.
                self._resources.remote_zip = open_remote_zip(filepath)
            validate_storage(self._path, zip_handle=self._resources.remote_zip)
        self._closed = False

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'SqliteZip storage (read-only) [{state}] @ {self._path}'

    @property
    def is_closed(self) -> bool:
        # A dead finalizer means the resources were already released, e.g. by the interpreter-exit hook of
        # ``weakref.finalize``, in which case the backend is effectively closed even if ``close`` was never called.
        return self._closed or not self._finalizer.alive

    def close(self) -> None:
        """Close the backend"""
        # Calling the finalizer releases the resources and marks it dead, so it will not fire again on garbage
        # collection or at interpreter exit; calling it on an already closed backend is a no-op.
        self._finalizer()
        self._closed = True

    def get_session(self) -> Session:
        """Return an SQLAlchemy session."""
        if self._closed:
            raise ClosedStorage(str(self))
        if self._resources.session is None:
            force_cache = self.profile.storage_config.get('force_cache', False)
            if force_cache or is_url(self._path) or is_zipfile(self._path):
                db_file = self._get_database_file()
                # If the database did not need to be extracted to a private temporary file, it comes from the cache,
                # which is shared between all profiles and processes whose archives have the same content: open it
                # read-only so that no consumer can corrupt it for the others.
                read_only = self._resources.db_file is None
            else:
                db_file = Path(self._path) / DB_FILENAME
                if not db_file.exists():
                    raise CorruptStorage(f'database could not be read: non-existent {db_file}')
                read_only = False
            self._resources.session = Session(create_sqla_engine(db_file, read_only=read_only), future=True)
        return self._resources.session

    @staticmethod
    def _open_zip(path: Union[str, Path]) -> ZipFile:
        """Open the zip archive at the given location, either from the local file system or remotely over HTTP."""
        if is_url(path):
            return open_remote_zip(str(path))
        try:
            return ZipFile(path, mode='r')
        except Exception as exc:
            msg = f'archive could not be read {path}: {exc}'
            raise CorruptStorage(msg) from exc

    def _get_database_file(self) -> Path:
        """Return the path of the extracted database file, extracting or downloading it if necessary.

        The local cache (see :mod:`aiida.storage.sqlite_zip.cache`) is always consulted: if it contains the database
        of the archive, no extraction (or for remote archives, download) is needed. The cache is only written to if
        the ``use_cache`` key of the storage configuration is set, or if the profile records a ``cached_database``
        (meaning it was configured for caching), in which case a missing cache file is simply repopulated. If the
        recorded ``cached_database`` no longer corresponds to the content of the archive, an exception is raised. If
        the ``force_cache`` key is set, the recorded cached database is used directly, without opening the archive.

        Without caching, the database is extracted to a temporary file that is deleted when the storage is closed.
        """
        import requests
        from remotezip import RemoteZipError

        from .cache import get_cache_dirpath, get_cache_filename, lookup_cache, store_in_cache

        storage_config = self.profile.storage_config
        pointer: Optional[str] = storage_config.get('cached_database')
        use_cache: bool = storage_config.get('use_cache', False)

        if storage_config.get('force_cache', False):
            if pointer is None:
                msg = (
                    'cannot force usage of the cached database: the profile does not record one. Only profiles set '
                    'up with `--use-cache`, or refreshed with `verdi profile cache-refresh`, record it.'
                )
                raise ConfigurationError(msg)
            version = storage_config.get('cached_database_version')
            if version is not None and version != self.version_head():
                msg = (
                    f'the database cached for profile `{self.profile.name}` was recorded for archive schema version '
                    f'`{version}`, but this version of AiiDA requires version `{self.version_head()}`. Migrate the '
                    f'archive and refresh the cache with `verdi profile cache-refresh {self.profile.name}` (this '
                    'requires the archive to be reachable).'
                )
                raise IncompatibleStorageSchema(msg)
            filepath = get_cache_dirpath() / pointer
            if not filepath.is_file():
                msg = f'the cached database `{filepath}` recorded for the profile does not exist'
                raise UnreachableStorage(msg)
            LOGGER.warning(
                f'Using the cached database `{pointer}` without validating it against the archive. The data may be '
                'outdated, and repository files will not be accessible if the archive cannot be reached.'
            )
            return filepath

        if is_url(self._path):
            # Reuse the single remote zip handle opened in the constructor without closing it: it is shared with the
            # repository and owned by the resources container.
            zip_context: ContextManager[ZipFile] = nullcontext(cast(ZipFile, self._resources.remote_zip))
        else:
            zip_context = self._open_zip(self._path)

        with zip_context as zip_handle:
            try:
                info = zip_handle.getinfo(DB_FILENAME)
            except KeyError as exc:
                msg = f'database could not be read: no `{DB_FILENAME}` in the archive'
                raise CorruptStorage(msg) from exc

            filename = get_cache_filename(info)

            if pointer is not None and pointer != filename:
                msg = (
                    f'the content of the archive at `{self._path}` no longer corresponds to the database cached for '
                    f'profile `{self.profile.name}`. If the archive is expected to have changed, refresh the cache '
                    f'with: verdi profile cache-refresh {self.profile.name}'
                )
                raise ConfigurationError(msg)

            filepath_cached = lookup_cache(filename)
            if filepath_cached is not None:
                return filepath_cached

            try:
                if use_cache or pointer is not None:
                    with zip_handle.open(DB_FILENAME) as source:
                        return store_in_cache(source, filename)

                # Extract to a temporary file, which is deleted again when the storage is closed
                fd, path = tempfile.mkstemp()
                os.close(fd)
                db_file = self._resources.db_file = Path(path)
                try:
                    with zip_handle.open(DB_FILENAME) as source, db_file.open('wb') as handle:
                        shutil.copyfileobj(source, handle)
                except BaseException:
                    # Do not leave the temporary file behind if the extraction fails: a subsequent call would
                    # create a new temporary file, orphaning this one forever.
                    db_file.unlink(missing_ok=True)
                    self._resources.db_file = None
                    raise
                return db_file
            except (RemoteZipError, requests.RequestException) as exc:
                msg = f'Could not read the database from the remote archive `{self._path}`: {exc}'
                raise UnreachableStorage(msg) from exc
            except (UnreachableStorage, CorruptStorage):
                raise
            except OSError:
                # A failure to write to the local file system (e.g. an unwritable cache directory or a full disk) is
                # not an archive problem: let it propagate as-is instead of misreporting it as archive corruption.
                raise
            except Exception as exc:
                msg = f'database could not be read: {exc}'
                raise CorruptStorage(msg) from exc

    def get_repository(self) -> '_RoBackendRepository':
        if self._closed:
            raise ClosedStorage(str(self))
        if self._resources.repo is None:
            if is_url(self._path):
                self._resources.repo = ZipfileBackendRepository(self._path, zip_handle=self._resources.remote_zip)
            elif is_zipfile(self._path):
                self._resources.repo = ZipfileBackendRepository(self._path)
            elif (Path(self._path) / REPO_FOLDER).exists():
                self._resources.repo = FolderBackendRepository(Path(self._path) / REPO_FOLDER)
            else:
                raise CorruptStorage(f'repository could not be read: non-existent {Path(self._path) / REPO_FOLDER}')
        return self._resources.repo

    def query(self) -> orm.SqliteQueryBuilder:
        return orm.SqliteQueryBuilder(self)

    def get_backend_entity(self, model):
        """Return the backend entity that corresponds to the given Model instance."""
        return orm.get_backend_entity(model, self)

    @cached_property
    def authinfos(self) -> orm.SqliteAuthInfoCollection:
        return orm.SqliteAuthInfoCollection(self)

    @cached_property
    def comments(self) -> orm.SqliteCommentCollection:
        return orm.SqliteCommentCollection(self)

    @cached_property
    def computers(self) -> orm.SqliteComputerCollection:
        return orm.SqliteComputerCollection(self)

    @cached_property
    def groups(self) -> orm.SqliteGroupCollection:
        return orm.SqliteGroupCollection(self)

    @cached_property
    def logs(self) -> orm.SqliteLogCollection:
        return orm.SqliteLogCollection(self)

    @cached_property
    def nodes(self) -> orm.SqliteNodeCollection:
        return orm.SqliteNodeCollection(self)

    @cached_property
    def users(self) -> orm.SqliteUserCollection:
        return orm.SqliteUserCollection(self)

    def _clear(self) -> None:
        raise ReadOnlyError()

    @contextmanager
    def transaction(self) -> Iterator[Session]:
        session = self.get_session()
        if session.in_transaction():
            with session.begin_nested() as savepoint:
                yield session
                savepoint.commit()
            session.commit()
        else:
            with session.begin():
                with session.begin_nested() as savepoint:
                    yield session
                    savepoint.commit()

    @property
    def in_transaction(self) -> bool:
        return False

    def bulk_insert(self, entity_type: EntityTypes, rows: list[dict], allow_defaults: bool = False) -> list[int]:
        raise ReadOnlyError()

    def bulk_update(self, entity_type: EntityTypes, rows: list[dict]) -> None:
        raise ReadOnlyError()

    def delete(self) -> None:
        """Delete the storage and all the data."""
        filepath = self.profile.storage_config['filepath']
        if is_url(filepath):
            LOGGER.report(f'Profile pointed to the remote archive `{filepath}`, which is left untouched.')
            return
        filepath = Path(filepath)
        if filepath.exists():
            filepath.unlink()
            LOGGER.report(f'Deleted archive at `{filepath}`.')

    def delete_nodes_and_connections(self, pks_to_delete: Iterable[int]) -> None:
        raise ReadOnlyError()

    def get_global_variable(self, key: str) -> NoReturn:
        raise NotImplementedError

    def set_global_variable(
        self, key: str, value: Any, description: Optional[str] = None, overwrite: bool = True
    ) -> NoReturn:
        raise ReadOnlyError()

    def maintain(self, full: bool = False, dry_run: bool = False, **kwargs: Any) -> NoReturn:
        raise NotImplementedError

    def get_info(self, detailed: bool = False) -> dict[str, Any]:
        # since extracting the database file is expensive, we only do it if detailed is True
        results = {'metadata': extract_metadata(self._path, zip_handle=self._resources.remote_zip)}

        # Truncate entities_starting_set in metadata if not detailed
        if not detailed:
            creation_params = results['metadata'].get('creation_parameters')
            if creation_params and creation_params.get('entities_starting_set') is not None:
                entities_starting_set = creation_params['entities_starting_set']
                truncated_entities = {}
                max_display = 5

                for entity_type, uuid_list in entities_starting_set.items():
                    if isinstance(uuid_list, list) and len(uuid_list) > max_display:
                        truncated_entities[entity_type] = uuid_list[:max_display] + [
                            f'... and {len(uuid_list) - max_display} more (use --detailed to show all)'
                        ]
                    else:
                        truncated_entities[entity_type] = uuid_list

                results['metadata']['creation_parameters']['entities_starting_set'] = truncated_entities

        if detailed:
            results.update(super().get_info(detailed=detailed))
            results['repository'] = self.get_repository().get_info(detailed)
        return results

    @staticmethod
    def get_current_archive_version(inpath: Union[str, Path]) -> str:
        """Return the current version from metadata, raising if invalid/corrupt."""

        if not is_url(inpath):
            inpath = Path(inpath)
            if not (tarfile.is_tarfile(str(inpath)) or zipfile.is_zipfile(str(inpath))):
                raise CorruptStorage(f'The input file is neither a tar nor a zip file: {inpath}')

        metadata = extract_metadata(inpath, search_limit=None)

        if 'export_version' not in metadata:
            raise CorruptStorage('No export_version found in metadata')

        return metadata['export_version']

    @staticmethod
    def validate_archive_versions(current_version: str, target_version: str) -> None:
        """Check if migration is needed, raising if legacy/unsupported/invalid."""
        from .migrator import list_versions

        if current_version in ('0.1', '0.2', '0.3') or target_version in ('0.1', '0.2', '0.3'):
            raise StorageMigrationError(
                f"Legacy migration from '{current_version}' -> '{target_version}' "
                'is not supported in aiida-core v2. First migrate them to the latest '
                'version in aiida-core v1.'
            )

        all_versions = list_versions()
        if target_version not in all_versions:
            raise StorageMigrationError(f"Unknown target version '{target_version}'")
        if current_version not in all_versions:
            raise StorageMigrationError(f"Unknown current version '{current_version}'")


class _RoBackendRepository(AbstractRepositoryBackend):
    """A backend abstract for a read-only folder or zip file."""

    def __init__(self, path: str | Path):
        """Initialise the repository backend.

        :param path: the path to the zip file or folder, or the URL of a remote zip file
        """
        self._path: Union[Path, str] = path if is_url(path) else Path(path)
        self._closed = False

    def close(self) -> None:
        """Close the repository."""
        self._closed = True

    @property
    def uuid(self) -> Optional[str]:
        return None

    @property
    def key_format(self) -> Optional[str]:
        return 'sha256'

    def initialise(self, **kwargs: Any) -> None:
        pass

    @property
    def is_initialised(self) -> bool:
        return True

    def erase(self) -> None:
        raise ReadOnlyError()

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        raise ReadOnlyError()

    def has_objects(self, keys: list[str]) -> list[bool]:
        return [self.has_object(key) for key in keys]

    def iter_object_streams(self, keys: Iterable[str]) -> Iterator[Tuple[str, BinaryIO]]:
        for key in keys:
            with self.open(key) as handle:
                yield key, handle

    def delete_objects(self, keys: list[str]) -> None:
        raise ReadOnlyError()

    def get_object_hash(self, key: str) -> str:
        return key

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs: Any) -> None:
        pass

    def get_info(self, detailed: bool = False, **kwargs: Any) -> InfoDictType:
        return {'objects': {'count': len(list(self.list_objects()))}}


class ZipfileBackendRepository(_RoBackendRepository):
    """A read-only backend for a zip file.

    The zip file should contain repository files with the key format: ``repo/<sha256 hash>``,
    i.e. files named by the sha256 hash of the file contents, inside a ``repo`` directory.
    """

    def __init__(self, path: str | Path, zip_handle: Optional[ZipFile] = None):
        """Initialise the repository backend.

        :param path: the path to the zip file, or the URL of a remote zip file.
        :param zip_handle: optionally, an already-open zip file handle for ``path``, which is reused instead of
            opening a new one. The caller remains responsible for closing it: the repository only closes the
            handle if it opened it itself.
        """
        super().__init__(path)
        self._folder = REPO_FOLDER
        self.__zipfile: None | ZipFile = zip_handle
        self.__owns_zipfile: bool = zip_handle is None

    def close(self) -> None:
        if self.__zipfile and self.__owns_zipfile:
            self.__zipfile.close()
        super().close()

    @property
    def _zipfile(self) -> ZipFile:
        """Return the open zip file."""
        if self._closed:
            raise ClosedStorage(f'repository is closed: {self._path}')
        if self.__zipfile is None:
            if is_url(self._path):
                self.__zipfile = open_remote_zip(str(self._path))
            else:
                try:
                    self.__zipfile = ZipFile(self._path, mode='r')
                except Exception as exc:
                    raise CorruptStorage(f'repository could not be read {self._path}: {exc}') from exc
        return self.__zipfile

    def has_object(self, key: str) -> bool:
        try:
            self._zipfile.getinfo(f'{self._folder}/{key}')
        except KeyError:
            return False
        return True

    def list_objects(self) -> Iterable[str]:
        prefix = f'{self._folder}/'
        prefix_len = len(prefix)
        for name in self._zipfile.namelist():
            if name.startswith(prefix) and name[prefix_len:]:
                yield name[prefix_len:]

    @contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        handle = None
        try:
            handle = self._zipfile.open(f'{self._folder}/{key}')
            yield cast(BinaryIO, handle)
        except KeyError:
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
        finally:
            if handle is not None:
                handle.close()


class FolderBackendRepository(_RoBackendRepository):
    """A read-only backend for a folder.

    The folder should contain repository files, named by the sha256 hash of the file contents.
    """

    def has_object(self, key: str) -> bool:
        return Path(self._path).joinpath(key).is_file()

    def list_objects(self) -> Iterable[str]:
        for subpath in Path(self._path).iterdir():
            if subpath.is_file():
                yield subpath.name

    @contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        filepath = Path(self._path).joinpath(key)
        if not filepath.is_file():
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
        with filepath.open('rb') as handle:
            yield cast(BinaryIO, handle)
