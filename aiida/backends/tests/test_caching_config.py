# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import tempfile
import unittest
import yaml

from aiida.backends.utils import get_current_profile
from aiida.calculations.plugins.templatereplacer import TemplatereplacerCalculation
from aiida.manage.caching import configure, get_use_cache, enable_caching, disable_caching
from aiida.orm import Bool, Float, Int


class CacheConfigTest(unittest.TestCase):
    """Tests the caching configuration."""

    def setUp(self):
        """Write a temporary config file, and load the configuration."""
        self.config_reference = {
            get_current_profile(): {
                'default': True,
                'enabled': ['aiida.orm.Bool', 'aiida.orm.Float'],
                'disabled': ['aiida.calculations.plugins.templatereplacer.TemplatereplacerCalculation', 'aiida.orm.Bool']
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
        self.assertFalse(get_use_cache(TemplatereplacerCalculation))

    def test_invalid_config(self):
        self.assertRaises(ValueError, get_use_cache, Bool)

    def test_contextmanager_enable_explicit(self):
        with enable_caching(TemplatereplacerCalculation):
            self.assertTrue(get_use_cache(TemplatereplacerCalculation))

    def test_contextmanager_disable_global(self):
        with disable_caching():
            self.assertTrue(get_use_cache(Float))  # explicitly set, hence not overwritten
            self.assertFalse(get_use_cache(Int))

    def test_disable_caching(self):
        with disable_caching(Float):
            self.assertFalse(get_use_cache(Float))
        self.assertTrue(get_use_cache(Float))
