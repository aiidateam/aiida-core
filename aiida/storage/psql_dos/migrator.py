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
import contextlib
import os
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


class PsqlDostoreMigrator:
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

            # check that we can access the disk-objectstore container, and get its id
            filepath = pathlib.Path(self.profile.repository_path) / 'container'
            container = Container(filepath)
            try:
                container_id = container.container_id
            except Exception as exc:
                raise exceptions.UnreachableStorage(f'Could not access disk-objectstore {filepath}: {exc}') from exc

            # finally, we check that the ID set within the disk-objectstore is equal to the one saved in the database,
            # i.e. this container is indeed the one associated with the db
            stmt = select(DbSetting.val).where(DbSetting.key == REPOSITORY_UUID_KEY)
            repo_uuid = connection.execute(stmt).scalar_one_or_none()
            if repo_uuid is None:
                raise exceptions.CorruptStorage('The database has no repository UUID set.')
            if repo_uuid != container_id:
                raise exceptions.CorruptStorage(
                    f'The database has a repository UUID configured to {repo_uuid} '
                    f'but the disk-objectstore\'s is {container_id}.'
                )

    def initialise(self) -> None:
        """Generate the initial storage schema for this profile, from the ORM models."""
        from aiida.storage.psql_dos.backend import CONTAINER_DEFAULTS
        from aiida.storage.psql_dos.models.base import get_orm_metadata

        # setup the database
        # see: https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
        get_orm_metadata().create_all(create_sqlalchemy_engine(self.profile.storage_config))

        # setup the repository
        filepath = pathlib.Path(self.profile.repository_path) / 'container'
        container = Container(filepath)
        container.init_container(clear=True, **CONTAINER_DEFAULTS)

        with create_sqlalchemy_engine(self.profile.storage_config).begin() as conn:
            # Create a "sync" between the database and repository, by saving its UUID in the settings table
            # this allows us to validate inconsistencies between the two
            conn.execute(
                insert(DbSetting
                       ).values(key=REPOSITORY_UUID_KEY, val=container.container_id, description='Repository UUID')
            )

            # finally, generate the version table, "stamping" it with the most recent revision
            with self._migration_context(conn) as context:
                context.stamp(context.script, 'main@head')

    def migrate(self) -> None:
        """Migrate the storage for this profile to the head version.

        :raises: :class:`~aiida.common.exceptions.UnreachableStorage` if the storage cannot be accessed
        """
        # the database can be in one of a few states:
        # 1. Completely empty -> we can simply initialise it with the current ORM schema
        # 2. Legacy django database -> we transfer the version to alembic, migrate to the head of the django branch,
        #    reset the revision as one on the main branch, and then migrate to the head of the main branch
        # 3. Legacy sqlalchemy database -> we migrate to the head of the sqlalchemy branch,
        #    reset the revision as one on the main branch, and then migrate to the head of the main branch
        # 4. Already on the main branch -> we migrate to the head of the main branch

        with self._connection_context() as connection:
            if not inspect(connection).has_table(self.alembic_version_tbl_name):
                if not inspect(connection).has_table(self.django_version_table.name):
                    # the database is assumed to be empty, so we need to initialise it
                    MIGRATE_LOGGER.report('initialising empty storage schema')
                    self.initialise()
                    return
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
        dir_path = os.path.dirname(os.path.realpath(__file__))
        config = Config()
        config.set_main_option('script_location', os.path.join(dir_path, ALEMBIC_REL_PATH))
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
