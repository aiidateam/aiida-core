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
from aiida.common.caching import configure, get_fast_forward_enabled, get_use_cache_default

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
                'use_cache': {'default': True},
                'fast_forward': {
                    'default': True,
                    'enabled': [],
                    'disabled': ['aiida.orm.calculation.job.simpleplugins.templatereplacer.TemplatereplacerCalculation']
                }
            }
        }
        with tempfile.NamedTemporaryFile() as tf, open(tf.name, 'w') as of:
            yaml.dump(self.config_reference, of)
            configure(config_file=tf.name)

    def tearDown(self):
        configure()

    def test_use_cache_default(self):
        self.assertTrue(get_use_cache_default())

    def test_fast_forward_default(self):
        from aiida.orm.calculation.job import JobCalculation
        self.assertTrue(get_fast_forward_enabled(JobCalculation))

    def test_fast_forward_disabled(self):
        from aiida.orm.calculation.job.simpleplugins.templatereplacer import TemplatereplacerCalculation
        self.assertFalse(get_fast_forward_enabled(TemplatereplacerCalculation))
