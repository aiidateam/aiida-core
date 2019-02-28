# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the configuration migration functionality."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import io
import os
import uuid
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

from aiida.common import json

from aiida.manage.configuration import Config
from aiida.manage.configuration.migrations.utils import check_and_migrate_config
from aiida.manage.configuration.migrations.migrations import _MIGRATION_LOOKUP


class TestConfigMigration(unittest.TestCase):
    """Tests for the configuration migration functionality."""

    @staticmethod
    def load_config_sample(filename):
        """Load a configuration file from a fixture."""
        currdir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(currdir, 'test_samples', filename)
        with io.open(filepath, 'r', encoding='utf8') as handle:
            return Config(filepath, json.load(handle))

    def setUp(self):
        super(TestConfigMigration, self).setUp()
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_check_and_migrate(self):
        """Test the full config migration."""
        config_initial = self.load_config_sample('input/0.json')
        with mock.patch.object(uuid, 'uuid4', return_value=uuid.UUID(hex='0' * 32)):
            config_migrated = check_and_migrate_config(config_initial, store=False)
        config_reference = self.load_config_sample('reference/final.json')
        self.assertEqual(config_migrated, config_reference)

    def test_0_1_migration(self):
        """Test the step between config versions 0 and 1."""
        config_initial = self.load_config_sample('input/0.json')
        config_reference = self.load_config_sample('reference/1.json')
        config_migrated = _MIGRATION_LOOKUP[0].apply(config_initial)
        self.assertEqual(config_migrated, config_reference)

    def test_1_2_migration(self):
        """Test the step between config versions 1 and 2."""
        config_initial = self.load_config_sample('input/1.json')
        config_reference = self.load_config_sample('reference/2.json')
        with mock.patch.object(uuid, 'uuid4', return_value=uuid.UUID(hex='0' * 32)):
            config_migrated = _MIGRATION_LOOKUP[1].apply(config_initial)
        self.assertEqual(config_migrated, config_reference)

    def test_2_3_migration(self):
        """Test the step between config versions 2 and 3."""
        config_initial = self.load_config_sample('input/2.json')
        config_reference = self.load_config_sample('reference/3.json')
        config_migrated = _MIGRATION_LOOKUP[2].apply(config_initial)
        self.assertEqual(config_migrated, config_reference)
