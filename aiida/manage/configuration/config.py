# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines the configuration file of an AiiDA instance and functions to create and load it."""
import codecs
from functools import lru_cache

try:
    # Python <= 3.8
    from importlib_resources import files
except ImportError:
    from importlib.resources import files

import json
import os
import shutil
import tempfile
from typing import Any, Dict, Optional, Sequence, Tuple

import jsonschema

from aiida.common.exceptions import ConfigurationError

from . import schema as schema_module
from .options import NO_DEFAULT, Option, get_option, get_option_names, parse_option
from .profile import Profile

__all__ = ('Config', 'config_schema', 'ConfigValidationError')

SCHEMA_FILE = 'config-v9.schema.json'


@lru_cache(1)
def config_schema() -> Dict[str, Any]:
    """Return the configuration schema."""
    return json.loads(files(schema_module).joinpath(SCHEMA_FILE).read_text(encoding='utf8'))


class ConfigValidationError(ConfigurationError):
    """Configuration error raised when the file contents fails validation."""

    def __init__(
        self, message: str, keypath: Sequence[Any] = (), schema: Optional[dict] = None, filepath: Optional[str] = None
    ):
        super().__init__(message)
        self._message = message
        self._keypath = keypath
        self._filepath = filepath
        self._schema = schema

    def __str__(self) -> str:
        prefix = f'{self._filepath}:' if self._filepath else ''
        path = '/' + '/'.join(str(k) for k in self._keypath) + ': ' if self._keypath else ''
        schema = f'\n  schema:\n  {self._schema}' if self._schema else ''
        return f'Validation Error: {prefix}{path}{self._message}{schema}'


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
            jsonschema.validate(instance=config, schema=config_schema())
        except jsonschema.ValidationError as error:
            raise ConfigValidationError(
                message=error.message, keypath=error.path, schema=error.schema, filepath=filepath
            )

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
        elif option.default is not NO_DEFAULT:
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

        # Default value is `None` unless `default=True` and the `option.default` is not `NO_DEFAULT`
        default_value = option.default if default and option.default is not NO_DEFAULT else None

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
            elif 'default' in option.schema:
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
