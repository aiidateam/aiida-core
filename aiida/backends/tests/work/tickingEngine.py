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
from concurrent.futures import ThreadPoolExecutor
from plum.engine.ticking import TickingEngine
from aiida.orm.data.base import get_true_node, Int
from aiida.work.process import Process
import aiida.work.util as util



class DummyProcess(Process):
    @classmethod
    def define(cls, spec):
        super(DummyProcess, cls).define(spec)
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self, a):
        self.out("ran", get_true_node())


class TestTickingEngine(AiidaTestCase):
    def setUp(self):
        super(TestTickingEngine, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.ticking_engine = TickingEngine()
        self.executor = ThreadPoolExecutor(max_workers=1)

    def tearDown(self):
        super(TestTickingEngine, self).tearDown()
        self.ticking_engine.shutdown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_get_process(self):
        # Test cancelling a future before the process runs
        future = self.ticking_engine.submit(DummyProcess, inputs={'a': Int(5)})

    def test_submit(self):
        fut = self.ticking_engine.submit(DummyProcess, inputs={'a': Int(5)})
        self._tick_till_finished()
        res = fut.result()
        self.assertTrue(res['ran'].value)

    def test_cancel(self):
        # Test cancelling a future before the process runs
        future = self.ticking_engine.submit(DummyProcess, inputs={'a': Int(5)})
        self.assertTrue(future.running())
        future.cancel()
        self.assertTrue(future.cancelled())

    def _tick_till_finished(self):
        self.executor.submit(self._keep_ticking())

    def _keep_ticking(self):
        while self.ticking_engine.tick():
            pass

