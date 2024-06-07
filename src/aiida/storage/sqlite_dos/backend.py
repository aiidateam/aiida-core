###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Storage implementation using Sqlite database and disk-objectstore container."""

from __future__ import annotations

from functools import cached_property, lru_cache
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from disk_objectstore import Container, backup_utils
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import insert
from sqlalchemy.orm import scoped_session, sessionmaker

from aiida.common import exceptions
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import Profile
from aiida.manage.configuration.settings import AIIDA_CONFIG_FOLDER
from aiida.orm.implementation import BackendEntity
from aiida.storage.psql_dos.models.settings import DbSetting
from aiida.storage.sqlite_zip import models, orm
from aiida.storage.sqlite_zip.migrator import get_schema_version_head
from aiida.storage.sqlite_zip.utils import create_sqla_engine

from ..psql_dos import PsqlDosBackend
from ..psql_dos.migrator import REPOSITORY_UUID_KEY, PsqlDosMigrator

if TYPE_CHECKING:
    from aiida.orm.entities import EntityTypes
    from aiida.repository.backend import DiskObjectStoreRepositoryBackend

__all__ = ('SqliteDosStorage',)

LOGGER = AIIDA_LOGGER.getChild(__file__)
FILENAME_DATABASE = 'database.sqlite'
FILENAME_CONTAINER = 'container'


class SqliteDosMigrator(PsqlDosMigrator):
    """Storage implementation using Sqlite database and disk-objectstore container.

    This storage backend is not recommended for use in production. The sqlite database is not the most performant and it
    does not support all the ``QueryBuilder`` functionality that is supported by the ``core.psql_dos`` storage backend.
    This storage is ideally suited for use cases that want to test or demo AiiDA as it requires no server but just a
    folder on the local filesystem.
    """

    def __init__(self, profile: Profile) -> None:
        filepath_database = Path(profile.storage_config['filepath']) / FILENAME_DATABASE
        filepath_database.touch()

        self.profile = profile
        self._engine = create_sqla_engine(filepath_database)
        self._connection = None

    def get_container(self) -> Container:
        """Return the disk-object store container.

        :returns: The disk-object store container configured for the repository path of the current profile.
        """
        filepath_container = Path(self.profile.storage_config['filepath']) / FILENAME_CONTAINER
        return Container(str(filepath_container))

    def initialise_database(self) -> None:
        """Initialise the database.

        This assumes that the database has no schema whatsoever and so the initial schema is created directly from the
        models at the current head version without migrating through all of them one by one.
        """
        models.SqliteBase.metadata.create_all(self._engine)

        repository_uuid = self.get_repository_uuid()

        # Create a "sync" between the database and repository, by saving its UUID in the settings table
        # this allows us to validate inconsistencies between the two
        self.connection.execute(
            insert(DbSetting).values(key=REPOSITORY_UUID_KEY, val=repository_uuid, description='Repository UUID')
        )

        # finally, generate the version table, "stamping" it with the most recent revision
        with self._migration_context() as context:
            context.stamp(context.script, 'main@head')  # type: ignore[arg-type]
            self.connection.commit()


class SqliteDosStorage(PsqlDosBackend):
    """A lightweight storage that is easy to install.

    This backend implementation uses an SQLite database and a disk-objectstore container as the file repository. As
    such, this storage plugin does not require any services, making it easy to install and use on most systems.
    """

    migrator = SqliteDosMigrator

    class Model(BaseModel, defer_build=True):
        """Model describing required information to configure an instance of the storage."""

        filepath: str = Field(
            title='Directory of the backend',
            description='Filepath of the directory in which to store data for this backend.',
            default_factory=lambda: str(AIIDA_CONFIG_FOLDER / 'repository' / f'sqlite_dos_{uuid4().hex}'),
        )

        @field_validator('filepath')
        @classmethod
        def filepath_is_absolute(cls, value: str) -> str:
            """Return the resolved and absolute filepath."""
            return str(Path(value).resolve().absolute())

    @property
    def filepath_root(self) -> Path:
        return Path(self.profile.storage_config['filepath'])

    @property
    def filepath_container(self) -> Path:
        return self.filepath_root / FILENAME_CONTAINER

    @property
    def filepath_database(self) -> Path:
        return self.filepath_root / FILENAME_DATABASE

    @classmethod
    def initialise(cls, profile: Profile, reset: bool = False) -> bool:
        filepath = Path(profile.storage_config['filepath'])

        try:
            filepath.mkdir(parents=True, exist_ok=True)
        except FileExistsError as exception:
            raise ValueError(
                f'`{filepath}` is a file and cannot be used for instance of `SqliteDosStorage`.'
            ) from exception

        if list(filepath.iterdir()):
            raise ValueError(
                f'`{filepath}` already exists but is not empty and cannot be used for instance of `SqliteDosStorage`.'
            )

        return super().initialise(profile, reset)

    def __str__(self) -> str:
        state = 'closed' if self.is_closed else 'open'
        return f'SqliteDosStorage[{self.filepath_root}]: {state},'

    def _initialise_session(self):
        """Initialise the SQLAlchemy session factory.

        Only one session factory is ever associated with a given class instance,
        i.e. once the instance is closed, it cannot be reopened.

        The session factory, returns a session that is bound to the current thread.
        Multi-thread support is currently required by the REST API.
        Although, in the future, we may want to move the multi-thread handling to higher in the AiiDA stack.
        """
        engine = create_sqla_engine(self.filepath_database)
        self._session_factory = scoped_session(sessionmaker(bind=engine, future=True, expire_on_commit=True))

    def delete(self) -> None:  # type: ignore[override]
        """Delete the storage and all the data."""
        if self.filepath_root.exists():
            rmtree(self.filepath_root)
            LOGGER.report(f'Deleted storage directory at `{self.filepath_root}`.')

    def get_container(self) -> 'Container':
        return Container(str(self.filepath_container))

    def get_repository(self) -> 'DiskObjectStoreRepositoryBackend':
        from aiida.repository.backend import DiskObjectStoreRepositoryBackend

        return DiskObjectStoreRepositoryBackend(container=self.get_container())

    @classmethod
    def version_head(cls) -> str:
        return get_schema_version_head()

    @classmethod
    def version_profile(cls, profile: Profile) -> str | None:
        return get_schema_version_head()

    def query(self) -> orm.SqliteQueryBuilder:
        return orm.SqliteQueryBuilder(self)

    def get_backend_entity(self, model) -> BackendEntity:
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

    @staticmethod
    @lru_cache(maxsize=18)
    def _get_mapper_from_entity(entity_type: 'EntityTypes', with_pk: bool):
        """Return the Sqlalchemy mapper and fields corresponding to the given entity.

        :param with_pk: if True, the fields returned will include the primary key
        """
        from sqlalchemy import inspect

        from ..sqlite_zip.models import MAP_ENTITY_TYPE_TO_MODEL

        model = MAP_ENTITY_TYPE_TO_MODEL[entity_type]
        mapper = inspect(model).mapper  # type: ignore[union-attr]
        keys = {key for key, col in mapper.c.items() if with_pk or col not in mapper.primary_key}
        return mapper, keys

    def _backup(
        self,
        dest: str,
        keep: Optional[int] = None,
    ):
        """Create a backup of the storage.

        :param dest: Path to where the backup will be created. Can be a path on the local file system, or a path on a
            remote that can be accessed over SSH in the form ``<user>@<host>:<path>``.
        :param keep: The maximum number of backups to keep. If the number of copies exceeds this number, the oldest
            backups are removed.
        """
        try:
            backup_manager = backup_utils.BackupManager(dest, keep=keep)
            backup_manager.backup_auto_folders(lambda path, prev: self._backup_storage(backup_manager, path, prev))
        except backup_utils.BackupError as exc:
            raise exceptions.StorageBackupError(*exc.args) from exc

    def _backup_storage(
        self,
        manager: backup_utils.BackupManager,
        path: Path,
        prev_backup: Path | None = None,
    ) -> None:
        """Create a backup of the sqlite database and disk-objectstore to the provided path.

        :param manager: BackupManager from backup_utils containing utilities such as for calling the rsync.
        :param path: Path to where the backup will be created.
        :param prev_backup: Path to the previous backup. Rsync calls will be hard-linked to this path, making the backup
            incremental and efficient.
        """
        LOGGER.report('Running storage maintenance')
        self.maintain(full=False, compress=False)

        LOGGER.report('Backing up disk-objectstore container')
        manager.call_rsync(self.filepath_container, path, link_dest=prev_backup, dest_trailing_slash=True)

        LOGGER.report('Backing up sqlite database')
        manager.call_rsync(self.filepath_database, path, link_dest=prev_backup, dest_trailing_slash=True)
