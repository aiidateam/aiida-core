# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from unittest import TestCase
from aiida.workflows2.ticking_engine import TickingEngine
from aiida.workflows2.process import Process


class DummyProcess(Process):
    @staticmethod
    def _define(spec):
        spec.dynamic_input()

    def __init__(self):
        super(DummyProcess, self).__init__()
        self.ran = False

    def _run(self, a):
        self.ran = True


class TestTickingEngine(TestCase):
    def test_get_process(self):
        te = TickingEngine()

        # Test cancelling a future before the process runs
        future = te.submit(DummyProcess(), inputs={'a': 5})
        self.assertIsNotNone(te.get_process(future._pid))

    def test_submit(self):
        te = TickingEngine()
        dp = DummyProcess()
        future = te.submit(dp, inputs={'a': 5})

        self.assertFalse(future.done())
        te.tick()
        # Make sure both the future and the process say they finished
        self.assertTrue(future.running())
        te.tick()
        self.assertTrue(future.done())
        self.assertTrue(dp.ran)

    def test_run(self):
        """
        Test that we can run a process and it completes.
        :return:
        """
        te = TickingEngine()
        dp = DummyProcess()
        te.run(dp, inputs={'a': 5})
        self.assertTrue(dp.ran)

    def test_cancel(self):
        te = TickingEngine()
        dp = DummyProcess()

        # Test cancelling a future before the process runs
        future = te.submit(dp, inputs={'a': 5})
        self.assertTrue(future.running())
        self.assertIsNotNone(te.get_process(future._pid))
        future.cancel()
        self.assertTrue(future.cancelled())
        with self.assertRaises(KeyError):
            te.get_process(future._pid)

