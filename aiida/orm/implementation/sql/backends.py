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
from typing import TYPE_CHECKING, Any, Generic, Optional, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.future.engine import Engine
from sqlalchemy.orm import Session

from aiida.common import json

from .. import backends

if TYPE_CHECKING:
    from aiida.backends.manager import BackendManager

__all__ = ('SqlBackend',)

# The template type for the base ORM model type
ModelType = TypeVar('ModelType')  # pylint: disable=invalid-name


def create_sqlalchemy_engine(profile, **kwargs):
    """Create SQLAlchemy engine.

    :param kwargs: keyword arguments that will be passed on to `sqlalchemy.create_engine`.
        See https://docs.sqlalchemy.org/en/13/core/engines.html?highlight=create_engine#sqlalchemy.create_engine for
        more info.
    """
    # The hostname may be `None`, which is a valid value in the case of peer authentication for example. In this case
    # it should be converted to an empty string, because otherwise the `None` will be converted to string literal "None"
    hostname = profile.database_hostname or ''
    separator = ':' if profile.database_port else ''

    engine_url = 'postgresql://{user}:{password}@{hostname}{separator}{port}/{name}'.format(
        separator=separator,
        user=profile.database_username,
        password=profile.database_password,
        hostname=hostname,
        port=profile.database_port,
        name=profile.database_name
    )
    return create_engine(
        engine_url, json_serializer=json.dumps, json_deserializer=json.loads, future=True, encoding='utf-8', **kwargs
    )


class SqlBackend(Generic[ModelType], backends.Backend):
    """
    A class for SQL based backends.  Assumptions are that:
        * there is an ORM
        * that it is possible to convert from ORM model instances to backend instances
        * that psycopg2 is used as the engine

    if any of these assumptions do not fit then just implement a backend from :class:`aiida.orm.implementation.Backend`
    """

    def __init__(self, profile, validate_db: bool = True):
        super().__init__(profile, validate_db)
        # set variables for QueryBuilder
        self._engine: Optional[Engine] = None
        self._session: Optional[Session] = None

    def get_session(self, **kwargs: Any) -> 'Session':
        """Return an SQLAlchemy database session.

        On first call (or after a reset) the session is initialised, then the same session is always returned.

        :param kwargs: keyword arguments to be passed to the engine
        """
        if self._engine is None:
            self._engine = create_sqlalchemy_engine(self._profile, **kwargs)
        if self._session is None:
            self._session = Session(bind=self._engine, future=True)
        return self._session

    def close(self):
        if self._session is not None:
            self._session.close()
            self._session = None
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

    def reset(self, **kwargs):
        self.close()
        self.get_session(**kwargs)

    @property
    @abc.abstractmethod
    def backend_manager(self) -> 'BackendManager':
        """Return the backend manager."""

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

    def get_repository_uuid(self):
        """Return the UUID of the repository that is associated with this database.

        :return: the UUID of the repository associated with this database or None if it doesn't exist.
        """
        return self.backend_manager.get_repository_uuid()

    def get_schema_generation_database(self):
        """Return the database schema version.

        :return: `distutils.version.LooseVersion` with schema version of the database
        """
        return self.backend_manager.get_schema_generation_database()

    def get_schema_version_database(self):
        """Return the database schema version.

        :return: `distutils.version.LooseVersion` with schema version of the database
        """
        return self.backend_manager.get_schema_version_database()

    def set_value(self, key: str, value: Any, description: Optional[str] = None) -> None:
        """Set a global key/value pair on the profile backend.

        :param key: the key identifying the setting
        :param value: the value for the setting
        :param description: optional setting description
        """
        return self.backend_manager.get_settings_manager().set(key, value, description)

    def get_value(self, key: str) -> Any:
        """Get a global key/value pair on the profile backend.

        :param key: the key identifying the setting
        :raises: `~aiida.common.exceptions.NotExistent` if the settings does not exist
        """
        return self.backend_manager.get_settings_manager().get(key)
