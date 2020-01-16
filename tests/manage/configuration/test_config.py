# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Config class."""

import os
import shutil
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions, json
from aiida.manage.configuration import Config, Profile, settings
from aiida.manage.configuration.migrations import CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION
from aiida.manage.configuration.options import get_option

from tests.utils.configuration import create_mock_profile


class TestConfigDirectory(AiidaTestCase):
    """Tests to make sure that the detection and creation of configuration folder is done correctly."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        """Save the current environment variable settings."""
        super().setUpClass(*args, **kwargs)
        cls.aiida_path_original = os.environ.get(settings.DEFAULT_AIIDA_PATH_VARIABLE, None)

    @classmethod
    def tearDownClass(cls, *args, **kwargs):
        """Restore the original environment variable settings."""
        super().tearDownClass(*args, **kwargs)
        if cls.aiida_path_original is not None:
            os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = cls.aiida_path_original
        else:
            try:
                del os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE]
            except KeyError:
                pass

    def test_environment_variable_not_set(self):
        """Check that if the environment variable is not set, config folder will be created in `DEFAULT_AIIDA_PATH`.

        To make sure we do not mess with the actual default `.aiida` folder, which often lives in the home folder
        we create a temporary directory and set the `DEFAULT_AIIDA_PATH` to it.
        """
        try:
            directory = tempfile.mkdtemp()

            # Change the default configuration folder path to temp folder instead of probably `~`.
            settings.DEFAULT_AIIDA_PATH = directory

            # Make sure that the environment variable is not set
            try:
                del os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE]
            except KeyError:
                pass
            settings.set_configuration_directory()

            config_folder = os.path.join(directory, settings.DEFAULT_CONFIG_DIR_NAME)
            self.assertTrue(os.path.isdir(config_folder))
            self.assertEqual(settings.AIIDA_CONFIG_FOLDER, config_folder)
        finally:
            shutil.rmtree(directory)

    def test_environment_variable_set_single_path_without_config_folder(self):  # pylint: disable=invalid-name
        """If `AIIDA_PATH` is set but does not contain a configuration folder, it should be created."""
        try:
            directory = tempfile.mkdtemp()

            # Set the environment variable and call configuration initialization
            env_variable = '{}'.format(directory)
            os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = env_variable
            settings.set_configuration_directory()

            # This should have created the configuration directory in the path
            config_folder = os.path.join(directory, settings.DEFAULT_CONFIG_DIR_NAME)
            self.assertTrue(os.path.isdir(config_folder))
            self.assertEqual(settings.AIIDA_CONFIG_FOLDER, config_folder)

        finally:
            shutil.rmtree(directory)

    def test_environment_variable_set_single_path_with_config_folder(self):  # pylint: disable=invalid-name
        """If `AIIDA_PATH` is set and already contains a configuration folder it should simply be used."""
        try:
            directory = tempfile.mkdtemp()
            os.makedirs(os.path.join(directory, settings.DEFAULT_CONFIG_DIR_NAME))

            # Set the environment variable and call configuration initialization
            env_variable = '{}'.format(directory)
            os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = env_variable
            settings.set_configuration_directory()

            # This should have created the configuration directory in the pathpath
            config_folder = os.path.join(directory, settings.DEFAULT_CONFIG_DIR_NAME)
            self.assertTrue(os.path.isdir(config_folder))
            self.assertEqual(settings.AIIDA_CONFIG_FOLDER, config_folder)
        finally:
            shutil.rmtree(directory)

    def test_environment_variable_path_including_config_folder(self):  # pylint: disable=invalid-name
        """If `AIIDA_PATH` is set and the path contains the base name of the config folder, it should work, i.e:

            `/home/user/.virtualenvs/dev/`
            `/home/user/.virtualenvs/dev/.aiida`

        Are both legal and will both result in the same configuration folder path.
        """
        try:
            directory = tempfile.mkdtemp()

            # Set the environment variable with a path that include base folder name and call config initialization
            env_variable = '{}'.format(os.path.join(directory, settings.DEFAULT_CONFIG_DIR_NAME))
            os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = env_variable
            settings.set_configuration_directory()

            # This should have created the configuration directory in the pathpath
            config_folder = os.path.join(directory, settings.DEFAULT_CONFIG_DIR_NAME)
            self.assertTrue(os.path.isdir(config_folder))
            self.assertEqual(settings.AIIDA_CONFIG_FOLDER, config_folder)

        finally:
            shutil.rmtree(directory)

    def test_environment_variable_set_multiple_path(self):  # pylint: disable=invalid-name
        """If `AIIDA_PATH` is set with multiple paths without actual config folder, one is created in the last."""
        try:
            directory_a = tempfile.mkdtemp()
            directory_b = tempfile.mkdtemp()
            directory_c = tempfile.mkdtemp()

            # Set the environment variable to contain three paths and call configuration initialization
            env_variable = '{}:{}:{}'.format(directory_a, directory_b, directory_c)
            os.environ[settings.DEFAULT_AIIDA_PATH_VARIABLE] = env_variable
            settings.set_configuration_directory()

            # This should have created the configuration directory in the last path
            config_folder = os.path.join(directory_c, settings.DEFAULT_CONFIG_DIR_NAME)
            self.assertTrue(os.path.isdir(config_folder))
            self.assertEqual(settings.AIIDA_CONFIG_FOLDER, config_folder)

        finally:
            shutil.rmtree(directory_a)
            shutil.rmtree(directory_b)
            shutil.rmtree(directory_c)


class TestConfig(AiidaTestCase):
    """Tests for the Config class."""

    def setUp(self):
        """Setup a mock config."""
        super().setUp()
        self.profile_name = 'test_profile'
        self.profile = create_mock_profile(self.profile_name)
        self.config_filebase = tempfile.mkdtemp()
        self.config_filename = 'config.json'
        self.config_filepath = os.path.join(self.config_filebase, self.config_filename)
        self.config_dictionary = {
            Config.KEY_VERSION: {
                Config.KEY_VERSION_CURRENT: CURRENT_CONFIG_VERSION,
                Config.KEY_VERSION_OLDEST_COMPATIBLE: OLDEST_COMPATIBLE_CONFIG_VERSION,
            },
            Config.KEY_PROFILES: {
                self.profile_name: self.profile.dictionary
            },
        }

    def tearDown(self):
        """Clean the temporary folder."""
        super().tearDown()
        if self.config_filebase and os.path.isdir(self.config_filebase):
            shutil.rmtree(self.config_filebase)

    def test_basic_properties(self):
        """Test the basic properties of the Config class."""
        config = Config(self.config_filepath, self.config_dictionary)

        self.assertEqual(config.filepath, self.config_filepath)
        self.assertEqual(config.dirpath, self.config_filebase)
        self.assertEqual(config.version, CURRENT_CONFIG_VERSION)
        self.assertEqual(config.version_oldest_compatible, OLDEST_COMPATIBLE_CONFIG_VERSION)
        self.assertEqual(config.dictionary, self.config_dictionary)

    def test_setting_versions(self):
        """Test the version setters."""
        config = Config(self.config_filepath, self.config_dictionary)

        self.assertEqual(config.version, CURRENT_CONFIG_VERSION)
        self.assertEqual(config.version_oldest_compatible, OLDEST_COMPATIBLE_CONFIG_VERSION)

        new_config_version = 1000
        new_compatible_version = 999

        config.version = new_config_version
        config.version_oldest_compatible = new_compatible_version

        self.assertEqual(config.version, new_config_version)
        self.assertEqual(config.version_oldest_compatible, new_compatible_version)

    def test_construct_empty_dictionary(self):
        """Constructing with empty dictionary should create basic skeleton."""
        config = Config(self.config_filepath, {})

        self.assertTrue(Config.KEY_PROFILES in config.dictionary)
        self.assertTrue(Config.KEY_VERSION in config.dictionary)
        self.assertTrue(Config.KEY_VERSION_CURRENT in config.dictionary[Config.KEY_VERSION])
        self.assertTrue(Config.KEY_VERSION_OLDEST_COMPATIBLE in config.dictionary[Config.KEY_VERSION])

    def test_default_profile(self):
        """Test setting and getting default profile."""
        config = Config(self.config_filepath, self.config_dictionary)

        # If not set should return None
        self.assertEqual(config.default_profile_name, None)

        # Setting it to a profile that does not exist should raise
        with self.assertRaises(exceptions.ProfileConfigurationError):
            config.set_default_profile('non_existing_profile')

        # After setting a default profile, it should return the right name
        config.add_profile(create_mock_profile(self.profile_name))
        config.set_default_profile(self.profile_name)
        self.assertTrue(config.default_profile_name, self.profile_name)

        # Setting it when a default is already set, should not overwrite by default
        alternative_profile_name = 'alternative_profile_name'
        config.add_profile(create_mock_profile(alternative_profile_name))
        config.set_default_profile(self.profile_name)
        self.assertTrue(config.default_profile_name, self.profile_name)

        # But with overwrite=True it should
        config.set_default_profile(self.profile_name, overwrite=True)
        self.assertTrue(config.default_profile_name, alternative_profile_name)

    def test_profiles(self):
        """Test the properties related to retrieving, creating, updating and removing profiles."""
        config = Config(self.config_filepath, self.config_dictionary)

        # Each item returned by config.profiles should be a Profile instance
        for profile in config.profiles:
            self.assertIsInstance(profile, Profile)
            self.assertTrue(profile.dictionary, self.config_dictionary[Config.KEY_PROFILES][profile.name])

        # The profile_names property should return the keys of the profiles dictionary
        self.assertEqual(config.profile_names, list(self.config_dictionary[Config.KEY_PROFILES]))

        # Test get_profile
        self.assertEqual(config.get_profile(self.profile_name).dictionary, self.profile.dictionary)

        # Update a profile
        updated_profile = create_mock_profile(self.profile_name)
        config.update_profile(updated_profile)
        self.assertEqual(config.get_profile(self.profile_name).dictionary, updated_profile.dictionary)

        # Removing an unexisting profile should raise
        with self.assertRaises(exceptions.ProfileConfigurationError):
            config.remove_profile('non_existing_profile')

        # Removing an existing should work and in this test case none should remain
        config.remove_profile(self.profile_name)
        self.assertEqual(config.profiles, [])
        self.assertEqual(config.profile_names, [])

    def test_option(self):
        """Test the setter, unsetter and getter of configuration options."""
        option_value = 131
        option_name = 'daemon.timeout'
        option = get_option(option_name)
        config = Config(self.config_filepath, self.config_dictionary)

        # Getting option that does not exist, should simply return the option default
        self.assertEqual(config.get_option(option_name, scope=self.profile_name), option.default)
        self.assertEqual(config.get_option(option_name, scope=None), option.default)

        # Unless we set default=False, in which case it should return None
        self.assertEqual(config.get_option(option_name, scope=self.profile_name, default=False), None)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), None)

        # Setting an option profile configuration wide
        config.set_option(option_name, option_value)

        # Getting configuration wide should get new value but None for profile specific
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value)
        self.assertEqual(config.get_option(option_name, scope=self.profile_name, default=False), None)

        # Setting an option profile specific
        config.set_option(option_name, option_value, scope=self.profile_name)
        self.assertEqual(config.get_option(option_name, scope=self.profile_name), option_value)

        # Unsetting profile specific
        config.unset_option(option_name, scope=self.profile_name)
        self.assertEqual(config.get_option(option_name, scope=self.profile_name, default=False), None)

        # Unsetting configuration wide
        config.unset_option(option_name, scope=None)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), None)
        self.assertEqual(config.get_option(option_name, scope=None, default=True), option.default)

        # Setting a `None` like option
        option_value = 0
        config.set_option(option_name, option_value)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value)

    def test_option_global_only(self):
        """Test that `global_only` options are only set globally even if a profile specific scope is set."""
        option_name = 'user.email'
        option_value = 'some@email.com'

        config = Config(self.config_filepath, self.config_dictionary)

        # Setting an option globally should be fine
        config.set_option(option_name, option_value, scope=None)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value)

        # Setting an option profile specific should actually not set it on the profile since it is `global_only`
        config.set_option(option_name, option_value, scope=None)
        self.assertEqual(config.get_option(option_name, scope=self.profile_name, default=False), None)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value)

    def test_set_option_override(self):
        """Test that `global_only` options are only set globally even if a profile specific scope is set."""
        option_name = 'user.email'
        option_value_one = 'first@email.com'
        option_value_two = 'second@email.com'

        config = Config(self.config_filepath, self.config_dictionary)

        # Setting an option if it does not exist should work
        config.set_option(option_name, option_value_one)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value_one)

        # Setting it again will override it by default
        config.set_option(option_name, option_value_two)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value_two)

        # If we set override to False, it should not override, big surprise
        config.set_option(option_name, option_value_one, override=False)
        self.assertEqual(config.get_option(option_name, scope=None, default=False), option_value_two)

    def test_store(self):
        """Test that the store method writes the configuration properly to disk."""
        config = Config(self.config_filepath, self.config_dictionary)
        config.store()

        with open(config.filepath, 'r') as handle:
            config_recreated = Config(config.filepath, json.load(handle))

            self.assertEqual(config.dictionary, config_recreated.dictionary)
