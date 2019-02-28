# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Node` utils."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Data
from aiida.orm.utils.node import load_node_class


class TestLoadNodeClass(AiidaTestCase):
    """Tests for the node plugin type generator and loaders."""

    def test_load_node_class_fallback(self):
        """Verify that `load_node_class` will fall back to `Data` class if entry point cannot be loaded."""
        loaded_class = load_node_class('data.some.non.existing.plugin.')
        self.assertEqual(loaded_class, Data)
