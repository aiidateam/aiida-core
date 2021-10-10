# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic backend related objects"""
import abc
import typing

from .. import backends

__all__ = ('SqlBackend',)

# The template type for the base ORM model type
ModelType = typing.TypeVar('ModelType')  # pylint: disable=invalid-name


class SqlBackend(typing.Generic[ModelType], backends.Backend):
    """
    A class for SQL based backends.  Assumptions are that:
        * there is an ORM
        * that it is possible to convert from ORM model instances to backend instances
        * that psycopg2 is used as the engine

    if any of these assumptions do not fit then just implement a backend from :class:`aiida.orm.implementation.Backend`
    """

    def __init__(self) -> None:
        from aiida.backends.manager import BackendManager
        super().__init__()
        self._backend_manager = BackendManager()

    @abc.abstractmethod
    def get_backend_entity(self, model):
        """
        Return the backend entity that corresponds to the given Model instance

        :param model: the ORM model instance to promote to a backend instance
        :return: the backend entity corresponding to the given model
        :rtype: :class:`aiida.orm.implementation.entities.BackendEntity`
        """

    @abc.abstractmethod
    def cursor(self):
        """
        Return a psycopg cursor.  This method should be used as a context manager i.e.::

            with backend.cursor():
                # Do stuff

        :return: a psycopg cursor
        :rtype: :class:`psycopg2.extensions.cursor`
        """

    @abc.abstractmethod
    def execute_raw(self, query):
        """Execute a raw SQL statement and return the result.

        :param query: a string containing a raw SQL statement
        :return: the result of the query
        """

    def execute_prepared_statement(self, sql, parameters):
        """Execute an SQL statement with optional prepared statements.

        :param sql: the SQL statement string
        :param parameters: dictionary to use to populate the prepared statement
        """
        results = []

        with self.cursor() as cursor:
            cursor.execute(sql, parameters)

            for row in cursor:
                results.append(row)

        return results

    @classmethod
    @abc.abstractmethod
    def load_environment(cls, profile, validate_schema=True, **kwargs):
        """Load the backend environment.

        :param profile: the profile whose backend environment to load
        :param validate_schema: boolean, if True, validate the schema after loading the environment.
        :param kwargs: keyword arguments that will be passed on to the backend specific scoped session getter function.
        """

    @abc.abstractmethod
    def reset_environment(self):
        """Reset the backend environment."""

    def get_repository_uuid(self):
        """Return the UUID of the repository that is associated with this database.

        :return: the UUID of the repository associated with this database or None if it doesn't exist.
        """
        return self._backend_manager.get_repository_uuid()

    def get_schema_generation_database(self):
        """Return the database schema version.

        :return: `distutils.version.LooseVersion` with schema version of the database
        """
        return self._backend_manager.get_schema_generation_database()

    def get_schema_version_database(self):
        """Return the database schema version.

        :return: `distutils.version.LooseVersion` with schema version of the database
        """
        return self._backend_manager.get_schema_version_database()

    def set_value(self, key: str, value: typing.Any, description: typing.Optional[str] = None) -> None:
        """Set a global key/value pair on the profile backend.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """
        return self._backend_manager.get_settings_manager().set(key, value, description)

    def get_value(self, key: str) -> typing.Any:
        """Get a global key/value pair on the profile backend.

        :param key: the key identifying the setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        return self._backend_manager.get_settings_manager().get(key)
