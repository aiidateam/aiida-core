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
from aiida.engine import Process, calcfunction, launch
from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.generic.futures import Future
from aiida.manage.caching import enable_caching
from aiida.orm import Int, Str, WorkflowNode


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
    monkeypatch.setattr(runner, '_broker_submit', True)
    with pytest.raises(exceptions.InvalidOperation, match='cannot submit a process function'):
        runner.submit(launchable, {'value': Int(1)})


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
