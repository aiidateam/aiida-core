# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.backends.testbase import AiidaTestCase
from aiida.work import workfunction
from aiida.orm.data.base import get_true_node
import aiida.orm
import aiida.work.utils as util
from aiida import work


@workfunction
def simple_wf():
    return {'result': get_true_node()}


@workfunction
def return_input(inp):
    return {'result': inp}


@workfunction
def single_return_value():
    return get_true_node()


class TestWf(AiidaTestCase):
    def setUp(self):
        super(TestWf, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestWf, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_blocking(self):
        self.assertTrue(simple_wf()['result'])
        self.assertTrue(return_input(get_true_node())['result'])

    def test_run(self):
        self.assertTrue(work.run(simple_wf)['result'])
        self.assertTrue(work.run(return_input, get_true_node())['result'])

    def test_run_and_get_node(self):
        result, calc_node = single_return_value.run_get_node()
        self.assertEqual(result, get_true_node())
        self.assertIsInstance(calc_node, aiida.orm.Calculation)

    def test_single_return_value(self):
        result = single_return_value()
        self.assertIsInstance(result, aiida.orm.Data)
        self.assertEqual(result, get_true_node())
