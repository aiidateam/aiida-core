# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the workfunction decorator and WorkFunctionNode."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.manage.caching import enable_caching
from aiida.common.links import LinkType
from aiida.engine import workfunction, Process
from aiida.orm import Int, WorkFunctionNode


class TestWorkFunction(AiidaTestCase):
    """Tests for workfunctions.

    .. note: tests common to all process functions should go in `aiida.backends.tests.work.test_process_function.py`
    """

    def setUp(self):
        super(TestWorkFunction, self).setUp()
        self.assertIsNone(Process.current())
        self.default_int = Int(256)

        @workfunction
        def test_workfunction(data):
            return data

        self.test_workfunction = test_workfunction

    def tearDown(self):
        super(TestWorkFunction, self).tearDown()
        self.assertIsNone(Process.current())

    def test_workfunction_node_type(self):
        """Verify that a workfunction gets a WorkFunctionNode as node instance."""
        _, node = self.test_workfunction.run_get_node(self.default_int)
        self.assertIsInstance(node, WorkFunctionNode)

    def test_workfunction_links(self):
        """Verify that a workfunction can only get RETURN links and no CREATE links."""
        _, node = self.test_workfunction.run_get_node(self.default_int)

        self.assertEqual(len(node.get_outgoing(link_type=LinkType.RETURN).all()), 1)
        self.assertEqual(len(node.get_outgoing(link_type=LinkType.CREATE).all()), 0)

    def test_workfunction_return_unstored(self):
        """Verify that a workfunction will raise when an unstored node is returned."""

        @workfunction
        def test_workfunction():
            return Int(2)

        with self.assertRaises(ValueError):
            test_workfunction.run_get_node()

    def test_workfunction_default_linkname(self):
        """Verify that a workfunction that returns a single Data node gets a default link label."""
        _, node = self.test_workfunction.run_get_node(self.default_int)

        self.assertEqual(node.outputs.result, self.default_int)
        self.assertEqual(getattr(node.outputs, Process.SINGLE_OUTPUT_LINKNAME), self.default_int)
        self.assertEqual(node.outputs[Process.SINGLE_OUTPUT_LINKNAME], self.default_int)

    def test_workfunction_caching(self):
        """Verify that a workfunction cannot be cached."""
        _ = self.test_workfunction(self.default_int)

        # Caching should always be disabled for a WorkFunctionNode
        with enable_caching(WorkFunctionNode):
            _, cached = self.test_workfunction.run_get_node(self.default_int)
            self.assertFalse(cached.is_created_from_cache)
