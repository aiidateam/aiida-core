# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the functionality that reads and modifies the caching configuration file."""

import tempfile
import unittest
import yaml

from aiida.common import exceptions
from aiida.manage.caching import configure, get_use_cache, enable_caching, disable_caching
from aiida.manage.configuration import get_profile


class CacheConfigTest(unittest.TestCase):
    """Tests the caching configuration."""

    def setUp(self):
        """Write a temporary config file, and load the configuration."""
        self.config_reference = {
            get_profile().name: {
                'default': True,
                'enabled': ['aiida.calculations:arithmetic.add'],
                'disabled': ['aiida.calculations:templatereplacer']
            }
        }
        with tempfile.NamedTemporaryFile() as handle:
            yaml.dump(self.config_reference, handle, encoding='utf-8')
            configure(config_file=handle.name)

    def tearDown(self):  # pylint: disable=no-self-use
        """Reset the configuration."""
        configure()

    def test_empty_enabled_disabled(self):  # pylint: disable=no-self-use
        """Test that `aiida.manage.caching.configure` does not except when either `enabled` or `disabled` is `None`.

        This will happen when the configuration file specifies either one of the keys but no actual values, e.g.::

            profile_name:
                default: False
                enabled:

        In this case, the dictionary parsed by yaml will contain `None` for the `enabled` key.
        Now this will be unlikely, but the same holds when all values are commented::

            profile_name:
                default: False
                enabled:
                    # - aiida.calculations:templatereplacer

        which is not unlikely to occurr in the wild.
        """
        configuration = {get_profile().name: {'default': True, 'enabled': None, 'disabled': None}}
        with tempfile.NamedTemporaryFile() as handle:
            yaml.dump(configuration, handle, encoding='utf-8')
            configure(config_file=handle.name)

            # Check that `get_use_cache` also does not except
            get_use_cache(identifier='aiida.calculations:templatereplacer')

    def test_invalid_enabled_disabled_directives(self):
        """Test that `configure` raises for invalid enable or disable directives."""

        def load_configuration(identifier):
            """Write the caching file for given configuration and load it."""
            configuration = {get_profile().name: {'default': True, 'enabled': [identifier]}}
            with tempfile.NamedTemporaryFile() as handle:
                yaml.dump(configuration, handle, encoding='utf-8')
                configure(config_file=handle.name)

        with self.assertRaises(exceptions.ConfigurationError):
            load_configuration(1)  # entry point string needs to be a string

        with self.assertRaises(exceptions.ConfigurationError):
            load_configuration('templatereplacer')  # entry point string needs to be fully qualified

        with self.assertRaises(exceptions.ConfigurationError):
            load_configuration('calculations:templatereplacer')  # entry point string needs to be fully qualified

        with self.assertRaises(exceptions.ConfigurationError):
            load_configuration('aiida.nonexistent_group:templatereplacer')  # invalid entry point group

    def test_invalid_config(self):
        """Test `get_use_cache` raises a `TypeError` if identifier is not a valid entry point string."""
        with self.assertRaises(TypeError):
            get_use_cache(identifier=int)

    def test_default(self):
        """Verify that when not specifying any specific identifier, the `default` is used, which is set to `True`."""
        self.assertTrue(get_use_cache())

    def test_caching_enabled(self):
        """Test `get_use_cache` when specifying identifier."""
        self.assertFalse(get_use_cache(identifier='aiida.calculations:templatereplacer'))

    def test_contextmanager_enable_explicit(self):
        """Test the `enable_caching` context manager."""
        with enable_caching(identifier='aiida.calculations:templatereplacer'):
            self.assertTrue(get_use_cache(identifier='aiida.calculations:templatereplacer'))

    def test_contextmanager_disable_global(self):
        """Test the `disable_caching` context manager without specific identifier."""
        with disable_caching():
            self.assertTrue(
                get_use_cache(identifier='aiida.calculations:arithmetic.add')
            )  # explicitly set, hence not overwritten
            self.assertFalse(get_use_cache(identifier='aiida.calculations:templatereplacer'))

    def test_disable_caching(self):
        """Test the `disable_caching` context manager with specific identifier."""
        with disable_caching(identifier='aiida.calculations:arithmetic.add'):
            self.assertFalse(get_use_cache(identifier='aiida.calculations:arithmetic.add'))
        self.assertTrue(get_use_cache(identifier='aiida.calculations:arithmetic.add'))
