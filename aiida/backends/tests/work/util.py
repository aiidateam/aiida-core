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

from aiida.work.process import Process
from aiida.work.workfunction import workfunction
from aiida.common.lang import override
from aiida.work.run import async
from aiida.orm.data.base import Int
from aiida.work.util import ProcessStack



class StackTester(Process):
    @override
    def _run(self):
        assert ProcessStack.get_active_process_id() == self.pid
        assert ProcessStack.get_active_process_calc_node() is self.calc
        nested_tester()


@workfunction
def registry_tester():
    # Call a wf
    future = async(nested_tester)
    out = future.result()
    assert future.pid == out['pid']
    assert future.pid == out['node_pk']

    # Call a Process
    StackTester.run()

    return {'pid': Int(ProcessStack.get_active_process_id()),
            'node_pk': Int(ProcessStack.get_active_process_calc_node().pk)}


@workfunction
def nested_tester():
    return {'pid': Int(ProcessStack.get_active_process_id()),
            'node_pk': Int(ProcessStack.get_active_process_calc_node().pk)}


class TestProcessRegistry(AiidaTestCase):
    """
    These these check that the registry is giving out the right pid which when
    using storage is equal to the node pk.
    """
    def setUp(self):
        super(TestProcessRegistry, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestProcessRegistry, self).tearDown()
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_process_pid_and_calc(self):
        StackTester.run()

    def test_wf_pid_and_calc(self):
        future = async(registry_tester)
        out = future.result()

        self.assertEqual(out['pid'], future.pid)
        self.assertEqual(out['node_pk'], future.pid)





