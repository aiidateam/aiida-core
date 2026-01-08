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

import contextlib
import pathlib
from functools import cached_property, lru_cache
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Generator, Optional
from uuid import uuid4

from alembic.config import Config
from disk_objectstore import Container, backup_utils
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import insert, inspect, select
from sqlalchemy.orm import scoped_session, sessionmaker

from aiida.common import exceptions
from aiida.common.log import AIIDA_LOGGER
from aiida.manage.configuration.profile import Profile
from aiida.manage.configuration.settings import AiiDAConfigDir
from aiida.orm.implementation import BackendEntity
from aiida.storage.log import MIGRATE_LOGGER
from aiida.storage.psql_dos.models.settings import DbSetting
from aiida.storage.sqlite_zip import models, orm
from aiida.storage.sqlite_zip.backend import validate_sqlite_version
from aiida.storage.sqlite_zip.utils import create_sqla_engine

from ..migrations import TEMPLATE_INVALID_SCHEMA_VERSION
from ..psql_dos import PsqlDosBackend
from ..psql_dos.migrator import PsqlDosMigrator

if TYPE_CHECKING:
    from disk_objectstore import Container

    from aiida.orm.entities import EntityTypes
    from aiida.repository.backend import DiskObjectStoreRepositoryBackend

__all__ = ('SqliteDosStorage',)

LOGGER = AIIDA_LOGGER.getChild(__file__)
FILENAME_DATABASE = 'database.sqlite'
FILENAME_CONTAINER = 'container'


ALEMBIC_REL_PATH = 'migrations'

REPOSITORY_UUID_KEY = 'repository|uuid'


class SqliteDosMigrator(PsqlDosMigrator):
    """Class for validating and migrating `sqlite_dos` storage instances.

    .. important:: This class should only be accessed via the storage backend class (apart from for test purposes)

    The class subclasses the ``PsqlDosMigrator``. It essentially changes two things in the implementation:

    * Changes the path to the migration version files. This allows custom migrations to be written for SQLite-based
      storage plugins, which is necessary since the PSQL-based migrations may use syntax that is not compatible.
    * The logic for validating the storage is significantly simplified since the SQLite-based storage plugins do not
      have to take legacy Django-based implementations into account.
    """

    alembic_version_tbl_name = 'alembic_version'

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

        # TODO for now we raise error later we deprecate with warinng
        class DeprecatedError(Exception):
            pass

        raise DeprecatedError(
            'Do not use `get_container` as it might leave resources open. Please use instead'
            '`with container_context() as container` since it ensures that resources are correctly freed.'
        )

    @contextlib.contextmanager
    def container_context(self) -> Generator['Container', None, None]:
        from disk_objectstore import Container

        filepath_container = Path(self.profile.storage_config['filepath']) / FILENAME_CONTAINER
        with Container(str(filepath_container)) as container:
            yield container

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

    def get_schema_version_profile(self) -> Optional[str]:  # type: ignore[override]
        """Return the schema version of the backend instance for this profile.

        Note, the version will be None if the database is empty or is a legacy django database.
        """
        with self._migration_context() as context:
            return context.get_current_revision()

    @staticmethod
    def _alembic_config():
        """Return an instance of an Alembic `Config`."""
        dirpath = pathlib.Path(__file__).resolve().parent
        config = Config()
        config.set_main_option('script_location', str(dirpath / ALEMBIC_REL_PATH))
        return config

    def validate_storage(self) -> None:
        """Validate that the storage for this profile

        1. That the database schema is at the head version, i.e. is compatible with the code API.
        2. That the repository ID is equal to the UUID set in the database

        :raises: :class:`aiida.common.exceptions.UnreachableStorage` if the storage cannot be connected to
        :raises: :class:`aiida.common.exceptions.IncompatibleStorageSchema`
            if the storage is not compatible with the code API.
        :raises: :class:`aiida.common.exceptions.CorruptStorage`
            if the repository ID is not equal to the UUID set in thedatabase.
        """
        # check there is an alembic_version table from which to get the schema version
        if not inspect(self.connection).has_table(self.alembic_version_tbl_name):
            raise exceptions.IncompatibleStorageSchema('The database has no known version.')

        # now we can check that the alembic version is the latest
        schema_version_code = self.get_schema_version_head()
        schema_version_database = self.get_schema_version_profile()
        if schema_version_database != schema_version_code:
            raise exceptions.IncompatibleStorageSchema(
                TEMPLATE_INVALID_SCHEMA_VERSION.format(
                    schema_version_database=schema_version_database,
                    schema_version_code=schema_version_code,
                    profile_name=self.profile.name,
                )
            )

        # finally, we check that the ID set within the disk-objectstore is equal to the one saved in the database,
        # i.e. this container is indeed the one associated with the db
        repository_uuid = self.get_repository_uuid()
        stmt = select(DbSetting.val).where(DbSetting.key == REPOSITORY_UUID_KEY)
        database_repository_uuid = self.connection.execute(stmt).scalar_one_or_none()
        if database_repository_uuid is None:
            raise exceptions.CorruptStorage('The database has no repository UUID set.')
        if database_repository_uuid != repository_uuid:
            raise exceptions.CorruptStorage(
                f'The database has a repository UUID configured to {database_repository_uuid} '
                f"but the disk-objectstore's is {repository_uuid}."
            )

    @property
    def is_database_initialised(self) -> bool:
        """Return whether the database is initialised.

        This is the case if it contains the table that holds the schema version for alembic.

        :returns: ``True`` if the database is initialised, ``False`` otherwise.
        """
        return inspect(self.connection).has_table(self.alembic_version_tbl_name)

    def migrate(self) -> None:
        """Migrate the storage for this profile to the head version.

        :raises: :class:`~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed.
        :raises: :class:`~aiida.common.exceptions.StorageMigrationError` if the storage is not initialised.
        """
        if not inspect(self.connection).has_table(self.alembic_version_tbl_name):
            raise exceptions.StorageMigrationError('storage is uninitialised, cannot migrate.')

        MIGRATE_LOGGER.report('Migrating to the head of the main branch')
        self.migrate_up('main@head')
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
            default_factory=lambda: str(AiiDAConfigDir.get() / 'repository' / f'sqlite_dos_{uuid4().hex}'),
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
        validate_sqlite_version()
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

    def __init__(self, profile: Profile) -> None:
        validate_sqlite_version()
        super().__init__(profile)

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
        # TODO for now we raise error later we deprecate with warinng
        class DeprecatedError(Exception):
            pass

        raise DeprecatedError(
            'Do not use `get_container` as it might leave resources open. Please use instead'
            '`with container_context() as container` since it ensures that resources are correctly freed.'
        )

    @contextlib.contextmanager
    def container_context(self) -> Generator['Container', None, None]:
        """Return the disk-object store container.
        :returns: The disk-object store container configured for the repository path of the current profile.
        """
        with Container(str(self.filepath_container)) as container:
            yield container

    def get_repository(self) -> 'DiskObjectStoreRepositoryBackend':
        from aiida.repository.backend import DiskObjectStoreRepositoryBackend

        with self.container_context() as container:
            return DiskObjectStoreRepositoryBackend(container=container)

    @classmethod
    def version_profile(cls, profile: Profile) -> Optional[str]:
        with cls.migrator_context(profile) as migrator:
            return migrator.get_schema_version_profile()

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
