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

import os
import shutil

from aiida.common import json

from .options import get_option, parse_option, NO_DEFAULT
from .profile import Profile

__all__ = ('Config',)


class Config:  # pylint: disable=too-many-public-methods
    """Object that represents the configuration file of an AiiDA instance."""

    KEY_VERSION = 'CONFIG_VERSION'
    KEY_VERSION_CURRENT = 'CURRENT'
    KEY_VERSION_OLDEST_COMPATIBLE = 'OLDEST_COMPATIBLE'
    KEY_DEFAULT_PROFILE = 'default_profile'
    KEY_PROFILES = 'profiles'
    KEY_OPTIONS = 'options'

    @classmethod
    def from_file(cls, filepath):
        """Instantiate a configuration object from the contents of a given file.

        .. note:: if the filepath does not exist an empty file will be created with the default configuration.

        :param filepath: the absolute path to the configuration file
        :return: `Config` instance
        """
        from aiida.cmdline.utils import echo
        from .migrations import check_and_migrate_config, config_needs_migrating

        try:
            with open(filepath, 'r', encoding='utf8') as handle:
                config = json.load(handle)
        except (IOError, OSError):
            config = Config(filepath, check_and_migrate_config({}))
            config.store()
        else:
            # If the configuration file needs to be migrated first create a specific backup so it can easily be reverted
            if config_needs_migrating(config):
                echo.echo_warning('current configuration file `{}` is outdated and will be migrated'.format(filepath))
                filepath_backup = cls._backup(filepath)
                echo.echo_warning('original backed up to `{}`'.format(filepath_backup))

            config = Config(filepath, check_and_migrate_config(config))

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
            filepath_backup = '{}.{}'.format(filepath, timezone.now().strftime('%Y%m%d-%H%M%S.%f'))

        shutil.copy(filepath, filepath_backup)

        return filepath_backup

    def __init__(self, filepath, config):
        """Instantiate a configuration object from a configuration dictionary and its filepath.

        If an empty dictionary is passed, the constructor will create the skeleton configuration dictionary.

        :param filepath: the absolute filepath of the configuration file
        :param config: the content of the configuration file in dictionary form
        """
        from .migrations import CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION

        version = config.get(self.KEY_VERSION, {})
        current_version = version.get(self.KEY_VERSION_CURRENT, CURRENT_CONFIG_VERSION)
        compatible_version = version.get(self.KEY_VERSION_OLDEST_COMPATIBLE, OLDEST_COMPATIBLE_CONFIG_VERSION)

        self._filepath = filepath
        self._current_version = current_version
        self._oldest_compatible_version = compatible_version
        self._profiles = {}

        known_keys = [self.KEY_VERSION, self.KEY_PROFILES, self.KEY_OPTIONS, self.KEY_DEFAULT_PROFILE]
        unknown_keys = set(config.keys()) - set(known_keys)

        if unknown_keys:
            keys = ', '.join(unknown_keys)
            self.handle_invalid('encountered unknown keys [{}] in `{}` which have been removed'.format(keys, filepath))

        try:
            self._options = config[self.KEY_OPTIONS]
        except KeyError:
            self._options = {}

        try:
            self._default_profile = config[self.KEY_DEFAULT_PROFILE]
        except KeyError:
            self._default_profile = None

        for name, config_profile in config.get(self.KEY_PROFILES, {}).items():
            if Profile.contains_unknown_keys(config_profile):
                self.handle_invalid('encountered unknown keys in profile `{}` which have been removed'.format(name))
            self._profiles[name] = Profile(name, config_profile, from_config=True)

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
        echo.echo_warning('backup of the original config file written to: `{}`'.format(filepath_backup))

    @property
    def dictionary(self):
        """Return the dictionary representation of the config as it would be written to file.

        :return: dictionary representation of config as it should be written to file
        """
        config = {
            self.KEY_VERSION: self.version_settings,
            self.KEY_PROFILES: {name: profile.dictionary for name, profile in self._profiles.items()}
        }

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
    def current_profile(self):
        """Return the currently loaded profile.

        :return: the current profile or None if not defined
        """
        from . import get_profile
        return get_profile()

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
            raise exceptions.ProfileConfigurationError('profile `{}` does not exist'.format(name))

    def get_profile(self, name=None):
        """Return the profile for the given name or the default one if not specified.

        :return: the profile instance or None if it does not exist
        :raises aiida.common.ProfileConfigurationError: if the name is not found in the configuration file
        """
        from aiida.common import exceptions

        if not name and not self.default_profile_name:
            raise exceptions.ProfileConfigurationError(
                'no default profile defined: {}\n{}'.format(self._default_profile, self.dictionary)
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
        """
        option, parsed_value = parse_option(option_name, option_value)

        if parsed_value is not None:
            value = parsed_value
        elif option.default is not NO_DEFAULT:
            value = option.default
        else:
            return

        if not option.global_only and scope is not None:
            self.get_profile(scope).set_option(option.key, value, override=override)
        else:
            if option.key not in self.options or override:
                self.options[option.key] = value

    def unset_option(self, option_name, scope=None):
        """Unset a configuration option for a certain scope.

        :param option_name: the name of the configuration option
        :param scope: unset the option for this profile or globally if not specified
        """
        option = get_option(option_name)

        if scope is not None:
            self.get_profile(scope).unset_option(option.key)
        else:
            self.options.pop(option.key, None)

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
            value = self.get_profile(scope).get_option(option.key, default_value)
        else:
            value = self.options.get(option.key, default_value)

        return value

    def store(self):
        """Write the current config to file.

        .. note:: if the configuration file already exists on disk and its contents differ from those in memory, a
            backup of the original file on disk will be created before overwriting it.

        :return: self
        """
        import tempfile
        from aiida.common.files import md5_from_filelike, md5_file

        # If the filepath of this configuration does not yet exist, simply write it.
        if not os.path.isfile(self.filepath):
            with open(self.filepath, 'wb') as handle:
                self._write(handle)
            return self

        # Otherwise, we write the content to a temporary file and compare its md5 checksum with the current config on
        # disk. When the checksums differ, we first create a backup and only then overwrite the existing file.
        with tempfile.NamedTemporaryFile() as handle:
            self._write(handle)
            handle.seek(0)

            if md5_from_filelike(handle) != md5_file(self.filepath):
                self._backup(self.filepath)

            shutil.copy(handle.name, self.filepath)

        return self

    def _write(self, filelike):
        """Write the contents of `self.dictionary` to the given file handle.

        :param filelike: the filelike object to write the current configuration to
        """
        from .settings import DEFAULT_UMASK, DEFAULT_CONFIG_INDENT_SIZE

        umask = os.umask(DEFAULT_UMASK)

        try:
            json.dump(self.dictionary, filelike, indent=DEFAULT_CONFIG_INDENT_SIZE)
        finally:
            os.umask(umask)
