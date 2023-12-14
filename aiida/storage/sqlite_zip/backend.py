# -*- coding: utf-8 -*-
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

from contextlib import contextmanager
from datetime import datetime
from functools import cached_property
import json
from pathlib import Path
import shutil
import tempfile
from typing import BinaryIO, Iterable, Iterator, Optional, Sequence, Tuple, cast
from zipfile import ZipFile, is_zipfile

from archive_path import ZipPath, extract_file_in_zip
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from aiida import __version__
from aiida.common.exceptions import ClosedStorage, CorruptStorage
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import Profile
from aiida.orm.entities import EntityTypes
from aiida.orm.implementation import StorageBackend
from aiida.repository.backend.abstract import AbstractRepositoryBackend

from . import orm
from .migrator import get_schema_version_head, migrate, validate_storage
from .utils import (
    DB_FILENAME,
    META_FILENAME,
    REPO_FOLDER,
    ReadOnlyError,
    create_sqla_engine,
    extract_metadata,
    read_version,
)

__all__ = ('SqliteZipBackend',)

LOGGER = AIIDA_LOGGER.getChild(__file__)


class SqliteZipBackend(StorageBackend):  # pylint: disable=too-many-public-methods
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

    class Configuration(BaseModel):
        """Model describing required information to configure an instance of the storage."""

        filepath: str = Field(title='Filepath of the archive', description='Filepath of the archive.')

        @field_validator('filepath')
        @classmethod
        def filepath_exists_and_is_absolute(cls, value: str) -> str:
            """Validate the filepath exists and return the resolved and absolute filepath."""
            filepath = Path(value)
            assert filepath.is_file(), f'The archive `{value}` does not exist.'
            return str(filepath.resolve().absolute())

    @classmethod
    def version_head(cls) -> str:
        return get_schema_version_head()

    @staticmethod
    def create_profile(filepath: str | Path, options: dict | None = None) -> Profile:
        """Create a new profile instance for this backend, from the path to the zip file."""
        profile_name = Path(filepath).name
        return Profile(
            profile_name, {
                'storage': {
                    'backend': 'core.sqlite_zip',
                    'config': {
                        'filepath': str(filepath)
                    }
                },
                'process_control': {
                    'backend': 'null',
                    'config': {}
                },
                'options': options or {},
            }
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
        filepath_archive = Path(profile.storage_config['filepath'])

        if filepath_archive.exists() and not reset:
            # The archive exists but ``reset == False``, so we try to migrate to the latest schema version. If the
            # migration works, we replace the original archive with the migrated one.
            with tempfile.TemporaryDirectory() as dirpath:
                filepath_migrated = Path(dirpath) / 'migrated.zip'
                LOGGER.report(f'Migrating existing {cls.__name__}')
                migrate(filepath_archive, filepath_migrated, cls.version_head())
                shutil.move(filepath_migrated, filepath_archive)  # type: ignore[arg-type]
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
                'compression': 6,
                'ctime': datetime.now().isoformat(),
            }

            # Create the database schema
            SqliteBase.metadata.create_all(create_sqla_engine(filepath_database))

            with ZipPath(
                filepath_zip, mode='w', compresslevel=metadata['compression'], info_order=(META_FILENAME, DB_FILENAME)
            ) as zip_handle:
                (zip_handle / META_FILENAME).write_text(json.dumps(metadata))
                (zip_handle / DB_FILENAME).putfile(filepath_database)

            shutil.move(filepath_zip, filepath_archive)  # type: ignore[arg-type]

        return True

    @classmethod
    def migrate(cls, profile: Profile):
        raise NotImplementedError('use the :func:`aiida.storage.sqlite_zip.migrator.migrate` function directly.')

    def __init__(self, profile: Profile):
        super().__init__(profile)
        self._path = Path(profile.storage_config['filepath'])
        validate_storage(self._path)
        # lazy open the archive zipfile and extract the database file
        self._db_file: Optional[Path] = None
        self._session: Optional[Session] = None
        self._repo: Optional[_RoBackendRepository] = None
        self._closed = False

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'SqliteZip storage (read-only) [{state}] @ {self._path}'

    @property
    def is_closed(self) -> bool:
        return self._closed

    def close(self):
        """Close the backend"""
        if self._session:
            self._session.close()
        if self._db_file and self._db_file.exists():
            self._db_file.unlink()
        if self._repo:
            self._repo.close()
        self._session = None
        self._db_file = None
        self._repo = None
        self._closed = True

    def get_session(self) -> Session:
        """Return an SQLAlchemy session."""
        if self._closed:
            raise ClosedStorage(str(self))
        if self._session is None:
            if is_zipfile(self._path):
                _, path = tempfile.mkstemp()
                db_file = self._db_file = Path(path)
                with db_file.open('wb') as handle:
                    try:
                        extract_file_in_zip(self._path, DB_FILENAME, handle, search_limit=4)
                    except Exception as exc:
                        raise CorruptStorage(f'database could not be read: {exc}') from exc
            else:
                db_file = self._path / DB_FILENAME
                if not db_file.exists():
                    raise CorruptStorage(f'database could not be read: non-existent {db_file}')
            self._session = Session(create_sqla_engine(db_file), future=True)
        return self._session

    def get_repository(self) -> '_RoBackendRepository':
        if self._closed:
            raise ClosedStorage(str(self))
        if self._repo is None:
            if is_zipfile(self._path):
                self._repo = ZipfileBackendRepository(self._path)
            elif (self._path / REPO_FOLDER).exists():
                self._repo = FolderBackendRepository(self._path / REPO_FOLDER)
            else:
                raise CorruptStorage(f'repository could not be read: non-existent {self._path / REPO_FOLDER}')
        return self._repo

    def query(self) -> orm.SqliteQueryBuilder:
        return orm.SqliteQueryBuilder(self)

    def get_backend_entity(self, model):
        """Return the backend entity that corresponds to the given Model instance."""
        return orm.get_backend_entity(model, self)

    @cached_property
    def authinfos(self):
        return orm.SqliteAuthInfoCollection(self)

    @cached_property
    def comments(self):
        return orm.SqliteCommentCollection(self)

    @cached_property
    def computers(self):
        return orm.SqliteComputerCollection(self)

    @cached_property
    def groups(self):
        return orm.SqliteGroupCollection(self)

    @cached_property
    def logs(self):
        return orm.SqliteLogCollection(self)

    @cached_property
    def nodes(self):
        return orm.SqliteNodeCollection(self)

    @cached_property
    def users(self):
        return orm.SqliteUserCollection(self)

    def _clear(self) -> None:
        raise ReadOnlyError()

    @contextmanager
    def transaction(self):
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
        filepath = Path(self.profile.storage_config['filepath'])
        if filepath.exists():
            filepath.unlink()
            LOGGER.report(f'Deleted archive at `{filepath}`.')

    def delete_nodes_and_connections(self, pks_to_delete: Sequence[int]):
        raise ReadOnlyError()

    def get_global_variable(self, key: str):
        raise NotImplementedError

    def set_global_variable(self, key: str, value, description: Optional[str] = None, overwrite=True) -> None:
        raise ReadOnlyError()

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        raise NotImplementedError

    def get_info(self, detailed: bool = False) -> dict:
        # since extracting the database file is expensive, we only do it if detailed is True
        results = {'metadata': extract_metadata(self._path)}
        if detailed:
            results.update(super().get_info(detailed=detailed))
            results['repository'] = self.get_repository().get_info(detailed)
        return results


class _RoBackendRepository(AbstractRepositoryBackend):  # pylint: disable=abstract-method
    """A backend abstract for a read-only folder or zip file."""

    def __init__(self, path: str | Path):
        """Initialise the repository backend.

        :param path: the path to the zip file
        """
        self._path = Path(path)
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

    def initialise(self, **kwargs) -> None:
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

    def iter_object_streams(self, keys: list[str]) -> Iterator[Tuple[str, BinaryIO]]:
        for key in keys:
            with self.open(key) as handle:  # pylint: disable=not-context-manager
                yield key, handle

    def delete_objects(self, keys: list[str]) -> None:
        raise ReadOnlyError()

    def get_object_hash(self, key: str) -> str:
        return key

    def maintain(self, dry_run: bool = False, live: bool = True, **kwargs) -> None:
        pass

    def get_info(self, detailed: bool = False, **kwargs) -> dict:
        return {'objects': {'count': len(list(self.list_objects()))}}


class ZipfileBackendRepository(_RoBackendRepository):
    """A read-only backend for a zip file.

    The zip file should contain repository files with the key format: ``repo/<sha256 hash>``,
    i.e. files named by the sha256 hash of the file contents, inside a ``repo`` directory.
    """

    def __init__(self, path: str | Path):
        super().__init__(path)
        self._folder = REPO_FOLDER
        self.__zipfile: None | ZipFile = None

    def close(self) -> None:
        if self._zipfile:
            self._zipfile.close()
        super().close()

    @property
    def _zipfile(self) -> ZipFile:
        """Return the open zip file."""
        if self._closed:
            raise ClosedStorage(f'repository is closed: {self._path}')
        if self.__zipfile is None:
            try:
                self.__zipfile = ZipFile(self._path, mode='r')  # pylint: disable=consider-using-with
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
        try:
            handle = self._zipfile.open(f'{self._folder}/{key}')
            yield cast(BinaryIO, handle)
        except KeyError:
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
        finally:
            handle.close()


class FolderBackendRepository(_RoBackendRepository):
    """A read-only backend for a folder.

    The folder should contain repository files, named by the sha256 hash of the file contents.
    """

    def has_object(self, key: str) -> bool:
        return self._path.joinpath(key).is_file()

    def list_objects(self) -> Iterable[str]:
        for subpath in self._path.iterdir():
            if subpath.is_file():
                yield subpath.name

    @contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        if not self._path.joinpath(key).is_file():
            raise FileNotFoundError(f'object with key `{key}` does not exist.')
        with self._path.joinpath(key).open('rb', encoding='utf-8') as handle:
            yield handle
