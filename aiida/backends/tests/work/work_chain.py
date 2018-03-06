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
import plumpy
import plumpy.test_utils
import unittest

from aiida.backends.testbase import AiidaTestCase
from aiida.common.links import LinkType
from aiida.daemon.workflowmanager import execute_steps
from aiida.orm.data.bool import Bool
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int
from aiida.orm.data.str import Str
from aiida.work.utils import ProcessStack
from aiida.workflows.wf_demo import WorkflowDemo
from aiida import work
from aiida.work.workchain import *

from . import utils


def run_and_check_success(process_class, **kwargs):
    """
    Instantiates the process class and executes it followed by a check
    that it is finished successfully

    :returns: instance of process
    """
    process = process_class(inputs=kwargs)
    process.execute()
    assert process.calc.is_finished_ok == True

    return process


class Wf(work.WorkChain):
    # Keep track of which steps were completed by the workflow
    finished_steps = {}

    @classmethod
    def define(cls, spec):
        super(Wf, cls).define(spec)
        spec.input("value", default=Str('A'))
        spec.input("n", default=Int(3))
        spec.outputs.dynamic = True
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

    def on_create(self):
        super(Wf, self).on_create()
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


class ReturnWorkChain(WorkChain):

    FAILURE_STATUS = 1

    @classmethod
    def define(cls, spec):
        super(ReturnWorkChain, cls).define(spec)
        spec.input('success', valid_type=Bool)
        spec.outline(
            cls.failure,
            cls.success
        )

    def failure(self):
        if self.inputs.success.value is False:
            return self.FAILURE_STATUS

    def success(self):
        return


class TestFinishStatus(AiidaTestCase):

    def test_failing_workchain(self):
        result, node = work.launch.run_get_node(ReturnWorkChain, success=Bool(False))
        self.assertEquals(node.finish_status, ReturnWorkChain.FAILURE_STATUS)
        self.assertEquals(node.is_finished, True)
        self.assertEquals(node.is_finished_ok, False)
        self.assertEquals(node.is_failed, True)

    def test_successful_workchain(self):
        result, node = work.launch.run_get_node(ReturnWorkChain, success=Bool(True))
        self.assertEquals(node.finish_status, 0)
        self.assertEquals(node.is_finished, True)
        self.assertEquals(node.is_finished_ok, True)
        self.assertEquals(node.is_failed, False)


class IfTest(work.WorkChain):
    @classmethod
    def define(cls, spec):
        super(IfTest, cls).define(spec)
        spec.outline(
            if_(cls.condition)(
                cls.step1,
                cls.step2
            )
        )

    def on_create(self, *args, **kwargs):
        super(IfTest, self).on_create(*args, **kwargs)
        self.ctx.s1 = False
        self.ctx.s2 = False

    def condition(self):
        return True

    def step1(self):
        self.ctx.s1 = True
        self.pause()

    def step2(self):
        self.ctx.s2 = True


class TestContext(AiidaTestCase):
    def test_attributes(self):
        wc = work.WorkChain()
        wc.ctx.new_attr = 5
        self.assertEqual(wc.ctx.new_attr, 5)

        del wc.ctx.new_attr
        with self.assertRaises(AttributeError):
            wc.ctx.new_attr

    def test_dict(self):
        wc = work.WorkChain()
        wc.ctx['new_attr'] = 5
        self.assertEqual(wc.ctx['new_attr'], 5)

        del wc.ctx['new_attr']
        with self.assertRaises(KeyError):
            wc.ctx['new_attr']


class TestWorkchain(AiidaTestCase):

    def setUp(self):
        super(TestWorkchain, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestWorkchain, self).tearDown()
        work.set_runner(None)
        self.runner.close()
        self.runner = None
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_run(self):
        A = Str('A')
        B = Str('B')
        C = Str('C')
        three = Int(3)

        # Try the if(..) part
        work.launch.run(Wf, value=A, n=three)
        # Check the steps that should have been run
        for step, finished in Wf.finished_steps.iteritems():
            if step not in ['s3', 's4', 'isB']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the elif(..) part
        finished_steps = work.launch.run(Wf, value=B, n=three)
        # Check the steps that should have been run
        for step, finished in finished_steps.iteritems():
            if step not in ['isA', 's2', 's4']:
                self.assertTrue(
                    finished, "Step {} was not called by workflow".format(step))

        # Try the else... part
        finished_steps = work.launch.run(Wf, value=C, n=three)
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

        with self.assertRaises(TypeError):
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
        run_and_check_success(Wf, a=x, b=x)

    def test_context(self):
        A = Str("a")
        B = Str("b")

        class ReturnA(work.Process):
            def _run(self):
                self.out('res', A)
                return

        class ReturnB(work.Process):
            def _run(self):
                self.out('res', B)
                return

        class Wf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.outline(cls.s1, cls.s2, cls.s3)

            def s1(self):
                return ToContext(
                    r1=Outputs(self.submit(ReturnA)),
                    r2=Outputs(self.submit(ReturnB)))

            def s2(self):
                assert self.ctx.r1['res'] == A
                assert self.ctx.r2['res'] == B

                # Try overwriting r1
                return ToContext(r1=Outputs(self.submit(ReturnB)))

            def s3(self):
                assert self.ctx.r1['res'] == B
                assert self.ctx.r2['res'] == B

        run_and_check_success(Wf)

    def test_str(self):
        self.assertIsInstance(str(Wf.spec()), basestring)

    def test_malformed_outline(self):
        """
        Test some malformed outlines
        """
        spec = _WorkChainSpec()

        with self.assertRaises(TypeError):
            spec.outline(5)

        # Test a function with wrong number of args
        with self.assertRaises(TypeError):
            spec.outline(lambda x, y: None)

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

        run_and_check_success(WcWithReturn)

    def test_tocontext_submit_workchain_no_daemon(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(MainWorkChain, cls).define(spec)
                spec.outline(cls.do_run, cls.check)
                spec.outputs.dynamic = True

            def do_run(self):
                return ToContext(subwc=self.submit(SubWorkChain))

            def check(self):
                pass
                assert self.ctx.subwc.out.value == Int(5)

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(SubWorkChain, cls).define(spec)
                spec.outline(cls.do_run)

            def do_run(self):
                self.out("value", Int(5))

        run_and_check_success(MainWorkChain)

    def test_tocontext_schedule_workchain(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(MainWorkChain, cls).define(spec)
                spec.outline(cls.do_run, cls.check)
                spec.outputs.dynamic = True

            def do_run(self):
                return ToContext(subwc=self.submit(SubWorkChain))

            def check(self):
                assert self.ctx.subwc.out.value == Int(5)

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(SubWorkChain, cls).define(spec)
                spec.outline(cls.do_run)

            def do_run(self):
                self.out('value', Int(5))

        run_and_check_success(MainWorkChain)

    # @unittest.skip('This is currently broken after merge')
    def test_if_block_persistence(self):
        """
        This test was created to capture issue #902
        """
        wc = IfTest()
        wc.execute(True)
        self.assertTrue(wc.ctx.s1)
        self.assertFalse(wc.ctx.s2)

        # Now bundle the thing
        bundle = plumpy.Bundle(wc)

        # Load from saved tate
        wc2 = bundle.unbundle()
        self.assertTrue(wc2.ctx.s1)
        self.assertFalse(wc2.ctx.s2)
        wc2.execute()
        self.assertTrue(wc2.ctx.s1)
        self.assertTrue(wc2.ctx.s2)

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
                spec.outputs.dynamic = True

            def run(self):
                from aiida.orm.backend import construct
                self._backend = construct()
                self._backend.log.delete_many({})
                self.report("Testing the report function")
                return

            def check(self):
                logs = self._backend.log.find()
                assert len(logs) == 1

        run_and_check_success(TestWorkChain)

    def test_to_context(self):
        val = Int(5)

        class SimpleWc(work.Process):
            def _run(self):
                self.out('_return', val)
                return

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Workchain, cls).define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(result_a=Outputs(self.submit(SimpleWc)))
                return ToContext(result_b=Outputs(self.submit(SimpleWc)))

            def result(self):
                assert self.ctx.result_a['_return'] == val
                assert self.ctx.result_b['_return'] == val
                return

        run_and_check_success(Workchain)

    def test_persisting(self):
        persister = plumpy.test_utils.TestPersister()
        runner = work.new_runner(persister=persister)
        workchain = Wf(runner=runner)
        workchain.execute()

    def _run_with_checkpoints(self, wf_class, inputs=None):
        if inputs is None:
            inputs = {}
        proc = run_and_check_success(wf_class, **inputs)
        return proc.finished_steps


class TestWorkchainWithOldWorkflows(AiidaTestCase):
    def setUp(self):
        super(TestWorkchainWithOldWorkflows, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestWorkchainWithOldWorkflows, self).tearDown()
        work.set_runner(None)
        self.runner.close()
        self.runner = None
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_call_old_wf(self):
        wf = WorkflowDemo()
        wf.start()
        while wf.is_running():
            execute_steps()

        class _TestWf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(_TestWf, cls).define(spec)
                spec.outline(cls.begin, cls.check)

            def begin(self):
                return ToContext(wf=wf)

            def check(self):
                assert self.ctx.wf is not None

        run_and_check_success(_TestWf)

    def test_old_wf_results(self):
        wf = WorkflowDemo()
        wf.start()
        while wf.is_running():
            execute_steps()

        class _TestWf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(_TestWf, cls).define(spec)
                spec.outline(cls.begin, cls.check)

            def begin(self):
                return ToContext(res=Outputs(wf))

            def check(self):
                assert set(self.ctx.res) == set(wf.get_results())

        run_and_check_success(_TestWf)


class TestWorkChainAbort(AiidaTestCase):
    """
    Test the functionality to abort a workchain
    """

    def setUp(self):
        super(TestWorkChainAbort, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestWorkChainAbort, self).tearDown()
        work.set_runner(None)
        self.runner.close()
        self.runner = None
        self.assertEquals(len(ProcessStack.stack()), 0)

    class AbortableWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super(TestWorkChainAbort.AbortableWorkChain, cls).define(spec)
            spec.outline(
                cls.begin,
                cls.check
            )

        def begin(self):
            self.pause()

        def check(self):
            raise RuntimeError('should have been aborted by now')

    def test_simple_run(self):
        """
        Run the workchain which should hit the exception and therefore end
        up in the EXCEPTED state
        """
        process = TestWorkChainAbort.AbortableWorkChain()

        with self.assertRaises(RuntimeError):
            process.execute(True)
            process.execute()

        self.assertEquals(process.calc.is_finished_ok, False)
        self.assertEquals(process.calc.is_excepted, True)
        self.assertEquals(process.calc.is_killed, False)

    @unittest.skip('Process kill needs to be fixed')
    def test_simple_kill_through_process(self):
        """
        Run the workchain for one step and then kill it by calling kill
        on the workchain itself. This should have the workchain end up
        in the KILLED state.
        """
        process = TestWorkChainAbort.AbortableWorkChain()

        with self.assertRaises(plumpy.KilledError):
            process.execute(True)
            process.kill()
            process.execute()

        self.assertEquals(process.calc.is_finished_ok, False)
        self.assertEquals(process.calc.is_excepted, False)
        self.assertEquals(process.calc.is_killed, True)


class TestWorkChainAbortChildren(AiidaTestCase):
    """
    Test the functionality to abort a workchain and verify that children
    are also aborted appropriately
    """

    def setUp(self):
        super(TestWorkchainWithOldWorkflows, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestWorkchainWithOldWorkflows, self).tearDown()
        work.set_runner(None)
        self.runner.close()
        self.runner = None
        self.assertEquals(len(ProcessStack.stack()), 0)

    class SubWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super(TestWorkChainAbortChildren.SubWorkChain, cls).define(spec)
            spec.outline(
                cls.begin,
                cls.check
            )

        def begin(self):
            pass

        def check(self):
            raise RuntimeError('should have been aborted by now')

    class MainWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super(TestWorkChainAbortChildren.MainWorkChain, cls).define(spec)
            spec.input('kill', default=Bool(False))
            spec.outline(
                cls.begin,
                cls.check
            )

        def begin(self):
            self.ctx.child = TestWorkChainAbortChildren.SubWorkChain()
            self.ctx.child.start()
            if self.inputs.kill:
                self.kill()

        def check(self):
            raise RuntimeError('should have been aborted by now')

        def on_kill(self, msg):
            super(TestWorkChainAbortChildren.MainWorkChain, self).on_kill(msg)
            if self.inputs.kill:
                assert self.ctx.child.calc.is_killed == True, 'Child was not killed'

    def setUp(self):
        super(TestWorkChainAbortChildren, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestWorkChainAbortChildren, self).tearDown()
        work.set_runner(None)
        self.runner.close()
        self.runner = None
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_simple_run(self):
        """
        Run the workchain which should hit the exception and therefore end
        up in the EXCEPTED state
        """
        process = TestWorkChainAbortChildren.MainWorkChain()

        with self.assertRaises(RuntimeError):
            process.execute()

        self.assertEquals(process.calc.is_finished_ok, False)
        self.assertEquals(process.calc.is_excepted, True)
        self.assertEquals(process.calc.is_killed, False)

    @unittest.skip('This requires children kill support over RMQ #1060')
    def test_simple_kill_through_process(self):
        """
        Run the workchain for one step and then kill it. This should have the
        workchain and its children end up in the KILLED state.
        """
        process = TestWorkChainAbortChildren.MainWorkChain(inputs={'kill': Bool(True)})

        with self.assertRaises(plumpy.KilledError):
            process.execute()

        with self.assertRaises(plumpy.KilledError):
            process.ctx.child.execute()

        child = process.calc.get_outputs(link_type=LinkType.CALL)[0]
        self.assertEquals(child.is_finished_ok, False)
        self.assertEquals(child.is_excepted, False)
        self.assertEquals(child.is_killed, True)

        self.assertEquals(process.calc.is_finished_ok, False)
        self.assertEquals(process.calc.is_excepted, False)
        self.assertEquals(process.calc.is_killed, True)


class TestImmutableInputWorkchain(AiidaTestCase):
    """
    Test that inputs cannot be modified
    """

    def setUp(self):
        super(TestImmutableInputWorkchain, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestImmutableInputWorkchain, self).tearDown()
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_immutable_input(self):
        """
        Check that from within the WorkChain self.inputs returns an AttributesFrozendict which should be immutable
        """
        test_class = self

        class Wf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.input('a', valid_type=Int)
                spec.input('b', valid_type=Int)
                spec.outline(
                    cls.step_one,
                    cls.step_two,
                )

            def step_one(self):
                # Attempt to manipulate the inputs dictionary which since it is a AttributesFrozendict should raise
                with test_class.assertRaises(TypeError):
                    self.inputs['a'] = Int(3)
                with test_class.assertRaises(AttributeError):
                    self.inputs.pop('b')
                with test_class.assertRaises(TypeError):
                    self.inputs['c'] = Int(4)

            def step_two(self):
                # Verify that original inputs are still there with same value and no inputs were added
                test_class.assertIn('a', self.inputs)
                test_class.assertIn('b', self.inputs)
                test_class.assertNotIn('c', self.inputs)
                test_class.assertEquals(self.inputs['a'].value, 1)

        run_and_check_success(Wf, a=Int(1), b=Int(2))

    def test_immutable_input_groups(self):
        """
        Check that namespaced inputs also return AttributeFrozendicts and are hence immutable
        """
        test_class = self

        class Wf(WorkChain):
            @classmethod
            def define(cls, spec):
                super(Wf, cls).define(spec)
                spec.input_namespace('subspace', dynamic=True)
                spec.outline(
                    cls.step_one,
                    cls.step_two,
                )

            def step_one(self):
                # Attempt to manipulate the namespaced inputs dictionary which should raise
                with test_class.assertRaises(TypeError):
                    self.inputs.subspace['one'] = Int(3)
                with test_class.assertRaises(AttributeError):
                    self.inputs.subspace.pop('two')
                with test_class.assertRaises(TypeError):
                    self.inputs.subspace['four'] = Int(4)

            def step_two(self):
                # Verify that original inputs are still there with same value and no inputs were added
                test_class.assertIn('one', self.inputs.subspace)
                test_class.assertIn('two', self.inputs.subspace)
                test_class.assertNotIn('four', self.inputs.subspace)
                test_class.assertEquals(self.inputs.subspace['one'].value, 1)

        x = Int(1)
        y = Int(2)
        run_and_check_success(Wf, subspace={'one': Int(1), 'two': Int(2)})

class GrandParentExposeWorkChain(work.WorkChain):
    @classmethod
    def define(cls, spec):
        super(GrandParentExposeWorkChain, cls).define(spec)

        spec.expose_inputs(ParentExposeWorkChain, namespace='sub.sub')
        spec.expose_outputs(ParentExposeWorkChain, namespace='sub.sub')

        spec.outline(cls.do_run, cls.finalize)

    def do_run(self):
        return ToContext(child=self.submit(
            ParentExposeWorkChain,
            **self.exposed_inputs(ParentExposeWorkChain, namespace='sub.sub')
        ))

    def finalize(self):
        self.out_many(
            self.exposed_outputs(
                self.ctx.child,
                ParentExposeWorkChain,
                namespace='sub.sub'
            )
        )

class ParentExposeWorkChain(work.WorkChain):
    @classmethod
    def define(cls, spec):
        super(ParentExposeWorkChain, cls).define(spec)

        spec.expose_inputs(ChildExposeWorkChain, include=['a'])
        spec.expose_inputs(
            ChildExposeWorkChain,
            exclude=['a'],
            namespace='sub_1',
        )
        spec.expose_inputs(
            ChildExposeWorkChain,
            include=['b'],
            namespace='sub_2',
        )
        spec.expose_inputs(
            ChildExposeWorkChain,
            include=['c'],
            namespace='sub_2.sub_3',
        )

        spec.expose_outputs(ChildExposeWorkChain, include=['a'])
        spec.expose_outputs(
            ChildExposeWorkChain,
            exclude=['a'],
            namespace='sub_1'
        )
        spec.expose_outputs(
            ChildExposeWorkChain,
            include=['b'],
            namespace='sub_2'
        )
        spec.expose_outputs(
            ChildExposeWorkChain,
            include=['c'],
            namespace='sub_2.sub_3'
        )

        spec.outline(
            cls.start_children,
            cls.finalize
        )

    def start_children(self):
        child_1 = self.submit(
            ChildExposeWorkChain,
            a=self.exposed_inputs(ChildExposeWorkChain)['a'],
            **self.exposed_inputs(ChildExposeWorkChain, namespace='sub_1', agglomerate=False)
        )
        child_2 = self.submit(
            ChildExposeWorkChain,
            **self.exposed_inputs(
                ChildExposeWorkChain,
                namespace='sub_2.sub_3',
            )
        )
        return ToContext(child_1=child_1, child_2=child_2)

    def finalize(self):
        exposed_1 = self.exposed_outputs(
            self.ctx.child_1,
            ChildExposeWorkChain,
            namespace='sub_1',
            agglomerate=False
        )
        self.out_many(exposed_1)
        exposed_2 = self.exposed_outputs(
            self.ctx.child_2,
            ChildExposeWorkChain,
            namespace='sub_2.sub_3'
        )
        self.out_many(exposed_2)

class ChildExposeWorkChain(work.WorkChain):
    @classmethod
    def define(cls, spec):
        super(ChildExposeWorkChain, cls).define(spec)

        spec.input('a', valid_type=Int)
        spec.input('b', valid_type=Float)
        spec.input('c', valid_type=Bool)

        spec.output('a', valid_type=Float)
        spec.output('b', valid_type=Float)
        spec.output('c', valid_type=Bool)

        spec.outline(cls.do_run)

    def do_run(self):
        self.out('a', self.inputs.a + self.inputs.b)
        self.out('b', self.inputs.b)
        self.out('c', self.inputs.c)

class TestWorkChainExpose(AiidaTestCase):
    """
    Test the expose inputs / outputs functionality
    """

    def setUp(self):
        super(TestWorkChainExpose, self).setUp()
        self.assertEquals(len(ProcessStack.stack()), 0)
        self.runner = utils.create_test_runner()

    def tearDown(self):
        super(TestWorkChainExpose, self).tearDown()
        work.set_runner(None)
        self.runner.close()
        self.runner = None
        self.assertEquals(len(ProcessStack.stack()), 0)

    def test_expose(self):
        res = work.launch.run(
            ParentExposeWorkChain,
            a=Int(1),
            sub_1={'b': Float(2.3), 'c': Bool(True)},
            sub_2={'b': Float(1.2), 'sub_3': {'c': Bool(False)}},
        )
        self.assertEquals(
            res,
            {
                'a': Float(2.2),
                'sub_1.b': Float(2.3), 'sub_1.c': Bool(True),
                'sub_2.b': Float(1.2), 'sub_2.sub_3.c': Bool(False)
            }
        )

    def test_nested_expose(self):
        res = work.launch.run(
            GrandParentExposeWorkChain,
            sub=dict(
                sub=dict(
                    a=Int(1),
                    sub_1={'b': Float(2.3), 'c': Bool(True)},
                    sub_2={'b': Float(1.2), 'sub_3': {'c': Bool(False)}},
                )
            )
        )
        self.assertEquals(
            res,
            {
                'sub.sub.a': Float(2.2),
                'sub.sub.sub_1.b': Float(2.3), 'sub.sub.sub_1.c': Bool(True),
                'sub.sub.sub_2.b': Float(1.2), 'sub.sub.sub_2.sub_3.c': Bool(False)
            }
        )
