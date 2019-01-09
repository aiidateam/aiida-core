# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the configuration options."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.configuration import with_temporary_config_instance
from aiida.manage.configuration.options import get_option, get_option_names, parse_option, Option, CONFIG_OPTIONS
from aiida.manage.configuration import get_config, get_config_option


class TestConfigurationOptions(AiidaTestCase):
    """Tests for the Options class."""

    def test_get_option_names(self):
        """Test `get_option_names` function."""
        self.assertEqual(get_option_names(), CONFIG_OPTIONS.keys())

    def test_get_option(self):
        """Test `get_option` function."""
        with self.assertRaises(ValueError):
            get_option('no_existing_option')

        option_name = list(CONFIG_OPTIONS)[0]
        option = get_option(option_name)
        self.assertIsInstance(option, Option)
        self.assertEqual(option.name, option_name)

    def test_parse_option(self):
        """Test `parse_option` function."""

        with self.assertRaises(ValueError):
            parse_option('logging.aiida_loglevel', 1)

        with self.assertRaises(ValueError):
            parse_option('logging.aiida_loglevel', 'INVALID_LOG_LEVEL')

    def test_options(self):
        """Test that all defined options can be converted into Option namedtuples."""
        for option_name, option_settings in CONFIG_OPTIONS.items():
            option = get_option(option_name)
            self.assertEqual(option.name, option_name)
            self.assertEqual(option.key, option_settings['key'])
            self.assertEqual(option.valid_type, option_settings['valid_type'])
            self.assertEqual(option.valid_values, option_settings['valid_values'])
            self.assertEqual(option.default, option_settings['default'])
            self.assertEqual(option.description, option_settings['description'])

    @with_temporary_config_instance
    def test_get_config_option_default(self):
        """Tests that `get_option` return option default if not specified globally or for current profile."""
        option_name = 'logging.aiida_loglevel'
        option = get_option(option_name)

        # If we haven't set the option explicitly, `get_config_option` should return the option default
        option_value = get_config_option(option_name)
        self.assertEqual(option_value, option.default)

    @with_temporary_config_instance
    def test_get_config_option_profile_specific(self):
        """Tests that `get_option` correctly gets a configuration option if specified for the current profile."""
        config = get_config()
        profile = config.current_profile

        option_name = 'logging.aiida_loglevel'
        option_value_profile = 'WARNING'

        # Setting a specific value for the current profile which should then be returned by `get_config_option`
        config.option_set(option_name, option_value_profile, scope=profile.name)
        option_value = get_config_option(option_name)
        self.assertEqual(option_value, option_value_profile)

    @with_temporary_config_instance
    def test_get_config_option_global(self):
        """Tests that `get_option` correctly agglomerates upwards and so retrieves globally set config options."""
        config = get_config()

        option_name = 'logging.aiida_loglevel'
        option_value_global = 'CRITICAL'

        # Setting a specific value globally which should then be returned by `get_config_option` due to agglomeration
        config.option_set(option_name, option_value_global)
        option_value = get_config_option(option_name)
        self.assertEqual(option_value, option_value_global)
