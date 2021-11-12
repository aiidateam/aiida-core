# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities and configuration of the SqlAlchemy database schema."""
import contextlib
import os

from alembic.command import downgrade, upgrade
import sqlalchemy
from sqlalchemy.orm.exc import NoResultFound

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.common import NotExistent

from ..manager import SCHEMA_GENERATION_VALUE, BackendManager, Setting, SettingsManager

ALEMBIC_REL_PATH = 'migrations'

# The database schema version required to perform schema reset for a given code schema generation
SCHEMA_VERSION_RESET = {'1': None}


class SqlaBackendManager(BackendManager):
    """Class to manage the database schema."""

    @staticmethod
    @contextlib.contextmanager
    def alembic_config():
        """Context manager to return an instance of an Alembic configuration.

        The current database connection is added in the `attributes` property, through which it can then also be
        retrieved, also in the `env.py` file, which is run when the database is migrated.
        """
        from alembic.config import Config

        from . import ENGINE

        with ENGINE.begin() as connection:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config = Config()
            config.set_main_option('script_location', os.path.join(dir_path, ALEMBIC_REL_PATH))
            config.attributes['connection'] = connection  # pylint: disable=unsupported-assignment-operation
            yield config

    @contextlib.contextmanager
    def alembic_script(self):
        """Context manager to return an instance of an Alembic `ScriptDirectory`."""
        from alembic.script import ScriptDirectory

        with self.alembic_config() as config:
            yield ScriptDirectory.from_config(config)

    @contextlib.contextmanager
    def migration_context(self):
        """Context manager to return an instance of an Alembic migration context.

        This migration context will have been configured with the current database connection, which allows this context
        to be used to inspect the contents of the database, such as the current revision.
        """
        from alembic.runtime.environment import EnvironmentContext
        from alembic.script import ScriptDirectory

        with self.alembic_config() as config:
            script = ScriptDirectory.from_config(config)
            with EnvironmentContext(config, script) as context:
                context.configure(context.config.attributes['connection'])
                yield context.get_context()

    def get_settings_manager(self):
        """Return an instance of the `SettingsManager`.

        :return: `SettingsManager`
        """
        if self._settings_manager is None:
            self._settings_manager = SqlaSettingsManager()

        return self._settings_manager

    def _load_backend_environment(self, **kwargs):
        """Load the backend environment.

        :param kwargs: keyword arguments that will be passed on to
            :py:func:`aiida.backends.sqlalchemy.get_scoped_session`.
        """
        get_scoped_session(**kwargs)

    def reset_backend_environment(self):
        """Reset the backend environment."""
        from . import reset_session
        reset_session()

    def list_schema_versions(self):
        """List all available schema versions (oldest to latest).

        :return: list of strings with schema versions
        """
        with self.alembic_script() as script:
            return list(reversed([entry.revision for entry in script.walk_revisions()]))

    def is_database_schema_ahead(self):
        """Determine whether the database schema version is ahead of the code schema version.

        .. warning:: this will not check whether the schema generations are equal

        :return: boolean, True if the database schema version is ahead of the code schema version.
        """
        with self.alembic_script() as script:
            return self.get_schema_version_backend() not in [entry.revision for entry in script.walk_revisions()]

    def get_schema_version_head(self):
        with self.alembic_script() as script:
            return script.get_current_head()

    def get_schema_version_reset(self, schema_generation_code):
        """Return schema version the database should have to be able to automatically reset to code schema generation.

        :param schema_generation_code: the schema generation of the code.
        :return: schema version
        """
        return SCHEMA_VERSION_RESET[schema_generation_code]

    def get_schema_version_backend(self):
        with self.migration_context() as context:
            return context.get_current_revision()

    def set_schema_version_backend(self, version: str) -> None:
        with self.migration_context() as context:
            return context.stamp(context.script, version)

    def _migrate_database_generation(self):
        self.set_schema_generation_database(SCHEMA_GENERATION_VALUE)
        self.set_schema_version_backend('head')

    def migrate_up(self, version: str):
        """Migrate the database up to a specific version.

        :param version: string with schema version to migrate to
        """
        with self.alembic_config() as config:
            upgrade(config, version)

    def migrate_down(self, version: str):
        """Migrate the database down to a specific version.

        :param version: string with schema version to migrate to
        """
        with self.alembic_config() as config:
            downgrade(config, version)

    def _migrate_database_version(self):
        """Migrate the database to the latest schema version."""
        super()._migrate_database_version()
        self.migrate_up('head')


class SqlaSettingsManager(SettingsManager):
    """Class to get, set and delete settings from the `DbSettings` table."""

    table_name = 'db_dbsetting'

    def validate_table_existence(self):
        """Verify that the `DbSetting` table actually exists.

        :raises: `~aiida.common.exceptions.NotExistent` if the settings table does not exist
        """
        inspector = sqlalchemy.inspect(get_scoped_session().bind)
        if self.table_name not in inspector.get_table_names():
            raise NotExistent('the settings table does not exist')

    def get(self, key):
        """Return the setting with the given key.

        :param key: the key identifying the setting
        :return: Setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        self.validate_table_existence()

        try:
            setting = get_scoped_session().query(DbSetting).filter_by(key=key).one()
        except NoResultFound:
            raise NotExistent(f'setting `{key}` does not exist') from NoResultFound

        return Setting(key, setting.getvalue(), setting.description, setting.time)

    def set(self, key, value, description=None):
        """Return the settings with the given key.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        from aiida.orm.implementation.utils import validate_attribute_extra_key

        self.validate_table_existence()
        validate_attribute_extra_key(key)

        other_attribs = {}
        if description is not None:
            other_attribs['description'] = description

        DbSetting.set_value(key, value, other_attribs=other_attribs)

    def delete(self, key):
        """Delete the setting with the given key.

        :param key: the key identifying the setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.sqlalchemy.models.settings import DbSetting
        self.validate_table_existence()

        try:
            setting = get_scoped_session().query(DbSetting).filter_by(key=key).one()
            setting.delete()
        except NoResultFound:
            raise NotExistent(f'setting `{key}` does not exist') from NoResultFound
