# -*- coding: utf-8 -*-
"""Module that defines the configuration file of an AiiDA instance and functions to create and load it."""
from __future__ import absolute_import

import io
import os
import shutil

from aiida.common import exceptions
from aiida.utils import json

from .migrations import check_and_migrate_config, CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION
from .profile import Profile
from .settings import DEFAULT_CONFIG_FILE_NAME, DEFAULT_UMASK, DEFAULT_CONFIG_INDENT_SIZE

__all__ = ('load_config', 'Config')

CONFIG = None


def create_config():
    """Create the template configuration file and store it.

    :raises ConfigurationError: if a configuration file already exists
    """
    from .settings import AIIDA_CONFIG_FOLDER
    from aiida.backends.settings import IN_RT_DOC_MODE, DUMMY_CONF_FILE

    if IN_RT_DOC_MODE:
        return DUMMY_CONF_FILE

    dirpath = os.path.expanduser(AIIDA_CONFIG_FOLDER)
    filepath = os.path.join(dirpath, DEFAULT_CONFIG_FILE_NAME)

    if os.path.isfile(filepath):
        raise exceptions.ConfigurationError('configuration file {} already exists'.format(filepath))

    config = Config(filepath, {})

    return config


def load_config(create=False):
    """Instantiate the Config object representing the configuration file of the current AiiDA instance.

    :param create: when set to True, will create the configuration file if it does not already exist
    :return: the config
    :rtype: :class:`~aiida.manage.configuration.config.Config`
    :raises MissingConfigurationError: if the configuration file could not be found and create=False
    """
    from .settings import AIIDA_CONFIG_FOLDER
    from aiida.backends.settings import IN_RT_DOC_MODE, DUMMY_CONF_FILE

    if IN_RT_DOC_MODE:
        return DUMMY_CONF_FILE

    global CONFIG  # pylint: disable=global-statement

    if CONFIG is None:
        dirpath = os.path.expanduser(AIIDA_CONFIG_FOLDER)
        filepath = os.path.join(dirpath, DEFAULT_CONFIG_FILE_NAME)

        if not os.path.isfile(filepath):
            if not create:
                raise exceptions.MissingConfigurationError('configuration file {} does not exist'.format(filepath))
            else:
                config = create_config()
        else:
            try:
                with io.open(filepath, 'r', encoding='utf8') as handle:
                    config = Config(filepath, json.load(handle))
            except IOError:
                raise exceptions.ConfigurationError('configuration file {} could not be read'.format(filepath))

        CONFIG = check_and_migrate_config(config)

    return CONFIG


class Config(object):
    """Object that represents the configuration file of an AiiDA instance."""

    KEY_VERSION = 'CONFIG_VERSION'
    KEY_CURRENT = 'CURRENT'
    KEY_OLDEST_COMPATIBLE = 'OLDEST_COMPATIBLE'
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
                    self.KEY_CURRENT: CURRENT_CONFIG_VERSION,
                    self.KEY_OLDEST_COMPATIBLE: OLDEST_COMPATIBLE_CONFIG_VERSION,
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
        return self._version_settings.get(self.KEY_CURRENT, 0)

    @version.setter
    def version(self, version):
        self._version_settings[self.KEY_CURRENT] = version

    @property
    def version_oldest_compatible(self):
        return self._version_settings.get(self.KEY_OLDEST_COMPATIBLE, 0)

    @version_oldest_compatible.setter
    def version_oldest_compatible(self, version_oldest_compatible):
        self._version_settings[self.KEY_OLDEST_COMPATIBLE] = version_oldest_compatible

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
    def current_profile_name(self):
        """Return the currently configured profile name or if not set, the default profile

        :return: the default profile or None if not defined
        """
        from aiida.backends import settings
        return settings.AIIDADB_PROFILE or self.default_profile_name

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
        return self.get_profile(self.current_profile_name)

    @property
    def default_profile(self):
        """Return the default profile.

        :return: the default profile or None if not defined
        """
        return self.get_profile(self.default_profile_name)

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
            return profiles.keys()

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

    def profile_exists(self, name):
        """Return whether the profile with the given name exists.

        :param name: name of the profile:
        :return: boolean, True if the profile exists, False otherwise
        """
        return name in self.profile_names

    def validate_profile(self, name):
        """Validate that a profile exists.

        :param name: name of the profile:
        :raises ProfileConfigurationError: if the name is not found in the configuration file
        """
        if not self.profile_exists(name):
            raise exceptions.ProfileConfigurationError('profile `{}` does not exist'.format(name))

    def get_profile(self, name):
        """Return the profile for the given name or the default one if not specified.

        :return: the profile instance or None if it does not exist
        :raises ProfileConfigurationError: if the name is not found in the configuration file
        """
        self.validate_profile(name)
        return Profile(name, self.dictionary[self.KEY_PROFILES][name])

    def add_profile(self, name, profile, store=True):
        """Add a profile to the configuration.

        :param name: the name of the profile to remove
        :param profile: the profile configuration dictionary
        :param store: boolean, if True will write the updated configuration to file
        """
        self.dictionary[self.KEY_PROFILES][name] = profile

        if store:
            self.store()

    def update_profile(self, profile, store=True):
        """Update a profile in the configuration.

        :param profile: the profile instance to update
        :param store: boolean, if True will write the updated configuration to file
        """
        self.dictionary[self.KEY_PROFILES][profile.name] = profile.dictionary

        if store:
            self.store()

    def remove_profile(self, name, store=True):
        """Remove a profile from the configuration.

        :param name: the name of the profile to remove
        :param store: boolean, if True will write the updated configuration to file
        :raises ProfileConfigurationError: if the given profile does not exist
        """
        self.validate_profile(name)
        self.dictionary[self.KEY_PROFILES].pop(name)

        if store:
            self.store()

    def set_default_profile(self, name, overwrite=False, store=True):
        """Set the given profile as the new default.

        :param name: name of the profile to set as new default
        :param overwrite: when True, set the profile as the new default even if a default profile is already defined
        :param store: boolean, if True will write the updated configuration to file
        :raises ProfileConfigurationError: if the given profile does not exist
        """
        if self.default_profile_name and not overwrite:
            return

        self.validate_profile(name)
        self.dictionary[self.KEY_DEFAULT_PROFILE] = name

        if store:
            self.store()

    def store(self):
        """Write the current config to file."""
        self._backup()

        umask = os.umask(DEFAULT_UMASK)

        try:
            with io.open(self.filepath, 'wb') as handle:
                json.dump(self.dictionary, handle, indent=DEFAULT_CONFIG_INDENT_SIZE)
        finally:
            os.umask(umask)

    def _backup(self):
        """Create a backup of the current config as it exists on disk."""
        if not os.path.isfile(self.filepath):
            return

        umask = os.umask(DEFAULT_UMASK)

        try:
            shutil.copy(self.filepath, self.filepath + '~')
        finally:
            os.umask(umask)
