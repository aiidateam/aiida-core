###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Conditional expressions selecting one value lazily at runtime.

Each `x if condition else y` lowers to a branch holding both arms, so only the taken arm ever
runs and the joined wire keeps the provenance of the selected side.
"""

import json
import typing as t
from copy import deepcopy

import pytest

from aiida.common.exceptions import GraphLanguageError, GraphTypeCheckError
from aiida.common.links import LinkType
from aiida.engine import run_get_node
from aiida.engine.processes.graphs import run as run_mod
from aiida.engine.processes.graphs.ir import GraphIR, ProcessTask
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from tests.engine.processes.graphs.programs import branches, conditionals

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(conditionals.choose_value, id='calls'),
        pytest.param(conditionals.const_arms, id='constants'),
        pytest.param(conditionals.ref_arms, id='references'),
        pytest.param(conditionals.expr_arms, id='expressions'),
        pytest.param(conditionals.arg_conditional, id='argument'),
        pytest.param(conditionals.nested_conditional, id='nested'),
        pytest.param(conditionals.boolop_conditional, id='boolop-guard'),
        pytest.param(conditionals.loop_conditional, id='loop-test'),
        pytest.param(branches.inline_conditional, id='returned-calls'),
    ],
)
def test_conditional_templates_round_trip_through_json(declaration: GraphHandle) -> None:
    """Selections lower to branches surviving serialization."""
    spec = compile_graph(declaration)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))) == spec


def test_call_arms_place_tasks_in_taken_arm_only() -> None:
    """Both calls lower into opposite arms; the enclosing scope holds no task."""
    spec = compile_graph(conditionals.choose_value)
    assert all(task.kind == 'branch' for task in spec.tasks)
    (combined,) = spec.tasks
    assert [task.name for task in combined.body.tasks] == ['add']
    assert [task.name for task in combined.otherwise.tasks] == ['add']


def test_reference_arms_run_no_tasks() -> None:
    """Selecting between wires lowers to alias arms with no placements."""
    spec = compile_graph(conditionals.ref_arms)
    (combined,) = [task for task in spec.tasks if task.kind == 'branch']
    assert combined.body.tasks == ()
    assert combined.otherwise.tasks == ()


def test_nested_selection_branches_within_taken_arm() -> None:
    """A selection inside an arm lowers to a branch within that arm's region."""
    spec = compile_graph(conditionals.nested_conditional)
    (combined,) = [task for task in spec.tasks if task.kind == 'branch']
    assert [task.kind for task in combined.body.tasks] == ['branch']
    assert [task.kind for task in combined.otherwise.tasks] == ['process']


@pytest.mark.parametrize(
    ('declaration', 'exception', 'message'),
    [
        pytest.param(conditionals.mismatched_arms, GraphTypeCheckError, 'incompatible types', id='mismatched-arms'),
        pytest.param(conditionals.unbound_arm, GraphLanguageError, 'is not known here', id='unbound-arm'),
        pytest.param(conditionals.loop_nonbool, GraphLanguageError, 'must be true or false', id='loop-nonbool'),
    ],
)
def test_rejected_selections_fail_during_build(
    declaration: GraphHandle, exception: type[Exception], message: str
) -> None:
    """Mismatched arms, unbound names, and non-boolean loop tests fail at build."""
    with pytest.raises(exception, match=message):
        declaration.build()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(5, True, 6, id='taken'),
        pytest.param(5, False, 7, id='otherwise'),
    ],
)
def test_choose_value_runs_taken_arm_only(value: int, flag: bool, expected: int) -> None:
    """Only the selected call runs, and the graph returns its node unchanged."""
    outputs, node = run_get_node(conditionals.choose_value, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    adds = [
        entry.node.outputs.result
        for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
        if 'add' in entry.link_label
    ]
    assert len(adds) == 1
    assert outputs['result'].uuid == adds[0].uuid


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(5, True, 6, id='taken'),
        pytest.param(5, False, 7, id='otherwise'),
    ],
)
def test_const_arms_run(value: int, flag: bool, expected: int) -> None:
    """The selected constant feeds the task without creating data."""
    outputs, node = run_get_node(conditionals.const_arms, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'other', 'flag', 'expected'),
    [
        pytest.param(5, 10, True, 6, id='taken'),
        pytest.param(5, 10, False, 11, id='otherwise'),
    ],
)
def test_ref_arms_run(value: int, other: int, flag: bool, expected: int) -> None:
    """The selected wire reaches the task with its stored node."""
    outputs, node = run_get_node(conditionals.ref_arms, value=value, other=other, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(5, True, 6, id='taken'),
        pytest.param(5, False, 4, id='otherwise'),
    ],
)
def test_expr_arms_run(value: int, flag: bool, expected: int) -> None:
    """Only the selected inline expression evaluates."""
    outputs, node = run_get_node(conditionals.expr_arms, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(5, True, 6, id='taken'),
        pytest.param(5, False, 1, id='otherwise'),
    ],
)
def test_arg_conditional_runs(value: int, flag: bool, expected: int) -> None:
    """A selection inside a call argument decides one input."""
    outputs, node = run_get_node(conditionals.arg_conditional, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'flip', 'expected'),
    [
        pytest.param(5, True, True, 6, id='inner-taken'),
        pytest.param(5, True, False, 7, id='inner-otherwise'),
        pytest.param(5, False, True, 8, id='outer-otherwise'),
    ],
)
def test_nested_conditional_runs(value: int, flag: bool, flip: bool, expected: int) -> None:
    """Each selection level runs only its selected side."""
    outputs, node = run_get_node(conditionals.nested_conditional, value=value, flag=flag, flip=flip)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    adds = [
        entry.link_label
        for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
        if 'add' in entry.link_label
    ]
    assert len(adds) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'other', 'expected'),
    [
        pytest.param(5, True, True, 6, id='taken'),
        pytest.param(5, False, True, 7, id='otherwise'),
    ],
)
def test_boolop_conditional_runs(value: int, flag: bool, other: bool, expected: int) -> None:
    """A joined boolean guards the selection like a bound name."""
    outputs, node = run_get_node(conditionals.boolop_conditional, value=value, flag=flag, other=other)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(3, True, 0, id='task-checked'),
        pytest.param(3, False, 3, id='skipped'),
    ],
)
def test_loop_conditional_runs(value: int, flag: bool, expected: int) -> None:
    """The task-checked selection re-evaluates before every iteration."""
    outputs, node = run_get_node(conditionals.loop_conditional, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


def _drive_to_completion(state: run_mod.GraphRun) -> dict[str, t.Any]:
    """Complete every pending task with a real run until the graph settles."""
    from aiida.engine import run_get_node as launch

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
def test_choose_value_restores_with_taken_arm_pending() -> None:
    """A checkpoint taken with the selected call dispatched restores the pending arm."""
    spec = compile_graph(conditionals.choose_value)
    state = run_mod.GraphRun(spec, given={'value': 5, 'flag': True})
    first = state.step()
    assert [start.instance for start in first.starts] == ['branch_1__add']
    for start in first.starts:
        assert isinstance(start.task, ProcessTask)
        from aiida.engine import run_get_node as launch

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
        assert _drive_to_completion(run)['result'].value == 6
