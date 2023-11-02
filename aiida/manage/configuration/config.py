# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines the configuration file of an AiiDA instance and functions to create and load it.

Despite the import of the annotations backport below which enables postponed type annotation evaluation as implemented
with PEP 563 (https://peps.python.org/pep-0563/), this is not compatible with ``pydantic`` for Python 3.9 and older (
See https://github.com/pydantic/pydantic/issues/2678 for details).
"""
from __future__ import annotations

import codecs
import json
import os
from typing import Any, Dict, List, Optional, Tuple
import uuid

from pydantic import (  # pylint: disable=no-name-in-module
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_serializer,
    field_validator,
)

from aiida.common.exceptions import ConfigurationError
from aiida.common.log import LogLevels

from .options import Option, get_option, get_option_names, parse_option
from .profile import Profile

__all__ = ('Config',)


class ConfigVersionSchema(BaseModel, defer_build=True):
    """Schema for the version configuration of an AiiDA instance."""

    CURRENT: int
    OLDEST_COMPATIBLE: int


class ProfileOptionsSchema(BaseModel, defer_build=True):
    """Schema for the options of an AiiDA profile."""

    model_config = ConfigDict(use_enum_values=True)

    runner__poll__interval: int = Field(60, description='Polling interval in seconds to be used by process runners.')
    daemon__default_workers: int = Field(
        1, description='Default number of workers to be launched by `verdi daemon start`.'
    )
    daemon__timeout: int = Field(
        2,
        description=
        'Used to set default timeout in the :class:`aiida.engine.daemon.client.DaemonClient` for calls to the daemon.'
    )
    daemon__worker_process_slots: int = Field(
        200, description='Maximum number of concurrent process tasks that each daemon worker can handle.'
    )
    daemon__recursion_limit: int = Field(3000, description='Maximum recursion depth for the daemon workers.')
    db__batch_size: int = Field(
        100000,
        description='Batch size for bulk CREATE operations in the database. Avoids hitting MaxAllocSize of PostgreSQL '
        '(1GB) when creating large numbers of database records in one go.'
    )
    verdi__shell__auto_import: str = Field(
        ':',
        description='Additional modules/functions/classes to be automatically loaded in `verdi shell`, split by `:`.'
    )
    logging__aiida_loglevel: LogLevels = Field(
        'REPORT', description='Minimum level to log to daemon log and the `DbLog` table for the `aiida` logger.'
    )
    logging__verdi_loglevel: LogLevels = Field(
        'REPORT', description='Minimum level to log to console when running a `verdi` command.'
    )
    logging__db_loglevel: LogLevels = Field('REPORT', description='Minimum level to log to the DbLog table.')
    logging__plumpy_loglevel: LogLevels = Field(
        'WARNING', description='Minimum level to log to daemon log and the `DbLog` table for the `plumpy` logger.'
    )
    logging__kiwipy_loglevel: LogLevels = Field(
        'WARNING', description='Minimum level to log to daemon log and the `DbLog` table for the `kiwipy` logger'
    )
    logging__paramiko_loglevel: LogLevels = Field(
        'WARNING', description='Minimum level to log to daemon log and the `DbLog` table for the `paramiko` logger'
    )
    logging__alembic_loglevel: LogLevels = Field(
        'WARNING', description='Minimum level to log to daemon log and the `DbLog` table for the `alembic` logger'
    )
    logging__sqlalchemy_loglevel: LogLevels = Field(
        'WARNING', description='Minimum level to log to daemon log and the `DbLog` table for the `sqlalchemy` logger'
    )
    logging__circus_loglevel: LogLevels = Field(
        'INFO', description='Minimum level to log to daemon log and the `DbLog` table for the `circus` logger'
    )
    logging__aiopika_loglevel: LogLevels = Field(
        'WARNING', description='Minimum level to log to daemon log and the `DbLog` table for the `aiopika` logger'
    )
    warnings__showdeprecations: bool = Field(True, description='Whether to print AiiDA deprecation warnings.')
    warnings__rabbitmq_version: bool = Field(
        True, description='Whether to print a warning when an incompatible version of RabbitMQ is configured.'
    )
    transport__task_retry_initial_interval: int = Field(
        20, description='Initial time interval for the exponential backoff mechanism.'
    )
    transport__task_maximum_attempts: int = Field(
        5, description='Maximum number of transport task attempts before a Process is Paused.'
    )
    rmq__task_timeout: int = Field(10, description='Timeout in seconds for communications with RabbitMQ.')
    storage__sandbox: Optional[str] = Field(
        None, description='Absolute path to the directory to store sandbox folders.'
    )
    caching__default_enabled: bool = Field(False, description='Enable calculation caching by default.')
    caching__enabled_for: List[str] = Field([], description='Calculation entry points to enable caching on.')
    caching__disabled_for: List[str] = Field([], description='Calculation entry points to disable caching on.')

    @field_validator('caching__enabled_for', 'caching__disabled_for')
    @classmethod
    def validate_caching_identifier_pattern(cls, value: List[str]) -> List[str]:
        """Validate the caching identifier patterns."""
        from aiida.manage.caching import _validate_identifier_pattern
        for identifier in value:
            _validate_identifier_pattern(identifier=identifier)

        return value


class GlobalOptionsSchema(ProfileOptionsSchema, defer_build=True):
    """Schema for the global options of an AiiDA instance."""
    autofill__user__email: Optional[str] = Field(
        None, description='Default user email to use when creating new profiles.'
    )
    autofill__user__first_name: Optional[str] = Field(
        None, description='Default user first name to use when creating new profiles.'
    )
    autofill__user__last_name: Optional[str] = Field(
        None, description='Default user last name to use when creating new profiles.'
    )
    autofill__user__institution: Optional[str] = Field(
        None, description='Default user institution to use when creating new profiles.'
    )
    rest_api__profile_switching: bool = Field(
        False, description='Toggle whether the profile can be specified in requests submitted to the REST API.'
    )
    warnings__development_version: bool = Field(
        True,
        description='Whether to print a warning when a profile is loaded while a development version is installed.'
    )


class ProfileStorageConfig(BaseModel, defer_build=True):
    """Schema for the storage backend configuration of an AiiDA profile."""

    backend: str
    config: Dict[str, Any]


class ProcessControlConfig(BaseModel, defer_build=True):
    """Schema for the process control configuration of an AiiDA profile."""

    broker_protocol: str = Field('amqp', description='Protocol for connecting to the message broker.')
    broker_username: str = Field('guest', description='Username for message broker authentication.')
    broker_password: str = Field('guest', description='Password for message broker.')
    broker_host: str = Field('127.0.0.1', description='Hostname of the message broker.')
    broker_port: int = Field(5432, description='Port of the message broker.')
    broker_virtual_host: str = Field('', description='Virtual host to use for the message broker.')
    broker_parameters: dict[
        str, Any] = Field(default_factory=dict, description='Arguments to be encoded as query parameters.')


class ProfileSchema(BaseModel, defer_build=True):
    """Schema for the configuration of an AiiDA profile."""

    uuid: str = Field(description='A UUID that uniquely identifies the profile.', default_factory=uuid.uuid4)
    storage: ProfileStorageConfig
    process_control: ProcessControlConfig
    default_user_email: Optional[str] = None
    test_profile: bool = False
    options: Optional[ProfileOptionsSchema] = None

    @field_serializer('uuid')
    def serialize_dt(self, value: uuid.UUID, _info):
        return str(value)


class ConfigSchema(BaseModel, defer_build=True):
    """Schema for the configuration of an AiiDA instance."""

    CONFIG_VERSION: Optional[ConfigVersionSchema] = None
    profiles: Optional[dict[str, ProfileSchema]] = None
    options: Optional[GlobalOptionsSchema] = None
    default_profile: Optional[str] = None


class Config:  # pylint: disable=too-many-public-methods
    """Object that represents the configuration file of an AiiDA instance."""

    KEY_VERSION = 'CONFIG_VERSION'
    KEY_VERSION_CURRENT = 'CURRENT'
    KEY_VERSION_OLDEST_COMPATIBLE = 'OLDEST_COMPATIBLE'
    KEY_DEFAULT_PROFILE = 'default_profile'
    KEY_PROFILES = 'profiles'
    KEY_OPTIONS = 'options'
    KEY_SCHEMA = '$schema'

    @classmethod
    def from_file(cls, filepath):
        """Instantiate a configuration object from the contents of a given file.

        .. note:: if the filepath does not exist an empty file will be created with the current default configuration
            and will be written to disk. If the filepath does already exist but contains a configuration with an
            outdated schema, the content will be migrated and then written to disk.

        :param filepath: the absolute path to the configuration file
        :return: `Config` instance
        """
        from aiida.cmdline.utils import echo

        from .migrations import check_and_migrate_config, config_needs_migrating

        try:
            with open(filepath, 'rb') as handle:
                config = json.load(handle)
        except FileNotFoundError:
            config = Config(filepath, check_and_migrate_config({}))
            config.store()
        else:
            migrated = False

            # If the configuration file needs to be migrated first create a specific backup so it can easily be reverted
            if config_needs_migrating(config, filepath):
                migrated = True
                echo.echo_warning(f'current configuration file `{filepath}` is outdated and will be migrated')
                filepath_backup = cls._backup(filepath)
                echo.echo_warning(f'original backed up to `{filepath_backup}`')

            config = Config(filepath, check_and_migrate_config(config))

            if migrated:
                config.store()

        return config

    @classmethod
    def _backup(cls, filepath):
        """Create a backup of the configuration file with the given filepath.

        :param filepath: absolute path to the configuration file to backup
        :return: the absolute path of the created backup
        """
        import shutil

        from aiida.common import timezone

        filepath_backup = None

        # Keep generating a new backup filename based on the current time until it does not exist
        while not filepath_backup or os.path.isfile(filepath_backup):
            filepath_backup = f"{filepath}.{timezone.now().strftime('%Y%m%d-%H%M%S.%f')}"

        shutil.copy(filepath, filepath_backup)

        return filepath_backup

    @staticmethod
    def validate(config: dict, filepath: Optional[str] = None):
        """Validate a configuration dictionary."""
        try:
            ConfigSchema(**config)
        except ValidationError as exception:
            raise ConfigurationError(f'invalid config schema: {filepath}: {str(exception)}')

    def __init__(self, filepath: str, config: dict, validate: bool = True):
        """Instantiate a configuration object from a configuration dictionary and its filepath.

        If an empty dictionary is passed, the constructor will create the skeleton configuration dictionary.

        :param filepath: the absolute filepath of the configuration file
        :param config: the content of the configuration file in dictionary form
        :param validate: validate the dictionary against the schema
        """
        from .migrations import CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION

        if validate:
            self.validate(config, filepath)

        self._filepath = filepath
        self._schema = config.get(self.KEY_SCHEMA, None)
        version = config.get(self.KEY_VERSION, {})
        self._current_version = version.get(self.KEY_VERSION_CURRENT, CURRENT_CONFIG_VERSION)
        self._oldest_compatible_version = version.get(
            self.KEY_VERSION_OLDEST_COMPATIBLE, OLDEST_COMPATIBLE_CONFIG_VERSION
        )
        self._profiles = {}

        known_keys = [self.KEY_SCHEMA, self.KEY_VERSION, self.KEY_PROFILES, self.KEY_OPTIONS, self.KEY_DEFAULT_PROFILE]
        unknown_keys = set(config.keys()) - set(known_keys)

        if unknown_keys:
            keys = ', '.join(unknown_keys)
            self.handle_invalid(f'encountered unknown keys [{keys}] in `{filepath}` which have been removed')

        try:
            self._options = config[self.KEY_OPTIONS]
        except KeyError:
            self._options = {}

        try:
            self._default_profile = config[self.KEY_DEFAULT_PROFILE]
        except KeyError:
            self._default_profile = None

        for name, config_profile in config.get(self.KEY_PROFILES, {}).items():
            self._profiles[name] = Profile(name, config_profile)

    def __eq__(self, other):
        """Two configurations are considered equal, when their dictionaries are equal."""
        return self.dictionary == other.dictionary

    def __ne__(self, other):
        """Two configurations are considered unequal, when their dictionaries are unequal."""
        return self.dictionary != other.dictionary

    def handle_invalid(self, message):
        """Handle an incoming invalid configuration dictionary.

        The current content of the configuration file will be written to a backup file.

        :param message: a string message to echo with describing the infraction
        """
        from aiida.cmdline.utils import echo
        filepath_backup = self._backup(self.filepath)
        echo.echo_warning(message)
        echo.echo_warning(f'backup of the original config file written to: `{filepath_backup}`')

    @property
    def dictionary(self) -> dict:
        """Return the dictionary representation of the config as it would be written to file.

        :return: dictionary representation of config as it should be written to file
        """
        config = {}
        if self._schema:
            config[self.KEY_SCHEMA] = self._schema

        config[self.KEY_VERSION] = self.version_settings
        config[self.KEY_PROFILES] = {name: profile.dictionary for name, profile in self._profiles.items()}

        if self._default_profile:
            config[self.KEY_DEFAULT_PROFILE] = self._default_profile

        if self._options:
            config[self.KEY_OPTIONS] = self._options

        return config

    @property
    def version(self):
        return self._current_version

    @version.setter
    def version(self, version):
        self._current_version = version

    @property
    def version_oldest_compatible(self):
        return self._oldest_compatible_version

    @version_oldest_compatible.setter
    def version_oldest_compatible(self, version_oldest_compatible):
        self._oldest_compatible_version = version_oldest_compatible

    @property
    def version_settings(self):
        return {
            self.KEY_VERSION_CURRENT: self.version,
            self.KEY_VERSION_OLDEST_COMPATIBLE: self.version_oldest_compatible
        }

    @property
    def filepath(self):
        return self._filepath

    @property
    def dirpath(self):
        return os.path.dirname(self.filepath)

    @property
    def default_profile_name(self):
        """Return the default profile name.

        :return: the default profile name or None if not defined
        """
        return self._default_profile

    @property
    def profile_names(self):
        """Return the list of profile names.

        :return: list of profile names
        """
        return list(self._profiles.keys())

    @property
    def profiles(self):
        """Return the list of profiles.

        :return: the profiles
        :rtype: list of `Profile` instances
        """
        return list(self._profiles.values())

    def validate_profile(self, name):
        """Validate that a profile exists.

        :param name: name of the profile:
        :raises aiida.common.ProfileConfigurationError: if the name is not found in the configuration file
        """
        from aiida.common import exceptions

        if name not in self.profile_names:
            raise exceptions.ProfileConfigurationError(f'profile `{name}` does not exist')

    def get_profile(self, name: Optional[str] = None) -> Profile:
        """Return the profile for the given name or the default one if not specified.

        :return: the profile instance or None if it does not exist
        :raises aiida.common.ProfileConfigurationError: if the name is not found in the configuration file
        """
        from aiida.common import exceptions

        if not name and not self.default_profile_name:
            raise exceptions.ProfileConfigurationError(
                f'no default profile defined: {self._default_profile}\n{self.dictionary}'
            )

        if not name:
            name = self.default_profile_name

        self.validate_profile(name)

        return self._profiles[name]

    def add_profile(self, profile):
        """Add a profile to the configuration.

        :param profile: the profile configuration dictionary
        :return: self
        """
        self._profiles[profile.name] = profile
        return self

    def update_profile(self, profile):
        """Update a profile in the configuration.

        :param profile: the profile instance to update
        :return: self
        """
        self._profiles[profile.name] = profile
        return self

    def remove_profile(self, name):
        """Remove a profile from the configuration.

        :param name: the name of the profile to remove
        :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
        :return: self
        """
        self.validate_profile(name)
        self._profiles.pop(name)
        return self

    def delete_profile(
        self,
        name: str,
        include_database: bool = True,
        include_database_user: bool = False,
        include_repository: bool = True
    ):
        """Delete a profile including its storage.

        :param include_database: also delete the database configured for the profile.
        :param include_database_user: also delete the database user configured for the profile.
        :param include_repository: also delete the repository configured for the profile.
        """
        import shutil

        from aiida.manage.external.postgres import Postgres

        profile = self.get_profile(name)

        if include_repository:
            # Note, this is currently being hardcoded, but really this `delete_profile` should get the storage backend
            # for the given profile and call `StorageBackend.erase` method. Currently this is leaking details
            # of the implementation of the PsqlDosBackend into a generic function which would fail for profiles that
            # use a different storage backend implementation.
            from aiida.storage.psql_dos.backend import get_filepath_container
            folder = get_filepath_container(profile).parent
            if folder.exists():
                shutil.rmtree(folder)

        if include_database:
            postgres = Postgres.from_profile(profile)
            if postgres.db_exists(profile.storage_config['database_name']):
                postgres.drop_db(profile.storage_config['database_name'])

        if include_database_user and postgres.dbuser_exists(profile.storage_config['database_username']):
            postgres.drop_dbuser(profile.storage_config['database_username'])

        self.remove_profile(name)
        self.store()

    def set_default_profile(self, name, overwrite=False):
        """Set the given profile as the new default.

        :param name: name of the profile to set as new default
        :param overwrite: when True, set the profile as the new default even if a default profile is already defined
        :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
        :return: self
        """
        if self.default_profile_name and not overwrite:
            return self

        self.validate_profile(name)
        self._default_profile = name
        return self

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, value):
        self._options = value

    def set_option(self, option_name, option_value, scope=None, override=True):
        """Set a configuration option for a certain scope.

        :param option_name: the name of the configuration option
        :param option_value: the option value
        :param scope: set the option for this profile or globally if not specified
        :param override: boolean, if False, will not override the option if it already exists

        :returns: the parsed value (potentially cast to a valid type)
        """
        option, parsed_value = parse_option(option_name, option_value)

        if parsed_value is not None:
            value = parsed_value
        elif option.default is not None:
            value = option.default
        else:
            return

        if not option.global_only and scope is not None:
            self.get_profile(scope).set_option(option.name, value, override=override)
        else:
            if option.name not in self.options or override:
                self.options[option.name] = value

        return value

    def unset_option(self, option_name: str, scope=None):
        """Unset a configuration option for a certain scope.

        :param option_name: the name of the configuration option
        :param scope: unset the option for this profile or globally if not specified
        """
        option = get_option(option_name)

        if scope is not None:
            self.get_profile(scope).unset_option(option.name)
        else:
            self.options.pop(option.name, None)

    def get_option(self, option_name, scope=None, default=True):
        """Get a configuration option for a certain scope.

        :param option_name: the name of the configuration option
        :param scope: get the option for this profile or globally if not specified
        :param default: boolean, If True will return the option default, even if not defined within the given scope
        :return: the option value or None if not set for the given scope
        """
        option = get_option(option_name)
        default_value = option.default if default else None

        if scope is not None:
            value = self.get_profile(scope).get_option(option.name, default_value)
        else:
            value = self.options.get(option.name, default_value)

        return value

    def get_options(self, scope: Optional[str] = None) -> Dict[str, Tuple[Option, str, Any]]:
        """Return a dictionary of all option values and their source ('profile', 'global', or 'default').

        :param scope: the profile name or globally if not specified
        :returns: (option, source, value)
        """
        profile = self.get_profile(scope) if scope else None
        output = {}
        for name in get_option_names():
            option = get_option(name)
            if profile and name in profile.options:
                value = profile.options.get(name)
                source = 'profile'
            elif name in self.options:
                value = self.options.get(name)
                source = 'global'
            elif option.default is not None:
                value = option.default
                source = 'default'
            else:
                continue
            output[name] = (option, source, value)
        return output

    def store(self):
        """Write the current config to file.

        .. note:: if the configuration file already exists on disk and its contents differ from those in memory, a
            backup of the original file on disk will be created before overwriting it.

        :return: self
        """
        import tempfile

        from aiida.common.files import md5_file, md5_from_filelike

        from .settings import DEFAULT_CONFIG_INDENT_SIZE

        # If the filepath of this configuration does not yet exist, simply write it.
        if not os.path.isfile(self.filepath):
            self._atomic_write()
            return self

        # Otherwise, we write the content to a temporary file and compare its md5 checksum with the current config on
        # disk. When the checksums differ, we first create a backup and only then overwrite the existing file.
        with tempfile.NamedTemporaryFile() as handle:
            json.dump(self.dictionary, codecs.getwriter('utf-8')(handle), indent=DEFAULT_CONFIG_INDENT_SIZE)
            handle.seek(0)

            if md5_from_filelike(handle) != md5_file(self.filepath):
                self._backup(self.filepath)

        self._atomic_write()

        return self

    def _atomic_write(self, filepath=None):
        """Write the config as it is in memory, i.e. the contents of ``self.dictionary``, to disk.

        .. note:: this command will write the config from memory to a temporary file in the same directory as the
            target file ``filepath``. It will then use ``os.rename`` to move the temporary file to ``filepath`` which
            will be overwritten if it already exists. The ``os.rename`` is the operation that gives the best guarantee
            of being atomic within the limitations of the application.

        :param filepath: optional filepath to write the contents to, if not specified, the default filename is used.
        """
        import tempfile

        from .settings import DEFAULT_CONFIG_INDENT_SIZE, DEFAULT_UMASK

        umask = os.umask(DEFAULT_UMASK)

        if filepath is None:
            filepath = self.filepath

        # Create a temporary file in the same directory as the target filepath, which guarantees that the temporary
        # file is on the same filesystem, which is necessary to be able to use ``os.rename``. Since we are moving the
        # temporary file, we should also tell the tempfile to not be automatically deleted as that will raise.
        with tempfile.NamedTemporaryFile(dir=os.path.dirname(filepath), delete=False, mode='w') as handle:
            try:
                json.dump(self.dictionary, handle, indent=DEFAULT_CONFIG_INDENT_SIZE)
            finally:
                os.umask(umask)

            handle.flush()
            os.rename(handle.name, self.filepath)
