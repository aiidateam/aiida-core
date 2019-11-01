# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import abc
import collections
import six

from aiida.backends import BACKEND_SQLA, BACKEND_DJANGO
from aiida.common.exceptions import ConfigurationError, ValidationError
from aiida.manage import configuration

AIIDA_ATTRIBUTE_SEP = '.'

SCHEMA_GENERATION_KEY = 'schema_generation'
SCHEMA_GENERATION_VALUE = '1'


Setting = collections.namedtuple('Setting', ['key', 'value', 'description', 'time'])


class SettingsManager(object):
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


def get_settings_manager():
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import DjangoSettingsManager
        manager = DjangoSettingsManager()
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import SqlaSettingsManager
        manager = SqlaSettingsManager()
    else:
        raise Exception('unknown backend type `{}`'.format(configuration.PROFILE.database_backend))

    return manager


def validate_schema_generation():
    """Verify that the database schema generation is compatible with the current code schema generation."""
    from aiida.common.exceptions import ConfigurationError, NotExistent
    try:
        schema_generation_database = get_db_schema_generation().value
    except NotExistent:
        schema_generation_database = '1'

    if schema_generation_database is None:
        schema_generation_database = '1'

    if schema_generation_database != SCHEMA_GENERATION_VALUE:
        raise ConfigurationError(
            'The schema generation of your database {} is newer than that of the code `{}` and is incompatible.'.format(
                schema_generation_database, SCHEMA_GENERATION_VALUE
            )
        )


def get_db_schema_generation():
    """Get the schema generation of the current database."""
    from aiida.backends.utils import get_settings_manager
    manager = get_settings_manager()
    return manager.get(SCHEMA_GENERATION_KEY)


def validate_attribute_key(key):
    """
    Validate the key string to check if it is valid (e.g., if it does not
    contain the separator symbol.).

    :return: None if the key is valid
    :raise aiida.common.ValidationError: if the key is not valid
    """
    if not isinstance(key, six.string_types):
        raise ValidationError('The key must be a string.')
    if not key:
        raise ValidationError('The key cannot be an empty string.')
    if AIIDA_ATTRIBUTE_SEP in key:
        raise ValidationError("The separator symbol '{}' cannot be present "
                              'in the key of attributes, extras, etc.'.format(AIIDA_ATTRIBUTE_SEP))


def load_dbenv(profile=None, *args, **kwargs):
    if configuration.PROFILE.database_backend == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import load_dbenv as load_dbenv_sqlalchemy
        to_return = load_dbenv_sqlalchemy(profile=profile, *args, **kwargs)
    elif configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import load_dbenv as load_dbenv_django
        to_return = load_dbenv_django(profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError('Invalid configuration.PROFILE.database_backend: {}'.format(
            configuration.PROFILE.database_backend))

    return to_return


def _load_dbenv_noschemacheck(profile=None, *args, **kwargs):
    if configuration.PROFILE.database_backend == BACKEND_SQLA:
        # Maybe schema version should be also checked for SQLAlchemy version.
        from aiida.backends.sqlalchemy.utils \
            import _load_dbenv_noschemacheck as _load_dbenv_noschemacheck_sqlalchemy
        to_return = _load_dbenv_noschemacheck_sqlalchemy(profile=profile, *args, **kwargs)
    elif configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import _load_dbenv_noschemacheck as _load_dbenv_noschemacheck_django
        to_return = _load_dbenv_noschemacheck_django(profile=profile, *args, **kwargs)
    else:
        raise ConfigurationError('Invalid configuration.PROFILE.database_backend: {}'.format(configuration.PROFILE.database_backend))

    return to_return


def delete_nodes_and_connections(pks):
    if configuration.PROFILE.database_backend == BACKEND_DJANGO:
        from aiida.backends.djsite.utils import delete_nodes_and_connections_django as delete_nodes_backend
    elif configuration.PROFILE.database_backend == BACKEND_SQLA:
        from aiida.backends.sqlalchemy.utils import delete_nodes_and_connections_sqla as delete_nodes_backend
    else:
        raise Exception('unknown backend {}'.format(configuration.PROFILE.database_backend))

    delete_nodes_backend(pks)
