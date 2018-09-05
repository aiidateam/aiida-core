# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
import plumpy

from aiida.backends.testbase import AiidaTestCase
from aiida import work
from aiida.workflows.wf_demo import WorkflowDemo
from aiida.daemon.workflowmanager import execute_steps
from . import utils


class Proc(work.Process):
    def _run(self):
        pass


def the_hans_klok_comeback(loop):
    loop.stop()


class TestWorkchain(AiidaTestCase):
    def setUp(self):
        super(TestWorkchain, self).setUp()
        self.runner = utils.create_test_runner()

    def tearDown(self):
        self.runner.close()
        self._runner = None

    def test_call_on_calculation_finish(self):
        loop = self.runner.loop
        proc = Proc(runner=self.runner)
        future = plumpy.Future()

        def calc_done(pk):
            self.assertEqual(pk, proc.calc.pk)
            loop.stop()
            future.set_result(True)

        self.runner.call_on_calculation_finish(proc.calc.pk, calc_done)

        # Run the calculation
        self.runner.loop.add_callback(proc.step_until_terminated)
        self._run_loop_for(5.)

        self.assertTrue(future.result())

    def test_call_on_wf_finish(self):
        loop = self.runner.loop
        future = plumpy.Future()

        # Need to start() so it's stored
        wf = WorkflowDemo()
        wf.start()

        def wf_done(pk):
            self.assertEqual(pk, wf.pk)
            loop.stop()
            future.set_result(True)

        self.runner.call_on_legacy_workflow_finish(wf.pk, wf_done)

        # Run the wf
        while wf.is_running():
            execute_steps()

        self._run_loop_for(10.)
        self.assertTrue(future.result())

    def _run_loop_for(self, seconds):
        loop = self.runner.loop
        loop.call_later(seconds, the_hans_klok_comeback, self.runner.loop)
        loop.start()


class TestRunner(AiidaTestCase):
    def setUp(self):
        super(TestWorkchain, self).setUp()
        self.runner = work.runners.new_runner(rmq_submit=True)

    def tearDown(self):
        super(TestWorkchain, self).tearDown()
        self.runner.close()
        self.runner = None
        work.runners.set_runner(None)
