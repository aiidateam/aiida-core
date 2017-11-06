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
from aiida.orm.calculation.inline import make_inline
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

    def test_caching(self):
        from aiida.common.caching import CONFIG, configure
        configure()
        use_cache_default = CONFIG['use_cache']['default']
        CONFIG['use_cache']['default'] = True
        calc1, res1 = self.incr_inline(inp=Int(11))
        calc2, res2 = self.incr_inline(inp=Int(11))
        self.assertEquals(res1['res'].value, res2['res'].value, 12)
        self.assertEquals(calc1.get_extra('cached_from', calc1.uuid), calc2.get_extra('cached_from'))

        CONFIG['use_cache']['default'] = use_cache_default

    def test_caching_change_code(self):
        from aiida.common.caching import CONFIG, configure
        configure()
        use_cache_default = CONFIG['use_cache']['default']
        CONFIG['use_cache']['default'] = True
        calc1, res1 = self.incr_inline(inp=Int(11))

        @make_inline
        def incr_inline(inp):
            return {'res': Int(inp.value + 2)}

        calc2, res2 = incr_inline(inp=Int(11))
        self.assertNotEquals(res1['res'].value, res2['res'].value)
        self.assertFalse('cached_from' in calc2.extras())

        CONFIG['use_cache']['default'] = use_cache_default
