# -*- coding: utf-8 -*-
import unittest
import aiida.workflows2.daemon as daemon
from aiida.workflows2.db_types import Bool
from aiida.workflows2.defaults import factory
from aiida.workflows2.process import Process
from aiida.workflows2.process_registry import ProcessRegistry
from aiida.workflows2.run import asyncd
from aiida.common.lang import override
from plum.wait_ons import checkpoint
from plum.persistence.pickle_persistence import PicklePersistence
from aiida.orm import load_node


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

class DummyProcess(Process):
    def _run(self):
        pass


class ProcessEventsTester(Process):
    EVENTS = ["create", "start", "continue_", "finish", "emitted", "stop",
              "destroy", ]

    @classmethod
    def _define(cls, spec):
        for label in ["create", "recreate", "start", "wait", "continue_",
                      "finish", "emitted", "stop", "destroy"]:
            spec.optional_output(label)

    def __init__(self, store_provenance=True):
        super(ProcessEventsTester, self).__init__(store_provenance)
        self._emitted = False

    @override
    def on_create(self, pid, inputs=None):
        super(ProcessEventsTester, self).on_create(pid, inputs)
        self.out("create", Bool(True))

    @override
    def on_recreate(self, pid, saved_instance_state):
        super(ProcessEventsTester, self).on_recreate(pid,
                                                     saved_instance_state)
        self.out("recreate", Bool(True))

    @override
    def on_start(self):
        super(ProcessEventsTester, self).on_start()
        self.out("start", Bool(True))

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
    def on_finish(self, retval):
        super(ProcessEventsTester, self).on_finish(retval)
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
    def test_asyncd(self):
        # This call should create an entry in the database with a PK
        pk = asyncd(DummyProcess)
        self.assertIsNotNone(pk)
        self.assertIsNotNone(load_node(pk=pk))

    def test_tick(self):
        import tempfile
        storage = PicklePersistence(factory, tempfile.mkdtemp())
        registry = ProcessRegistry(storage)

        pk = asyncd(ProcessEventsTester, _jobs_store=storage)
        # Tick the engine a number of times or until there is no more work
        for i in range(0, 100):
            if not daemon.tick_workflow_engine(registry):
                break
        self.assertTrue(registry.is_finished(pk))
