# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=import-error,no-name-in-module
"""Utilities and configuration of the Django database schema."""

import os
import django

from aiida.common import NotExistent
from ..manager import BackendManager, SettingsManager, Setting, SCHEMA_VERSION_KEY, SCHEMA_VERSION_DESCRIPTION

# The database schema version required to perform schema reset for a given code schema generation
SCHEMA_VERSION_RESET = {'1': None}


class DjangoBackendManager(BackendManager):
    """Class to manage the database schema."""

    def get_settings_manager(self):
        """Return an instance of the `SettingsManager`.

        :return: `SettingsManager`
        """
        if self._settings_manager is None:
            self._settings_manager = DjangoSettingsManager()

        return self._settings_manager

    def _load_backend_environment(self, **kwargs):
        """Load the backend environment.

        The scoped session is needed for the QueryBuilder only.

        :param kwargs: keyword arguments that will be passed on to :py:func:`aiida.backends.djsite.get_scoped_session`.
        """
        os.environ['DJANGO_SETTINGS_MODULE'] = 'aiida.backends.djsite.settings'
        django.setup()  # pylint: disable=no-member

        # For QueryBuilder only
        from . import get_scoped_session
        get_scoped_session(**kwargs)

    def reset_backend_environment(self):
        """Reset the backend environment."""
        from . import reset_session
        reset_session()

    def is_database_schema_ahead(self):
        """Determine whether the database schema version is ahead of the code schema version.

        .. warning:: this will not check whether the schema generations are equal

        :return: boolean, True if the database schema version is ahead of the code schema version.
        """
        # For Django the versions numbers are numerical so we can compare them
        from distutils.version import StrictVersion
        return StrictVersion(self.get_schema_version_database()) > StrictVersion(self.get_schema_version_code())

    def get_schema_version_code(self):
        """Return the code schema version."""
        from .db.models import SCHEMA_VERSION
        return SCHEMA_VERSION

    def get_schema_version_reset(self, schema_generation_code):
        """Return schema version the database should have to be able to automatically reset to code schema generation.

        :param schema_generation_code: the schema generation of the code.
        :return: schema version
        """
        return SCHEMA_VERSION_RESET[schema_generation_code]

    def get_schema_generation_database(self):
        """Return the database schema version.

        :return: `distutils.version.StrictVersion` with schema version of the database
        """
        from django.db.utils import ProgrammingError
        from aiida.manage.manager import get_manager

        backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access

        try:
            result = backend.execute_raw(r"""SELECT tval FROM db_dbsetting WHERE key = 'schema_generation';""")
        except ProgrammingError:
            result = backend.execute_raw(r"""SELECT val FROM db_dbsetting WHERE key = 'schema_generation';""")

        try:
            return str(int(result[0][0]))
        except (IndexError, TypeError, ValueError):
            return '1'

    def get_schema_version_database(self):
        """Return the database schema version.

        :return: `distutils.version.StrictVersion` with schema version of the database
        """
        from django.db.utils import ProgrammingError
        from aiida.manage.manager import get_manager

        backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access

        try:
            result = backend.execute_raw(r"""SELECT tval FROM db_dbsetting WHERE key = 'db|schemaversion';""")
        except ProgrammingError:
            result = backend.execute_raw(r"""SELECT val FROM db_dbsetting WHERE key = 'db|schemaversion';""")
        return result[0][0]

    def set_schema_version_database(self, version):
        """Set the database schema version.

        :param version: string with schema version to set
        """
        return self.get_settings_manager().set(SCHEMA_VERSION_KEY, version, description=SCHEMA_VERSION_DESCRIPTION)

    def _migrate_database_generation(self):
        """Reset the database schema generation.

        For Django we also have to clear the `django_migrations` table that contains a history of all applied
        migrations. After clearing it, we reinsert the name of the new initial schema .
        """
        # pylint: disable=cyclic-import
        from aiida.manage.manager import get_manager
        super()._migrate_database_generation()

        backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access
        backend.execute_raw(r"""DELETE FROM django_migrations WHERE app = 'db';""")
        backend.execute_raw(
            r"""INSERT INTO django_migrations (app, name, applied) VALUES ('db', '0001_initial', NOW());"""
        )

    def _migrate_database_version(self):
        """Migrate the database to the current schema version."""
        super()._migrate_database_version()
        from django.core.management import call_command  # pylint: disable=no-name-in-module,import-error
        call_command('migrate')


class DjangoSettingsManager(SettingsManager):
    """Class to get, set and delete settings from the `DbSettings` table."""

    table_name = 'db_dbsetting'

    def validate_table_existence(self):
        """Verify that the `DbSetting` table actually exists.

        :raises: `~aiida.common.exceptions.NotExistent` if the settings table does not exist
        """
        from django.db import connection
        if self.table_name not in connection.introspection.table_names():
            raise NotExistent('the settings table does not exist')

    def get(self, key):
        """Return the setting with the given key.

        :param key: the key identifying the setting
        :return: Setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.djsite.db.models import DbSetting

        self.validate_table_existence()
        setting = DbSetting.objects.filter(key=key).first()

        if setting is None:
            raise NotExistent(f'setting `{key}` does not exist')

        return Setting(setting.key, setting.val, setting.description, setting.time)

    def set(self, key, value, description=None):
        """Return the settings with the given key.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """
        from aiida.backends.djsite.db.models import DbSetting
        from aiida.orm.implementation.utils import validate_attribute_extra_key

        self.validate_table_existence()
        validate_attribute_extra_key(key)

        other_attribs = dict()
        if description is not None:
            other_attribs['description'] = description

        DbSetting.set_value(key, value, other_attribs=other_attribs)

    def delete(self, key):
        """Delete the setting with the given key.

        :param key: the key identifying the setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        from aiida.backends.djsite.db.models import DbSetting

        self.validate_table_existence()

        try:
            DbSetting.del_value(key=key)
        except KeyError:
            raise NotExistent(f'setting `{key}` does not exist') from KeyError
