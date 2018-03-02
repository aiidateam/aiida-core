# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import aiida.orm
import aiida.work.utils as util
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data.bool import get_true_node
from aiida.orm.data.int import Int
from aiida.orm import load_node
from aiida.work.launch import run, run_get_node
from aiida.work.workfunctions import workfunction


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
        self.assertTrue(run(simple_wf)['result'])
        self.assertTrue(run(return_input, get_true_node())['result'])

    def test_run_and_get_node(self):
        result, calc_node = single_return_value.run_get_node()
        self.assertEqual(result, get_true_node())
        self.assertIsInstance(calc_node, aiida.orm.Calculation)

    def test_single_return_value(self):
        result = single_return_value()
        self.assertIsInstance(result, aiida.orm.Data)
        self.assertEqual(result, get_true_node())

    def test_simple_workflow(self):
        @workfunction
        def add(a, b):
            return a + b

        @workfunction
        def mul(a, b):
            return a * b

        @workfunction
        def add_mul_wf(a, b, c):
            return mul(add(a, b), c)

        result = add_mul_wf(Int(3), Int(4), Int(5))

    def test_finish_status(self):
        """
        If a workfunction reaches the FINISHED process state, it has to have been successful
        which means that the finish status always has to be 0
        """
        result, calculation = single_return_value.run_get_node()
        self.assertEquals(calculation.finish_status, 0)
        self.assertEquals(calculation.is_finished_ok, True)
        self.assertEquals(calculation.is_failed, False)

    def test_hashes(self):
        result, w1 = run_get_node(return_input, inp=Int(2))
        result, w2 = run_get_node(return_input, inp=Int(2))
        self.assertEqual(w1.get_hash(), w2.get_hash())

    def test_hashes_different(self):
        result, w1 = run_get_node(return_input, inp=Int(2))
        result, w2 = run_get_node(return_input, inp=Int(3))
        self.assertNotEqual(w1.get_hash(), w2.get_hash())

    def _check_hash_consistent(self, pid):
        wc = load_node(pid)
        self.assertEqual(wc.get_hash(), wc.get_extra('_aiida_hash'))