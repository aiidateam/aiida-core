###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Short-circuit boolean composition with `and` and `or`.

Each pair lowers to a branch evaluating the right side only when the left side selects it, so
task calls and guarded operations on the right never run when skipped. Operands must statically
read as booleans, including presence and member predicates which lower to ephemeral boolean
control values wherever a boolean reads. Python operand tricks and arbitrary identities fail
at build.
"""

import json
import typing as t
from copy import deepcopy

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.common.links import LinkType
from aiida.engine import run_get_node
from aiida.engine.processes.graphs import run as run_mod
from aiida.engine.processes.graphs.ir import BranchControl, GraphIR, ProcessTask
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from tests.engine.processes.graphs.programs import booleans

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(booleans.guarded_divisor, id='guarded'),
        pytest.param(booleans.lazy_rhs, id='lazy-rhs'),
        pytest.param(booleans.lazy_or, id='lazy-or'),
        pytest.param(booleans.chained_guards, id='chained'),
        pytest.param(booleans.mixed_guards, id='mixed'),
        pytest.param(booleans.negated_guard, id='negated'),
        pytest.param(booleans.picked_guard, id='operand'),
        pytest.param(booleans.bounded_count, id='bounded-loop'),
        pytest.param(booleans.none_guarded, id='none-guard'),
        pytest.param(booleans.member_guarded, id='member-guard'),
        pytest.param(booleans.presence_rhs, id='presence-rhs'),
        pytest.param(booleans.or_presence_rhs, id='or-presence-rhs'),
        pytest.param(booleans.presence_value, id='presence-value'),
        pytest.param(booleans.named_present, id='named-present'),
        pytest.param(booleans.negated_present, id='negated-present'),
        pytest.param(booleans.negated_rhs, id='negated-rhs'),
        pytest.param(booleans.member_value, id='member-value'),
        pytest.param(booleans.member_not_value, id='member-not-value'),
        pytest.param(booleans.negated_member_rhs, id='negated-member-rhs'),
        pytest.param(booleans.lazy_presence_and, id='lazy-presence-and'),
        pytest.param(booleans.lazy_presence_or, id='lazy-presence-or'),
        pytest.param(booleans.conditional_present, id='conditional-present'),
        pytest.param(booleans.conditional_joined_present, id='conditional-joined'),
        pytest.param(booleans.while_present, id='while-present'),
        pytest.param(booleans.while_named_present, id='while-named'),
    ],
)
def test_boolop_templates_round_trip_through_json(declaration: GraphHandle) -> None:
    """Joined booleans lower to branch selections surviving serialization."""
    spec = compile_graph(declaration)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))) == spec


def test_guarded_divisor_branches_on_joined_comparison() -> None:
    """The divisor check and the guarded remainder each bind their own operation wire."""
    spec = compile_graph(booleans.guarded_divisor)
    operations = [task.operation for task in spec.tasks if task.kind == 'operation']
    assert operations[0] == 'ne'
    assert spec.task_names[1:3] == ('branch_2', 'branch_3')


def test_nested_combination_claims_distinct_wires() -> None:
    """A nested left side lowers before the outer alias is claimed, so wires stay distinct."""
    spec = compile_graph(booleans.mixed_guards)
    joined = [edge.target_port for edge in spec.dependencies if edge.target_port is not None]
    assert 'conjunction_2' in joined
    assert joined.count('conjunction') == 0


def test_task_calls_stay_visible_in_taken_arms() -> None:
    """The right-hand task lowers into the taken arm, never into the enclosing scope."""
    spec = compile_graph(booleans.lazy_rhs)
    assert all(task.kind == 'branch' for task in spec.tasks)
    (combined,) = [task for task in spec.tasks if task.name == 'branch_1']
    assert isinstance(combined, BranchControl)
    assert [task.name for task in combined.body.tasks] == ['is_positive']
    assert all(task.kind == 'operation' for task in combined.otherwise.tasks)


@pytest.mark.parametrize(
    ('declaration', 'message'),
    [
        pytest.param(booleans.int_operands, 'must be boolean', id='int-operand'),
        pytest.param(booleans.literal_operands, 'must be boolean', id='literal-operands'),
        pytest.param(
            booleans.arbitrary_identity_value,
            'arbitrary `is` identity tests never run',
            id='arbitrary-identity-value',
        ),
        pytest.param(
            booleans.arbitrary_identity_rhs,
            'arbitrary `is` identity tests never run',
            id='arbitrary-identity-rhs',
        ),
    ],
)
def test_rejected_operands_fail_during_build(declaration: GraphHandle, message: str) -> None:
    """Non-boolean operands and arbitrary identities fail at build."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('divisor', 'expected'),
    [
        pytest.param(0, 6, id='skipped'),
        pytest.param(2, 5, id='taken'),
        pytest.param(3, 6, id='unguarded-false'),
    ],
)
def test_guarded_divisor_runs(divisor: int, expected: int) -> None:
    """A zero divisor skips the guarded remainder instead of dividing by zero."""
    outputs, node = run_get_node(booleans.guarded_divisor, value=4, divisor=divisor)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('flag', 'value', 'expected', 'runs_check'),
    [
        pytest.param(False, 5, 7, False, id='skipped'),
        pytest.param(True, 5, 6, True, id='taken'),
        pytest.param(True, -5, -3, True, id='taken-false'),
    ],
)
def test_lazy_rhs_runs(flag: bool, value: int, expected: int, runs_check: bool) -> None:
    """The right-hand task runs only when the flag selects it."""
    outputs, node = run_get_node(booleans.lazy_rhs, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    labels = [entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()]
    assert any('is_positive' in label for label in labels) == runs_check


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('flag', 'value', 'expected', 'runs_check'),
    [
        pytest.param(True, -5, -4, False, id='short-circuit'),
        pytest.param(False, 5, 6, True, id='evaluated-true'),
        pytest.param(False, -5, -3, True, id='evaluated-false'),
    ],
)
def test_lazy_or_runs(flag: bool, value: int, expected: int, runs_check: bool) -> None:
    """The right-hand task runs only when the flag does not already select the side."""
    outputs, node = run_get_node(booleans.lazy_or, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    labels = [entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()]
    assert any('is_positive' in label for label in labels) == runs_check


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('flag', 'other', 'value', 'expected'),
    [
        pytest.param(True, True, 5, 6, id='all-taken'),
        pytest.param(False, True, 5, 7, id='first-skipped'),
        pytest.param(True, False, 5, 7, id='second-skipped'),
        pytest.param(True, True, -5, -3, id='task-false'),
    ],
)
def test_chained_guards_run(flag: bool, other: bool, value: int, expected: int) -> None:
    """Three operands fold left to right, skipping every unselected side."""
    outputs, node = run_get_node(booleans.chained_guards, value=value, flag=flag, other=other)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('flag', 'other', 'value', 'expected'),
    [
        pytest.param(True, True, -3, -2, id='and-taken'),
        pytest.param(False, True, -3, -1, id='or-false'),
        pytest.param(False, False, 5, 6, id='or-taken'),
    ],
)
def test_mixed_guards_run(flag: bool, other: bool, value: int, expected: int) -> None:
    """`and` inside `or` still skips each unselected side."""
    outputs, node = run_get_node(booleans.mixed_guards, value=value, flag=flag, other=other)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('flag', 'value', 'expected'),
    [
        pytest.param(True, 5, 7, id='negated-taken'),
        pytest.param(False, 5, 6, id='negated-skipped'),
    ],
)
def test_negated_guard_runs(flag: bool, value: int, expected: int) -> None:
    """`not` reads the joined boolean like any other boolean wire."""
    outputs, node = run_get_node(booleans.negated_guard, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('flag', 'value', 'expected'),
    [
        pytest.param(True, 5, 5, id='taken'),
        pytest.param(False, 5, 0, id='flag-skipped'),
        pytest.param(True, -5, 0, id='task-skipped'),
    ],
)
def test_picked_guard_runs(flag: bool, value: int, expected: int) -> None:
    """A joined boolean wires into a task argument like a bound name."""
    outputs, node = run_get_node(booleans.picked_guard, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'target', 'max_steps', 'expected'),
    [
        pytest.param(5, 2, 10, 5, id='target'),
        pytest.param(5, 2, 1, 5, id='budget'),
        pytest.param(5, 5, 10, 5, id='zero'),
    ],
)
def test_bounded_count_runs(value: int, target: int, max_steps: int, expected: int) -> None:
    """The loop steps until the target matches or the attempt budget runs out."""
    outputs, node = run_get_node(booleans.bounded_count, value=value, target=target, max_steps=max_steps)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(None, True, 3, id='absent'),
        pytest.param(5, True, 2, id='present-taken'),
        pytest.param(5, False, 3, id='flag-skipped'),
    ],
)
def test_none_guarded_runs(value: int | None, flag: bool, expected: int) -> None:
    """Presence on the left selects the side without computing a value."""
    outputs, node = run_get_node(booleans.none_guarded, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'fallback', 'expected'),
    [
        pytest.param(3, 5, 6, id='member-taken'),
        pytest.param(3, 0, 0, id='bound-skipped'),
        pytest.param(4, 5, 5, id='member-skipped'),
    ],
)
def test_member_guarded_runs(value: int, fallback: int, expected: int) -> None:
    """A declared error member on the left selects the side without computing a value."""
    outputs, node = run_get_node(booleans.member_guarded, value=value, fallback=fallback)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(None, True, 2, id='absent-taken'),
        pytest.param(None, False, 3, id='absent-flag-skipped'),
        pytest.param(5, True, 3, id='present-skipped'),
        pytest.param(5, False, 3, id='flag-skipped'),
    ],
)
def test_presence_rhs_runs(value: int | None, flag: bool, expected: int) -> None:
    """Presence on the right selects the side through an ephemeral boolean value."""
    outputs, node = run_get_node(booleans.presence_rhs, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(None, False, 2, id='absent-taken'),
        pytest.param(5, False, 3, id='present-skipped'),
        pytest.param(5, True, 2, id='flag-taken'),
    ],
)
def test_or_presence_rhs_runs(value: int | None, flag: bool, expected: int) -> None:
    """Presence on the right of `or` selects the side like any other boolean."""
    outputs, node = run_get_node(booleans.or_presence_rhs, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        pytest.param(None, 2, id='absent'),
        pytest.param(5, 3, id='present'),
    ],
)
def test_presence_value_runs(value: int | None, expected: int) -> None:
    """A named presence predicate wires into a branch like a bound boolean."""
    outputs, node = run_get_node(booleans.presence_value, value=value)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(None, True, 3, id='absent'),
        pytest.param(5, True, 2, id='present-taken'),
        pytest.param(5, False, 3, id='flag-skipped'),
    ],
)
def test_named_present_runs(value: int | None, flag: bool, expected: int) -> None:
    """A named `is not None` wire joins with a flag on the left."""
    outputs, node = run_get_node(booleans.named_present, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(None, True, 3, id='absent'),
        pytest.param(5, True, 2, id='present-taken'),
        pytest.param(5, False, 3, id='flag-skipped'),
    ],
)
def test_negated_present_runs(value: int | None, flag: bool, expected: int) -> None:
    """A named `not (value is None)` wire joins like any other boolean."""
    outputs, node = run_get_node(booleans.negated_present, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(None, True, 3, id='absent'),
        pytest.param(5, True, 2, id='present-taken'),
        pytest.param(5, False, 3, id='flag-skipped'),
    ],
)
def test_negated_rhs_runs(value: int | None, flag: bool, expected: int) -> None:
    """A negated presence test on the right selects through its boolean value."""
    outputs, node = run_get_node(booleans.negated_rhs, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'fallback', 'expected'),
    [
        pytest.param(3, 5, 6, id='member-taken'),
        pytest.param(3, 0, 0, id='bound-skipped'),
        pytest.param(4, 5, 5, id='member-skipped'),
    ],
)
def test_member_value_runs(value: int, fallback: int, expected: int) -> None:
    """A named `is` member wire joins with a comparison on the right."""
    outputs, node = run_get_node(booleans.member_value, value=value, fallback=fallback)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'fallback', 'expected'),
    [
        pytest.param(4, 0, 1, id='member-taken'),
        pytest.param(3, 0, 0, id='bound-skipped'),
        pytest.param(3, -1, -1, id='both-skipped'),
    ],
)
def test_member_not_value_runs(value: int, fallback: int, expected: int) -> None:
    """A named `is not` member wire joins on the left of `or`."""
    outputs, node = run_get_node(booleans.member_not_value, value=value, fallback=fallback)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'fallback', 'expected'),
    [
        pytest.param(4, 5, 6, id='member-taken'),
        pytest.param(3, 5, 5, id='member-skipped'),
        pytest.param(4, -1, -1, id='bound-skipped'),
    ],
)
def test_negated_member_rhs_runs(value: int, fallback: int, expected: int) -> None:
    """A negated member test on the right selects through its boolean value."""
    outputs, node = run_get_node(booleans.negated_member_rhs, value=value, fallback=fallback)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'other', 'expected', 'runs_check'),
    [
        pytest.param(None, 5, 7, False, id='absent-skipped'),
        pytest.param(5, 5, 6, True, id='present-taken'),
        pytest.param(5, -5, -3, True, id='present-false'),
    ],
)
def test_lazy_presence_and_runs(value: int | None, other: int, expected: int, runs_check: bool) -> None:
    """The right-hand task runs only when presence selects it."""
    outputs, node = run_get_node(booleans.lazy_presence_and, value=value, other=other)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    labels = [entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()]
    assert any('is_positive' in label for label in labels) == runs_check


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'other', 'expected', 'runs_check'),
    [
        pytest.param(None, 5, 6, False, id='absent-short-circuit'),
        pytest.param(5, 5, 6, True, id='present-taken'),
        pytest.param(5, -5, -3, True, id='present-false'),
    ],
)
def test_lazy_presence_or_runs(value: int | None, other: int, expected: int, runs_check: bool) -> None:
    """Presence on the left of `or` short-circuits the right-hand task."""
    outputs, node = run_get_node(booleans.lazy_presence_or, value=value, other=other)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    labels = [entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()]
    assert any('is_positive' in label for label in labels) == runs_check


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        pytest.param(None, 3, id='absent'),
        pytest.param(5, 2, id='present'),
    ],
)
def test_conditional_present_runs(value: int | None, expected: int) -> None:
    """A selection tests presence directly in its condition."""
    outputs, node = run_get_node(booleans.conditional_present, value=value)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'flag', 'expected'),
    [
        pytest.param(5, True, 2, id='taken'),
        pytest.param(None, True, 3, id='absent'),
        pytest.param(5, False, 3, id='flag-skipped'),
    ],
)
def test_conditional_joined_present_runs(value: int | None, flag: bool, expected: int) -> None:
    """A selection guards on a joined presence predicate on the right."""
    outputs, node = run_get_node(booleans.conditional_joined_present, value=value, flag=flag)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        pytest.param(3, 0, id='absent'),
        pytest.param(4, 1, id='present'),
    ],
)
def test_while_present_runs(value: int, expected: int) -> None:
    """A direct presence test re-evaluates before every iteration."""
    outputs, node = run_get_node(booleans.while_present, value=value)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        pytest.param(3, 0, id='absent'),
        pytest.param(4, 1, id='present'),
    ],
)
def test_while_named_present_runs(value: int, expected: int) -> None:
    """A named presence wire recomputes before every iteration."""
    outputs, node = run_get_node(booleans.while_named_present, value=value)
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
def test_guarded_task_loop_runs() -> None:
    """A task-stepped loop joins the flag with a task check every iteration."""
    outputs, node = run_get_node(booleans.guarded_task_loop, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 0
    outputs, node = run_get_node(booleans.guarded_task_loop, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 2


@pytest.mark.usefixtures('aiida_profile_clean')
def test_guarded_task_loop_restores_mid_loop() -> None:
    """A checkpoint taken inside a joined-condition loop restores the pending iteration."""
    spec = compile_graph(booleans.guarded_task_loop)
    state = run_mod.GraphRun(spec, given={'value': 2, 'flag': True})
    first = state.step()
    assert [start.instance for start in first.starts] == ['add']
    for start in first.starts:
        assert isinstance(start.task, ProcessTask)
        from aiida.engine import run_get_node as launch

        _, node = launch(start.task.spec.process_class, **start.inputs)
        assert node.pk is not None
        state.started(start.instance, node.pk)
        state.completed(start.instance, node.pk)
    arm = state.step()
    assert [start.instance for start in arm.starts] == ['branch_2__is_positive']
    for start in arm.starts:
        assert isinstance(start.task, ProcessTask)
        from aiida.engine import run_get_node as launch

        _, node = launch(start.task.spec.process_class, **start.inputs)
        assert node.pk is not None
        state.started(start.instance, node.pk)
        state.completed(start.instance, node.pk)
    second = state.step()
    assert [start.instance for start in second.starts] == ['loop_3_iteration_0__step_down']
    for start in second.starts:
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
        assert _drive_to_completion(run)['result'].value == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_while_present_restores_mid_loop() -> None:
    """A checkpoint inside a direct-presence loop restores the pending iteration."""
    spec = compile_graph(booleans.while_present)
    state = run_mod.GraphRun(spec, given={'value': 4})
    first = state.step()
    assert [start.instance for start in first.starts] == ['check_even']
    for start in first.starts:
        assert isinstance(start.task, ProcessTask)
        from aiida.engine import run_get_node as launch

        _, node = launch(start.task.spec.process_class, **start.inputs)
        assert node.pk is not None
        state.started(start.instance, node.pk)
        state.completed(start.instance, node.pk)
    second = state.step()
    assert {start.instance for start in second.starts} == {
        'loop_4_iteration_0__add',
        'loop_4_iteration_0__add_2',
    }
    for start in second.starts:
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
        assert _drive_to_completion(run)['result'].value == 1
