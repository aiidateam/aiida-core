
import unittest
import tempfile
from os.path import join
from shutil import rmtree

import aiida.workflows2.daemon as daemon
from aiida.orm.data.base import TRUE
from aiida.workflows2.process import Process
from aiida.workflows2.process_registry import ProcessRegistry
from aiida.workflows2.run import submit
from aiida.common.lang import override
from plum.wait_ons import checkpoint
from plum.persistence.pickle_persistence import PicklePersistence
from aiida.orm import load_node
import aiida.workflows2.util as util
from aiida.workflows2.test_utils import DummyProcess, ExceptionProcess


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
        self.out("create", TRUE)

    @override
    def on_run(self):
        super(ProcessEventsTester, self).on_run()
        self.out("run", TRUE)

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        super(ProcessEventsTester, self)._on_output_emitted(
            output_port, value, dynamic)
        if not self._emitted:
            self._emitted = True
            self.out("emitted", TRUE)

    @override
    def on_wait(self, wait_on):
        super(ProcessEventsTester, self).on_wait(wait_on)
        self.out("wait", TRUE)

    @override
    def on_continue(self, wait_on):
        super(ProcessEventsTester, self).on_continue(wait_on)
        self.out("continue_", TRUE)

    @override
    def on_finish(self):
        super(ProcessEventsTester, self).on_finish()
        self.out("finish", TRUE)

    @override
    def on_stop(self):
        super(ProcessEventsTester, self).on_stop()
        self.out("stop", TRUE)

    @override
    def on_destroy(self):
        super(ProcessEventsTester, self).on_destroy()
        self.out("destroy", TRUE)

    @override
    def _run(self):
        return checkpoint(self.finish)

    def finish(self, wait_on):
        pass


class TestDaemon(unittest.TestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

        self.storedir = tempfile.mkdtemp()
        self.storage = PicklePersistence(
            running_directory=join(self.storedir, 'r'),
            finished_directory=join(self.storedir, 'fin'),
            failed_directory=join(self.storedir, 'fail'))

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        rmtree(self.storedir)

    def test_asyncd(self):
        # This call should create an entry in the database with a PK
        pk = submit(DummyProcess)
        self.assertIsNotNone(pk)
        self.assertIsNotNone(load_node(pk=pk))

    def test_tick(self):
        registry = ProcessRegistry()

        pk = submit(ProcessEventsTester, _jobs_store=self.storage)
        # Tick the engine a number of times or until there is no more work
        i = 0
        while daemon.tick_workflow_engine(self.storage, print_exceptions=False):
            self.assertLess(i, 10, "Engine not done after 10 ticks")
            i += 1
        self.assertTrue(registry.has_finished(pk))

    def test_multiple_processes(self):
        submit(DummyProcess, _jobs_store=self.storage)
        submit(ExceptionProcess, _jobs_store=self.storage)
        submit(ExceptionProcess, _jobs_store=self.storage)
        submit(DummyProcess, _jobs_store=self.storage)

        self.assertFalse(daemon.tick_workflow_engine(self.storage, print_exceptions=False))
