# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import os
import unittest
import json

from ._utils import check_and_migrate_config
from ._migrations import _MIGRATION_LOOKUP

def load_config_sample(filename):
    with open(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'test_samples',
        filename
    ), 'r') as f:
        return json.load(f)

class TestConfigMigration(unittest.TestCase):
    def test_check_and_migrate(self):
        """
        Test the full config migration.
        """
        initial_config = load_config_sample('input/0.json')
        final_config = check_and_migrate_config(initial_config, store=False)
        reference_config = load_config_sample('reference/final.json')
        self.assertEqual(final_config, reference_config)

    def test_0_1_migration(self):
        """
        Test the step between config versions 0 and 1.
        """
        initial_config = load_config_sample('input/0.json')
        reference_config = load_config_sample('reference/1.json')
        final_config = _MIGRATION_LOOKUP[0].apply(initial_config)
        self.assertEqual(final_config, reference_config)
