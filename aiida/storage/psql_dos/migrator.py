# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Schema validation and migration utilities.

This code interacts directly with the database, outside of the ORM,
taking a `Profile` as input for the connection configuration.

.. important:: This code should only be accessed via the storage backend class, not directly!
"""
from __future__ import annotations

import contextlib
import pathlib
from typing import ContextManager, Dict, Iterator, Optional

from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext, MigrationInfo
from alembic.script import ScriptDirectory
from disk_objectstore import Container
from sqlalchemy import String, Table, column, desc, insert, inspect, select, table
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.future.engine import Connection
from sqlalchemy.orm import Session

from aiida.common import exceptions
from aiida.manage.configuration.profile import Profile
from aiida.storage.log import MIGRATE_LOGGER
from aiida.storage.psql_dos.models.settings import DbSetting
from aiida.storage.psql_dos.utils import create_sqlalchemy_engine

TEMPLATE_LEGACY_DJANGO_SCHEMA = """
Database schema is using the legacy Django schema.
To migrate the database schema version to the current one, run the following command:

    verdi -p {profile_name} storage migrate
"""

TEMPLATE_INVALID_SCHEMA_VERSION = """
Database schema version `{schema_version_database}` is incompatible with the required schema version `{schema_version_code}`.
To migrate the database schema version to the current one, run the following command:

    verdi -p {profile_name} storage migrate
"""

ALEMBIC_REL_PATH = 'migrations'

REPOSITORY_UUID_KEY = 'repository|uuid'


class PsqlDosMigrator:
    """Class for validating and migrating `psql_dos` storage instances.

    .. important:: This class should only be accessed via the storage backend class (apart from for test purposes)
    """

    alembic_version_tbl_name = 'alembic_version'
    django_version_table = table(
        'django_migrations', column('id'), column('app', String(255)), column('name', String(255)), column('applied')
    )

    def __init__(self, profile: Profile) -> None:
        self.profile = profile

    @classmethod
    def get_schema_versions(cls) -> Dict[str, str]:
        """Return all available schema versions (oldest to latest).

        :return: schema version -> description
        """
        return {entry.revision: entry.doc for entry in reversed(list(cls._alembic_script().walk_revisions()))}

    @classmethod
    def get_schema_version_head(cls) -> str:
        """Return the head schema version for this storage, i.e. the latest schema this storage can be migrated to."""
        return cls._alembic_script().revision_map.get_current_head('main')

    def _connection_context(self, connection: Optional[Connection] = None) -> ContextManager[Connection]:
        """Return a context manager, with a connection to the database.

        :raises: `UnreachableStorage` if the database connection fails
        """
        if connection is not None:
            return contextlib.nullcontext(connection)
        try:
            return create_sqlalchemy_engine(self.profile.storage_config).connect()
        except OperationalError as exception:
            raise exceptions.UnreachableStorage(f'Could not connect to database: {exception}') from exception

    def get_schema_version_profile(self, _connection: Optional[Connection] = None, check_legacy=False) -> Optional[str]:
        """Return the schema version of the backend instance for this profile.

        Note, the version will be None if the database is empty or is a legacy django database.
        """
        with self._migration_context(_connection) as context:
            version = context.get_current_revision()
        if version is None and check_legacy:
            with self._connection_context(_connection) as connection:
                stmt = select(self.django_version_table.c.name).where(self.django_version_table.c.app == 'db')
                stmt = stmt.order_by(desc(self.django_version_table.c.id)).limit(1)
                try:
                    return connection.execute(stmt).scalar()
                except (OperationalError, ProgrammingError):
                    connection.rollback()
        return version

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
        with self._connection_context() as connection:

            # check there is an alembic_version table from which to get the schema version
            if not inspect(connection).has_table(self.alembic_version_tbl_name):
                # if not present, it might be that this is a legacy django database
                if inspect(connection).has_table(self.django_version_table.name):
                    raise exceptions.IncompatibleStorageSchema(
                        TEMPLATE_LEGACY_DJANGO_SCHEMA.format(profile_name=self.profile.name)
                    )
                raise exceptions.IncompatibleStorageSchema('The database has no known version.')

            # now we can check that the alembic version is the latest
            schema_version_code = self.get_schema_version_head()
            schema_version_database = self.get_schema_version_profile(connection, check_legacy=False)
            if schema_version_database != schema_version_code:
                raise exceptions.IncompatibleStorageSchema(
                    TEMPLATE_INVALID_SCHEMA_VERSION.format(
                        schema_version_database=schema_version_database,
                        schema_version_code=schema_version_code,
                        profile_name=self.profile.name
                    )
                )

            # finally, we check that the ID set within the disk-objectstore is equal to the one saved in the database,
            # i.e. this container is indeed the one associated with the db
            repository_uuid = self.get_repository_uuid()
            stmt = select(DbSetting.val).where(DbSetting.key == REPOSITORY_UUID_KEY)
            database_repository_uuid = connection.execute(stmt).scalar_one_or_none()
            if database_repository_uuid is None:
                raise exceptions.CorruptStorage('The database has no repository UUID set.')
            if database_repository_uuid != repository_uuid:
                raise exceptions.CorruptStorage(
                    f'The database has a repository UUID configured to {database_repository_uuid} '
                    f'but the disk-objectstore\'s is {repository_uuid}.'
                )

    def get_container(self) -> Container:
        """Return the disk-object store container.

        :returns: The disk-object store container configured for the repository path of the current profile.
        """
        from .backend import get_filepath_container
        return Container(get_filepath_container(self.profile))

    def get_repository_uuid(self) -> str:
        """Return the UUID of the repository.

        :returns: The repository UUID.
        :raises: :class:`~aiida.common.exceptions.UnreachableStorage` if the UUID cannot be retrieved, which probably
            means that the repository is not initialised.
        """
        try:
            return self.get_container().container_id
        except Exception as exception:
            raise exceptions.UnreachableStorage(
                f'Could not access disk-objectstore {self.get_container()}: {exception}'
            ) from exception

    def initialise(self, reset: bool = False) -> bool:
        """Initialise the storage backend.

        This is typically used once when a new storage backed is created. If this method returns without exceptions the
        storage backend is ready for use. If the backend already seems initialised, this method is a no-op.

        :param reset: If ``true``, destroy the backend if it already exists including all of its data before recreating
            and initialising it. This is useful for example for test profiles that need to be reset before or after
            tests having run.
        :returns: ``True`` if the storage was initialised by the function call, ``False`` if it was already initialised.
        """
        if reset:
            self.reset_repository()
            self.reset_database()

        initialised: bool = False

        if not self.is_initialised:
            self.initialise_repository()
            self.initialise_database()
            initialised = True

        # Call migrate in the case the storage was already initialised but not yet at the latest schema version. If it
        # was, then the following is a no-op anyway.
        self.migrate()

        return initialised

    @property
    def is_initialised(self) -> bool:
        """Return whether the storage is initialised.

        This is the case if both the database and the repository are initialised.

        :returns: ``True`` if the storage is initialised, ``False`` otherwise.
        """
        return self.is_repository_initialised and self.is_database_initialised

    @property
    def is_repository_initialised(self) -> bool:
        """Return whether the repository is initialised.

        :returns: ``True`` if the repository is initialised, ``False`` otherwise.
        """
        return self.get_container().is_initialised

    @property
    def is_database_initialised(self) -> bool:
        """Return whether the database is initialised.

        This is the case if it contains the table that holds the schema version for alembic or Django.

        :returns: ``True`` if the database is initialised, ``False`` otherwise.
        """
        with self._connection_context() as connection:
            return (
                inspect(connection).has_table(self.alembic_version_tbl_name) or
                inspect(connection).has_table(self.django_version_table.name)
            )

    def reset_repository(self) -> None:
        """Reset the repository by deleting all of its contents.

        This will also destroy the configuration and so in order to use it again, it will have to be reinitialised.
        """
        import shutil
        try:
            shutil.rmtree(self.get_container().get_folder())
        except FileNotFoundError:
            pass

    def reset_database(self) -> None:
        """Reset the database by deleting all content from all tables.

        This will also destroy the settings table and so in order to use it again, it will have to be reinitialised.
        """
        with self._connection_context() as connection:
            if inspect(connection).has_table(self.alembic_version_tbl_name):
                for table_name in (
                    'db_dbgroup_dbnodes', 'db_dbgroup', 'db_dblink', 'db_dbnode', 'db_dblog', 'db_dbauthinfo',
                    'db_dbuser', 'db_dbcomputer', 'db_dbsetting'
                ):
                    connection.execute(table(table_name).delete())
                connection.commit()

    def initialise_repository(self) -> None:
        """Initialise the repository."""
        from aiida.storage.psql_dos.backend import CONTAINER_DEFAULTS
        container = self.get_container()
        container.init_container(clear=True, **CONTAINER_DEFAULTS)

    def initialise_database(self) -> None:
        """Initialise the database.

        This assumes that the database has no schema whatsoever and so the initial schema is created directly from the
        models at the current head version without migrating through all of them one by one.
        """
        from aiida.storage.psql_dos.models.base import get_orm_metadata

        # setup the database
        # see: https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
        MIGRATE_LOGGER.report('initialising empty storage schema')
        get_orm_metadata().create_all(create_sqlalchemy_engine(self.profile.storage_config))

        repository_uuid = self.get_repository_uuid()

        with create_sqlalchemy_engine(self.profile.storage_config).begin() as conn:
            # Create a "sync" between the database and repository, by saving its UUID in the settings table
            # this allows us to validate inconsistencies between the two
            conn.execute(
                insert(DbSetting).values(key=REPOSITORY_UUID_KEY, val=repository_uuid, description='Repository UUID')
            )

            # finally, generate the version table, "stamping" it with the most recent revision
            with self._migration_context(conn) as context:
                context.stamp(context.script, 'main@head')

    def migrate(self) -> None:
        """Migrate the storage for this profile to the head version.

        :raises: :class:`~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed.
        :raises: :class:`~aiida.common.exceptions.StorageMigrationError` if the storage is not initialised.
        """
        # The database can be in one of a few states:
        # 1. Legacy django database -> we transfer the version to alembic, migrate to the head of the django branch,
        #    reset the revision as one on the main branch, and then migrate to the head of the main branch
        # 2. Legacy sqlalchemy database -> we migrate to the head of the sqlalchemy branch,
        #    reset the revision as one on the main branch, and then migrate to the head of the main branch
        # 3. Already on the main branch -> we migrate to the head of the main branch

        with self._connection_context() as connection:
            if not inspect(connection).has_table(self.alembic_version_tbl_name):
                if not inspect(connection).has_table(self.django_version_table.name):
                    raise exceptions.StorageMigrationError('storage is uninitialised, cannot migrate.')
                # the database is a legacy django one,
                # so we need to copy the version from the 'django_migrations' table to the 'alembic_version' one
                legacy_version = self.get_schema_version_profile(connection, check_legacy=True)
                if legacy_version is None:
                    raise exceptions.StorageMigrationError(
                        'No schema version could be read from the database. '
                        "Check that either the 'alembic_version' or 'django_migrations' tables "
                        'are present and accessible, using e.g. `verdi devel run-sql "SELECT * FROM alembic_version"`'
                    )
                # the version should be of the format '00XX_description'
                version = f'django_{legacy_version[:4]}'
                with self._migration_context(connection) as context:
                    context.stamp(context.script, version)
                connection.commit()
                # now we can continue with the migration as normal
            else:
                version = self.get_schema_version_profile(connection)

        # find what branch the current version is on
        branches = self._alembic_script().revision_map.get_revision(version).branch_labels

        if 'django' in branches or 'sqlalchemy' in branches:
            # migrate up to the top of the respective legacy branches
            if 'django' in branches:
                MIGRATE_LOGGER.report('Migrating to the head of the legacy django branch')
                self.migrate_up('django@head')
            elif 'sqlalchemy' in branches:
                MIGRATE_LOGGER.report('Migrating to the head of the legacy sqlalchemy branch')
                self.migrate_up('sqlalchemy@head')
            # now re-stamp with the comparable revision on the main branch
            with self._connection_context() as connection:
                with self._migration_context(connection) as context:
                    context._ensure_version_table(purge=True)  # pylint: disable=protected-access
                    context.stamp(context.script, 'main_0001')
                connection.commit()

        # finally migrate to the main head revision
        MIGRATE_LOGGER.report('Migrating to the head of the main branch')
        self.migrate_up('main@head')

    def migrate_up(self, version: str) -> None:
        """Migrate the database up to a specific version.

        :param version: string with schema version to migrate to
        """
        with self._alembic_connect() as config:
            upgrade(config, version)

    def migrate_down(self, version: str) -> None:
        """Migrate the database down to a specific version.

        :param version: string with schema version to migrate to
        """
        with self._alembic_connect() as config:
            downgrade(config, version)

    @staticmethod
    def _alembic_config():
        """Return an instance of an Alembic `Config`."""
        dirpath = pathlib.Path(__file__).resolve().parent
        config = Config()
        config.set_main_option('script_location', str(dirpath / ALEMBIC_REL_PATH))
        return config

    @classmethod
    def _alembic_script(cls):
        """Return an instance of an Alembic `ScriptDirectory`."""
        return ScriptDirectory.from_config(cls._alembic_config())

    @contextlib.contextmanager
    def _alembic_connect(self, _connection: Optional[Connection] = None) -> Iterator[Config]:
        """Context manager to return an instance of an Alembic configuration.

        The profiles's database connection is added in the `attributes` property, through which it can then also be
        retrieved, also in the `env.py` file, which is run when the database is migrated.
        """
        with self._connection_context(_connection) as connection:
            config = self._alembic_config()
            config.attributes['connection'] = connection  # pylint: disable=unsupported-assignment-operation
            config.attributes['aiida_profile'] = self.profile  # pylint: disable=unsupported-assignment-operation

            def _callback(step: MigrationInfo, **kwargs):  # pylint: disable=unused-argument
                """Callback to be called after a migration step is executed."""
                from_rev = step.down_revision_ids[0] if step.down_revision_ids else '<base>'
                MIGRATE_LOGGER.report(f'- {from_rev} -> {step.up_revision_id}')

            config.attributes['on_version_apply'] = _callback  # pylint: disable=unsupported-assignment-operation

            yield config

    @contextlib.contextmanager
    def _migration_context(self, _connection: Optional[Connection] = None) -> Iterator[MigrationContext]:
        """Context manager to return an instance of an Alembic migration context.

        This migration context will have been configured with the current database connection, which allows this context
        to be used to inspect the contents of the database, such as the current revision.
        """
        with self._alembic_connect(_connection) as config:
            script = ScriptDirectory.from_config(config)
            with EnvironmentContext(config, script) as context:
                context.configure(context.config.attributes['connection'])
                yield context.get_context()

    # the following are used for migration tests

    @contextlib.contextmanager
    def session(self) -> Iterator[Session]:
        """Context manager to return a session for the database."""
        with self._connection_context() as connection:
            session = Session(connection.engine, future=True)
            try:
                yield session
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    def get_current_table(self, table_name: str) -> Table:
        """Return a table instantiated at the correct migration.

        Note that this is obtained by inspecting the database and not by looking into the models file.
        So, special methods possibly defined in the models files/classes are not present.
        """
        with self._connection_context() as connection:
            base = automap_base()
            base.prepare(autoload_with=connection.engine)
            return getattr(base.classes, table_name)
