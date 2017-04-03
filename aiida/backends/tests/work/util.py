# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import time
from aiida.backends.testbase import AiidaTestCase

from aiida.work.process import Process
from aiida.work.workfunction import workfunction
from aiida.common.lang import override
from aiida.work.run import async
from aiida.orm.data.base import Int
from aiida.orm.calculation import Calculation
from aiida.work.util import ProcessStack, CalculationHeartbeat, HeartbeatError



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


class TestCalculationHeartbeat(AiidaTestCase):
    def setUp(self):
        super(TestCalculationHeartbeat, self).setUp()
        self.lock_lost = False

    def test_start_stop(self):
        c = Calculation()
        heartbeat = CalculationHeartbeat(c)
        heartbeat.start()
        heartbeat.stop()

    def test_acquire_locked(self):
        c = Calculation()
        # Start one heartbeat
        with CalculationHeartbeat(c):
            # Try starting another on the same calculation
            with self.assertRaises(HeartbeatError):
                with CalculationHeartbeat(c):
                    pass

    def test_heartbeat_lost(self):
        c = Calculation()
        # Start a heartbeat
        with CalculationHeartbeat(c, 0.5, lost_callback=self._lock_lost) as heartbeat:
            # Now steal its lock and wait for it to try and update the heartbeat
            c._set_attr(CalculationHeartbeat.HEARTBEAT_TAG, 0)
            time.sleep(1)
            self.assertTrue(self.lock_lost)

    def _lock_lost(self, calc):
        self.lock_lost = True









