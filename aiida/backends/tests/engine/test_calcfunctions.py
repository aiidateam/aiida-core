# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the calcfunction decorator and CalcFunctionNode."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.engine import calcfunction, Process
from aiida.manage.caching import enable_caching
from aiida.orm import Int, CalcFunctionNode


class TestCalcFunction(AiidaTestCase):
    """Tests for calcfunctions.

    .. note: tests common to all process functions should go in `aiida.backends.tests.work.test_process_function.py`
    """

    def setUp(self):
        super(TestCalcFunction, self).setUp()
        self.assertIsNone(Process.current())
        self.default_int = Int(256)

        @calcfunction
        def test_calcfunction(data):
            return Int(data.value + 1)

        self.test_calcfunction = test_calcfunction

    def tearDown(self):
        super(TestCalcFunction, self).tearDown()
        self.assertIsNone(Process.current())

    def test_calcfunction_node_type(self):
        """Verify that a calcfunction gets a CalcFunctionNode as node instance."""
        _, node = self.test_calcfunction.run_get_node(self.default_int)
        self.assertIsInstance(node, CalcFunctionNode)

    def test_calcfunction_links(self):
        """Verify that a calcfunction can only get CREATE links and no RETURN links."""
        _, node = self.test_calcfunction.run_get_node(self.default_int)

        self.assertEqual(len(node.get_outgoing(link_type=LinkType.CREATE).all()), 1)
        self.assertEqual(len(node.get_outgoing(link_type=LinkType.RETURN).all()), 0)

    def test_calcfunction_return_stored(self):
        """Verify that a calcfunction will raise when a stored node is returned."""

        @calcfunction
        def test_calcfunction():
            return Int(2).store()

        with self.assertRaises(ValueError):
            test_calcfunction.run_get_node()

    def test_calcfunction_default_linkname(self):
        """Verify that a calcfunction that returns a single Data node gets a default link label."""
        _, node = self.test_calcfunction.run_get_node(self.default_int)

        self.assertEqual(node.outputs.result, self.default_int.value + 1)
        self.assertEqual(getattr(node.outputs, Process.SINGLE_OUTPUT_LINKNAME), self.default_int.value + 1)
        self.assertEqual(node.outputs[Process.SINGLE_OUTPUT_LINKNAME], self.default_int.value + 1)

    def test_calcfunction_caching(self):
        """Verify that a calcfunction can be cached."""
        _, original = self.test_calcfunction.run_get_node(Int(5))

        # Caching a CalcFunctionNode should be possible
        with enable_caching(CalcFunctionNode):
            _, cached = self.test_calcfunction.run_get_node(Int(5))
            self.assertTrue(cached.is_created_from_cache)
            self.assertIn(cached.get_cache_source(), original.uuid)

    def test_calcfunction_caching_change_code(self):
        """Verify that changing the source codde of a calcfunction invalidates any existing cached nodes."""
        result_original = self.test_calcfunction(self.default_int)

        with enable_caching(CalcFunctionNode):

            @calcfunction
            def test_calcfunction(data):
                """This calcfunction has a different source code from the one setup in the setUp method."""
                return Int(data.value + 2)

            result_cached, cached = test_calcfunction.run_get_node(self.default_int)
            self.assertNotEqual(result_original, result_cached)
            self.assertFalse(cached.is_created_from_cache)

    def test_calcfunction_do_not_store_provenance(self):
        """Run the function without storing the provenance."""
        data = Int(1)
        result, node = self.test_calcfunction.run_get_node(data, metadata={'store_provenance': False})  # pylint: disable=unexpected-keyword-arg
        self.assertFalse(result.is_stored)
        self.assertFalse(data.is_stored)
        self.assertFalse(node.is_stored)
        self.assertEqual(result, data + 1)

    def test_calculation_cannot_call(self):
        """Verify that calling another process from within a calcfunction raises as it is forbidden."""

        @calcfunction
        def test_calcfunction_caller(data):
            self.test_calcfunction(data)

        with self.assertRaises(exceptions.InvalidOperation):
            test_calcfunction_caller(self.default_int)

    def test_calculation_call_store_provenance_false(self):  # pylint: disable=invalid-name
        """Verify that a `calcfunction` can call another calcfunction as long as `store_provenance` is False."""

        @calcfunction
        def test_calcfunction_caller(data):
            return self.test_calcfunction(data, metadata={'store_provenance': False})  # pylint: disable=unexpected-keyword-arg

        result, node = test_calcfunction_caller.run_get_node(self.default_int)

        self.assertTrue(isinstance(result, Int))
        self.assertTrue(isinstance(node, CalcFunctionNode))

        # The node of the outermost `calcfunction` should have a single `CREATE` link and no `CALL_CALC` links
        self.assertEqual(len(node.get_outgoing(link_type=LinkType.CREATE).all()), 1)
        self.assertEqual(len(node.get_outgoing(link_type=LinkType.CALL_CALC).all()), 0)
