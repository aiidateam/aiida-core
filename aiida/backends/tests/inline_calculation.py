# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Tests for inline calculations.
"""

from aiida.orm.data.base import Int
from aiida.common.caching import enable_caching
from aiida.orm.calculation.inline import make_inline, InlineCalculation
from aiida.backends.testbase import AiidaTestCase

class TestInlineCalculation(AiidaTestCase):
    """
    Tests for the InlineCalculation calculations.
    """
    def setUp(self):
        @make_inline
        def incr_inline(inp):
            return {'res': Int(inp.value + 1)}

        self.incr_inline = incr_inline

    def test_incr(self):
        """
        Simple test for the inline increment function.
        """
        for i in [-4, 0, 3, 10]:
            calc, res = self.incr_inline(inp=Int(i))
            self.assertEqual(res['res'].value, i + 1)
