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
"""Utilities and configuration of the SqlAlchemy database schema."""

import os
import contextlib

from alembic import command
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory

from sqlalchemy.orm.exc import NoResultFound

from aiida.backends.sqlalchemy import get_scoped_session
from aiida.common import NotExistent
from ..manager import BackendManager, SettingsManager, Setting

ALEMBIC_FILENAME = 'alembic.ini'
ALEMBIC_REL_PATH = 'migrations'

# The database schema version required to perform schema reset for a given code schema generation
SCHEMA_VERSION_RESET = {'1': None}


class SqlaBackendManager(BackendManager):
    """Class to manage the database schema."""

    @staticmethod
    @contextlib.contextmanager
    def alembic_config():
        """Context manager to return an instance of an Alembic configuration with the current connection inserted.

        :return: instance of :py:class:`alembic.config.Config`
        """
        from . import ENGINE

        with ENGINE.begin() as connection:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            config = Config(os.path.join(dir_path, ALEMBIC_FILENAME))
            config.set_main_option('script_location', os.path.join(dir_path, ALEMBIC_REL_PATH))
            config.attributes['connection'] = connection  # pylint: disable=unsupported-assignment-operation
            yield config

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

    def is_database_schema_ahead(self):
        """Determine whether the database schema version is ahead of the code schema version.

        .. warning:: this will not check whether the schema generations are equal

        :return: boolean, True if the database schema version is ahead of the code schema version.
        """
        from alembic.util import CommandError

        # In the case of SqlAlchemy, if the database revision is ahead of the code, that means the revision stored in
        # the database is not even present in the code base. Therefore we cannot locate it in the revision graph and
        # determine whether it is ahead of the current code head. We simply try to get the revision and if it does not
        # exist it means it is ahead.
        with self.alembic_config() as config:
            try:
                script = ScriptDirectory.from_config(config)
                script.get_revision(self.get_schema_version_database())
            except CommandError:
                # Raised when the revision of the database is not present in the revision graph.
                return True
            else:
                return False

    def get_schema_version_code(self):
        """Return the code schema version."""
        with self.alembic_config() as config:
            script = ScriptDirectory.from_config(config)
            schema_version_code = script.get_current_head()

        return schema_version_code

    def get_schema_version_reset(self, schema_generation_code):
        """Return schema version the database should have to be able to automatically reset to code schema generation.

        :param schema_generation_code: the schema generation of the code.
        :return: schema version
        """
        return SCHEMA_VERSION_RESET[schema_generation_code]

    def get_schema_version_database(self):
        """Return the database schema version.

        :return: `distutils.version.StrictVersion` with schema version of the database
        """

        def get_database_version(revision, _):
            """Get the current revision."""
            if isinstance(revision, tuple) and revision:
                config.attributes['rev'] = revision[0]  # pylint: disable=unsupported-assignment-operation
            else:
                config.attributes['rev'] = None  # pylint: disable=unsupported-assignment-operation
            return []

        with self.alembic_config() as config:

            script = ScriptDirectory.from_config(config)

            with EnvironmentContext(config, script, fn=get_database_version):
                script.run_env()
                return config.attributes['rev']  # pylint: disable=unsubscriptable-object

    def set_schema_version_database(self, version):
        """Set the database schema version.

        :param version: string with schema version to set
        """
        # pylint: disable=cyclic-import
        from aiida.manage.manager import get_manager
        backend = get_manager()._load_backend(schema_check=False)  # pylint: disable=protected-access
        backend.execute_raw(r"""UPDATE alembic_version SET version_num='{}';""".format(version))

    def _migrate_database_version(self):
        """Migrate the database to the current schema version."""
        super()._migrate_database_version()
        with self.alembic_config() as config:
            command.upgrade(config, 'head')


class SqlaSettingsManager(SettingsManager):
    """Class to get, set and delete settings from the `DbSettings` table."""

    table_name = 'db_dbsetting'

    def validate_table_existence(self):
        """Verify that the `DbSetting` table actually exists.

        :raises: `~aiida.common.exceptions.NotExistent` if the settings table does not exist
        """
        from sqlalchemy.engine import reflection
        inspector = reflection.Inspector.from_engine(get_scoped_session().bind)
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
            raise NotExistent('setting `{}` does not exist'.format(key)) from NoResultFound

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

        other_attribs = dict()
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
            raise NotExistent('setting `{}` does not exist'.format(key)) from NoResultFound
