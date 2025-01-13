###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: N806
"""Tests for the `WorkChain` class."""

import asyncio
import inspect

import plumpy
import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.common.links import LinkType
from aiida.common.utils import Capturing
from aiida.engine import ExitCode, Process, ToContext, WorkChain, append_, calcfunction, if_, launch, return_, while_
from aiida.engine.persistence import ObjectLoader
from aiida.manage import enable_caching, get_manager
from aiida.orm import Bool, Float, Int, Str, load_node


def run_until_paused(proc):
    """Set up a future that will be resolved when process is paused"""
    listener = plumpy.ProcessListener()
    paused = plumpy.Future()

    if proc.paused:
        paused.set_result(True)
    else:

        def on_paused(_paused_proc):
            paused.set_result(True)
            proc.remove_process_listener(listener)

        listener.on_process_paused = on_paused
        proc.add_process_listener(listener)

    return paused


def run_until_waiting(proc):
    """Set up a future that will be resolved on entering the WAITING state"""
    from aiida.engine import ProcessState

    listener = plumpy.ProcessListener()
    in_waiting = plumpy.Future()

    if proc.state == ProcessState.WAITING:
        in_waiting.set_result(True)
    else:

        def on_waiting(_):
            in_waiting.set_result(True)
            proc.remove_process_listener(listener)

        listener.on_process_waiting = on_waiting
        proc.add_process_listener(listener)

    return in_waiting


def run_and_check_success(process_class, **kwargs):
    """Instantiates the process class and executes it followed by a check
    that it is finished successfully

    :returns: instance of process
    """
    process = process_class(inputs=kwargs)
    launch.run(process)
    assert process.node.is_finished_ok is True

    return process


class Wf(WorkChain):
    """ "Dummy work chain implementation with various steps and logical constructs in the outline."""

    # Keep track of which steps were completed by the workflow
    finished_steps: dict = {}

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('value', default=lambda: Str('A'))
        spec.input('n', default=lambda: Int(3))
        spec.outputs.dynamic = True
        spec.outline(
            cls.step1,
            if_(cls.is_a)(cls.step2).elif_(cls.is_b)(cls.step3).else_(cls.step4),
            cls.step5,
            while_(cls.larger_then_n)(
                cls.step6,
            ),
        )

    def on_create(self):
        super().on_create()
        # Reset the finished step
        self.finished_steps = {
            k: False
            for k in [
                self.step1.__name__,
                self.step2.__name__,
                self.step3.__name__,
                self.step4.__name__,
                self.step5.__name__,
                self.step6.__name__,
                self.is_a.__name__,
                self.is_b.__name__,
                self.larger_then_n.__name__,
            ]
        }

    def step1(self):
        self._set_finished(inspect.stack()[0].function)

    def step2(self):
        self._set_finished(inspect.stack()[0].function)

    def step3(self):
        self._set_finished(inspect.stack()[0].function)

    def step4(self):
        self._set_finished(inspect.stack()[0].function)

    def step5(self):
        self.ctx.counter = 0
        self._set_finished(inspect.stack()[0].function)

    def step6(self):
        self.ctx.counter = self.ctx.counter + 1
        self._set_finished(inspect.stack()[0].function)

    def is_a(self):
        self._set_finished(inspect.stack()[0].function)
        return self.inputs.value.value == 'A'

    def is_b(self):
        self._set_finished(inspect.stack()[0].function)
        return self.inputs.value.value == 'B'

    def larger_then_n(self):
        keep_looping = self.ctx.counter < self.inputs.n.value
        if not keep_looping:
            self._set_finished(inspect.stack()[0].function)
        return keep_looping

    def _set_finished(self, function_name):
        self.finished_steps[function_name] = True


class CalcFunctionWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('a')
        spec.input('b')
        spec.output('out_member')
        spec.output('out_static')
        spec.outline(
            cls.run_add_member,
            cls.run_add_static,
        )

    @calcfunction
    def add_member(a, b):  # noqa: N805
        return a + b

    @staticmethod
    @calcfunction
    def add_static(a, b):
        return a + b

    def run_add_member(self):
        self.out('out_member', CalcFunctionWorkChain.add_member(self.inputs.a, self.inputs.b))

    def run_add_static(self):
        self.out('out_static', self.add_static(self.inputs.a, self.inputs.b))


class PotentialFailureWorkChain(WorkChain):
    """Work chain that can finish with a non-zero exit code."""

    EXIT_STATUS = 1
    EXIT_MESSAGE = 'Well you did ask for it'
    OUTPUT_LABEL = 'optional_output'
    OUTPUT_VALUE = 144

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('success', valid_type=Bool)
        spec.input('through_return', valid_type=Bool, default=lambda: Bool(False))
        spec.input('through_exit_code', valid_type=Bool, default=lambda: Bool(False))
        spec.exit_code(cls.EXIT_STATUS, 'EXIT_STATUS', cls.EXIT_MESSAGE)
        spec.outline(if_(cls.should_return_out_of_outline)(return_(cls.EXIT_STATUS)), cls.failure, cls.success)
        spec.output(cls.OUTPUT_LABEL, required=False)

    def should_return_out_of_outline(self):
        return self.inputs.through_return.value

    def failure(self):
        if self.inputs.success.value is False:
            # Returning either 0 or ExitCode with non-zero status should terminate the workchain
            if self.inputs.through_exit_code.value is False:
                return self.EXIT_STATUS

            return self.exit_codes.EXIT_STATUS

        # Returning 0 or ExitCode with zero status should *not* terminate the workchain
        if self.inputs.through_exit_code.value is False:
            return 0

        return ExitCode()

    def success(self):
        self.out(self.OUTPUT_LABEL, Int(self.OUTPUT_VALUE).store())


@pytest.mark.requires_rmq
class TestExitStatus:
    """This class should test the various ways that one can exit from the outline flow of a WorkChain, other than
    it running it all the way through. Currently this can be done directly in the outline by calling the `return_`
    construct, or from an outline step function by returning a non-zero integer or an ExitCode with a non-zero status
    """

    def test_failing_workchain_through_integer(self):
        _, node = launch.run.get_node(PotentialFailureWorkChain, success=Bool(False))
        assert node.exit_status == PotentialFailureWorkChain.EXIT_STATUS
        assert node.exit_message is None
        assert node.is_finished is True
        assert node.is_finished_ok is False
        assert node.is_failed is True
        assert PotentialFailureWorkChain.OUTPUT_LABEL not in node.base.links.get_outgoing().all_link_labels()

    def test_failing_workchain_through_exit_code(self):
        _, node = launch.run.get_node(PotentialFailureWorkChain, success=Bool(False), through_exit_code=Bool(True))
        assert node.exit_status == PotentialFailureWorkChain.EXIT_STATUS
        assert node.exit_message == PotentialFailureWorkChain.EXIT_MESSAGE
        assert node.is_finished is True
        assert node.is_finished_ok is False
        assert node.is_failed is True
        assert PotentialFailureWorkChain.OUTPUT_LABEL not in node.base.links.get_outgoing().all_link_labels()

    def test_successful_workchain_through_integer(self):
        _, node = launch.run.get_node(PotentialFailureWorkChain, success=Bool(True))
        assert node.exit_status == 0
        assert node.is_finished is True
        assert node.is_finished_ok is True
        assert node.is_failed is False
        assert PotentialFailureWorkChain.OUTPUT_LABEL in node.base.links.get_outgoing().all_link_labels()
        assert (
            node.base.links.get_outgoing().get_node_by_label(PotentialFailureWorkChain.OUTPUT_LABEL)
            == PotentialFailureWorkChain.OUTPUT_VALUE
        )

    def test_successful_workchain_through_exit_code(self):
        _, node = launch.run.get_node(PotentialFailureWorkChain, success=Bool(True), through_exit_code=Bool(True))
        assert node.exit_status == 0
        assert node.is_finished is True
        assert node.is_finished_ok is True
        assert node.is_failed is False
        assert PotentialFailureWorkChain.OUTPUT_LABEL in node.base.links.get_outgoing().all_link_labels()
        assert (
            node.base.links.get_outgoing().get_node_by_label(PotentialFailureWorkChain.OUTPUT_LABEL)
            == PotentialFailureWorkChain.OUTPUT_VALUE
        )

    def test_return_out_of_outline(self):
        _, node = launch.run.get_node(PotentialFailureWorkChain, success=Bool(True), through_return=Bool(True))
        assert node.exit_status == PotentialFailureWorkChain.EXIT_STATUS
        assert node.is_finished is True
        assert node.is_finished_ok is False
        assert node.is_failed is True
        assert PotentialFailureWorkChain.OUTPUT_LABEL not in node.base.links.get_outgoing().all_link_labels()


class IfTest(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.outline(if_(cls.condition)(cls.step1, cls.step2))

    def on_create(self):
        super().on_create()
        self.ctx.s1 = False
        self.ctx.s2 = False

    def condition(self):
        return True

    def step1(self):
        self.ctx.s1 = True
        self.pause()

    def step2(self):
        self.ctx.s2 = True


@pytest.mark.requires_rmq
class TestContext:
    def test_attributes(self):
        wc = IfTest()
        wc.ctx.new_attr = 5
        assert wc.ctx.new_attr == 5

        del wc.ctx.new_attr
        with pytest.raises(AttributeError):
            wc.ctx.new_attr

    def test_dict(self):
        wc = IfTest()
        wc.ctx['new_attr'] = 5
        assert wc.ctx['new_attr'] == 5

        del wc.ctx['new_attr']
        with pytest.raises(KeyError):
            wc.ctx['new_attr']


@pytest.mark.requires_rmq
class TestWorkchain:
    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    def test_run_base_class(self):
        """Verify that it is impossible to run, submit or instantiate a base `WorkChain` class."""
        with pytest.raises(exceptions.InvalidOperation):
            WorkChain()

        with pytest.raises(exceptions.InvalidOperation):
            launch.run(WorkChain)

        with pytest.raises(exceptions.InvalidOperation):
            launch.run.get_node(WorkChain)

        with pytest.raises(exceptions.InvalidOperation):
            launch.run.get_pk(WorkChain)

        with pytest.raises(exceptions.InvalidOperation):
            launch.submit(WorkChain)

    def test_run(self):
        A = Str('A')
        B = Str('B')
        C = Str('C')
        three = Int(3)

        # Try the if(..) part
        launch.run(Wf, value=A, n=three)
        # Check the steps that should have been run
        for step, finished in Wf.finished_steps.items():
            if step not in ['step3', 'step4', 'is_b']:
                assert finished, f'Step {step} was not called by workflow'

        # Try the elif(..) part
        finished_steps = launch.run(Wf, value=B, n=three)
        # Check the steps that should have been run
        for step, finished in finished_steps.items():
            if step not in ['is_a', 'step2', 'step4']:
                assert finished, f'Step {step} was not called by workflow'

        # Try the else... part
        finished_steps = launch.run(Wf, value=C, n=three)
        # Check the steps that should have been run
        for step, finished in finished_steps.items():
            if step not in ['is_a', 'step2', 'is_b', 'step3']:
                assert finished, f'Step {step} was not called by workflow'

    def test_incorrect_outline(self):
        class IncorrectOutline(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                # Try defining an invalid outline
                spec.outline(5)

        with pytest.raises(TypeError):
            IncorrectOutline.spec()

    def test_define_not_calling_super(self):
        """A `WorkChain` that does not call super in `define` classmethod should raise."""

        class IncompleteDefineWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                pass

        with pytest.raises(AssertionError):
            launch.run(IncompleteDefineWorkChain)

    def test_out_unstored(self):
        """Calling `self.out` on an unstored `Node` should raise.

        It indicates that users created new data whose provenance will be lost. The node should be properly marked as
        excepted.
        """

        class IllegalWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.illegal)
                spec.outputs.dynamic = True

            def illegal(self):
                self.out('not_allowed', orm.Int(2))

        with pytest.raises(ValueError):
            _, node = launch.run_get_node(IllegalWorkChain)

        node = (
            orm.QueryBuilder().append(orm.ProcessNode, tag='node').order_by({'node': {'id': 'desc'}}).first(flat=True)
        )
        assert node.is_excepted
        assert node.is_sealed
        assert 'ValueError: Workflow<IllegalWorkChain> tried returning an unstored `Data` node.' in node.exception

    def test_same_input_node(self):
        class SimpleWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('a', valid_type=Int)
                spec.input('b', valid_type=Int)
                # Try defining an invalid outline
                spec.outline(cls.check_a_b)

            def check_a_b(self):
                assert 'a' in self.inputs
                assert 'b' in self.inputs

        x = Int(1)
        run_and_check_success(SimpleWorkChain, a=x, b=x)

    def test_context(self):
        A = Str('a').store()
        B = Str('b').store()

        class ReturnA(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('res', A)

        class ReturnB(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('res', B)

        class OverrideContextWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.s1, cls.s2, cls.s3)

            def s1(self):
                return ToContext(r1=self.submit(ReturnA), r2=self.submit(ReturnB))

            def s2(self):
                assert self.ctx.r1.outputs.res == A
                assert self.ctx.r2.outputs.res == B

                # Try overwriting r1
                return ToContext(r1=self.submit(ReturnB))

            def s3(self):
                assert self.ctx.r1.outputs.res == B
                assert self.ctx.r2.outputs.res == B

        run_and_check_success(OverrideContextWorkChain)

    def test_unstored_nodes_in_context(self):
        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.setup_context, cls.read_context)

            def setup_context(self):
                self.ctx['some_string'] = 'Verify that strings in the context do not cause infinite recursions'
                self.ctx['node'] = Int(1)

            def read_context(self):
                assert self.ctx['node'].is_stored, 'the node in the context was not stored during step transition'

        run_and_check_success(TestWorkChain)

    def test_str(self):
        assert isinstance(str(Wf.spec()), str)

    def test_invalid_if_predicate(self, recwarn):
        """Test that workchain raises if the predicate of an ``if_`` condition does not return a boolean."""

        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(if_(cls.predicate)(cls.run_step))

            def predicate(self):
                """Invalid predicate whose return value is not a boolean."""
                return 'true'

            def run_step(self):
                pass

        launch.run(TestWorkChain)
        assert any('The conditional predicate `predicate` returned `true`' in str(r.message) for r in recwarn)

    def test_invalid_while_predicate(self, recwarn):
        """Test that workchain raises if the predicate of an ``while_`` condition does not return a boolean."""

        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(while_(cls.predicate)(cls.run_step))

            def predicate(self):
                """Invalid predicate whose return value is not a boolean."""
                return 'true'

            def run_step(self):
                # Need to return an exit code to abort the workchain, otherwise we would be stuck in an infinite loop
                return ExitCode(1)

        launch.run(TestWorkChain)
        assert any('The conditional predicate `predicate` returned `true`' in str(r.message) for r in recwarn)

    def test_malformed_outline(self):
        """Test some malformed outlines"""
        from aiida.engine.processes.workchains.workchain import WorkChainSpec

        spec = WorkChainSpec()

        with pytest.raises(TypeError):
            spec.outline(5)

        # Test a function with wrong number of args
        with pytest.raises(TypeError):
            spec.outline(lambda x, y: None)

    def test_checkpointing(self):
        A = Str('A')
        B = Str('B')
        C = Str('C')
        three = Int(3)

        # Try the if(..) part
        finished_steps = self._run_with_checkpoints(Wf, inputs={'value': A, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.items():
            if step not in ['step3', 'step4', 'is_b']:
                assert finished, f'Step {step} was not called by workflow'

        # Try the elif(..) part
        finished_steps = self._run_with_checkpoints(Wf, inputs={'value': B, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.items():
            if step not in ['is_a', 'step2', 'step4']:
                assert finished, f'Step {step} was not called by workflow'

        # Try the else... part
        finished_steps = self._run_with_checkpoints(Wf, inputs={'value': C, 'n': three})
        # Check the steps that should have been run
        for step, finished in finished_steps.items():
            if step not in ['is_a', 'step2', 'is_b', 'step3']:
                assert finished, f'Step {step} was not called by workflow'

    def test_return(self):
        class WcWithReturn(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.s1, if_(cls.is_a)(return_), cls.after)

            def s1(self):
                pass

            def is_a(self):
                return True

            def after(self):
                raise RuntimeError("Shouldn't get here")

        run_and_check_success(WcWithReturn)

    def test_call_link_label(self):
        """Test that the `call_link_label` metadata input is properly used and set."""
        label_workchain = 'some_not_default_call_link_label'
        label_calcfunction = 'call_link_label_for_calcfunction'

        @calcfunction
        def calculation_function():
            return

        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_launch)

            def do_launch(self):
                # "Call" a calculation function simply by running it
                inputs = {'metadata': {'call_link_label': label_calcfunction}}
                calculation_function(**inputs)

                # Call a sub work chain
                inputs = {'metadata': {'call_link_label': label_workchain}}
                return ToContext(subwc=self.submit(SubWorkChain, **inputs))

        class SubWorkChain(WorkChain):
            pass

        process = run_and_check_success(MainWorkChain)

        # Verify that the `CALL` link of the calculation function is there with the correct label
        link_triple = process.node.base.links.get_outgoing(
            link_type=LinkType.CALL_CALC, link_label_filter=label_calcfunction
        ).one()
        assert isinstance(link_triple.node, orm.CalcFunctionNode)

        # Verify that the `CALL` link of the work chain is there with the correct label
        link_triple = process.node.base.links.get_outgoing(
            link_type=LinkType.CALL_WORK, link_label_filter=label_workchain
        ).one()
        assert isinstance(link_triple.node, orm.WorkChainNode)

    def test_tocontext_submit_workchain_no_daemon(self):
        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_run, cls.check)
                spec.outputs.dynamic = True

            def do_run(self):
                return ToContext(subwc=self.submit(SubWorkChain))

            def check(self):
                assert self.ctx.subwc.outputs.value == Int(5)

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_run)
                spec.outputs.dynamic = True

            def do_run(self):
                self.out('value', Int(5).store())

        run_and_check_success(MainWorkChain)

    def test_tocontext_schedule_workchain(self):
        node = Int(5).store()

        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_run, cls.check)
                spec.outputs.dynamic = True

            def do_run(self):
                return ToContext(subwc=self.submit(SubWorkChain))

            def check(self):
                assert self.ctx.subwc.outputs.value == node

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_run)
                spec.outputs.dynamic = True

            def do_run(self):
                self.out('value', node)

        run_and_check_success(MainWorkChain)

    def test_process_status_sub_processes(self):
        """Test that process status is set on node when waiting for sub processes."""

        class MainWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_run)

            def do_run(self):
                pks = []
                for _ in range(2):
                    node = self.submit(SubWorkChain)
                    pks.append(node.pk)
                    self.to_context(subwc=node)

                assert 'Waiting' in self.node.process_status
                assert str(pks[0]) in self.node.process_status
                assert str(pks[1]) in self.node.process_status

        class SubWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.do_run)

            def do_run(self):
                return

        run_and_check_success(MainWorkChain)

    def test_if_block_persistence(self):
        """Test a reloaded `If` conditional can be resumed.

        This test was created to capture issue #902
        """
        runner = get_manager().get_runner()
        wc = IfTest()
        runner.schedule(wc)

        async def run_async(workchain):
            # run the original workchain until paused
            await run_until_paused(workchain)
            assert workchain.ctx.s1
            assert not workchain.ctx.s2

            # Now bundle the workchain
            bundle = plumpy.Bundle(workchain)
            # Need to close the process before recreating a new instance
            workchain.close()

            # Load from saved state
            workchain2 = bundle.unbundle()
            assert workchain2.ctx.s1
            assert not workchain2.ctx.s2

            # check bundling again creates the same saved state
            bundle2 = plumpy.Bundle(workchain2)
            assert bundle == bundle2

            # run the loaded workchain to completion
            runner.schedule(workchain2)
            workchain2.play()
            await workchain2.future()
            assert workchain2.ctx.s1
            assert workchain2.ctx.s2

            # ensure the original paused workchain future is finalised
            # to avoid warnings
            workchain.future().set_result(None)

        runner.loop.run_until_complete(run_async(wc))

    def test_report_dbloghandler(self):
        """Test whether the WorkChain, through its Process, has a logger
        set for which the DbLogHandler has been attached. Because if this
        is not the case, the 'report' method will not actually hit the
        DbLogHandler and the message will not be stored in the database
        """

        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.emit_report, cls.check)
                spec.outputs.dynamic = True

            def emit_report(self):
                self.report('Testing the report function')

            def check(self):
                messages = [log.message for log in orm.Log.collection.get_logs_for(self.node)]
                assert any('Testing the report function' in message for message in messages)

        run_and_check_success(TestWorkChain)

    def test_to_context(self):
        val = Int(5).store()

        class SimpleWc(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val)

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(result_a=self.submit(SimpleWc))
                return ToContext(result_b=self.submit(SimpleWc))

            def result(self):
                assert self.ctx.result_a.outputs.result == val
                assert self.ctx.result_b.outputs.result == val

        run_and_check_success(Workchain)

    def test_nested_to_context(self):
        val = Int(5).store()

        class SimpleWc(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val)

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(**{'sub1.sub2.result_a': self.submit(SimpleWc)})
                return ToContext(**{'sub1.sub2.result_b': self.submit(SimpleWc)})

            def result(self):
                assert self.ctx.sub1.sub2.result_a.outputs.result == val
                assert self.ctx.sub1.sub2.result_b.outputs.result == val

        run_and_check_success(Workchain)

    def test_nested_to_context_with_append(self):
        val1 = Int(5).store()
        val2 = Int(6).store()

        class SimpleWc1(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val1)

        class SimpleWc2(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val2)

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(**{'sub1.workchains': append_(self.submit(SimpleWc1))})
                return ToContext(**{'sub1.workchains': append_(self.submit(SimpleWc2))})

            def result(self):
                assert self.ctx.sub1.workchains[0].outputs.result == val1
                assert self.ctx.sub1.workchains[1].outputs.result == val2

        run_and_check_success(Workchain)

    def test_nested_to_context_no_overlap(self):
        val = Int(5).store()

        class SimpleWc(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val)

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(**{'result_a': self.submit(SimpleWc)})
                return ToContext(**{'result_a.sub1': self.submit(SimpleWc)})

            def result(self):
                raise RuntimeError('Never reached: the second to_context above should fail')

        process = Workchain()
        with pytest.raises(ValueError):
            launch.run(process)

    def test_nested_to_context_no_overlap_with_append(self):
        val = Int(5).store()

        class SimpleWc(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val)

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(workchains=append_(self.submit(SimpleWc)))  # make the workchains point to a list
                return ToContext(**{'workchains.sub1.sub2': self.submit(SimpleWc)})  # now try to treat it as a sub-dict

            def result(self):
                raise RuntimeError('Never reached: the second to_context above should fail')

        process = Workchain()
        with pytest.raises(ValueError):
            launch.run(process)

    def test_nested_to_context_no_overlap_with_append2(self):
        val = Int(5).store()

        class SimpleWc(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.result)
                spec.outputs.dynamic = True

            def result(self):
                self.out('result', val)

        class Workchain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.begin, cls.result)

            def begin(self):
                self.to_context(workchains=append_(self.submit(SimpleWc)))  # make the workchains point to a list
                return ToContext(
                    **{'workchains.sub1': self.submit(SimpleWc)}
                )  # now try to treat the final path element it as a sub-dict

            def result(self):
                raise RuntimeError('Never reached: the second to_context above should fail')

        process = Workchain()
        with pytest.raises(ValueError):
            launch.run(process)

    def test_namespace_nondb_mapping(self):
        """Regression test for a bug in _flatten_inputs"""
        value = {'a': 1, 'b': {'c': 2}}

        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)

                spec.input('namespace.sub', non_db=True)
                spec.outline(cls.check_input)

            def check_input(self):
                assert self.inputs.namespace.sub == value

        run_and_check_success(TestWorkChain, namespace={'sub': value})

    def test_nondb_dynamic(self):
        """Test that non-db inputs can be passed in a dynamic input namespace."""
        value = [1, 2, {'a': 1}]

        class TestWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input_namespace('namespace', dynamic=True)
                spec.outline(cls.check_input)

            def check_input(self):
                assert self.inputs.namespace.value == value

        run_and_check_success(TestWorkChain, namespace={'value': value})

    def test_exit_codes(self):
        status = 418
        label = 'SOME_EXIT_CODE'
        message = 'I am a teapot'

        class ExitCodeWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline()
                spec.exit_code(status, label, message)

        wc = ExitCodeWorkChain()

        # The exit code can be gotten by calling it with the status or label, as well as using attribute dereferencing
        assert wc.exit_codes(status).status == status
        assert wc.exit_codes(label).status == status
        assert wc.exit_codes.SOME_EXIT_CODE.status == status

        with pytest.raises(AttributeError):
            wc.exit_codes.NON_EXISTENT_ERROR

        assert ExitCodeWorkChain.exit_codes.SOME_EXIT_CODE.status == status
        assert ExitCodeWorkChain.exit_codes.SOME_EXIT_CODE.message == message

        assert ExitCodeWorkChain.exit_codes['SOME_EXIT_CODE'].status == status
        assert ExitCodeWorkChain.exit_codes['SOME_EXIT_CODE'].message == message

        assert ExitCodeWorkChain.exit_codes[label].status == status
        assert ExitCodeWorkChain.exit_codes[label].message == message

    @staticmethod
    def _run_with_checkpoints(wf_class, inputs=None):
        if inputs is None:
            inputs = {}
        proc = run_and_check_success(wf_class, **inputs)
        return proc.finished_steps

    def test_member_calcfunction(self):
        """Test defining a calcfunction as a ``WorkChain`` member method."""
        results, node = launch.run.get_node(CalcFunctionWorkChain, a=Int(1), b=Int(2))
        assert node.is_finished_ok
        assert results['out_member'] == 3
        assert results['out_static'] == 3

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_member_calcfunction_caching(self):
        """Test defining a calcfunction as a ``WorkChain`` member method with caching enabled."""
        results, node = launch.run.get_node(CalcFunctionWorkChain, a=Int(1), b=Int(2))
        assert node.is_finished_ok
        assert results['out_member'] == 3
        assert results['out_static'] == 3

        with enable_caching():
            results, cached_node = launch.run.get_node(CalcFunctionWorkChain, a=Int(1), b=Int(2))
            assert cached_node.is_finished_ok
            assert results['out_member'] == 3
            assert results['out_static'] == 3

            # Check that the calcfunctions called by the workchain have been cached
            for called in cached_node.called:
                assert called.base.caching.is_created_from_cache
                assert called.base.caching.get_cache_source() in [n.uuid for n in node.called]

    def test_member_calcfunction_daemon(self, entry_points, daemon_client, submit_and_await):
        """Test defining a calcfunction as a ``WorkChain`` member method submitted to the daemon."""
        entry_points.add(CalcFunctionWorkChain, 'aiida.workflows:testing.calcfunction.workchain')

        daemon_client.start_daemon()

        builder = CalcFunctionWorkChain.get_builder()
        builder.a = Int(1)
        builder.b = Int(2)

        node = submit_and_await(builder)
        assert node.is_finished_ok
        assert node.outputs.out_member == 3
        assert node.outputs.out_static == 3


@pytest.mark.requires_rmq
class TestWorkChainAbort:
    """Test the functionality to abort a workchain"""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    class AbortableWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.outline(cls.begin, cls.check)

        def begin(self):
            self.pause()

        def check(self):
            raise RuntimeError('should have been aborted by now')

    def test_simple_run(self):
        """Run the workchain which should hit the exception and therefore end
        up in the EXCEPTED state
        """
        runner = get_manager().get_runner()
        process = TestWorkChainAbort.AbortableWorkChain()

        async def run_async():
            await run_until_paused(process)

            process.play()

            with Capturing():
                with pytest.raises(RuntimeError):
                    await process.future()

        runner.schedule(process)
        runner.loop.run_until_complete(run_async())

        assert process.node.is_finished_ok is False
        assert process.node.is_excepted is True
        assert process.node.is_killed is False

    def test_simple_kill_through_process(self):
        """Run the workchain for one step and then kill it by calling kill
        on the workchain itself. This should have the workchain end up
        in the KILLED state.
        """
        runner = get_manager().get_runner()
        process = TestWorkChainAbort.AbortableWorkChain()

        async def run_async():
            await run_until_paused(process)

            assert process.paused
            process.kill()

            with pytest.raises(plumpy.ClosedError):
                launch.run(process)

        runner.schedule(process)
        runner.loop.run_until_complete(run_async())

        assert process.node.is_finished_ok is False
        assert process.node.is_excepted is False
        assert process.node.is_killed is True


@pytest.mark.requires_rmq
class TestWorkChainAbortChildren:
    """Test the functionality to abort a workchain and verify that children
    are also aborted appropriately
    """

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    class SubWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('kill', default=lambda: Bool(False))
            spec.outline(cls.begin, cls.check)

        def begin(self):
            """If the Main should be killed, pause the child to give the Main a chance to call kill on its children"""
            if self.inputs.kill:
                self.pause()

        def check(self):
            raise RuntimeError('should have been aborted by now')

    class MainWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('kill', default=lambda: Bool(False))
            spec.outline(cls.submit_child, cls.check)

        def submit_child(self):
            return ToContext(child=self.submit(TestWorkChainAbortChildren.SubWorkChain, kill=self.inputs.kill))

        def check(self):
            raise RuntimeError('should have been aborted by now')

    def test_simple_run(self):
        """Run the workchain which should hit the exception and therefore end
        up in the EXCEPTED state
        """
        process = TestWorkChainAbortChildren.MainWorkChain()

        with Capturing():
            with pytest.raises(RuntimeError):
                launch.run(process)

        assert process.node.is_finished_ok is False
        assert process.node.is_excepted is True
        assert process.node.is_killed is False

    def test_simple_kill_through_process(self):
        """Run the workchain for one step and then kill it. This should have the
        workchain and its children end up in the KILLED state.
        """
        runner = get_manager().get_runner()
        process = TestWorkChainAbortChildren.MainWorkChain(inputs={'kill': Bool(True)})

        async def run_async():
            await run_until_waiting(process)

            result = process.kill()
            if asyncio.isfuture(result):
                await result

            with pytest.raises(plumpy.KilledError):
                await process.future()

        runner.schedule(process)
        runner.loop.run_until_complete(run_async())

        child = process.node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).first().node
        assert child.is_finished_ok is False
        assert child.is_excepted is False
        assert child.is_killed is True

        assert process.node.is_finished_ok is False
        assert process.node.is_excepted is False
        assert process.node.is_killed is True


@pytest.mark.requires_rmq
class TestImmutableInputWorkchain:
    """Test that inputs cannot be modified"""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    def test_immutable_input(self):
        """Check that from within the WorkChain self.inputs returns an AttributesFrozendict which should be immutable"""

        class FrozenDictWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('a', valid_type=Int)
                spec.input('b', valid_type=Int)
                spec.outline(
                    cls.step_one,
                    cls.step_two,
                )

            def step_one(self):
                # Attempt to manipulate the inputs dictionary which since it is a AttributesFrozendict should raise
                with pytest.raises(TypeError):
                    self.inputs['a'] = Int(3)
                with pytest.raises(AttributeError):
                    self.inputs.pop('b')
                with pytest.raises(TypeError):
                    self.inputs['c'] = Int(4)

            def step_two(self):
                # Verify that original inputs are still there with same value and no inputs were added
                assert 'a' in self.inputs
                assert 'b' in self.inputs
                assert 'c' not in self.inputs
                assert self.inputs['a'].value == 1

        run_and_check_success(FrozenDictWorkChain, a=Int(1), b=Int(2))

    def test_immutable_input_groups(self):
        """Check that namespaced inputs also return AttributeFrozendicts and are hence immutable"""

        class ImmutableGroups(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input_namespace('subspace', dynamic=True)
                spec.outline(
                    cls.step_one,
                    cls.step_two,
                )

            def step_one(self):
                # Attempt to manipulate the namespaced inputs dictionary which should raise
                with pytest.raises(TypeError):
                    self.inputs.subspace['one'] = Int(3)
                with pytest.raises(AttributeError):
                    self.inputs.subspace.pop('two')
                with pytest.raises(TypeError):
                    self.inputs.subspace['four'] = Int(4)

            def step_two(self):
                # Verify that original inputs are still there with same value and no inputs were added
                assert 'one' in self.inputs.subspace
                assert 'two' in self.inputs.subspace
                assert 'four' not in self.inputs.subspace
                assert self.inputs.subspace['one'].value == 1

        run_and_check_success(ImmutableGroups, subspace={'one': Int(1), 'two': Int(2)})


class SerializeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input(
            'test',
            valid_type=Str,
            serializer=lambda x: Str(ObjectLoader().identify_object(x)),
        )
        spec.input('reference', valid_type=Str)

        spec.outline(cls.do_test)

    def do_test(self):
        assert isinstance(self.inputs.test, Str)
        assert self.inputs.test == self.inputs.reference


@pytest.mark.requires_rmq
class TestSerializeWorkChain:
    """Test workchains with serialized input / output."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    @staticmethod
    def test_serialize():
        """Test a simple serialization of a class to its identifier."""
        run_and_check_success(SerializeWorkChain, test=Int, reference=Str(ObjectLoader().identify_object(Int)))

    @staticmethod
    def test_serialize_builder():
        """Test serailization when using a builder."""
        builder = SerializeWorkChain.get_builder()
        builder.test = Int
        builder.reference = Str(ObjectLoader().identify_object(Int))
        launch.run(builder)


class GrandParentExposeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.expose_inputs(ParentExposeWorkChain, namespace='sub.sub')
        spec.expose_outputs(ParentExposeWorkChain, namespace='sub.sub')

        spec.outline(cls.do_run, cls.finalize)

    def do_run(self):
        return ToContext(
            child=self.submit(ParentExposeWorkChain, **self.exposed_inputs(ParentExposeWorkChain, namespace='sub.sub'))
        )

    def finalize(self):
        self.out_many(self.exposed_outputs(self.ctx.child, ParentExposeWorkChain, namespace='sub.sub'))


class ParentExposeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)

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
        spec.expose_outputs(ChildExposeWorkChain, exclude=['a'], namespace='sub_1')
        spec.expose_outputs(ChildExposeWorkChain, include=['b'], namespace='sub_2')
        spec.expose_outputs(ChildExposeWorkChain, include=['c'], namespace='sub_2.sub_3')

        spec.outline(cls.start_children, cls.finalize)

    def start_children(self):
        child_1 = self.submit(
            ChildExposeWorkChain,
            a=self.exposed_inputs(ChildExposeWorkChain)['a'],
            **self.exposed_inputs(ChildExposeWorkChain, namespace='sub_1', agglomerate=False),
        )
        child_2 = self.submit(
            ChildExposeWorkChain,
            **self.exposed_inputs(
                ChildExposeWorkChain,
                namespace='sub_2.sub_3',
            ),
        )
        return ToContext(child_1=child_1, child_2=child_2)

    def finalize(self):
        exposed_1 = self.exposed_outputs(self.ctx.child_1, ChildExposeWorkChain, namespace='sub_1', agglomerate=False)
        self.out_many(exposed_1)
        exposed_2 = self.exposed_outputs(self.ctx.child_2, ChildExposeWorkChain, namespace='sub_2.sub_3')
        self.out_many(exposed_2)


class ChildExposeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('a', valid_type=Int)
        spec.input('b', valid_type=Float)
        spec.input('c', valid_type=Bool)

        spec.output('a', valid_type=Float)
        spec.output('b', valid_type=Float)
        spec.output('c', valid_type=Bool)

        spec.outline(cls.do_run)

    def do_run(self):
        summed = self.inputs.a + self.inputs.b
        summed.store()
        self.out('a', summed)
        self.out('b', self.inputs.b)
        self.out('c', self.inputs.c)


@pytest.mark.requires_rmq
class TestWorkChainExpose:
    """Test the expose inputs / outputs functionality"""

    def test_expose(self):
        res = launch.run(
            ParentExposeWorkChain,
            a=Int(1),
            sub_1={'b': Float(2.3), 'c': Bool(True)},
            sub_2={'b': Float(1.2), 'sub_3': {'c': Bool(False)}},
        )
        assert res == {
            'a': Float(2.2),
            'sub_1': {'b': Float(2.3), 'c': Bool(True)},
            'sub_2': {'b': Float(1.2), 'sub_3': {'c': Bool(False)}},
        }

    def test_nested_expose(self):
        res = launch.run(
            GrandParentExposeWorkChain,
            sub={
                'sub': {
                    'a': Int(1),
                    'sub_1': {'b': Float(2.3), 'c': Bool(True)},
                    'sub_2': {'b': Float(1.2), 'sub_3': {'c': Bool(False)}},
                }
            },
        )
        assert res == {
            'sub': {
                'sub': {
                    'a': Float(2.2),
                    'sub_1': {'b': Float(2.3), 'c': Bool(True)},
                    'sub_2': {'b': Float(1.2), 'sub_3': {'c': Bool(False)}},
                }
            }
        }

    @pytest.mark.filterwarnings('ignore::UserWarning')
    def test_issue_1741_expose_inputs(self):
        """Test that expose inputs works correctly when copying a stored default value.

        .. note:: a node instance is used for a port default, which is normally not advisable, but given that this
            regression test relies on the default being a stored node, we cannot change it. Given that the default is
            only used within this test, it should not pose any problems.

        """

        class Parent(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.input('a', default=Int(5).store())
                spec.outline(cls.step1)

            def step1(self):
                pass

        class Child(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.expose_inputs(Parent)
                spec.outline(cls.step1)

            def step1(self):
                pass

        launch.run(Child)

    def test_expose_process_function(self):
        """Test that process functions can be exposed and the port attributes are preserved."""

        @calcfunction  # type: ignore[misc]
        def test_function(a: str, b: int):
            """Some calcfunction.

            :param a: A string argument.
            :param b: An integer argument.
            """

        class ExposeProcessFunctionWorkChain(WorkChain):
            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.expose_inputs(test_function)

        input_namespace = ExposeProcessFunctionWorkChain.spec().inputs
        assert 'a' in input_namespace
        assert 'b' in input_namespace
        assert input_namespace['a'].valid_type == (orm.Str,)
        assert input_namespace['a'].help == 'A string argument.'
        assert input_namespace['b'].valid_type == (orm.Int,)
        assert input_namespace['b'].help == 'An integer argument.'


@pytest.mark.requires_rmq
class TestWorkChainMisc:
    class PointlessWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.outline(cls.return_dict)

        def return_dict(self):
            """Only return a dictionary, which should be allowed, even though it accomplishes nothing."""
            return {}

    class IllegalSubmitWorkChain(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.outline(cls.illegal_submit)

        def illegal_submit(self):
            """Only return a dictionary, which should be allowed, even though it accomplishes nothing."""
            from aiida.engine import submit

            submit(TestWorkChainMisc.PointlessWorkChain)

    @staticmethod
    def test_run_pointless_workchain():
        """Running the pointless workchain should not incur any exceptions"""
        launch.run(TestWorkChainMisc.PointlessWorkChain)

    def test_global_submit_raises(self):
        """Using top-level submit should raise."""
        with pytest.raises(exceptions.InvalidOperation):
            launch.run(TestWorkChainMisc.IllegalSubmitWorkChain)


@pytest.mark.requires_rmq
class TestDefaultUniqueness:
    """Test that default inputs of exposed nodes will get unique UUIDS."""

    class Parent(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.expose_inputs(TestDefaultUniqueness.Child, namespace='child_one')
            spec.expose_inputs(TestDefaultUniqueness.Child, namespace='child_two')
            spec.outline(cls.do_run)

        def do_run(self):
            inputs = self.exposed_inputs(TestDefaultUniqueness.Child, namespace='child_one')
            child_one = self.submit(TestDefaultUniqueness.Child, **inputs)
            inputs = self.exposed_inputs(TestDefaultUniqueness.Child, namespace='child_two')
            child_two = self.submit(TestDefaultUniqueness.Child, **inputs)
            return ToContext(workchain_child_one=child_one, workchain_child_two=child_two)

    class Child(WorkChain):
        @classmethod
        def define(cls, spec):
            super().define(spec)
            spec.input('a', valid_type=Bool, default=lambda: Bool(True))

        def step(self):
            pass

    def test_unique_default_inputs(self):
        """The default value for the Child will be constructed at import time, which will be an unstored Bool node with
        a given ID. When `expose_inputs` is called on the ProcessSpec of the Parent workchain, for the Child workchain,
        the ports of the Child will be deepcopied into the portnamespace of the Parent, in this case twice, into
        different namespaces. The port in each namespace will have a deepcopied version of the unstored Bool node. When
        the Parent workchain is now called without inputs, both those nodes will be stored and used as inputs, but they
        will have the same UUID, unless the deepcopy will have guaranteed that a new UUID is generated for unstored
        nodes.
        """
        inputs = {'child_one': {}, 'child_two': {}}
        _, node = launch.run.get_node(TestDefaultUniqueness.Parent, **inputs)

        nodes = node.base.links.get_incoming().all_nodes()
        uuids = {n.uuid for n in nodes}

        # Trying to load one of the inputs through the UUID should fail,
        # as both `child_one.a` and `child_two.a` should have the same UUID.
        node = load_node(uuid=node.base.links.get_incoming().get_node_by_label('child_one__a').uuid)
        assert len(uuids) == len(nodes), f'Only {len(uuids)} unique UUIDS for {len(nodes)} input nodes'


def test_illegal_override_run():
    """Test that overriding a protected workchain method raises a ``RuntimeError``."""
    with pytest.raises(RuntimeError, match='the method `run` is protected cannot be overridden.'):

        class IllegalWorkChain(WorkChain):
            """Work chain that illegally overrides the ``run`` method."""

            @classmethod
            def define(cls, spec):
                super().define(spec)
                spec.outline(cls.run)

            async def run(self):
                pass
