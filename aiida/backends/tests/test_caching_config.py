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
from aiida.common.caching import configure, get_use_cache, get_use_cache_default

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
        self.assertTrue(get_use_cache_default())

    def test_caching_enabled(self):
        from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation
        self.assertFalse(get_use_cache(TemplatereplacerCalculation))
