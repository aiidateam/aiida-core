# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module that defines the configuration file of an AiiDA instance and functions to create and load it."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import shutil

from aiida.common import json

from .migrations import CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION
from .options import get_option, parse_option, NO_DEFAULT
from .profile import Profile
from .settings import DEFAULT_UMASK, DEFAULT_CONFIG_INDENT_SIZE

__all__ = ('Config',)


class Config(object):  # pylint: disable=useless-object-inheritance
    """Object that represents the configuration file of an AiiDA instance."""

    KEY_VERSION = 'CONFIG_VERSION'
    KEY_VERSION_CURRENT = 'CURRENT'
    KEY_VERSION_OLDEST_COMPATIBLE = 'OLDEST_COMPATIBLE'
    KEY_DEFAULT_PROFILE = 'default_profile'
    KEY_PROFILES = 'profiles'

    def __init__(self, filepath, dictionary):
        """Instantiate a configuration object from a configuration dictionary and its filepath.

        If an empty dictionary is passed, the constructor will create the skeleton configuration dictionary.

        :param filepath: the absolute filepath of the configuration file
        :param dictionary: the content of the configuration file in dictionary form
        """
        if not dictionary:
            # Construct the default configuration template
            dictionary = {
                self.KEY_VERSION: {
                    self.KEY_VERSION_CURRENT: CURRENT_CONFIG_VERSION,
                    self.KEY_VERSION_OLDEST_COMPATIBLE: OLDEST_COMPATIBLE_CONFIG_VERSION,
                },
                self.KEY_PROFILES: {},
            }

        self._filepath = filepath
        self._dictionary = dictionary

    def __eq__(self, other):
        """Two configurations are considered equal, when their dictionaries are equal."""
        return self.dictionary == other.dictionary

    def __ne__(self, other):
        """Two configurations are considered unequal, when their dictionaries are unequal."""
        return self.dictionary != other.dictionary

    @property
    def dictionary(self):
        return self._dictionary

    @property
    def version(self):
        return self._version_settings.get(self.KEY_VERSION_CURRENT, 0)

    @version.setter
    def version(self, version):
        self._version_settings[self.KEY_VERSION_CURRENT] = version

    @property
    def version_oldest_compatible(self):
        return self._version_settings.get(self.KEY_VERSION_OLDEST_COMPATIBLE, 0)

    @version_oldest_compatible.setter
    def version_oldest_compatible(self, version_oldest_compatible):
        self._version_settings[self.KEY_VERSION_OLDEST_COMPATIBLE] = version_oldest_compatible

    @property
    def _version_settings(self):
        return self.dictionary.setdefault(self.KEY_VERSION, {})

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
        try:
            return self.dictionary[self.KEY_DEFAULT_PROFILE]
        except KeyError:
            return None

    @property
    def current_profile(self):
        """Return the currently loaded profile.

        :return: the current profile or None if not defined
        """
        from aiida.backends import settings

        current_profile_name = settings.AIIDADB_PROFILE

        if current_profile_name:
            return self.get_profile(current_profile_name)

        return None

    @property
    def profile_names(self):
        """Return the list of profile names.

        :return: list of profile names
        """
        try:
            profiles = self.dictionary[self.KEY_PROFILES]
        except KeyError:
            return []
        else:
            return list(profiles)

    @property
    def profiles(self):
        """Return the list of profiles.

        :return: the profiles
        :rtype: list of `Profile` instances
        """
        try:
            profiles = self.dictionary[self.KEY_PROFILES]
        except KeyError:
            return []
        else:
            return [Profile(name, profile) for name, profile in profiles.items()]

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
            raise exceptions.ProfileConfigurationError('no default profile defined')

        if not name:
            name = self.default_profile_name

        self.validate_profile(name)

        return Profile(name, self.dictionary[self.KEY_PROFILES][name])

    def _get_profile_dictionary(self, name):
        """Return the internal profile dictionary for the given name or the default one if not specified.

        :return: the profile instance or None if it does not exist
        :raises aiida.common.ProfileConfigurationError: if the name is not found in the configuration file
        """
        self.validate_profile(name)
        return self.dictionary[self.KEY_PROFILES][name]

    def add_profile(self, name, profile):
        """Add a profile to the configuration.

        :param name: the name of the profile to remove
        :param profile: the profile configuration dictionary
        :return: self
        """
        self.dictionary[self.KEY_PROFILES][name] = profile
        return self

    def update_profile(self, profile):
        """Update a profile in the configuration.

        :param profile: the profile instance to update
        :return: self
        """
        self.dictionary[self.KEY_PROFILES][profile.name] = profile.dictionary
        return self

    def remove_profile(self, name):
        """Remove a profile from the configuration.

        :param name: the name of the profile to remove
        :raises aiida.common.ProfileConfigurationError: if the given profile does not exist
        :return: self
        """
        self.validate_profile(name)
        self.dictionary[self.KEY_PROFILES].pop(name)
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
        self.dictionary[self.KEY_DEFAULT_PROFILE] = name
        return self

    def option_set(self, option_name, option_value, scope=None):
        """Set a configuration option.

        :param option_name: the name of the configuration option
        :param option_value: the option value
        :param scope: set the option for this profile or globally if not specified
        """
        option, parsed_value = parse_option(option_name, option_value)

        if scope is not None:
            dictionary = self._get_profile_dictionary(scope)
        else:
            dictionary = self.dictionary

        if parsed_value:
            dictionary[option.key] = parsed_value
        elif option.default is not NO_DEFAULT:
            dictionary[option.key] = option.default
        else:
            pass

    def option_unset(self, option_name, scope=None):
        """Unset a configuration option.

        :param option_name: the name of the configuration option
        :param scope: unset the option for this profile or globally if not specified
        """
        option = get_option(option_name)

        if scope is not None:
            dictionary = self._get_profile_dictionary(scope)
        else:
            dictionary = self.dictionary

        dictionary.pop(option.key, None)

    def option_get(self, option_name, scope=None, default=True):
        """Get a configuration option.

        :param option_name: the name of the configuration option
        :param scope: get the option for this profile or globally if not specified
        :param default: boolean, If True will return the option default, even if not defined within the given scope
        :return: the option value or None if not set for the given scope
        """
        option = get_option(option_name)

        if scope is not None:
            dictionary = self.get_profile(scope).dictionary
        else:
            dictionary = self.dictionary

        return dictionary.get(option.key, option.default if default else None)

    def store(self):
        """Write the current config to file."""
        self._backup()

        umask = os.umask(DEFAULT_UMASK)

        try:
            with io.open(self.filepath, 'wb') as handle:
                json.dump(self.dictionary, handle, indent=DEFAULT_CONFIG_INDENT_SIZE)
        finally:
            os.umask(umask)

        return self

    def _backup(self):
        """Create a backup of the current config as it exists on disk."""
        if not os.path.isfile(self.filepath):
            return

        umask = os.umask(DEFAULT_UMASK)

        try:
            shutil.copy(self.filepath, self.filepath + '~')
        finally:
            os.umask(umask)
