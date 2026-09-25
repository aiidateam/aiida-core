###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test process runners."""

import threading

import pytest

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.exceptions import ConfigurationError
from aiida.engine import Process, launch
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


class NotebookProc(Proc):
    """Stands in for a process class defined in a notebook cell, once ``unresolvable_in_main`` has relabelled it."""


@pytest.fixture
def a_class_no_worker_could_load(monkeypatch, unresolvable_in_main):
    """Return a process class in ``__main__``, with the daemon recording paths that lead somewhere else.

    Together those are the one situation `Runner.submit` refuses: the class has no name a worker resolves, so it
    has to travel, and nothing believable is recorded about which modules that worker already has.
    """
    from aiida.engine.processes import _class_identity

    monkeypatch.setattr(_class_identity, 'get_daemon_import_paths', lambda: ('/somewhere/else',))

    return unresolvable_in_main(NotebookProc)


@pytest.mark.requires_broker
def test_submit_refuses_a_class_the_worker_could_not_load(manager, a_class_no_worker_could_load):
    """Only submission depends on the daemon's environment, so only submission carries the check.

    Running the same process here needs nothing of it, which is why this cannot live where the checkpoint is
    written: that runs for both.
    """
    runner = manager.create_runner(broker_submit=True, poll_interval=0.5)

    try:
        with pytest.raises(ConfigurationError, match=r'.*verdi daemon restart.*'):
            runner.submit(a_class_no_worker_could_load, a=Str('input'))
    finally:
        runner.close()


@pytest.mark.requires_broker
def test_submit_refused_before_a_node_exists(manager, a_class_no_worker_could_load):
    """A refusal leaves no trace, which is why the check runs before the process is instantiated.

    Instantiating stores the node and writes its first checkpoint, so checking afterwards left a `Created` node,
    its checkpoint and the class's file behind on every attempt, and a user hits this repeatedly until the daemon
    is restarted.
    """
    from aiida.orm import ProcessNode, QueryBuilder

    before: int = QueryBuilder().append(ProcessNode).count()
    runner = manager.create_runner(broker_submit=True, poll_interval=0.5)

    try:
        for _ in range(2):
            with pytest.raises(ConfigurationError):
                runner.submit(a_class_no_worker_could_load, a=Str('input'))
    finally:
        runner.close()

    assert QueryBuilder().append(ProcessNode).count() == before
