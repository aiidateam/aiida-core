###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test process runners."""

import asyncio
import threading

import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common import exceptions
from aiida.engine import ExitCode, Process, ToContext, WorkChain, calcfunction, launch
from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.generic.futures import Future
from aiida.engine.processes.states import Wait
from aiida.manage.caching import enable_caching
from aiida.orm import CalcFunctionNode, Int, QueryBuilder, Str, WorkflowNode


@pytest.fixture
def runner(manager):
    """Construct and return a ``Runner``.

    This fixture depends on ``manager`` so that the manager teardown resets the global profile state after the test,
    clearing any shared runner state before later tests run.
    """
    runner = manager.create_runner(poll_interval=0.5)
    yield runner
    runner.close()


class Proc(Process):
    """Process class."""

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('a')

    async def run(self):
        pass


@calcfunction
def add_one(value: Int) -> Int:
    """Add one to the input."""
    return Int(value.value + 1)


class TerminatingProcess(Process):
    """Exercise every terminal outcome of locally scheduled execution."""

    _node_class = WorkflowNode

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('mode', valid_type=Str)

    async def run(self):
        mode = self.inputs.mode.value
        if mode == 'excepted':
            msg = 'child failed'
            raise RuntimeError(msg)
        if mode == 'killed':
            self.call_soon(self.kill)
            return Wait()
        return ExitCode(1 if mode == 'failed' else 0)


class AwaitingWorkChain(WorkChain):
    """Wait for a local child, including another work chain."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('mode', valid_type=Str)
        spec.input('nested', valid_type=Int, default=lambda: Int(0))
        spec.outline(cls.launch_child, cls.check_child)

    def launch_child(self):
        if self.inputs.nested.value:
            child = self.submit(AwaitingWorkChain, mode=self.inputs.mode)
        else:
            child = self.submit(TerminatingProcess, mode=self.inputs.mode)
        return ToContext(child=child)

    def check_child(self):
        assert self.ctx.child.is_terminated
        assert self.ctx.child.is_sealed


def the_hans_klok_comeback(loop):
    loop.stop()


@pytest.mark.requires_broker
def test_call_on_process_finish(runner):
    """Test call on calculation finish."""
    loop = runner.loop
    proc = Proc(runner=runner, inputs={'a': Str('input')})
    future = Future()
    event = threading.Event()

    def calc_done():
        if event.is_set():
            future.set_exception(AssertionError('the callback was called twice, which should never happen'))

        future.set_result(True)
        event.set()
        loop.stop()

    runner.call_on_process_finish(proc.node.pk, calc_done)

    # Run the calculation
    runner.loop.create_task(proc.step_until_terminated())
    loop.call_later(5, the_hans_klok_comeback, runner.loop)
    loop.run_forever()

    assert not future.exception()
    assert future.result()


@pytest.fixture
def local_runner(manager):
    """Use production-like polling without a broker to expose missing local notifications."""
    runner = manager.create_runner(communicator=None, poll_interval=3600)
    yield runner
    runner.close()


@pytest.mark.parametrize('method', ['submit', 'schedule'])
@pytest.mark.parametrize('mode', ['finished', 'failed', 'excepted', 'killed'])
def test_local_completion(local_runner, method, mode):
    """Every terminal state wakes all local watchers without waiting for polling."""
    node = getattr(local_runner, method)(TerminatingProcess, mode=Str(mode))
    notifications = []
    completed = local_runner.loop.create_future()

    def on_done():
        notifications.append((node.process_state.value, node.is_sealed))
        if len(notifications) == 2:
            completed.set_result(None)

    local_runner.call_on_process_finish(node.pk, on_done)
    local_runner.call_on_process_finish(node.pk, on_done)
    local_runner.run_until_complete(asyncio.wait_for(completed, timeout=5))
    expected_state = 'finished' if mode == 'failed' else mode
    assert notifications == [(expected_state, True)] * 2
    if mode == 'failed':
        assert node.exit_status == 1
    assert not local_runner._local_process_tasks

    # A watcher registered after execution was removed from the local registry still fires.
    late = local_runner.loop.create_future()
    local_runner.call_on_process_finish(node.pk, lambda: late.set_result(None))
    local_runner.run_until_complete(asyncio.wait_for(late, timeout=5))
    assert len(notifications) == 2


@pytest.mark.parametrize('cancelled', [False, True])
def test_local_execution_interrupted(local_runner, monkeypatch, caplog, cancelled):
    """A broken execution task is not mistaken for terminal process state."""
    process = TerminatingProcess(runner=local_runner, inputs={'mode': Str('finished')})

    async def interrupted():
        if cancelled:
            raise asyncio.CancelledError
        msg = 'unexpected execution failure'
        raise RuntimeError(msg)

    monkeypatch.setattr(process, 'step_until_terminated', interrupted)
    monkeypatch.setattr(local_runner, '_poll_interval', 0.01)
    node = local_runner.schedule(process)
    completed = local_runner.loop.create_future()
    local_runner.call_on_process_finish(node.pk, lambda: completed.set_result(None))

    async def check():
        await asyncio.sleep(0.03)
        assert not completed.done()
        assert not node.is_terminated
        assert not local_runner._local_process_tasks
        process.kill()
        await asyncio.wait_for(completed, timeout=5)

    local_runner.run_until_complete(check())
    assert node.is_killed
    if not cancelled:
        assert 'unexpected execution failure' in caplog.text


def test_nonlocal_completion_polling(local_runner, monkeypatch):
    """Execution not owned by the runner still has a polling fallback."""
    monkeypatch.setattr(local_runner, '_poll_interval', 0.01)
    process = TerminatingProcess(runner=local_runner, inputs={'mode': Str('finished')})
    completed = local_runner.loop.create_future()
    local_runner.call_on_process_finish(process.node.pk, lambda: completed.set_result(None))

    async def execute():
        await process.step_until_terminated()
        await asyncio.wait_for(completed, timeout=5)

    local_runner.run_until_complete(execute())
    assert process.node.is_finished_ok


@pytest.mark.parametrize('mode', ['finished', 'failed', 'excepted', 'killed'])
@pytest.mark.timeout(10)
def test_nested_workchain_local_completion(local_runner, mode):
    """Nested work chains resume promptly even when their leaf fails or is killed."""
    _, node = local_runner.run_get_node(AwaitingWorkChain, mode=Str(mode), nested=Int(1))
    assert node.is_finished_ok


@pytest.mark.timeout(10)
def test_graph_local_completion(local_runner):
    """Sequential graph tasks do not incur a polling interval per dependency."""
    from tests.engine.processes.graphs.programs.calls import multiply_add

    outputs, node = local_runner.run_get_node(multiply_add, x=2, y=3, z=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 10


def test_submit(runner):
    """Test that inputs can be specified either as a positional dictionary or through keyword arguments."""
    inputs = {'a': Str('input')}

    with pytest.raises(ValueError, match='Cannot specify both `inputs` and `kwargs`'):
        runner.submit(Proc, inputs, **inputs)

    runner.submit(Proc, inputs)
    runner.submit(Proc, **inputs)


@pytest.mark.parametrize(
    'launchable',
    [
        pytest.param(add_one, id='function'),
        pytest.param(add_one.process_class, id='process-class'),
        pytest.param(ProcessBuilder(add_one.process_class), id='builder'),
    ],
)
@pytest.mark.usefixtures('aiida_profile_clean')
def test_broker_submit_of_process_function_raises(runner, monkeypatch, launchable) -> None:
    """Daemon submit cannot persist a process function; run it instead."""
    before = QueryBuilder().append(CalcFunctionNode, project='id').count()
    monkeypatch.setattr(runner, '_broker_submit', True)
    with pytest.raises(exceptions.InvalidOperation, match='cannot submit a process function'):
        runner.submit(launchable, {'value': Int(1)})
    assert QueryBuilder().append(CalcFunctionNode, project='id').count() == before


@pytest.mark.usefixtures('aiida_profile_clean')
def test_broker_submit_of_process_instance_raises(runner, monkeypatch) -> None:
    """An instantiated process function is rejected without storing a node."""
    process = add_one.process_class(runner=runner, inputs={'value': Int(1)})
    before = QueryBuilder().append(CalcFunctionNode, project='id').count()
    monkeypatch.setattr(runner, '_broker_submit', True)
    with pytest.raises(exceptions.InvalidOperation, match='cannot submit a process function'):
        runner.submit(process)
    assert QueryBuilder().append(CalcFunctionNode, project='id').count() == before


@pytest.mark.usefixtures('aiida_profile_clean')
def test_function_process_rejects_persistence(runner) -> None:
    """Legacy process functions still refuse persistence when asked."""
    with pytest.raises(RuntimeError, match='Cannot persist'):
        add_one.process_class(runner=runner, inputs={'value': Int(1)}, enable_persistence=True)


def test_run_return_value_cached(aiida_code_installed):
    """Test that :meth:`aiida.engine.runners.Runner._run` return process results even when cached.

    Regression test for https://github.com/aiidateam/aiida-core/issues/5994.
    """
    inputs = {
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'),
        'x': Int(1),
        'y': Int(-2),
    }
    results_source, node_source = launch.run_get_node(ArithmeticAddCalculation, **inputs)
    assert node_source.base.caching.is_valid_cache

    with enable_caching():
        results_cached, node_cached = launch.run_get_node(ArithmeticAddCalculation, **inputs)

    assert node_cached.base.caching.get_cache_source() == node_source.uuid
    assert sorted(results_cached.keys()) == sorted(results_source.keys())
    assert sorted(results_cached.keys()) == ['remote_folder', 'retrieved', 'sum']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_broker_submit_of_task_process_persists(runner, monkeypatch) -> None:
    """Daemon submit of a graph task persists the checkpoint and dispatches it."""
    import typing as t

    from tests.engine.processes.graphs.programs import tasks as graph_tasks

    continued: list[int] = []

    class _Controller:
        def continue_process(self, pid: int, **kwargs: t.Any) -> None:
            continued.append(pid)

    monkeypatch.setattr(runner, '_broker_submit', True)
    monkeypatch.setattr(runner, '_controller', _Controller())
    node = runner.submit(graph_tasks.add, x=2, y=3)
    assert node.pk is not None
    assert len(continued) == 1
    assert runner.persister.load_checkpoint(continued[0]) is not None


def test_schedule_accepts_process_function(runner) -> None:
    """Scheduling a process function runs it like a process class instead of rejecting it."""
    from aiida.engine import calcfunction
    from aiida.orm import CalcFunctionNode

    @calcfunction
    def add(x: Int, y: Int) -> Int:
        return x + y

    node = runner.schedule(add, {'x': Int(1), 'y': Int(2)})
    assert isinstance(node, CalcFunctionNode)

    async def wait_terminated() -> None:
        while not node.is_terminated:
            await asyncio.sleep(0.01)

    runner.loop.run_until_complete(wait_terminated())
    assert node.is_finished_ok
    assert node.outputs.result.value == 3
