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

from functools import cached_property
from pathlib import Path
from shutil import rmtree
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from disk_objectstore import Container
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import insert
from sqlalchemy.orm import scoped_session, sessionmaker

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
    from aiida.repository.backend import DiskObjectStoreRepositoryBackend

__all__ = ('SqliteDosStorage',)

LOGGER = AIIDA_LOGGER.getChild(__file__)


class SqliteDosMigrator(PsqlDosMigrator):
    """Storage implementation using Sqlite database and disk-objectstore container.

    This storage backend is not recommended for use in production. The sqlite database is not the most performant and it
    does not support all the ``QueryBuilder`` functionality that is supported by the ``core.psql_dos`` storage backend.
    This storage is ideally suited for use cases that want to test or demo AiiDA as it requires no server but just a
    folder on the local filesystem.
    """

    def __init__(self, profile: Profile) -> None:
        filepath_database = Path(profile.storage_config['filepath']) / 'database.sqlite'
        filepath_database.touch()

        self.profile = profile
        self._engine = create_sqla_engine(filepath_database)
        self._connection = None

    def get_container(self) -> Container:
        """Return the disk-object store container.

        :returns: The disk-object store container configured for the repository path of the current profile.
        """
        filepath_container = Path(self.profile.storage_config['filepath']) / 'container'
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
    """A lightweight backend intended for demos and testing.

    This backend implementation uses an Sqlite database and
    """

    migrator = SqliteDosMigrator

    class Model(BaseModel):
        """Model describing required information to configure an instance of the storage."""

        filepath: str = Field(
            title='Directory of the backend',
            description='Filepath of the directory in which to store data for this backend.',
            default_factory=lambda: AIIDA_CONFIG_FOLDER / 'repository' / f'sqlite_dos_{uuid4().hex}',
        )

        @field_validator('filepath')
        @classmethod
        def filepath_is_absolute(cls, value: str) -> str:
            """Return the resolved and absolute filepath."""
            return str(Path(value).resolve().absolute())

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
        return f'SqliteDosStorage[{self._profile.storage_config["filepath"]}]: {state},'

    def _initialise_session(self):
        """Initialise the SQLAlchemy session factory.

        Only one session factory is ever associated with a given class instance,
        i.e. once the instance is closed, it cannot be reopened.

        The session factory, returns a session that is bound to the current thread.
        Multi-thread support is currently required by the REST API.
        Although, in the future, we may want to move the multi-thread handling to higher in the AiiDA stack.
        """
        engine = create_sqla_engine(Path(self._profile.storage_config['filepath']) / 'database.sqlite')
        self._session_factory = scoped_session(sessionmaker(bind=engine, future=True, expire_on_commit=True))

    def is_backup_implemented(self):
        return False

    def _backup_backend(
        self,
        dest: str,
        keep: Optional[int] = None,
    ):
        raise NotImplementedError

    def delete(self) -> None:  # type: ignore[override]
        """Delete the storage and all the data."""
        filepath = Path(self.profile.storage_config['filepath'])
        if filepath.exists():
            rmtree(filepath)
            LOGGER.report(f'Deleted storage directory at `{filepath}`.')

    def get_repository(self) -> 'DiskObjectStoreRepositoryBackend':
        from aiida.repository.backend import DiskObjectStoreRepositoryBackend

        container = Container(str(Path(self.profile.storage_config['filepath']) / 'container'))
        return DiskObjectStoreRepositoryBackend(container=container)

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
