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
from aiida.backends.testbase import AiidaTestCase
from aiida.common.caching import enable_caching
from aiida.orm.calculation.inline import make_inline, InlineCalculation
from aiida.orm.data.int import Int


class TestInlineCalculation(AiidaTestCase):
    """
    Tests for the InlineCalculation calculations.
    """

    def setUp(self):

        @make_inline
        def incr_inline(inp):
            return {'res': Int(inp.value + 1)}

        self.incr_inline = incr_inline

    def test_inline_calculation_process_state(self):
        """
        Test the process state for an inline calculation
        """
        calculation, result = self.incr_inline(inp=Int(11))

        self.assertEquals(calculation.is_terminated, True)
        self.assertEquals(calculation.is_excepted, False)
        self.assertEquals(calculation.is_killed, False)
        self.assertEquals(calculation.is_finished, True)
        self.assertEquals(calculation.is_finished_ok, True)
        self.assertEquals(calculation.is_failed, False)

    def test_exit_status(self):
        """
        If an InlineCalculation reaches the FINISHED process state, it has to have been successful
        which means that the exit status always has to be 0
        """
        calculation, result = self.incr_inline(inp=Int(11))
        self.assertEquals(calculation.is_finished, True)
        self.assertEquals(calculation.is_finished_ok, True)
        self.assertEquals(calculation.is_failed, False)
        self.assertEquals(calculation.exit_status, 0)

    def test_incr(self):
        """
        Simple test for the inline increment function.
        """
        for i in [-4, 0, 3, 10]:
            calc, res = self.incr_inline(inp=Int(i))
            self.assertEqual(res['res'].value, i + 1)

    def test_caching(self):
        with enable_caching(InlineCalculation):
            calc1, res1 = self.incr_inline(inp=Int(11))
            calc2, res2 = self.incr_inline(inp=Int(11))
            self.assertEquals(res1['res'].value, res2['res'].value, 12)
            self.assertEquals(calc1.get_extra('_aiida_cached_from', calc1.uuid), calc2.get_extra('_aiida_cached_from'))

    def test_caching_change_code(self):
        with enable_caching(InlineCalculation):
            calc1, res1 = self.incr_inline(inp=Int(11))

            @make_inline
            def incr_inline(inp):
                return {'res': Int(inp.value + 2)}

            calc2, res2 = incr_inline(inp=Int(11))
            self.assertNotEquals(res1['res'].value, res2['res'].value)
            self.assertFalse('_aiida_cached_from' in calc2.extras())


    def test_source_code_attributes(self):
        """
        Verify that upon storing the inline function is properly introspected and the expected
        information is stored in the nodes attributes and repository folder
        """
        FUNCTION_NAME = 'test_function_inline'

        @make_inline
        def test_function_inline(inp):
            return {'result': Int(inp.value + 1)}

        node, result = test_function_inline(inp=Int(5))

        # Read the source file of the inline function that should be stored in the repository
        # into memory, which should be exactly this test file
        function_source_file = node.function_source_file

        with open(function_source_file) as handle:
            function_source_code = handle.readlines()

        # Get the attributes that should be stored in the node
        function_name = node.function_name
        function_starting_line_number = node.function_starting_line_number

        # Verify that the function name is correct and the first source code linenumber is stored
        self.assertEquals(function_name, FUNCTION_NAME)
        self.assertIsInstance(function_starting_line_number, int)

        # Check that first line number is correct. Note that the first line should correspond
        # to the `@make_inline` directive, but since the list is zero-indexed we actually get the
        # following line, which should correspond to the function name i.e. `def test_function_inline(inp)`
        function_name_from_source = function_source_code[function_starting_line_number]
        self.assertTrue(function_name in function_name_from_source)