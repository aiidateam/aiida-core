import unittest
import aiida.workflows2.daemon as daemon
from aiida.workflows2.db_types import Bool
from aiida.workflows2.process import Process
from aiida.workflows2.process_registry import ProcessRegistry
from aiida.workflows2.run import asyncd
from aiida.common.lang import override
from plum.wait_ons import checkpoint
from plum.persistence.pickle_persistence import PicklePersistence
from aiida.orm import load_node
import aiida.workflows2.util as util

from workflows2.common import DummyProcess


class ProcessEventsTester(Process):
    EVENTS = ["create", "run", "continue_", "finish", "emitted", "stop",
              "destroy", ]

    @classmethod
    def _define(cls, spec):
        super(ProcessEventsTester, cls)._define(spec)
        for label in ["create", "run", "wait", "continue_",
                      "finish", "emitted", "stop", "destroy"]:
            spec.optional_output(label)

    def __init__(self):
        super(ProcessEventsTester, self).__init__()
        self._emitted = False

    @override
    def on_create(self, pid, inputs, saved_instance_state):
        super(ProcessEventsTester, self).on_create(
            pid, inputs, saved_instance_state)
        self.out("create", Bool(True))

    @override
    def on_run(self):
        super(ProcessEventsTester, self).on_run()
        self.out("run", Bool(True))

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        super(ProcessEventsTester, self)._on_output_emitted(
            output_port, value, dynamic)
        if not self._emitted:
            self._emitted = True
            self.out("emitted", Bool(True))

    @override
    def on_wait(self, wait_on):
        super(ProcessEventsTester, self).on_wait(wait_on)
        self.out("wait", Bool(True))

    @override
    def on_continue(self, wait_on):
        super(ProcessEventsTester, self).on_continue(wait_on)
        self.out("continue_", Bool(True))

    @override
    def on_finish(self):
        super(ProcessEventsTester, self).on_finish()
        self.out("finish", Bool(True))

    @override
    def on_stop(self):
        super(ProcessEventsTester, self).on_stop()
        self.out("stop", Bool(True))

    @override
    def on_destroy(self):
        super(ProcessEventsTester, self).on_destroy()
        self.out("destroy", Bool(True))

    @override
    def _run(self):
        return checkpoint(self.finish)

    def finish(self, wait_on):
        pass


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_asyncd(self):
        # This call should create an entry in the database with a PK
        pk = asyncd(DummyProcess)
        self.assertIsNotNone(pk)
        self.assertIsNotNone(load_node(pk=pk))

    def test_tick(self):
        import tempfile
        storage = PicklePersistence(
            auto_persist=False, running_directory=tempfile.mkdtemp())
        registry = ProcessRegistry()

        pk = asyncd(ProcessEventsTester, _jobs_store=storage)
        # Tick the engine a number of times or until there is no more work
        i = 0
        while daemon.tick_workflow_engine(storage):
            self.assertLess(i, 10, "Engine not done after 10 ticks")
            i += 1
        self.assertTrue(registry.has_finished(pk))
