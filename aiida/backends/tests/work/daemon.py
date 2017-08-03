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
import tempfile
from shutil import rmtree

from plum.wait_ons import checkpoint

from aiida.work.persistence import Persistence
from aiida.orm.data.base import get_true_node
import aiida.work.daemon as daemon
from aiida.work.process import Process
from aiida.work.process_registry import ProcessRegistry
from aiida.work.run import submit
from aiida.common.lang import override
from aiida.orm import load_node
import aiida.work.util as util
from aiida.work.test_utils import DummyProcess, ExceptionProcess


class ProcessEventsTester(Process):
    EVENTS = ["create", "run", "continue_", "finish", "emitted", "stop",
              "destroy", ]

    @classmethod
    def define(cls, spec):
        super(ProcessEventsTester, cls).define(spec)
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
        self.out("create", get_true_node())

    @override
    def on_run(self):
        super(ProcessEventsTester, self).on_run()
        self.out("run", get_true_node())

    @override
    def _on_output_emitted(self, output_port, value, dynamic):
        super(ProcessEventsTester, self)._on_output_emitted(
            output_port, value, dynamic)
        if not self._emitted:
            self._emitted = True
            self.out("emitted", get_true_node())

    @override
    def on_wait(self, wait_on):
        super(ProcessEventsTester, self).on_wait(wait_on)
        self.out("wait", get_true_node())

    @override
    def on_continue(self, wait_on):
        super(ProcessEventsTester, self).on_continue(wait_on)
        self.out("continue_", get_true_node())

    @override
    def on_finish(self):
        super(ProcessEventsTester, self).on_finish()
        self.out("finish", get_true_node())

    @override
    def on_stop(self):
        super(ProcessEventsTester, self).on_stop()
        self.out("stop", get_true_node())

    @override
    def on_destroy(self):
        super(ProcessEventsTester, self).on_destroy()
        self.out("destroy", get_true_node())

    @override
    def _run(self):
        return checkpoint(self.finish)

    def finish(self, wait_on):
        pass


class FailCreateFromSavedStateProcess(DummyProcess):
    """
    This class emulates a failure that occurs when loading the process from
    a saved state.
    """

    @override
    def on_create(self, pid, inputs, saved_instance_state):
        super(FailCreateFromSavedStateProcess, self).on_create(
            pid, inputs, saved_instance_state)
        if saved_instance_state is not None:
            raise RuntimeError()


class TestDaemon(AiidaTestCase):
    def setUp(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)

        self.storedir = tempfile.mkdtemp()
        self.storage = Persistence.create_from_basedir(self.storedir)

    def tearDown(self):
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        rmtree(self.storedir)

    def test_submit(self):
        # This call should create an entry in the database with a PK
        rinfo = submit(DummyProcess)
        self.assertIsNotNone(rinfo)
        self.assertIsNotNone(load_node(pk=rinfo.pid))

    def test_tick(self):
        registry = ProcessRegistry()

        rinfo = submit(ProcessEventsTester, _jobs_store=self.storage)
        # Tick the engine a number of times or until there is no more work
        i = 0
        while daemon.tick_workflow_engine(self.storage, print_exceptions=False):
            self.assertLess(i, 10, "Engine not done after 10 ticks")
            i += 1
        self.assertTrue(registry.has_finished(rinfo.pid))

    def test_multiple_processes(self):
        submit(DummyProcess, _jobs_store=self.storage)
        submit(ExceptionProcess, _jobs_store=self.storage)
        submit(ExceptionProcess, _jobs_store=self.storage)
        submit(DummyProcess, _jobs_store=self.storage)

        self.assertFalse(daemon.tick_workflow_engine(self.storage, print_exceptions=False))

    def test_create_fail(self):
        registry = ProcessRegistry()

        dp_rinfo = submit(DummyProcess, _jobs_store=self.storage)
        fail_rinfo = submit(FailCreateFromSavedStateProcess, _jobs_store=self.storage)

        # Tick the engine a number of times or until there is no more work
        i = 0
        while daemon.tick_workflow_engine(self.storage, print_exceptions=False):
            self.assertLess(i, 10, "Engine not done after 10 ticks")
            i += 1

        self.assertTrue(registry.has_finished(dp_rinfo.pid))
        self.assertFalse(registry.has_finished(fail_rinfo.pid))
