###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Iteration-local bindings in loop bodies.

Names assigned in a loop body without an enclosing binding are iteration-locals: declared on
their first write, fresh every pass, never routed in, carried, or exported. Only names read
before any write, the loop condition, or pre-bound names become carried state.
"""

import json
import typing as t
from copy import deepcopy

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.engine import run_get_node
from aiida.engine import run_get_node as launch
from aiida.engine.processes.graphs import run as run_mod
from aiida.engine.processes.graphs.ir import GraphIR, ProcessTask
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from tests.engine.processes.graphs.programs import loops

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(loops.fresh_name_in_loop, id='fresh-name'),
        pytest.param(loops.iteration_local, id='local-step'),
        pytest.param(loops.branch_local_join, id='branch-local'),
        pytest.param(loops.nested_local_loop, id='nested-local'),
    ],
)
def test_locals_stay_out_of_loop_state(declaration: GraphHandle) -> None:
    """Iteration-locals never enter the loop inputs, outputs, or the enclosing names."""
    spec = compile_graph(declaration)
    (loop,) = [task for task in spec.tasks if task.kind == 'loop']
    assert 'step' not in loop.body.inputs
    assert 'step' not in loop.body.outputs
    assert 'fresh' not in loop.body.inputs
    assert 'fresh' not in loop.body.outputs
    assert 'step' not in spec.inputs
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))) == spec


def test_nested_loop_carries_outer_local() -> None:
    """A nested loop carries an iteration-local declared before it, without exporting it."""
    spec = compile_graph(loops.nested_local_loop)
    (loop,) = [task for task in spec.tasks if task.kind == 'loop']
    (inner,) = [task for task in loop.body.tasks if task.kind == 'loop']
    assert sorted(inner.body.inputs) == ['condition', 'step']
    assert sorted(inner.body.outputs) == ['condition', 'step']
    assert 'step' not in loop.body.outputs


@pytest.mark.parametrize(
    ('declaration', 'message'),
    [
        pytest.param(loops.local_use_before_def, 'set .step. before the loop instead', id='use-before-def'),
        pytest.param(loops.local_conditional_assign, 'set .step. before the loop instead', id='conditional-assign'),
        pytest.param(loops.local_leaks_after_loop, '.step. is not known here', id='post-loop-access'),
    ],
)
def test_uninitialized_locals_fail_during_build(declaration: GraphHandle, message: str) -> None:
    """Reads before any write, possibly unbound arms, and post-loop access fail at build."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(3, True, 0, id='multi'),
        pytest.param(0, True, -1, id='single'),
        pytest.param(5, False, 5, id='zero'),
    ],
)
def test_iteration_local_runs(value: int, flag: bool, expected: int) -> None:
    """Zero, one, and many iterations rebind carried state from a fresh local each pass."""
    outputs, node = run_get_node(loops.iteration_local, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(3, True, 0, id='multi'),
        pytest.param(-2, True, -2, id='else-first'),
        pytest.param(5, False, 5, id='zero'),
    ],
)
def test_branch_local_join_runs(value: int, flag: bool, expected: int) -> None:
    """Branch arms bind the local on every path; each pass reads the freshly joined value."""
    outputs, node = run_get_node(loops.branch_local_join, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_local_loop_runs() -> None:
    """A nested loop drains the outer local each pass without leaking it outward."""
    outputs, node = run_get_node(loops.nested_local_loop, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 0
    outputs, node = run_get_node(loops.nested_local_loop, value=5, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_fresh_name_in_loop_runs() -> None:
    """A formerly rejected fresh name now runs as iteration-local state."""
    outputs, node = run_get_node(loops.fresh_name_in_loop, value=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 0


def _drive_to_completion(state: run_mod.GraphRun) -> dict[str, t.Any]:
    """Complete every pending task with a real run until the graph settles.

    Task placements run as child processes of the graph; driving them directly through the
    engine resolves the same values the daemon would, without any broker.
    """
    while True:
        step = state.step()
        if not step.starts and not state.pending:
            return state.outputs()
        for start in step.starts:
            assert isinstance(start.task, ProcessTask)
            _, node = launch(start.task.spec.process_class, **start.inputs)
            assert node.pk is not None
            state.started(start.instance, node.pk)
            state.completed(start.instance, node.pk)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_locals_restore_mid_loop_without_stale_values() -> None:
    """A checkpoint taken with a local task dispatched restores each iteration fresh."""
    spec = compile_graph(loops.iteration_local)
    state = run_mod.GraphRun(spec, given={'value': 1, 'flag': True})
    first = state.step()
    assert [start.instance for start in first.starts] == ['add']
    # Settle the carried total, then dispatch the first local step and checkpoint.
    for start in first.starts:
        assert isinstance(start.task, ProcessTask)
        _, node = launch(start.task.spec.process_class, **start.inputs)
        assert node.pk is not None
        state.started(start.instance, node.pk)
        state.completed(start.instance, node.pk)
    pending = state.step()
    assert [start.instance for start in pending.starts] == ['loop_2_iteration_0__decrement']
    for start in pending.starts:
        assert isinstance(start.task, ProcessTask)
        _, node = launch(start.task.spec.process_class, **start.inputs)
        assert node.pk is not None
        state.started(start.instance, node.pk)
    saved = deepcopy(state.to_dict())
    restored = run_mod.GraphRun.from_dict(spec, dict(state.given), saved)
    assert restored.to_dict() == saved
    assert restored.pending == state.pending
    for run in (state, restored):
        for label, pk in run.pending.items():
            run.completed(label, pk)
        assert _drive_to_completion(run)['result'].value == 0
