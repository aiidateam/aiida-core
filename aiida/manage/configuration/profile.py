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
from copy import deepcopy
import os
import pathlib
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Type

from aiida.common import exceptions

from .options import parse_option
from .settings import DAEMON_DIR, DAEMON_LOG_DIR

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend

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

    KEY_UUID = 'PROFILE_UUID'
    KEY_DEFAULT_USER_EMAIL = 'default_user_email'
    KEY_STORAGE = 'storage'
    KEY_PROCESS = 'process_control'
    KEY_STORAGE_BACKEND = 'backend'
    KEY_STORAGE_CONFIG = 'config'
    KEY_PROCESS_BACKEND = 'backend'
    KEY_PROCESS_CONFIG = 'config'
    KEY_OPTIONS = 'options'
    KEY_TEST_PROFILE = 'test_profile'

    # keys that are expected to be in the parsed configuration
    REQUIRED_KEYS = (
        KEY_STORAGE,
        KEY_PROCESS,
    )

    def __init__(self, name: str, config: Mapping[str, Any], validate=True):
        """Load a profile with the profile configuration."""
        if not isinstance(config, collections.abc.Mapping):
            raise TypeError(f'config should be a mapping but is {type(config)}')
        if validate and not set(config.keys()).issuperset(self.REQUIRED_KEYS):
            raise exceptions.ConfigurationError(
                f'profile {name!r} configuration does not contain all required keys: {self.REQUIRED_KEYS}'
            )

        self._name = name
        self._attributes: Dict[str, Any] = deepcopy(config)

        # Create a default UUID if not specified
        if self._attributes.get(self.KEY_UUID, None) is None:
            from uuid import uuid4
            self._attributes[self.KEY_UUID] = uuid4().hex

    def __str__(self) -> str:
        return f'Profile<{self.uuid!r} ({self.name!r})>'

    def copy(self):
        """Return a copy of the profile."""
        return self.__class__(self.name, self._attributes)

    @property
    def uuid(self) -> str:
        """Return the profile uuid.

        :return: string UUID
        """
        return self._attributes[self.KEY_UUID]

    @uuid.setter
    def uuid(self, value: str) -> None:
        self._attributes[self.KEY_UUID] = value

    @property
    def default_user_email(self) -> Optional[str]:
        """Return the default user email."""
        return self._attributes.get(self.KEY_DEFAULT_USER_EMAIL, None)

    @default_user_email.setter
    def default_user_email(self, value: Optional[str]) -> None:
        """Set the default user email."""
        self._attributes[self.KEY_DEFAULT_USER_EMAIL] = value

    @property
    def storage_backend(self) -> str:
        """Return the type of the storage backend."""
        return self._attributes[self.KEY_STORAGE][self.KEY_STORAGE_BACKEND]

    @property
    def storage_config(self) -> Dict[str, Any]:
        """Return the configuration required by the storage backend."""
        return self._attributes[self.KEY_STORAGE][self.KEY_STORAGE_CONFIG]

    def set_storage(self, name: str, config: Dict[str, Any]) -> None:
        """Set the storage backend and its configuration.

        :param name: the name of the storage backend
        :param config: the configuration of the storage backend
        """
        self._attributes.setdefault(self.KEY_STORAGE, {})
        self._attributes[self.KEY_STORAGE][self.KEY_STORAGE_BACKEND] = name
        self._attributes[self.KEY_STORAGE][self.KEY_STORAGE_CONFIG] = config

    @property
    def storage_cls(self) -> Type['StorageBackend']:
        """Return the storage backend class for this profile."""
        if self.storage_backend == 'psql_dos':
            from aiida.storage.psql_dos.backend import PsqlDosBackend
            return PsqlDosBackend
        if self.storage_backend == 'sqlite_zip':
            from aiida.storage.sqlite_zip.backend import SqliteZipBackend
            return SqliteZipBackend
        raise ValueError(f'unknown storage backend type: {self.storage_backend}')

    @property
    def process_control_backend(self) -> str:
        """Return the type of the process control backend."""
        return self._attributes[self.KEY_PROCESS][self.KEY_PROCESS_BACKEND]

    @property
    def process_control_config(self) -> Dict[str, Any]:
        """Return the configuration required by the process control backend."""
        return self._attributes[self.KEY_PROCESS][self.KEY_PROCESS_CONFIG]

    def set_process_controller(self, name: str, config: Dict[str, Any]) -> None:
        """Set the process control backend and its configuration.

        :param name: the name of the process backend
        :param config: the configuration of the process backend
        """
        self._attributes.setdefault(self.KEY_PROCESS, {})
        self._attributes[self.KEY_PROCESS][self.KEY_PROCESS_BACKEND] = name
        self._attributes[self.KEY_PROCESS][self.KEY_PROCESS_CONFIG] = config

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
    def dictionary(self) -> Dict[str, Any]:
        """Return the profile attributes as a dictionary with keys as it is stored in the config

        :return: the profile configuration dictionary
        """
        return self._attributes

    @property
    def is_test_profile(self) -> bool:
        """Return whether the profile is a test profile

        :return: boolean, True if test profile, False otherwise
        """
        # Check explicitly for ``True`` for safety. If an invalid value is defined, we default to treating it as not
        # a test profile as that can unintentionally clear the database.
        return self._attributes.get(self.KEY_TEST_PROFILE, False) is True

    @is_test_profile.setter
    def is_test_profile(self, value: bool) -> None:
        """Set whether the profile is a test profile.

        :param value: boolean indicating whether this profile is a test profile.
        """
        self._attributes[self.KEY_TEST_PROFILE] = value

    @property
    def repository_path(self) -> pathlib.Path:
        """Return the absolute path of the repository configured for this profile.

        The URI should be in the format `protocol://address`

        :note: At the moment, only the file protocol is supported.

        :return: absolute filepath of the profile's file repository
        """
        from urllib.parse import urlparse

        parts = urlparse(self.storage_config['repository_uri'])

        if parts.scheme != 'file':
            raise exceptions.ConfigurationError('invalid repository protocol, only the local `file://` is supported')

        if not os.path.isabs(parts.path):
            raise exceptions.ConfigurationError('invalid repository URI: the path has to be absolute')

        return pathlib.Path(os.path.expanduser(parts.path))

    @property
    def rmq_prefix(self) -> str:
        """Return the prefix that should be used for RMQ resources

        :return: the rmq prefix string
        """
        return f'aiida-{self.uuid}'

    def get_rmq_url(self) -> str:
        """Return the RMQ url for this profile."""
        from aiida.manage.external.rmq import get_rmq_url

        if self.process_control_backend != 'rabbitmq':
            raise exceptions.ConfigurationError(
                f"invalid process control backend, only 'rabbitmq' is supported: {self.process_control_backend}"
            )
        kwargs = {key[7:]: val for key, val in self.process_control_config.items() if key.startswith('broker_')}
        additional_kwargs = kwargs.pop('parameters', {})
        return get_rmq_url(**kwargs, **additional_kwargs)

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
