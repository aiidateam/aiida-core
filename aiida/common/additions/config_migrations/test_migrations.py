# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import os
import uuid
import json
import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from ._utils import check_and_migrate_config
from ._migrations import _MIGRATION_LOOKUP


def load_config_sample(filename):
    currdir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(currdir, 'test_samples', filename)
    with open(filepath, 'r') as f:
        return json.load(f)


class TestConfigMigration(unittest.TestCase):

    def test_check_and_migrate(self):
        """
        Test the full config migration.
        """
        initial_config = load_config_sample('input/0.json')
        with mock.patch.object(uuid, 'uuid4', return_value=uuid.UUID(hex='0'*32)):
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

    def test_1_2_migration(self):
        """
        Test the step between config versions 1 and 2.
        """
        self.maxDiff = None
        initial_config = load_config_sample('input/1.json')
        reference_config = load_config_sample('reference/2.json')
        with mock.patch.object(uuid, 'uuid4', return_value=uuid.UUID(hex='0'*32)):
            final_config = _MIGRATION_LOOKUP[1].apply(initial_config)
        self.assertEqual(final_config, reference_config)

    def test_2_3_migration(self):
        """
        Test the step between config versions 2 and 3.
        """
        initial_config = load_config_sample('input/2.json')
        reference_config = load_config_sample('reference/3.json')
        final_config = _MIGRATION_LOOKUP[2].apply(initial_config)
        self.assertEqual(final_config, reference_config)
