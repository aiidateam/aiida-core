# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import inspect

from aiida.backends.testbase import AiidaTestCase
from aiida.work.workchain import WorkChain, \
    ToContext, _Block, _If, _While, if_, while_, return_
from aiida.work.workchain import _WorkChainSpec, Outputs
from aiida.work.workfunction import workfunction
from aiida.orm.data.base import Int, Str
import aiida.work.utils as util
from aiida.workflows.wf_demo import WorkflowDemo
from aiida.daemon.workflowmanager import execute_steps
from aiida import work


def run(process_or_workfunction, *args, **inputs):
    with work.create_runner(submit_to_daemon=False, rmq_control_panel=None) as runner:
        return work.rrun(runner, process_or_workfunction, *args, **inputs)


class Wf(WorkChain):
    # Keep track of which steps were completed by the workflow
    finished_steps = {}

    @classmethod
    def define(cls, spec):
        super(Wf, cls).define(spec)
        spec.input("value")
        spec.input("n")
        spec.dynamic_output()
        spec.outline(
            cls.s1,
            if_(cls.isA)(
                cls.s2
            ).elif_(cls.isB)(
                cls.s3
            ).else_(
                cls.s4
            ),
            cls.s5,
            while_(cls.ltN)(
                cls.s6
            ),
        )

    def __init__(self, inputs=None, pid=None, logger=None):
        super(Wf, self).__init__(inputs, pid, logger)
        # Reset the finished step
        self.finished_steps = {
            k: False for k in
            [self.s1.__name__, self.s2.__name__, self.s3.__name__,
             self.s4.__name__, self.s5.__name__, self.s6.__name__,
             self.isA.__name__, self.isB.__name__, self.ltN.__name__]
        }

    def s1(self):
        self._set_finished(inspect.stack()[0][3])

    def s2(self):
        self._set_finished(inspect.stack()[0][3])

    def s3(self):
        self._set_finished(inspect.stack()[0][3])

    def s4(self):
        self._set_finished(inspect.stack()[0][3])

    def s5(self):
        self.ctx.counter = 0
        self._set_finished(inspect.stack()[0][3])

    def s6(self):
        self.ctx.counter = self.ctx.counter + 1
        self._set_finished(inspect.stack()[0][3])

    def isA(self):
        self._set_finished(inspect.stack()[0][3])
        return self.inputs.value.value == 'A'

    def isB(self):
        self._set_finished(inspect.stack()[0][3])
        return self.inputs.value.value == 'B'

    def ltN(self):
        keep_looping = self.ctx.counter < self.inputs.n.value
        if not keep_looping:
            self._set_finished(inspect.stack()[0][3])
        return keep_looping

    def _set_finished(self, function_name):
        self.finished_steps[function_name] = True


class TestWorkchain(AiidaTestCase):
    def setUp(self):
        super(TestWorkchain, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestWorkchain, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_run(self):
        A = Str('A')
        B = Str('B')
        C = Str('C')
        three = Int(3)

        # Try the if(..) part
        run(Wf, value=A, n=three)
        # Check the steps that should have been run
        for step, finished in Wf.finished_steps.iteritems():
            if step not in ['s3', 's4', 'isB']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the elif(..) part
        finished_steps = run(Wf, value=B, n=three)
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 's4']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the else... part
        finished_steps = run(Wf, value=C, n=three)
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 'isB', 's3']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

    def test_incorrect_outline(self):
        class Wf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                # Try defining an invalid outline
                spec.outline(5)

        with self.assertRaises(ValueError):
            Wf.spec()

    def test_context(self):
        A = Str("a")
        B = Str("b")

        @workfunction
        def a():
            return A

        @workfunction
        def b():
            return B

        class Wf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.outline(cls.s1, cls.s2, cls.s3)

            def s1(self):
                return ToContext(
                    r1=Outputs(self.runner.submit(a)),
                    r2=Outputs(self.runner.submit(b)))

            def s2(self):
                assert self.ctx.r1['_return'] == A
                assert self.ctx.r2['_return'] == B

                # Try overwriting r1
                return ToContext(r1=Outputs(self.runner.submit(b)))

            def s3(self):
                assert self.ctx.r1['_return'] == B
                assert self.ctx.r2['_return'] == B

        run(Wf)

    def test_str(self):
        self.assertIsInstance(str(Wf.spec()), basestring)

    def test_malformed_outline(self):
        """
        Test some malformed outlines
        """
        spec = _WorkChainSpec()

        with self.assertRaises(ValueError):
            spec.outline(5)

        with self.assertRaises(ValueError):
            spec.outline(type)

    def test_checkpointing(self):
        A = Str('A')
        B = Str('B')
        C = Str('C')
        three = Int(3)

        # Try the if(..) part
        finished_steps = \
            self._run_with_checkpoints(Wf, inputs={'value': A, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['s3', 's4', 'isB']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the elif(..) part
        finished_steps = \
            self._run_with_checkpoints(Wf, inputs={'value': B, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 's4']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the else... part
        finished_steps = \
            self._run_with_checkpoints(Wf, inputs={'value': C, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 'isB', 's3']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

    def test_return(self):
        class WcWithReturn(WorkChain):
            @classmethod
            def define(cls, spec):
                super(WcWithReturn, cls).define(spec)
                spec.outline(
                    cls.s1,
                    if_(cls.isA)(
                        return_
                    ),
                    cls.after
                )

            def s1(self):
                pass

            def isA(self):
                return True

            def after(self):
                raise RuntimeError("Shouldn't get here")

        run(WcWithReturn)

    def test_tocontext_submit_workchain_no_daemon(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(MainWorkChain, cls).define(spec)
                spec.outline(cls.run, cls.check)
                spec.dynamic_output()

            def run(self):
                return ToContext(subwc=self.runner.submit(SubWorkChain))

            def check(self):
                assert self.ctx.subwc.out.value == Int(5)

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(SubWorkChain, cls).define(spec)
                spec.outline(cls.run)

            def run(self):
                self.out("value", Int(5))

        run(MainWorkChain)

    def test_tocontext_schedule_workchain(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(MainWorkChain, cls).define(spec)
                spec.outline(cls.run, cls.check)
                spec.dynamic_output()

            def run(self):
                return ToContext(subwc=self.runner.submit(SubWorkChain))

            def check(self):
                assert self.ctx.subwc.out.value == Int(5)

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(SubWorkChain, cls).define(spec)
                spec.outline(cls.run)

            def run(self):
                self.out("value", Int(5))

        run(MainWorkChain)

    def test_report_dbloghandler(self):
        """
        Test whether the WorkChain, through its Process, has a logger
        set for which the DbLogHandler has been attached. Because if this
        is not the case, the 'report' method will not actually hit the
        DbLogHandler and the message will not be stored in the database
        """

        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(TestWorkChain, cls).define(spec)
                spec.outline(cls.run, cls.check)
                spec.dynamic_output()

            def run(self):
                from aiida.orm.backend import construct
                self._backend = construct()
                self._backend.log.delete_many({})
                self.report("Testing the report function")
                return

            def check(self):
                logs = self._backend.log.find()
                assert len(logs) == 1

        run(TestWorkChain)

    def test_to_context(self):
        val = Int(5)

        @workfunction
        def wf():
            return val

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Workchain, cls).define(spec)
                spec.outline(cls.run, cls.result)

            def run(self):
                self.to_context(result_a=Outputs(self.runner.submit(wf)))
                return ToContext(result_b=Outputs(self.runner.submit(wf)))

            def result(self):
                assert self.ctx.result_a['_return'] == val
                assert self.ctx.result_b['_return'] == val
                return

        run(Workchain)

    def _run_with_checkpoints(self, wf_class, inputs=None):
        proc = wf_class(inputs=inputs)
        run(proc)

        return wf_class.finished_steps


class TestWorkchainWithOldWorkflows(AiidaTestCase):
    def test_call_old_wf(self):
        wf = WorkflowDemo()
        wf.start()
        while wf.is_running():
            execute_steps()

        class _TestWf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(_TestWf, cls).define(spec)
                spec.outline(cls.start, cls.check)

            def start(self):
                return ToContext(wf=self.runner.submit(work.legacy.WaitOnWorkflow, wf.pk))

            def check(self):
                assert self.ctx.wf is not None

        run(_TestWf)

    def test_old_wf_results(self):
        wf = WorkflowDemo()
        wf.start()
        while wf.is_running():
            execute_steps()

        class _TestWf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(_TestWf, cls).define(spec)
                spec.outline(cls.start, cls.check)

            def start(self):
                return ToContext(res=Outputs(self.runner.submit(work.legacy.WaitOnWorkflow, wf.pk)))

            def check(self):
                assert set(self.ctx.res) == set(wf.get_results())

        run(_TestWf)
