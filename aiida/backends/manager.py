# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for settings and utilities to determine and set the database schema versions."""

import abc
import collections

from aiida.common import exceptions

SCHEMA_VERSION_KEY = 'db|schemaversion'
SCHEMA_VERSION_DESCRIPTION = 'Database schema version'

SCHEMA_GENERATION_KEY = 'schema_generation'  # The key to store the database schema generation in the settings table
SCHEMA_GENERATION_DESCRIPTION = 'Database schema generation'
SCHEMA_GENERATION_VALUE = '1'  # The current schema generation

# Mapping of schema generation onto a tuple of valid schema reset generation and `aiida-core` version number. Given the
# current code schema generation as the key, the first element of the tuple tells what schema generation the database
# should have to be able to reset the schema. If the generation of the database is correct, but the schema version of
# the database does not match the one required for the reset, it means the user first has to downgrade the `aiida-core`
# version and perform the latest migrations. The required version is provided by the tuples second element.
SCHEMA_GENERATION_RESET = {
    '1': ('1', '1.*'),
}

TEMPLATE_INVALID_SCHEMA_GENERATION = """
Database schema generation `{schema_generation_database}` is incompatible with the required schema generation `{schema_generation_code}`.
To migrate the database schema generation to the current one, run the following command:

    verdi -p {profile_name} database migrate
"""

TEMPLATE_INVALID_SCHEMA_VERSION = """
Database schema version `{schema_version_database}` is incompatible with the required schema version `{schema_version_code}`.
To migrate the database schema version to the current one, run the following command:

    verdi -p {profile_name} database migrate
"""

TEMPLATE_MIGRATE_SCHEMA_VERSION_INVALID_VERSION = """
Cannot migrate the database version from `{schema_version_database}` to `{schema_version_code}`.
The database version is ahead of the version of the code and downgrades of the database are not supported.
"""

TEMPLATE_MIGRATE_SCHEMA_GENERATION_INVALID_GENERATION = """
Cannot migrate database schema generation from `{schema_generation_database}` to `{schema_generation_code}`.
This version of `aiida-core` can only migrate databases with schema generation `{schema_generation_reset}`
"""

TEMPLATE_MIGRATE_SCHEMA_GENERATION_INVALID_VERSION = """
Cannot migrate database schema generation from `{schema_generation_database}` to `{schema_generation_code}`.
The current database version is `{schema_version_database}` but `{schema_version_reset}` is required for generation migration.
First install `aiida-core~={aiida_core_version_reset}` and migrate the database to the latest version.
After the database schema is migrated to version `{schema_version_reset}` you can reinstall this version of `aiida-core` and migrate the schema generation.
"""

Setting = collections.namedtuple('Setting', ['key', 'value', 'description', 'time'])


class SettingsManager:
    """Class to get, set and delete settings from the `DbSettings` table."""

    @abc.abstractmethod
    def get(self, key):
        """Return the setting with the given key.

        :param key: the key identifying the setting
        :return: Setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """

    @abc.abstractmethod
    def set(self, key, value, description=None):
        """Return the settings with the given key.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """

    @abc.abstractmethod
    def delete(self, key):
        """Delete the setting with the given key.

        :param key: the key identifying the setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """


class BackendManager:
    """Class to manage the database schema and environment."""

    _settings_manager = None

    @abc.abstractmethod
    def get_settings_manager(self):
        """Return an instance of the `SettingsManager`.

        :return: `SettingsManager`
        """

    def load_backend_environment(self, profile, validate_schema=True):
        """Load the backend environment.

        :param profile: the profile whose backend environment to load
        :param validate_schema: boolean, if True, validate the schema first before loading the environment.
        """
        self._load_backend_environment()

        if validate_schema:
            self.validate_schema(profile)

    @abc.abstractmethod
    def _load_backend_environment(self):
        """Load the backend environment."""

    @abc.abstractmethod
    def reset_backend_environment(self):
        """Reset the backend environment."""

    def migrate(self):
        """Migrate the database to the latest schema generation or version."""
        try:
            # If the settings table does not exist, we are dealing with an empty database. We cannot perform the checks
            # because they rely on the settings table existing, so instead we do not validate but directly call method
            # `_migrate_database_version` which will perform the migration to create the initial schema.
            self.get_settings_manager().validate_table_existence()
        except exceptions.NotExistent:
            self._migrate_database_version()
            return

        if SCHEMA_GENERATION_VALUE != self.get_schema_generation_database():
            self.validate_schema_generation_for_migration()
            self._migrate_database_generation()

        if self.get_schema_version_code() != self.get_schema_version_database():
            self.validate_schema_version_for_migration()
            self._migrate_database_version()

    def _migrate_database_generation(self):
        """Migrate the database schema generation.

        .. warning:: this should NEVER be called directly because there is no validation performed on whether the
            current database schema generation and version can actually be migrated.

        This normally just consists out of setting the schema generation value, but depending on the backend more might
        be needed. In that case, this method should be overridden and call `super` first, followed by the additional
        logic that is required.
        """
        self.set_schema_generation_database(SCHEMA_GENERATION_VALUE)
        self.set_schema_version_database(self.get_schema_version_code())

    def _migrate_database_version(self):
        """Migrate the database to the current schema version.

        .. warning:: this should NEVER be called directly because there is no validation performed on whether the
            current database schema generation and version can actually be migrated.
        """

    @abc.abstractmethod
    def is_database_schema_ahead(self):
        """Determine whether the database schema version is ahead of the code schema version.

        .. warning:: this will not check whether the schema generations are equal

        :return: boolean, True if the database schema version is ahead of the code schema version.
        """

    @abc.abstractmethod
    def get_schema_version_code(self):
        """Return the code schema version."""

    @abc.abstractmethod
    def get_schema_version_reset(self, schema_generation_code):
        """Return schema version the database should have to be able to automatically reset to code schema generation.

        :param schema_generation_code: the schema generation of the code.
        :return: schema version
        """

    @abc.abstractmethod
    def get_schema_version_database(self):
        """Return the database schema version.

        :return: `distutils.version.LooseVersion` with schema version of the database
        """

    @abc.abstractmethod
    def set_schema_version_database(self, version):
        """Set the database schema version.

        :param version: string with schema version to set
        """

    def get_schema_generation_database(self):
        """Return the database schema generation.

        :return: `distutils.version.LooseVersion` with schema generation of the database
        """
        try:
            setting = self.get_settings_manager().get(SCHEMA_GENERATION_KEY)
            return setting.value
        except exceptions.NotExistent:
            return '1'

    def set_schema_generation_database(self, generation):
        """Set the database schema generation.

        :param generation: string with schema generation to set
        """
        self.get_settings_manager().set(SCHEMA_GENERATION_KEY, generation)

    def validate_schema(self, profile):
        """Validate that the current database generation and schema are up-to-date with that of the code.

        :param profile: the profile for which to validate the database schema
        :raises `aiida.common.exceptions.ConfigurationError`: if database schema version or generation is not up-to-date
        """
        self.validate_schema_generation(profile)
        self.validate_schema_version(profile)

    def validate_schema_generation_for_migration(self):
        """Validate whether the current database schema generation can be migrated.

        :raises `aiida.common.exceptions.IncompatibleDatabaseSchema`: if database schema generation cannot be migrated
        """
        schema_generation_code = SCHEMA_GENERATION_VALUE
        schema_generation_database = self.get_schema_generation_database()
        schema_version_database = self.get_schema_version_database()
        schema_version_reset = self.get_schema_version_reset(schema_generation_code)
        schema_generation_reset, aiida_core_version_reset = SCHEMA_GENERATION_RESET[schema_generation_code]

        if schema_generation_database != schema_generation_reset:
            raise exceptions.IncompatibleDatabaseSchema(
                TEMPLATE_MIGRATE_SCHEMA_GENERATION_INVALID_GENERATION.format(
                    schema_generation_database=schema_generation_database,
                    schema_generation_code=schema_generation_code,
                    schema_generation_reset=schema_generation_reset
                )
            )

        if schema_version_database != schema_version_reset:
            raise exceptions.IncompatibleDatabaseSchema(
                TEMPLATE_MIGRATE_SCHEMA_GENERATION_INVALID_VERSION.format(
                    schema_generation_database=schema_generation_database,
                    schema_generation_code=schema_generation_code,
                    schema_version_database=schema_version_database,
                    schema_version_reset=schema_version_reset,
                    aiida_core_version_reset=aiida_core_version_reset
                )
            )

    def validate_schema_version_for_migration(self):
        """Validate whether the current database schema version can be migrated.

        .. warning:: this will not validate that the schema generation is correct.

        :raises `aiida.common.exceptions.IncompatibleDatabaseSchema`: if database schema version cannot be migrated
        """
        schema_version_code = self.get_schema_version_code()
        schema_version_database = self.get_schema_version_database()

        if self.is_database_schema_ahead():
            # Database is newer than the code so a downgrade would be necessary but this is not supported.
            raise exceptions.IncompatibleDatabaseSchema(
                TEMPLATE_MIGRATE_SCHEMA_VERSION_INVALID_VERSION.format(
                    schema_version_database=schema_version_database,
                    schema_version_code=schema_version_code,
                )
            )

    def validate_schema_generation(self, profile):
        """Validate that the current database schema generation is up-to-date with that of the code.

        :raises `aiida.common.exceptions.IncompatibleDatabaseSchema`: if database schema generation is not up-to-date
        """
        schema_generation_code = SCHEMA_GENERATION_VALUE
        schema_generation_database = self.get_schema_generation_database()

        if schema_generation_database != schema_generation_code:
            raise exceptions.IncompatibleDatabaseSchema(
                TEMPLATE_INVALID_SCHEMA_GENERATION.format(
                    schema_generation_database=schema_generation_database,
                    schema_generation_code=schema_generation_code,
                    profile_name=profile.name,
                )
            )

    def validate_schema_version(self, profile):
        """Validate that the current database schema version is up-to-date with that of the code.

        :param profile: the profile for which to validate the database schema
        :raises `aiida.common.exceptions.IncompatibleDatabaseSchema`: if database schema version is not up-to-date
        """
        schema_version_code = self.get_schema_version_code()
        schema_version_database = self.get_schema_version_database()

        if schema_version_database != schema_version_code:
            raise exceptions.IncompatibleDatabaseSchema(
                TEMPLATE_INVALID_SCHEMA_VERSION.format(
                    schema_version_database=schema_version_database,
                    schema_version_code=schema_version_code,
                    profile_name=profile.name
                )
            )
