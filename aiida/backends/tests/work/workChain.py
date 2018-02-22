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
import aiida.backends.settings as settings

from aiida.orm import load_node
from aiida.backends.testbase import AiidaTestCase
from plum.engine.ticking import TickingEngine
from plum.persistence.bundle import Bundle
import plum.process_monitor
from aiida.orm.calculation.work import WorkCalculation
from aiida.work.workchain import WorkChain, \
    ToContext, _Block, _If, _While, if_, while_, return_
from aiida.work.workchain import _WorkChainSpec, Outputs
from aiida.work.workfunction import workfunction
from aiida.work.run import run, legacy_workflow
from aiida.orm.data.base import Int, Str, Bool
import aiida.work.util as util
from aiida.common.links import LinkType
from aiida.workflows.wf_demo import WorkflowDemo
from aiida.daemon.workflowmanager import execute_steps


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

    def __init__(self):
        super(Wf, self).__init__()
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


class IfTest(WorkChain):
    @classmethod
    def define(cls, spec):
        super(IfTest, cls).define(spec)
        spec.outline(
            if_(cls.condition)(
                cls.step1,
                cls.step2
            )
        )

    def on_create(self, pid, inputs, saved_state):
        super(IfTest, self).on_create(pid, inputs, saved_state)
        if saved_state is None:
            self.ctx.s1 = False
            self.ctx.s2 = False

    def condition(self):
        return True

    def step1(self):
        self.ctx.s1 = True

    def step2(self):
        self.ctx.s2 = True


class TestWorkchain(AiidaTestCase):
    def setUp(self):
        super(TestWorkchain, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestWorkchain, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

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

    def test_same_input_node(self):
        class Wf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.input('a', valid_type=Int)
                spec.input('b', valid_type=Int)
                # Try defining an invalid outline
                spec.outline(cls.check_a_b)

            def check_a_b(self):
                assert 'a' in self.inputs
                assert 'b' in self.inputs

        x = Int(1)
        run(Wf, a=x, b=x)

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
                self.ctx.r1 = run(a)
                self.ctx.r2 = run(b)

            def s2(self):
                assert self.ctx.r1 == A
                assert self.ctx.r2 == B

                # Try overwriting r1
                self.ctx.r1 = run(b)

            def s3(self):
                assert self.ctx.r1 == B
                assert self.ctx.r2 == B

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

    def test_if_block_persistence(self):
        """ This test was created to capture issue #902 """
        wc = IfTest.new_instance()

        while not wc.ctx.s1 and not wc.has_finished():
            wc.tick()
        self.assertTrue(wc.ctx.s1)
        self.assertFalse(wc.ctx.s2)

        # Now bundle the thing
        b = Bundle()
        wc.save_instance_state(b)
        # Abort the current one
        wc.stop()
        wc.destroy(execute=True)

        # Load from saved tate
        wc = IfTest.create_from(b)
        self.assertTrue(wc.ctx.s1)
        self.assertFalse(wc.ctx.s2)

        wc.run_until_complete()

    def _run_with_checkpoints(self, wf_class, inputs=None):
        finished_steps = {}

        te = TickingEngine()
        fut = te.submit(wf_class, inputs)
        while not fut.done():
            pid = fut.pid
            te.tick()
            finished_steps.update(wf_class.finished_steps)
        te.shutdown()

        return finished_steps


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
                return ToContext(wf=legacy_workflow(wf.pk))

            def check(self):
                assert self.ctx.wf is not None

        _TestWf.new_instance().run_until_complete()

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
                return ToContext(res=Outputs(legacy_workflow(wf.pk)))

            def check(self):
                assert set(self.ctx.res) == set(wf.get_results())

        _TestWf.new_instance().run_until_complete()


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


class TestWorkChainAbort(AiidaTestCase):
    """
    Test the functionality to abort a workchain
    """

    class AbortableWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super(TestWorkChainAbort.AbortableWorkChain, cls).define(spec)
            spec.outline(
                cls.start,
                cls.check
            )

        def start(self):
            pass

        def check(self):
            raise RuntimeError('should have been aborted by now')

    def setUp(self):
        super(TestWorkChainAbort, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestWorkChainAbort, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_simple_run(self):
        """
        Run the workchain which should hit the exception and therefore end
        up in the FAILED state
        """
        engine = TickingEngine()
        future = engine.submit(TestWorkChainAbort.AbortableWorkChain)

        while not future.done():
            engine.tick()

        self.assertEquals(future.process.calc.has_finished_ok(), False)
        self.assertEquals(future.process.calc.has_failed(), True)
        self.assertEquals(future.process.calc.has_aborted(), False)
        engine.shutdown()

    def test_simple_kill_through_node(self):
        """
        Run the workchain for one step and then kill it by calling kill
        on the underlying WorkCalculation node. This should have the
        workchain end up in the ABORTED state.
        """
        engine = TickingEngine()
        future = engine.submit(TestWorkChainAbort.AbortableWorkChain)

        while not future.done():
            engine.tick()
            future.process.calc.kill()

        self.assertEquals(future.process.calc.has_finished_ok(), False)
        self.assertEquals(future.process.calc.has_failed(), False)
        self.assertEquals(future.process.calc.has_aborted(), True)
        engine.shutdown()

    def test_simple_kill_through_process(self):
        """
        Run the workchain for one step and then kill it by calling kill
        on the workchain itself. This should have the workchain end up
        in the ABORTED state.
        """
        engine = TickingEngine()
        future = engine.submit(TestWorkChainAbort.AbortableWorkChain)

        while not future.done():
            engine.tick()
            future.process.abort()

        self.assertEquals(future.process.calc.has_finished_ok(), False)
        self.assertEquals(future.process.calc.has_failed(), False)
        self.assertEquals(future.process.calc.has_aborted(), True)
        engine.shutdown()


class TestWorkChainAbortChildren(AiidaTestCase):
    """
    Test the functionality to abort a workchain and verify that children
    are also aborted appropriately
    """

    class SubWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super(TestWorkChainAbortChildren.SubWorkChain, cls).define(spec)
            spec.outline(
                cls.start,
                cls.check
            )

        def start(self):
            pass

        def check(self):
            raise RuntimeError('should have been aborted by now')

    class MainWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super(TestWorkChainAbortChildren.MainWorkChain, cls).define(spec)
            spec.input('kill', default=Bool(False))
            spec.outline(
                cls.start,
                cls.check
            )

        def start(self):
            self.child = TestWorkChainAbortChildren.SubWorkChain.new_instance()
            if self.inputs.kill:
                self.calc.kill()
            self.child.run_until_complete()

        def check(self):
            raise RuntimeError('should have been aborted by now')

    def setUp(self):
        super(TestWorkChainAbortChildren, self).setUp()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def tearDown(self):
        super(TestWorkChainAbortChildren, self).tearDown()
        self.assertEquals(len(util.ProcessStack.stack()), 0)
        self.assertEquals(len(plum.process_monitor.MONITOR.get_pids()), 0)

    def test_simple_run(self):
        """
        Run the workchain which should hit the exception and therefore end
        up in the FAILED state
        """
        engine = TickingEngine()
        future = engine.submit(TestWorkChainAbortChildren.MainWorkChain)

        while not future.done():
            engine.tick()

        self.assertEquals(future.process.calc.has_finished_ok(), False)
        self.assertEquals(future.process.calc.has_failed(), True)
        self.assertEquals(future.process.calc.has_aborted(), False)
        engine.shutdown()

    def test_simple_kill_through_node(self):
        """
        Run the workchain for one step and then kill it by calling kill
        on the underlying WorkCalculation node. This should have the
        workchain end up in the ABORTED state.
        """
        engine = TickingEngine()
        future = engine.submit(TestWorkChainAbortChildren.MainWorkChain, {'kill': Bool(True)})

        while not future.done():
            engine.tick()

        child = future.process.calc.get_outputs(link_type=LinkType.CALL)[0]
        self.assertEquals(child.has_finished_ok(), False)
        self.assertEquals(child.has_failed(), False)
        self.assertEquals(child.has_aborted(), True)

        self.assertEquals(future.process.calc.has_finished_ok(), False)
        self.assertEquals(future.process.calc.has_failed(), False)
        self.assertEquals(future.process.calc.has_aborted(), True)
        engine.shutdown()
