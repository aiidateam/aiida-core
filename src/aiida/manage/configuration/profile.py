###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA profile related code"""

from __future__ import annotations

import collections
import os
import pathlib
from copy import deepcopy
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Type, Union

from aiida.common import exceptions

from .options import parse_option

if TYPE_CHECKING:
    from aiida.orm.implementation import StorageBackend
    from aiida.tools.dumping.config import DumpConfig

__all__ = ('Profile',)


class Profile:
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
        self._attributes: Dict[str, Any] = deepcopy(config)  # type: ignore[arg-type]

        # Create a default UUID if not specified
        if self._attributes.get(self.KEY_UUID, None) is None:
            from uuid import uuid4

            self._attributes[self.KEY_UUID] = uuid4().hex

    def __repr__(self) -> str:
        return f'Profile<uuid={self.uuid!r} name={self.name!r}>'

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
        from aiida.plugins import StorageFactory

        return StorageFactory(self.storage_backend)

    @property
    def process_control_backend(self) -> str | None:
        """Return the type of the process control backend."""
        return self._attributes[self.KEY_PROCESS][self.KEY_PROCESS_BACKEND]

    @property
    def process_control_config(self) -> Dict[str, Any]:
        """Return the configuration required by the process control backend."""
        return self._attributes[self.KEY_PROCESS][self.KEY_PROCESS_CONFIG] or {}

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
        from urllib.request import url2pathname

        from aiida.common.warnings import warn_deprecation

        warn_deprecation('This method has been deprecated', version=3)

        if 'repository_uri' not in self.storage_config:
            raise KeyError('repository_uri not defined in profile storage config')

        parts = urlparse(self.storage_config['repository_uri'])

        if parts.scheme != 'file':
            raise exceptions.ConfigurationError('invalid repository protocol, only the local `file://` is supported')

        if not os.path.isabs(url2pathname(parts.path)):
            raise exceptions.ConfigurationError('invalid repository URI: the path has to be absolute')

        return pathlib.Path(os.path.expanduser(url2pathname(parts.path)))

    @property
    def filepaths(self):
        """Return the filepaths used by this profile.

        :return: a dictionary of filepaths
        """
        from aiida.common.warnings import warn_deprecation
        from aiida.manage.configuration.settings import AiiDAConfigPathResolver

        warn_deprecation('This method has been deprecated, use `filepaths` method from `Config` obj instead', version=3)

        daemon_dir = AiiDAConfigPathResolver().daemon_dir
        daemon_log_dir = AiiDAConfigPathResolver().daemon_log_dir

        return {
            'circus': {
                'log': str(daemon_log_dir / f'circus-{self.name}.log'),
                'pid': str(daemon_dir / f'circus-{self.name}.pid'),
                'port': str(daemon_dir / f'circus-{self.name}.port'),
                'socket': {
                    'file': str(daemon_dir / f'circus-{self.name}.sockets'),
                    'controller': 'circus.c.sock',
                    'pubsub': 'circus.p.sock',
                    'stats': 'circus.s.sock',
                },
            },
            'daemon': {
                'log': str(daemon_log_dir / f'aiida-{self.name}.log'),
                'pid': str(daemon_dir / f'aiida-{self.name}.pid'),
            },
        }

    def dump(
        self, config: Optional[DumpConfig] = None, output_path: Optional[Union[str, Path]] = None
    ) -> Optional[Path]:
        """Dump data stored in an AiiDA profile to disk in a human-readable directory tree.

        :param config: DumpConfig configuration object, defaults to None
        :param output_path: Dumping output path, defaults to None
        :return: Resolved output path where the profile data was dumped.
        """
        from aiida.common import AIIDA_LOGGER
        from aiida.tools.dumping.config import DumpConfig, DumpMode
        from aiida.tools.dumping.engine import DumpEngine
        from aiida.tools.dumping.utils import DumpPaths

        logger = AIIDA_LOGGER.getChild('tools.dumping.profile')

        if not config:
            config = DumpConfig()

        # --- Check final determined scope ---
        if not (config.all_entries or config.filters_set) and config.dump_mode != DumpMode.DRY_RUN:
            msg = (
                'No profile data explicitly selected. No dump will be performed.',
                'Either select everything via `--all`, or filter via `--groups`, `--user`, etc.',
            )
            logger.warning(msg)
            return None

        if output_path:
            target_path: Path = Path(output_path).resolve()
        else:
            target_path = DumpPaths.get_default_dump_path(entity=self)

        engine = DumpEngine(
            base_output_path=target_path,
            config=config,
            dump_target_entity=self,
        )
        engine.dump(entity=self)

        return target_path
