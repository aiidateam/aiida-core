# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `run` functions."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.backends.tests.utils.processes import DummyProcess
from aiida.engine import run, run_get_node
from aiida.orm import Int, Str, ProcessNode


class TestRun(AiidaTestCase):
    """Tests for the `run` functions."""

    @staticmethod
    def test_run():
        """Test the `run` function."""
        inputs = {'a': Int(2), 'b': Str('test')}
        run(DummyProcess, **inputs)

    def test_run_get_node(self):
        """Test the `run_get_node` function."""
        inputs = {'a': Int(2), 'b': Str('test')}
        result, node = run_get_node(DummyProcess, **inputs)  # pylint: disable=unused-variable
        self.assertIsInstance(node, ProcessNode)
