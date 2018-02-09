# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import unittest
import tempfile

import yaml

from aiida.backends.utils import get_current_profile
from aiida.common.caching import configure, get_use_cache, enable_caching, disable_caching
from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation

class CacheConfigTest(unittest.TestCase):
    """
    Tests the caching configuration.
    """
    def setUp(self):
        """
        Write a temporary config file, and load the configuration.
        """
        self.config_reference = {
            get_current_profile(): {
                'default': True,
                'enabled': [],
                'disabled': ['aiida.orm.calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation']
            }
        }
        with tempfile.NamedTemporaryFile() as tf, open(tf.name, 'w') as of:
            yaml.dump(self.config_reference, of)
            configure(config_file=tf.name)

    def tearDown(self):
        configure()

    def test_default(self):
        self.assertTrue(get_use_cache())

    def test_caching_enabled(self):
        self.assertFalse(get_use_cache(TemplatereplacerCalculation))

    def test_invalid_config(self):
        with enable_caching(TemplatereplacerCalculation):
            self.assertRaises(ValueError, get_use_cache, TemplatereplacerCalculation)

    def test_disable_caching(self):
        from aiida.orm.data.base import Float
        with disable_caching(Float):
            self.assertFalse(get_use_cache(Float))
        self.assertTrue(get_use_cache(Float))
