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
from aiida.orm.data.base import get_true_node
from aiida.work.run import async, run
import aiida.work.util as util



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

    def test_async(self):
        self.assertTrue(async(simple_wf).result()['result'])
        self.assertTrue(async(return_input, get_true_node()).result()['result'])

    def test_run(self):
        self.assertTrue(run(simple_wf)['result'])
        self.assertTrue(run(return_input, get_true_node())['result'])
