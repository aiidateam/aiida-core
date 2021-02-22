# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the configuration options."""
import pytest

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import ConfigurationError
from aiida.manage.configuration.options import get_option, get_option_names, parse_option, Option
from aiida.manage.configuration import get_config, get_config_option, ConfigValidationError


class TestConfigurationOptions(AiidaTestCase):
    """Tests for the Options class."""

    def test_get_option_names(self):
        """Test `get_option_names` function."""
        self.assertIsInstance(get_option_names(), list)
        self.assertEqual(len(get_option_names()), 26)

    def test_get_option(self):
        """Test `get_option` function."""
        with self.assertRaises(ConfigurationError):
            get_option('no_existing_option')

        option_name = get_option_names()[0]
        option = get_option(option_name)
        self.assertIsInstance(option, Option)
        self.assertEqual(option.name, option_name)

    def test_parse_option(self):
        """Test `parse_option` function."""

        with self.assertRaises(ConfigValidationError):
            parse_option('logging.aiida_loglevel', 1)

        with self.assertRaises(ConfigValidationError):
            parse_option('logging.aiida_loglevel', 'INVALID_LOG_LEVEL')

    def test_options(self):
        """Test that all defined options can be converted into Option namedtuples."""
        for option_name in get_option_names():
            option = get_option(option_name)
            self.assertEqual(option.name, option_name)
            self.assertIsInstance(option.description, str)
            option.valid_type  # pylint: disable=pointless-statement
            option.default  # pylint: disable=pointless-statement

    @pytest.mark.usefixtures('config_with_profile')
    def test_get_config_option_default(self):
        """Tests that `get_option` return option default if not specified globally or for current profile."""
        option_name = 'logging.aiida_loglevel'
        option = get_option(option_name)

        # If we haven't set the option explicitly, `get_config_option` should return the option default
        option_value = get_config_option(option_name)
        self.assertEqual(option_value, option.default)

    @pytest.mark.usefixtures('config_with_profile')
    def test_get_config_option_profile_specific(self):
        """Tests that `get_option` correctly gets a configuration option if specified for the current profile."""
        config = get_config()
        profile = config.current_profile

        option_name = 'logging.aiida_loglevel'
        option_value_profile = 'WARNING'

        # Setting a specific value for the current profile which should then be returned by `get_config_option`
        config.set_option(option_name, option_value_profile, scope=profile.name)
        option_value = get_config_option(option_name)
        self.assertEqual(option_value, option_value_profile)

    @pytest.mark.usefixtures('config_with_profile')
    def test_get_config_option_global(self):
        """Tests that `get_option` correctly agglomerates upwards and so retrieves globally set config options."""
        config = get_config()

        option_name = 'logging.aiida_loglevel'
        option_value_global = 'CRITICAL'

        # Setting a specific value globally which should then be returned by `get_config_option` due to agglomeration
        config.set_option(option_name, option_value_global)
        option_value = get_config_option(option_name)
        self.assertEqual(option_value, option_value_global)
