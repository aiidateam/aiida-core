# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0.1"
__authors__ = "The AiiDA team."

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.db_types import Bool, Int
from unittest import TestCase
from plum.engine.ticking import TickingEngine
from aiida.workflows2.process import Process
from concurrent.futures import ThreadPoolExecutor


class DummyProcess(Process):
    @classmethod
    def _define(cls, spec):
        spec.dynamic_input()
        spec.dynamic_output()

    def _run(self, a):
        self.out("ran", Bool(True))


class TestTickingEngine(TestCase):
    def setUp(self):
        self.ticking_engine = TickingEngine()
        self.executor = ThreadPoolExecutor(max_workers=1)

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

