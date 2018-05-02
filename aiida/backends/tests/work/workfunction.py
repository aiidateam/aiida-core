# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import plum.process_monitor
from aiida.backends.testbase import AiidaTestCase
from aiida.work.workfunction import workfunction
from aiida.orm.data.base import get_true_node, Int
from aiida.orm import load_node
from aiida.work.run import run
import aiida.work.util as util
from aiida.common import caching


@workfunction
def simple_wf():
    return {'result': get_true_node()}


@workfunction
def return_input(inp):
    return {'result': inp}


class TestWf(AiidaTestCase):
    def setUp(self):
        super(TestWf, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestWf, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_blocking(self):
        self.assertTrue(simple_wf()['result'])
        self.assertTrue(return_input(get_true_node())['result'])

    def test_run(self):
        self.assertTrue(run(simple_wf)['result'])
        self.assertTrue(run(return_input, get_true_node())['result'])

    def test_hashes(self):
        _, pid1 = run(return_input, inp=Int(2), _return_pid=True)
        _, pid2 = run(return_input,  inp=Int(2), _return_pid=True)
        w1 = load_node(pid1)
        w2 = load_node(pid2)
        self.assertEqual(w1.get_hash(), w2.get_hash())

    def test_hashes_different(self):
        _, pid1 = run(return_input, inp=Int(2), _return_pid=True)
        _, pid2 = run(return_input,  inp=Int(3), _return_pid=True)
        w1 = load_node(pid1)
        w2 = load_node(pid2)
        self.assertNotEqual(w1.get_hash(), w2.get_hash())

    def _check_hash_consistent(self, pid):
        wc = load_node(pid)
        self.assertEqual(wc.get_hash(), wc.get_extra('_aiida_hash'))
