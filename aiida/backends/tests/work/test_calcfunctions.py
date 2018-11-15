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

import io

from aiida.backends.testbase import AiidaTestCase
from aiida.common.caching import enable_caching
from aiida.orm.data.int import Int
from aiida.orm.node.process import CalcFunctionNode
from aiida.work import calcfunction


class TestCalcFunctionNode(AiidaTestCase):
    """
    Tests for the calcfunction decorator and CalcFunctionNode.
    """

    def setUp(self):

        @calcfunction
        def increment_calcfunction(inp):
            return {'res': Int(inp.value + 1)}

        self.increment_calcfunction = increment_calcfunction

    def test_do_not_store_provenance(self):
        """Run the function without storing the provenance."""
        inp = 2
        result = self.increment_calcfunction(inp=Int(inp), store_provenance=False)  # pylint: disable=unexpected-keyword-arg
        self.assertFalse(result['res'].is_stored)
        self.assertEqual(result['res'], inp + 1)

    def test_calculation_function_process_state(self):
        """
        Test the process state for a calculation function
        """
        _, node = self.increment_calcfunction.run_get_node(inp=Int(11))

        self.assertEqual(node.is_terminated, True)
        self.assertEqual(node.is_excepted, False)
        self.assertEqual(node.is_killed, False)
        self.assertEqual(node.is_finished, True)
        self.assertEqual(node.is_finished_ok, True)
        self.assertEqual(node.is_failed, False)

    def test_exit_status(self):
        """
        If a calcfunction reaches the FINISHED process state, it has to have been successful
        which means that the exit status always has to be 0
        """
        _, node = self.increment_calcfunction.run_get_node(inp=Int(11))

        self.assertEqual(node.is_finished, True)
        self.assertEqual(node.is_finished_ok, True)
        self.assertEqual(node.is_failed, False)
        self.assertEqual(node.exit_status, 0)

    def test_incr(self):
        """
        Simple test for the increment calculation function.
        """
        for i in [-4, 0, 3, 10]:
            result = self.increment_calcfunction(inp=Int(i))
            self.assertEqual(result['res'].value, i + 1)

    def test_caching(self):
        """Test caching within the context manager using targeting the `CalcFunctionNode` class."""
        with enable_caching(CalcFunctionNode):
            result1, node1 = self.increment_calcfunction.run_get_node(inp=Int(11))
            result2, node2 = self.increment_calcfunction.run_get_node(inp=Int(11))
            self.assertEqual(result1['res'].value, result2['res'].value, 12)
            self.assertEqual(node1.get_extra('_aiida_cached_from', node1.uuid), node2.get_extra('_aiida_cached_from'))

    def test_caching_change_code(self):
        """Test caching within the context manager using targeting the `CalcFunctionNode` class."""
        with enable_caching(CalcFunctionNode):
            result1 = self.increment_calcfunction(inp=Int(11))

            @calcfunction
            def increment_calcfunction(inp):
                return {'res': Int(inp.value + 2)}

            result2, node2 = increment_calcfunction.run_get_node(inp=Int(11))
            self.assertNotEqual(result1['res'].value, result2['res'].value)
            self.assertFalse('_aiida_cached_from' in node2.extras())

    def test_source_code_attributes(self):
        """
        Verify that upon storing the calculation function is properly introspected and the expected
        information is stored in the nodes attributes and repository folder
        """
        function_name = 'test_calcfunction'

        @calcfunction
        def test_calcfunction(inp):
            return {'result': Int(inp.value + 1)}

        _, node = test_calcfunction.run_get_node(inp=Int(5))

        # Read the source file of the calculation function that should be stored in the repository
        # into memory, which should be exactly this test file
        function_source_file = node.function_source_file

        with io.open(function_source_file, encoding='utf8') as handle:
            function_source_code = handle.readlines()

        # Get the attributes that should be stored in the node
        function_name = node.function_name
        function_starting_line_number = node.function_starting_line_number

        # Verify that the function name is correct and the first source code linenumber is stored
        self.assertEqual(function_name, function_name)
        self.assertIsInstance(function_starting_line_number, int)

        # Check that first line number is correct. Note that the first line should correspond
        # to the `@calcfunction` directive, but since the list is zero-indexed we actually get the
        # following line, which should correspond to the function name i.e. `def test_calcfunction(inp)`
        function_name_from_source = function_source_code[function_starting_line_number]
        self.assertTrue(function_name in function_name_from_source)
