# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the Config class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import shutil
import tempfile

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import create_mock_profile
from aiida.common import exceptions
from aiida.manage.configuration import Config, Profile
from aiida.manage.configuration.migrations import CURRENT_CONFIG_VERSION, OLDEST_COMPATIBLE_CONFIG_VERSION
from aiida.manage.configuration.options import get_option
from aiida.common import json


class TestConfig(AiidaTestCase):
    """Tests for the Config class."""

    def setUp(self):
        """Setup a mock config."""
        super(TestConfig, self).setUp()
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
                self.profile_name: self.profile
            },
        }

    def tearDown(self):
        """Clean the temporary folder."""
        super(TestConfig, self).tearDown()
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
        config.add_profile(self.profile_name, create_mock_profile(self.profile_name))
        config.set_default_profile(self.profile_name)
        self.assertTrue(config.default_profile_name, self.profile_name)

        # Setting it when a default is already set, should not overwrite by default
        alternative_profile_name = 'alterantive_profile_name'
        config.add_profile(alternative_profile_name, create_mock_profile(alternative_profile_name))
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
        profile = Profile(self.profile_name, self.profile)
        self.assertEqual(config.get_profile(self.profile_name).dictionary, profile.dictionary)

        # Update a profile
        updated_profile = Profile(self.profile_name, create_mock_profile(self.profile_name))
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
        self.assertEqual(config.option_get(option_name, scope=self.profile_name), option.default)
        self.assertEqual(config.option_get(option_name, scope=None), option.default)

        # Unless we set default=False, in which case it should return None
        self.assertEqual(config.option_get(option_name, scope=self.profile_name, default=False), None)
        self.assertEqual(config.option_get(option_name, scope=None, default=False), None)

        # Setting an option profile configuration wide
        config.option_set(option_name, option_value)

        # Getting configuration wide should get new value but None for profile specific
        self.assertEqual(config.option_get(option_name, scope=None, default=False), option_value)
        self.assertEqual(config.option_get(option_name, scope=self.profile_name, default=False), None)

        # Setting an option profile specific
        config.option_set(option_name, option_value, scope=self.profile_name)
        self.assertEqual(config.option_get(option_name, scope=self.profile_name), option_value)

        # Unsetting profile specific
        config.option_unset(option_name, scope=self.profile_name)
        self.assertEqual(config.option_get(option_name, scope=self.profile_name, default=False), None)

        # Unsetting configuration wide
        config.option_unset(option_name, scope=None)
        self.assertEqual(config.option_get(option_name, scope=None, default=False), None)
        self.assertEqual(config.option_get(option_name, scope=None, default=True), option.default)

    def test_store(self):
        """Test that the store method writes the configuration properly to disk."""
        config = Config(self.config_filepath, self.config_dictionary)
        config.store()

        with open(config.filepath, 'r') as handle:
            config_recreated = Config(config.filepath, json.load(handle))

            self.assertEqual(config.dictionary, config_recreated.dictionary)
