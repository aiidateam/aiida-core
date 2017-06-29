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
import unittest

from plum.wait_ons import Checkpoint

from aiida.work.persistence import Persistence
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.data.base import get_true_node
import aiida.work.daemon as daemon
from aiida.work.process import Process
from aiida.work.process_registry import ProcessRegistry
from aiida.work.run import submit
from aiida.common.lang import override
from aiida.orm import load_node
import aiida.work.util as util
from aiida.work.test_utils import DummyProcess, ExceptionProcess
import aiida.work.daemon as work_daemon
from aiida.work.util import CalculationHeartbeat


class ProcessEventsTester(Process):
    EVENTS = ["create", "start", "run", "wait", "resume", "finish", "emitted",
              "stop", "failed", ]

    @classmethod
    def define(cls, spec):
        super(ProcessEventsTester, cls).define(spec)
        for label in ["create", "start", "run", "wait", "resume",
                      "finish", "emitted", "stop"]:
            spec.optional_output(label)

    def __init__(self, inputs, pid, logger=None):
        super(ProcessEventsTester, self).__init__(inputs, pid, logger)
        self._emitted = False

    @override
    def on_create(self):
        super(ProcessEventsTester, self).on_create()
        self.out("create", get_true_node())

    @override
    def on_start(self):
        super(ProcessEventsTester, self).on_start()
        self.out("start", get_true_node())

    @override
    def on_run(self):
        super(ProcessEventsTester, self).on_run()
        self.out("run", get_true_node())

    @override
    def on_output_emitted(self, output_port, value, dynamic):
        super(ProcessEventsTester, self).on_output_emitted(
            output_port, value, dynamic)
        if not self._emitted:
            self._emitted = True
            self.out("emitted", get_true_node())

    @override
    def on_wait(self, wait_on):
        super(ProcessEventsTester, self).on_wait(wait_on)
        self.out("wait", get_true_node())

    @override
    def on_resume(self):
        super(ProcessEventsTester, self).on_resume()
        self.out("resume", get_true_node())

    @override
    def on_finish(self):
        super(ProcessEventsTester, self).on_finish()
        self.out("finish", get_true_node())

    @override
    def on_stop(self):
        super(ProcessEventsTester, self).on_stop()
        self.out("stop", get_true_node())

    @override
    def _run(self):
        return Checkpoint(), self.finish

    def finish(self, wait_on):
        pass


class FailCreateFromSavedStateProcess(DummyProcess):
    """
    This class emulates a failure that occurs when loading the process from
    a saved state.
    """

    @override
    def load_instance_state(self, saved_state, logger):
        super(FailCreateFromSavedStateProcess, self).load_instance_state(saved_state)
        raise RuntimeError()


@unittest.skip("Moving to new daemon")
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
        while daemon.launch_pending_jobs(self.storage):
            self.assertLess(i, 10, "Engine not done after 10 ticks")
            i += 1
        self.assertTrue(registry.has_finished(rinfo.pid))

    def test_multiple_processes(self):
        submit(DummyProcess, _jobs_store=self.storage)
        submit(ExceptionProcess, _jobs_store=self.storage)
        submit(ExceptionProcess, _jobs_store=self.storage)
        submit(DummyProcess, _jobs_store=self.storage)

        self.assertFalse(daemon.launch_pending_jobs(self.storage))

    def test_create_fail(self):
        registry = ProcessRegistry()

        dp_rinfo = submit(DummyProcess, _jobs_store=self.storage)
        fail_rinfo = submit(FailCreateFromSavedStateProcess, _jobs_store=self.storage)

        # Tick the engine a number of times or until there is no more work
        i = 0
        while daemon.launch_pending_jobs(self.storage):
            self.assertLess(i, 10, "Engine not done after 10 ticks")
            i += 1

        self.assertTrue(registry.has_finished(dp_rinfo.pid))
        self.assertFalse(registry.has_finished(fail_rinfo.pid))


class TestJobCalculationDaemon(AiidaTestCase):
    def test_launch_pending_submitted(self):
        num_at_start = len(work_daemon.get_all_pending_job_calculations())

        # Create the calclation
        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }
        c = JobCalculation(**calc_params)
        c.store()
        c.submit()

        self.assertIsNone(c.get_attr(CalculationHeartbeat.HEARTBEAT_EXPIRES, None))
        pending = work_daemon.get_all_pending_job_calculations()
        self.assertEqual(len(pending), num_at_start + 1)
        self.assertIn(c.pk, [p.pk for p in pending])

    def test_launch_pending_expired(self):
        num_at_start = len(work_daemon.get_all_pending_job_calculations())

        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }
        c = JobCalculation(**calc_params)
        c._set_attr(CalculationHeartbeat.HEARTBEAT_EXPIRES, 0)
        c.store()
        c.submit()

        pending = work_daemon.get_all_pending_job_calculations()
        self.assertEqual(len(pending), num_at_start + 1)
        self.assertIn(c.pk, [p.pk for p in pending])
