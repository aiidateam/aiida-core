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
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Type, Union

from aiida.common import exceptions

from .options import parse_option

if TYPE_CHECKING:
    from aiida.orm import Code, Computer, Group, User
    from aiida.orm.implementation import StorageBackend

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
        self,
        output_path: Optional[Union[str, Path]] = None,
        # Dump mode options
        dry_run: bool = False,
        overwrite: bool = False,
        # Scope options
        all_entries: bool = False,
        groups: Optional[Union[List[str], List[Group]]] = None,
        user: Optional[Union[List[str], List[User]]] = None,
        computers: Optional[Union[List[str], List[Computer]]] = None,
        codes: Optional[Union[List[str], List[Code]]] = None,
        # Time filtering options
        past_days: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        filter_by_last_dump_time: bool = True,
        # Node collection options
        only_top_level_calcs: bool = True,
        only_top_level_workflows: bool = True,
        # Process dump options
        include_inputs: bool = True,
        include_outputs: bool = False,
        include_attributes: bool = True,
        include_extras: bool = False,
        flat: bool = False,
        dump_unsealed: bool = False,
        symlink_calcs: bool = False,
        # Group/Profile options
        delete_missing: bool = True,
        organize_by_groups: bool = True,
        also_ungrouped: bool = False,
        relabel_groups: bool = True,
    ) -> Path:
        """Dump data stored in an AiiDA profile to disk in a human-readable directory tree.

        :param output_path: Target directory for the dump, defaults to None
        :param dry_run: Show what would be dumped without actually dumping, defaults to False
        :param overwrite: Overwrite existing dump directories, defaults to False
        :param all_entries: Dump all entries in the profile, defaults to False
        :param groups: List of groups to dump (UUIDs, labels, or Group objects), defaults to None
        :param user: User to filter by (User object or email), defaults to None
        :param computers: List of computers to filter by, defaults to None
        :param codes: List of codes to filter by, defaults to None
        :param past_days: Only include nodes modified in the past N days, defaults to None
        :param start_date: Only include nodes modified after this date, defaults to None
        :param end_date: Only include nodes modified before this date, defaults to None
        :param filter_by_last_dump_time: Filter nodes by last dump time, defaults to True
        :param only_top_level_calcs: Only dump top-level calculations, defaults to True
        :param only_top_level_workflows: Only dump top-level workflows, defaults to True
        :param include_inputs: Include input files in the dump, defaults to True
        :param include_outputs: Include output files in the dump, defaults to False
        :param include_attributes: Include node attributes in metadata, defaults to True
        :param include_extras: Include node extras in metadata, defaults to False
        :param flat: Use flat directory structure, defaults to False
        :param dump_unsealed: Allow dumping of unsealed nodes, defaults to False
        :param symlink_calcs: Create symlinks for calculation nodes, defaults to False
        :param delete_missing: Delete dump files for nodes no longer in scope, defaults to True
        :param organize_by_groups: Organize output by groups, defaults to True
        :param also_ungrouped: Also dump ungrouped nodes, defaults to False
        :param relabel_groups: Update group directory names when labels change, defaults to True
        :return: Path where the profile was dumped, or None if nothing was dumped
        """
        from aiida.common import AIIDA_LOGGER
        from aiida.tools._dumping.config import ProfileDumpConfig
        from aiida.tools._dumping.engine import DumpEngine
        from aiida.tools._dumping.utils import DumpPaths

        logger = AIIDA_LOGGER.getChild('tools._dumping.profile')

        # Construct ProfileDumpConfig from kwargs
        config_data = {
            'all_entries': all_entries,
            'dry_run': dry_run,
            'overwrite': overwrite,
            'groups': groups or [],
            'user': user,
            'computers': computers or [],
            'codes': codes or [],
            'past_days': past_days,
            'start_date': start_date,
            'end_date': end_date,
            'filter_by_last_dump_time': filter_by_last_dump_time,
            'only_top_level_calcs': only_top_level_calcs,
            'only_top_level_workflows': only_top_level_workflows,
            'include_inputs': include_inputs,
            'include_outputs': include_outputs,
            'include_attributes': include_attributes,
            'include_extras': include_extras,
            'flat': flat,
            'dump_unsealed': dump_unsealed,
            'symlink_calcs': symlink_calcs,
            'delete_missing': delete_missing,
            'organize_by_groups': organize_by_groups,
            'also_ungrouped': also_ungrouped,
            'relabel_groups': relabel_groups,
        }

        config = ProfileDumpConfig.model_validate(config_data)

        if output_path:
            target_path: Path = Path(output_path).resolve()
        else:
            target_path = DumpPaths.get_default_dump_path(entity=self)

        # Check final determined scope
        if not (config.all_entries or config.filters_set) and not dry_run:
            msg = (
                'No profile data explicitly selected. No dump will be performed. '
                'Either select everything via `all_entries=True`, or filter via `groups`, `user`, etc.'
            )
            logger.warning(msg)
            return target_path

        engine = DumpEngine(
            base_output_path=target_path,
            config=config,
            dump_target_entity=self,
        )
        engine.dump()

        return target_path
