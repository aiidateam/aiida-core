# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA profile related code"""
import collections
import os

from aiida.common import exceptions

from .options import parse_option
from .settings import DAEMON_DIR, DAEMON_LOG_DIR

__all__ = ('Profile',)

CIRCUS_PID_FILE_TEMPLATE = os.path.join(DAEMON_DIR, 'circus-{}.pid')
DAEMON_PID_FILE_TEMPLATE = os.path.join(DAEMON_DIR, 'aiida-{}.pid')
CIRCUS_LOG_FILE_TEMPLATE = os.path.join(DAEMON_LOG_DIR, 'circus-{}.log')
DAEMON_LOG_FILE_TEMPLATE = os.path.join(DAEMON_LOG_DIR, 'aiida-{}.log')
CIRCUS_PORT_FILE_TEMPLATE = os.path.join(DAEMON_DIR, 'circus-{}.port')
CIRCUS_SOCKET_FILE_TEMPATE = os.path.join(DAEMON_DIR, 'circus-{}.sockets')
CIRCUS_CONTROLLER_SOCKET_TEMPLATE = 'circus.c.sock'
CIRCUS_PUBSUB_SOCKET_TEMPLATE = 'circus.p.sock'
CIRCUS_STATS_SOCKET_TEMPLATE = 'circus.s.sock'


class Profile:  # pylint: disable=too-many-public-methods
    """Class that models a profile as it is stored in the configuration file of an AiiDA instance."""

    RMQ_PREFIX = 'aiida-{uuid}'
    KEY_OPTIONS = 'options'
    KEY_UUID = 'PROFILE_UUID'
    KEY_DEFAULT_USER = 'default_user_email'
    KEY_DATABASE_ENGINE = 'AIIDADB_ENGINE'
    KEY_DATABASE_BACKEND = 'AIIDADB_BACKEND'
    KEY_DATABASE_NAME = 'AIIDADB_NAME'
    KEY_DATABASE_PORT = 'AIIDADB_PORT'
    KEY_DATABASE_HOSTNAME = 'AIIDADB_HOST'
    KEY_DATABASE_USERNAME = 'AIIDADB_USER'
    KEY_DATABASE_PASSWORD = 'AIIDADB_PASS'  # noqa
    KEY_BROKER_PROTOCOL = 'broker_protocol'
    KEY_BROKER_USERNAME = 'broker_username'
    KEY_BROKER_PASSWORD = 'broker_password'  # noqa
    KEY_BROKER_HOST = 'broker_host'
    KEY_BROKER_PORT = 'broker_port'
    KEY_BROKER_VIRTUAL_HOST = 'broker_virtual_host'
    KEY_BROKER_PARAMETERS = 'broker_parameters'
    KEY_REPOSITORY_URI = 'AIIDADB_REPOSITORY_URI'

    # A mapping of valid attributes to the key under which they are stored in the configuration dictionary
    _map_config_to_internal = {
        KEY_OPTIONS: 'options',
        KEY_UUID: 'uuid',
        KEY_DEFAULT_USER: 'default_user',
        KEY_DATABASE_ENGINE: 'database_engine',
        KEY_DATABASE_BACKEND: 'database_backend',
        KEY_DATABASE_NAME: 'database_name',
        KEY_DATABASE_PORT: 'database_port',
        KEY_DATABASE_HOSTNAME: 'database_hostname',
        KEY_DATABASE_USERNAME: 'database_username',
        KEY_DATABASE_PASSWORD: 'database_password',
        KEY_BROKER_PROTOCOL: 'broker_protocol',
        KEY_BROKER_USERNAME: 'broker_username',
        KEY_BROKER_PASSWORD: 'broker_password',
        KEY_BROKER_HOST: 'broker_host',
        KEY_BROKER_PORT: 'broker_port',
        KEY_BROKER_VIRTUAL_HOST: 'broker_virtual_host',
        KEY_BROKER_PARAMETERS: 'broker_parameters',
        KEY_REPOSITORY_URI: 'repository_uri',
    }

    @classmethod
    def contains_unknown_keys(cls, dictionary):
        """Return whether the profile dictionary contains any unsupported keys.

        :param dictionary: a profile dictionary
        :return: boolean, True when the dictionay contains unsupported keys
        """
        return set(dictionary.keys()) - set(cls._map_config_to_internal.keys())

    def __init__(self, name, attributes, from_config=False):
        if not isinstance(attributes, collections.abc.Mapping):
            raise TypeError(f'attributes should be a mapping but is {type(attributes)}')

        self._name = name
        self._attributes = {}

        for internal_key, value in attributes.items():
            if from_config:
                try:
                    internal_key = self._map_config_to_internal[internal_key]
                except KeyError:
                    from aiida.cmdline.utils import echo
                    echo.echo_warning(
                        f'removed unsupported key `{internal_key}` with value `{value}` from profile `{name}`'
                    )
                    continue
            setattr(self, internal_key, value)

        # Create a default UUID if not specified
        if self.uuid is None:
            from uuid import uuid4
            self.uuid = uuid4().hex

        # Currently, whether a profile is a test profile is solely determined by its name starting with 'test_'
        self._test_profile = bool(self.name.startswith('test_'))

    @property
    def uuid(self):
        """Return the profile uuid.

        :return: string UUID
        """
        try:
            return self._attributes[self.KEY_UUID]
        except KeyError:
            return None

    @uuid.setter
    def uuid(self, value):
        self._attributes[self.KEY_UUID] = value

    @property
    def default_user(self):
        return self._attributes.get(self.KEY_DEFAULT_USER, None)

    @default_user.setter
    def default_user(self, value):
        self._attributes[self.KEY_DEFAULT_USER] = value

    @property
    def database_engine(self):
        return self._attributes[self.KEY_DATABASE_ENGINE]

    @database_engine.setter
    def database_engine(self, value):
        self._attributes[self.KEY_DATABASE_ENGINE] = value

    @property
    def database_backend(self):
        return self._attributes[self.KEY_DATABASE_BACKEND]

    @database_backend.setter
    def database_backend(self, value):
        self._attributes[self.KEY_DATABASE_BACKEND] = value

    @property
    def database_name(self):
        return self._attributes[self.KEY_DATABASE_NAME]

    @database_name.setter
    def database_name(self, value):
        self._attributes[self.KEY_DATABASE_NAME] = value

    @property
    def database_port(self):
        return self._attributes[self.KEY_DATABASE_PORT]

    @database_port.setter
    def database_port(self, value):
        self._attributes[self.KEY_DATABASE_PORT] = value

    @property
    def database_hostname(self):
        return self._attributes[self.KEY_DATABASE_HOSTNAME]

    @database_hostname.setter
    def database_hostname(self, value):
        self._attributes[self.KEY_DATABASE_HOSTNAME] = value

    @property
    def database_username(self):
        return self._attributes[self.KEY_DATABASE_USERNAME]

    @database_username.setter
    def database_username(self, value):
        self._attributes[self.KEY_DATABASE_USERNAME] = value

    @property
    def database_password(self):
        return self._attributes[self.KEY_DATABASE_PASSWORD]

    @database_password.setter
    def database_password(self, value):
        self._attributes[self.KEY_DATABASE_PASSWORD] = value

    @property
    def broker_protocol(self):
        return self._attributes[self.KEY_BROKER_PROTOCOL]

    @broker_protocol.setter
    def broker_protocol(self, value):
        self._attributes[self.KEY_BROKER_PROTOCOL] = value

    @property
    def broker_host(self):
        return self._attributes[self.KEY_BROKER_HOST]

    @broker_host.setter
    def broker_host(self, value):
        self._attributes[self.KEY_BROKER_HOST] = value

    @property
    def broker_port(self):
        return self._attributes[self.KEY_BROKER_PORT]

    @broker_port.setter
    def broker_port(self, value):
        self._attributes[self.KEY_BROKER_PORT] = value

    @property
    def broker_username(self):
        return self._attributes[self.KEY_BROKER_USERNAME]

    @broker_username.setter
    def broker_username(self, value):
        self._attributes[self.KEY_BROKER_USERNAME] = value

    @property
    def broker_password(self):
        return self._attributes[self.KEY_BROKER_PASSWORD]

    @broker_password.setter
    def broker_password(self, value):
        self._attributes[self.KEY_BROKER_PASSWORD] = value

    @property
    def broker_virtual_host(self):
        return self._attributes[self.KEY_BROKER_VIRTUAL_HOST]

    @broker_virtual_host.setter
    def broker_virtual_host(self, value):
        self._attributes[self.KEY_BROKER_VIRTUAL_HOST] = value

    @property
    def broker_parameters(self):
        return self._attributes.get(self.KEY_BROKER_PARAMETERS, {})

    @broker_parameters.setter
    def broker_parameters(self, value):
        self._attributes[self.KEY_BROKER_PARAMETERS] = value

    @property
    def repository_uri(self):
        return self._attributes[self.KEY_REPOSITORY_URI]

    @repository_uri.setter
    def repository_uri(self, value):
        self._attributes[self.KEY_REPOSITORY_URI] = value

    @property
    def options(self):
        self._attributes.setdefault(self.KEY_OPTIONS, {})
        return self._attributes[self.KEY_OPTIONS]

    @options.setter
    def options(self, value):
        self._attributes[self.KEY_OPTIONS] = value

    def get_option(self, option_key, default=None):
        return self.options.get(option_key, default)

    def set_option(self, option_key, value, override=True):
        """Set a configuration option for a certain scope.

        :param option_key: the key of the configuration option
        :param option_value: the option value
        :param override: boolean, if False, will not override the option if it already exists
        """
        _, parsed_value = parse_option(option_key, value)  # ensure the value is validated
        if option_key not in self.options or override:
            self.options[option_key] = parsed_value

    def unset_option(self, option_key):
        self.options.pop(option_key, None)

    @property
    def name(self):
        """Return the profile name.

        :return: the profile name
        """
        return self._name

    @property
    def dictionary(self):
        """Return the profile attributes as a dictionary with keys as it is stored in the config

        :return: the profile configuration dictionary
        """
        return self._attributes

    @property
    def rmq_prefix(self):
        """Return the prefix that should be used for RMQ resources

        :return: the rmq prefix string
        """
        return self.RMQ_PREFIX.format(uuid=self.uuid)

    @property
    def is_test_profile(self):
        """Return whether the profile is a test profile

        :return: boolean, True if test profile, False otherwise
        """
        return self._test_profile

    @property
    def repository_path(self):
        """Return the absolute path of the repository configured for this profile.

        :return: absolute filepath of the profile's file repository
        """
        return self._parse_repository_uri()[1]

    def _parse_repository_uri(self):
        """
        This function validates the REPOSITORY_URI, that should be in the format protocol://address

        :note: At the moment, only the file protocol is supported.

        :return: a tuple (protocol, address).
        """
        from urllib.parse import urlparse

        parts = urlparse(self.repository_uri)

        if parts.scheme != 'file':
            raise exceptions.ConfigurationError('invalid repository protocol, only the local `file://` is supported')

        if not os.path.isabs(parts.path):
            raise exceptions.ConfigurationError('invalid repository URI: the path has to be absolute')

        return parts.scheme, os.path.expanduser(parts.path)

    def get_rmq_url(self):
        from aiida.manage.external.rmq import get_rmq_url
        return get_rmq_url(
            protocol=self.broker_protocol,
            username=self.broker_username,
            password=self.broker_password,
            host=self.broker_host,
            port=self.broker_port,
            virtual_host=self.broker_virtual_host,
            **self.broker_parameters
        )

    def configure_repository(self):
        """Validates the configured repository and in the case of a file system repo makes sure the folder exists."""
        import errno

        try:
            os.makedirs(self.repository_path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise exceptions.ConfigurationError(
                    f'could not create the configured repository `{self.repository_path}`: {str(exception)}'
                )

    @property
    def filepaths(self):
        """Return the filepaths used by this profile.

        :return: a dictionary of filepaths
        """
        return {
            'circus': {
                'log': CIRCUS_LOG_FILE_TEMPLATE.format(self.name),
                'pid': CIRCUS_PID_FILE_TEMPLATE.format(self.name),
                'port': CIRCUS_PORT_FILE_TEMPLATE.format(self.name),
                'socket': {
                    'file': CIRCUS_SOCKET_FILE_TEMPATE.format(self.name),
                    'controller': CIRCUS_CONTROLLER_SOCKET_TEMPLATE,
                    'pubsub': CIRCUS_PUBSUB_SOCKET_TEMPLATE,
                    'stats': CIRCUS_STATS_SOCKET_TEMPLATE,
                }
            },
            'daemon': {
                'log': DAEMON_LOG_FILE_TEMPLATE.format(self.name),
                'pid': DAEMON_PID_FILE_TEMPLATE.format(self.name),
            }
        }
