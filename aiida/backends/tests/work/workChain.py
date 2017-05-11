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
import unittest

from aiida.backends.testbase import AiidaTestCase
import plum.process_monitor
from plum.wait_ons import wait_until
from aiida.orm.calculation.work import WorkCalculation
from aiida.orm.calculation.job.quantumespresso.pw import PwCalculation
from aiida.orm.data.base import Int, Str
import aiida.work.util as util
from aiida.common.links import LinkType
from aiida.workflows.wf_demo import WorkflowDemo
from aiida.work.workchain import WorkChain, \
    ToContext, _Block, _If, _While, if_, while_, return_, assign_, append_
from aiida.work.workchain import ToContext, _WorkChainSpec, Outputs
from aiida.work import workfunction, ProcessState, run, async, submit
from aiida.work.run import legacy_workflow
import aiida.work.globals
from aiida.daemon.workflowmanager import execute_steps

PwProcess = PwCalculation.process()


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
        self._set_finished(inspect.stack()[0][3])

    def s6(self):
        self.ctx.counter = self.ctx.get('counter', 0) + 1
        self._set_finished(inspect.stack()[0][3])

    def isA(self):
        self._set_finished(inspect.stack()[0][3])
        return self.inputs.value.value == 'A'

    def isB(self):
        self._set_finished(inspect.stack()[0][3])
        return self.inputs.value.value == 'B'

    def ltN(self):
        keep_looping = self.ctx.get('counter') < self.inputs.n.value
        if not keep_looping:
            self._set_finished(inspect.stack()[0][3])
        return keep_looping

    def _set_finished(self, function_name):
        self.finished_steps[function_name] = True


class TestContext(AiidaTestCase):
    def test_attributes(self):
        c = WorkChain.Context()
        c.new_attr = 5
        self.assertEqual(c.new_attr, 5)

        del c.new_attr
        with self.assertRaises(AttributeError):
            c.new_attr

    def test_dict(self):
        c = WorkChain.Context()
        c['new_attr'] = 5
        self.assertEqual(c['new_attr'], 5)

        del c['new_attr']
        with self.assertRaises(KeyError):
            c['new_attr']


class TestWorkchain(AiidaTestCase):
    def setUp(self):
        super(TestWorkchain, self).setUp()

        self.procman = aiida.work.globals.get_process_manager()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)
        self.assertEquals(aiida.work.globals.get_event_emitter().num_listening(), 0)

    def tearDown(self):
        super(TestWorkchain, self).tearDown()

        self.procman.abort_all(timeout=10.)
        self.assertEqual(self.procman.get_num_processes(), 0, "Failed to abort all processes")
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)
        self.assertEquals(aiida.work.globals.get_event_emitter().num_listening(), 0)

    def test_run(self):
        A = Str('A')
        B = Str('B')
        C = Str('C')
        three = Int(3)

        # Try the if(..) part
        Wf.run(value=A, n=three)
        # Check the steps that should have been run
        for step, finished in Wf.finished_steps.iteritems():
            if step not in ['s3', 's4', 'isB']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the elif(..) part
        finished_steps = Wf.run(value=B, n=three)
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 's4']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the else... part
        finished_steps = Wf.run(value=C, n=three)
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

    # @unittest.skip("Currently trying to find the bug that cases this test to deadlock.")
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
                return ToContext(r1=Outputs(async(a)), r2=Outputs(async(b)))

            def s2(self):
                assert self.ctx.r1['_return'] == A
                assert self.ctx.r2['_return'] == B

                # Try overwriting r1
                return ToContext(r1=Outputs(async(b)))

            def s3(self):
                assert self.ctx.r1['_return'] == B
                assert self.ctx.r2['_return'] == B

        Wf.run()

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

        WcWithReturn.run()

    def test_tocontext_submit_workchain_no_daemon(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(MainWorkChain, cls).define(spec)
                spec.outline(cls.run, cls.check)
                spec.dynamic_output()

            def run(self):
                return ToContext(subwc=submit(SubWorkChain))

            def check(self):
                assert self.ctx.subwc.out.value == Int(5)

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(SubWorkChain, cls).define(spec)
                spec.outline(cls.run)

            def run(self):
                self.out("value", Int(5))

        p = MainWorkChain.new()
        future = self.procman.play(p)
        self.assertTrue(wait_until(p, ProcessState.WAITING, timeout=4.))
        self.assertTrue(future.abort(timeout=3600.), "Failed to abort process")

    def test_tocontext_async_workchain(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(MainWorkChain, cls).define(spec)
                spec.outline(cls.run, cls.check)
                spec.dynamic_output()

            def run(self):
                return ToContext(subwc=async(SubWorkChain))

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

    def test_insert_interstep_assign(self):
        val = Int(5)

        @workfunction
        def wf():
            return val

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Workchain, cls).define(spec)
                spec.outline(cls.run, cls.test)

            def run(self):
                self.insert_intersteps(ToContext(result_a=Outputs(async(wf))))
                self.insert_intersteps(ToContext(result_b=assign_(Outputs(async(wf)))))
                return

            def test(self):
                assert self.ctx.result_a['_return'] == val
                assert self.ctx.result_b['_return'] == val
                return

        run(Workchain)

    # def test_insert_interstep_append(self):
    #     val = Int(5)
    #
    #     @workfunction
    #     def wf():
    #         return val
    #
    #     class Workchain(WorkChain):
    #         @classmethod
    #         def define(cls, spec):
    #             super(Workchain, cls).define(spec)
    #             spec.outline(cls.run, cls.test)
    #
    #         def run(self):
    #             self.insert_intersteps(ToContext(result_a=append_(Outputs(async(wf)))))
    #             self.insert_intersteps(ToContext(result_a=append_(Outputs(async(wf)))))
    #             return
    #
    #         def test(self):
    #             assert self.ctx.result_a[0]['_return'] == val
    #             assert len(self.ctx.result_a) == 2
    #             return
    #
    #     run(Workchain)

    # def test_insert_interstep_assign_append(self):
    #     val = Int(5)
    #
    #     @workfunction
    #     def wf():
    #         return val
    #
    #     class Workchain(WorkChain):
    #         @classmethod
    #         def define(cls, spec):
    #             super(Workchain, cls).define(spec)
    #             spec.outline(cls.run, cls.result)
    #
    #         def run(self):
    #             self.insert_intersteps(ToContext(result_a=assign_(Outputs(async(wf)))))
    #             self.insert_intersteps(ToContext(result_a=append_(Outputs(async(wf)))))
    #             return
    #
    #         def result(self):
    #             return
    #
    #     with self.assertRaises(TypeError):
    #         run(Workchain)

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
                self.to_context(result_a=Outputs(async(wf)))
                return ToContext(result_b=Outputs(async(wf)))

            def result(self):
                assert self.ctx.result_a['_return'] == val
                assert self.ctx.result_b['_return'] == val
                return

        run(Workchain)

    def _run_with_checkpoints(self, wf_class, inputs=None):
        wf = wf_class.new(inputs)
        wf.play()

        return wf_class.finished_steps


# class TestWorkchainWithOldWorkflows(AiidaTestCase):
#     def test_call_old_wf(self):
#         wf = WorkflowDemo()
#         wf.start()
#         while wf.is_running():
#             execute_steps()
#
#         class _TestWf(WorkChain):
#             @classmethod
#             def define(cls, spec):
#                 super(_TestWf, cls).define(spec)
#                 spec.outline(cls.start, cls.check)
#
#             def start(self):
#                 return ToContext(wf=legacy_workflow(wf.pk))
#
#             def check(self):
#                 assert self.ctx.wf is not None
#
#         _TestWf.run()
#
#     def test_old_wf_results(self):
#         wf = WorkflowDemo()
#         wf.start()
#         while wf.is_running():
#             execute_steps()
#
#         class _TestWf(WorkChain):
#             @classmethod
#             def define(cls, spec):
#                 super(_TestWf, cls).define(spec)
#                 spec.outline(cls.start, cls.check)
#
#             def start(self):
#                 return ToContext(res=Outputs(legacy_workflow(wf.pk)))
#
#             def check(self):
#                 assert set(self.ctx.res) == set(wf.get_results())
#
#         _TestWf.run()


class TestHelpers(AiidaTestCase):
    """
    Test the helper functions/classes used by workchains
    """

    def test_get_proc_outputs(self):
        c = WorkCalculation()
        a = Int(5)
        b = Int(10)
        a.add_link_from(c, u'a', link_type=LinkType.CREATE)
        b.add_link_from(c, u'b', link_type=LinkType.CREATE)
        c.store()
        for n in [a, b, c]:
            n.store()

        from aiida.work.interstep import _get_proc_outputs_from_registry
        outputs = _get_proc_outputs_from_registry(c.pk)
        self.assertListEqual(outputs.keys(), [u'a', u'b'])
        self.assertEquals(outputs['a'], a)
        self.assertEquals(outputs['b'], b)
