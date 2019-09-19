# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import tempfile
import unittest
import yaml

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
        with tempfile.NamedTemporaryFile() as tmpf:
            yaml.dump(self.config_reference, tmpf, encoding='utf-8')
            configure(config_file=tmpf.name)

    def tearDown(self):
        configure()

    def test_default(self):
        self.assertTrue(get_use_cache())

    def test_caching_enabled(self):
        self.assertFalse(get_use_cache(identifier='aiida.calculations:templatereplacer'))

    def test_invalid_config(self):
        with self.assertRaises(TypeError):
            get_use_cache(identifier=int)

    def test_contextmanager_enable_explicit(self):
        with enable_caching(identifier='aiida.calculations:templatereplacer'):
            self.assertTrue(get_use_cache(identifier='aiida.calculations:templatereplacer'))

    def test_contextmanager_disable_global(self):
        with disable_caching():
            self.assertTrue(get_use_cache(identifier='aiida.calculations:arithmetic.add'))  # explicitly set, hence not overwritten
            self.assertFalse(get_use_cache(identifier='aiida.calculations:templatereplacer'))

    def test_disable_caching(self):
        with disable_caching(identifier='aiida.calculations:arithmetic.add'):
            self.assertFalse(get_use_cache(identifier='aiida.calculations:arithmetic.add'))
        self.assertTrue(get_use_cache(identifier='aiida.calculations:arithmetic.add'))
