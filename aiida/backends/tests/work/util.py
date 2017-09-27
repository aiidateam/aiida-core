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
from aiida.work.launch import async, run
from aiida.orm.data.base import Int
from aiida.orm.calculation import Calculation
from aiida.work.utils import ProcessStack, CalculationHeartbeat, HeartbeatError


class StackTester(Process):
    @override
    def _run(self):
        assert ProcessStack.get_active_process_id() == self.pid
        assert ProcessStack.get_active_process_calc_node() is self.calc
        nested_tester()


@workfunction
def nested_tester():
    return {'pid': Int(ProcessStack.get_active_process_id()),
            'node_pk': Int(ProcessStack.get_active_process_calc_node().pk)}


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
