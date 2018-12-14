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
from aiida.manage.configuration.options import get_option, get_option_names, parse_option, Option, CONFIG_OPTIONS


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
