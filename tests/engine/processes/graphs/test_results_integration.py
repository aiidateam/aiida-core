###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Cross-feature regressions: declared `Result` failures across scopes.

Upstream `feature/graph-exit-codes` covers single-scope `Result` branching,
`CalcJob` exit mapping (`errors=`), loop retries with absent-arm rebinding,
and `is`/`is not` member branches in the flat scheduler. These tests pin the
same semantics in the single-process scope scheduler, where nested graphs,
branches, loops, and maps are checkpointable logical scopes of one
:class:`GraphProcess` and only task runs and map collectors become children:

- a declared `Err` inside a nested graph counts as completed and the outer
  branch selects on the absent `value` arm (`is None`);
- a loop retries a declared failure with an inline counter and a named retry
  predicate, and a final task materializes the recovered value;
- a branch distinguishes one declared enum member (`is`/`is not`), including
  through a serialized IR round trip;
- a fallible task cannot map directly: the existing single-output map shape
  rejects its `value`/`error` arms at build time.
"""

import json

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.engine import ProcessState, graph, par_map, task
from aiida.engine.launch import run_get_node
from aiida.engine.processes.exit_code import ExitCodeEnum
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.results import Err, Ok, Result
from aiida.engine.processes.graphs.run import GraphRun
from aiida.orm import CalcFunctionNode, DataList, Int
from aiida.orm.utils.serialize import deserialize_unsafe, serialize
from tests.engine.processes.graphs.programs import results

pytestmark = pytest.mark.presto


class FlakyErrors(ExitCodeEnum):
    """Two declared failures for cross-scope branch and retry tests."""

    ODD = (400, 'odd input, retry with the next integer')
    TOO_BIG = (401, 'input above the retry ceiling')


@task
def flaky_increment(x: int) -> Result[int, FlakyErrors]:
    """Fail declared outcomes for odd or large inputs, else succeed."""
    if x > 10:
        return Err(FlakyErrors.TOO_BIG)
    if x % 2:
        return Err(FlakyErrors.ODD)
    return Ok(x + 1)


@graph
def nested_flaky(x: int) -> int:
    """Wrap one fallible task in a nested scope, propagating failures."""
    value = flaky_increment(x=x)
    return value


@task
def mark_absent() -> bool:
    """Report that the nested scope left no value arm."""
    return True


@task
def mark_present(value: int) -> bool:
    """Report that the nested scope left a value arm."""
    return False


@graph
def branch_on_nested_error(x: int) -> bool:
    """Branch outside the nested scope on the absent success arm."""
    value, error = nested_flaky(x=x).catch()
    if error is not None:
        selected = mark_absent()
    else:
        selected = mark_present(value=value)
    return selected


@task
def should_retry(error: FlakyErrors | None, attempt: int) -> bool:
    """Retry while a declared failure remains and attempts do."""
    return error is not None and attempt < 5


@task
def ensure_value(value: int | None, error: FlakyErrors | None) -> int:
    """Read the recovered value, failing loudly when none remains."""
    if error is not None or value is None:
        raise ValueError('the step never succeeded.')
    return value


@graph
def retry_until_even(x: int) -> int:
    """Retry a declared `ODD` failure with an inline counter and a named predicate."""
    value, error = flaky_increment(x=x).catch()
    retry = should_retry(error=error, attempt=x)
    while retry:
        x = x + 1
        value, error = flaky_increment(x=x).catch()
        retry = should_retry(error=error, attempt=x)
    return ensure_value(value=value, error=error)


@task
def label_odd() -> str:
    """Name the distinguished declared member."""
    return 'odd'


@task
def label_other(error: FlakyErrors) -> str:
    """Name any other declared failure."""
    return 'other-error'


@task
def label_ok(value: int) -> str:
    """Name the successful outcome."""
    return 'ok'


@graph
def branch_on_member(x: int) -> str:
    """Distinguish one declared member from every other outcome."""
    value, error = flaky_increment(x=x).catch()
    if error is FlakyErrors.ODD:
        selected = label_odd()
    elif error is not None:
        selected = label_other(error=error)
    else:
        selected = label_ok(value=value)
    return selected


@graph
def map_fallible(values: DataList) -> DataList:
    """Map a fallible task directly; the single-output shape rejects the extra arm."""
    return par_map(flaky_increment, values)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_on_nested_error_arm():
    """A nested declared failure completes and the outer branch sees the error arm."""
    _, node = run_get_node(branch_on_nested_error, x=1)
    assert node.is_finished_ok, f'graph failed: {node.exit_message}'
    assert node.outputs.result.value is True

    _, node = run_get_node(branch_on_nested_error, x=2)
    assert node.is_finished_ok, f'graph failed: {node.exit_message}'
    assert node.outputs.result.value is False


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_retries_declared_failure():
    """A loop re-enters after a declared failure and settles on the first `Ok`."""
    _, node = run_get_node(retry_until_even, x=1)
    assert node.is_finished_ok, f'graph failed: {node.exit_message}'
    # `1` fails declared-odd, `2` succeeds with `3`.
    assert node.outputs.result.value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_on_error_member():
    """`is` selects the named member, `is not None` catches the other failure."""
    _, odd = run_get_node(branch_on_member, x=1)
    assert odd.is_finished_ok, f'graph failed: {odd.exit_message}'
    assert odd.outputs.result.value == 'odd'

    _, big = run_get_node(branch_on_member, x=11)
    assert big.is_finished_ok, f'graph failed: {big.exit_message}'
    assert big.outputs.result.value == 'other-error'

    _, ok = run_get_node(branch_on_member, x=2)
    assert ok.is_finished_ok, f'graph failed: {ok.exit_message}'
    assert ok.outputs.result.value == 'ok'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_on_error_member_survives_serialized_ir():
    """The stored member test selects the same arm after an IR round trip."""
    spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(branch_on_member).to_dict())))
    member_tests = [
        entry.condition_test
        for entry in spec.tasks
        if hasattr(entry, 'condition_test') and entry.condition_test in ('is_member', 'is_not_member')
    ]
    assert member_tests, 'expected a stored member test after serialization'
    _, odd = run_get_node(branch_on_member, x=1)
    assert odd.is_finished_ok, f'graph failed: {odd.exit_message}'
    assert odd.outputs.result.value == 'odd'


def test_fallible_task_cannot_map_directly():
    """A fallible task exposes two arms, so the single-output map shape rejects it."""
    with pytest.raises(GraphLanguageError, match='single output'):
        map_fallible.build()


@graph
def propagate_through_nested(x: int) -> bool:
    """The success consumer must not run after propagation."""
    value = nested_flaky(x=x)
    return mark_present(value=value)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bare_failure_preserves_exit_code_and_blocks_consumers():
    assert propagate_through_nested.build() is None
    outputs, node = run_get_node(propagate_through_nested, x=1)
    assert node.is_failed
    assert (node.exit_status, node.exit_message) == FlakyErrors.ODD.value[:2]
    assert not outputs
    assert [called.process_label for called in node.called] == ['flaky_increment']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bare_success_returns_original_node():
    outputs, node = run_get_node(nested_flaky, x=2)
    (child,) = node.called
    assert node.is_finished_ok
    assert outputs['result'].pk == child.outputs.value.pk


@graph
def choose_early(first: int, second: int, early: bool) -> int:
    if early:
        return first
    else:
        return second


@graph
def call_early(first: int, second: int, early: bool) -> int:
    return choose_early(first=first, second=second, early=early)


@pytest.mark.parametrize(('early', 'expected'), [(True, 1), (False, 2)])
def test_success_returns_from_both_arms(early, expected):
    first, second = Int(1), Int(2)
    outputs, node = run_get_node(call_early, first=first, second=second, early=early)
    assert node.is_finished_ok
    assert outputs['result'].pk == (first if early else second).pk
    assert outputs['result'].value == expected
    assert not node.called


@graph
def guarded_join(x: int, reject: bool, enter: bool) -> Result[int, FlakyErrors]:
    if enter:
        if reject:
            return Err(FlakyErrors.ODD)
        else:
            return Ok(x)
    elif reject:
        return Err(FlakyErrors.TOO_BIG)
    else:
        selected = flaky_increment(x=x)
    return Ok(selected)


@pytest.mark.parametrize(('enter', 'error'), [(True, FlakyErrors.ODD), (False, FlakyErrors.TOO_BIG)])
def test_nested_error_returns(enter, error):
    outputs, node = run_get_node(guarded_join, x=2, reject=True, enter=enter)
    assert (node.exit_status, node.exit_message) == error.value[:2]
    assert not outputs
    assert not node.called


def test_only_continuing_arm_provides_join_value():
    outputs, node = run_get_node(guarded_join, x=2, reject=False, enter=False)
    assert node.is_finished_ok
    (child,) = node.called
    assert outputs['result'].pk == child.outputs.value.pk


@task
def advance_early(x: int) -> int:
    return x + 1


@graph
def stop_in_loop(x: int, fail_at: int, limit: int) -> Result[int, FlakyErrors]:
    current = x
    while current < limit:
        if current >= fail_at:
            return Err(FlakyErrors.TOO_BIG)
        current = advance_early(x=current)
    _following = mark_present(value=x)
    return Ok(current)


@graph
def capture_loop_return(x: int) -> bool:
    value, error = stop_in_loop(x=x, fail_at=1, limit=3).catch()
    if error is FlakyErrors.TOO_BIG:
        if value is None:
            return mark_absent()
    return mark_present(value=value)


@graph
def propagate_loop_return(x: int) -> int:
    return stop_in_loop(x=x, fail_at=1, limit=3)


def test_loop_return_blocks_later_iteration_and_independent_continuation():
    outputs, node = run_get_node(propagate_loop_return, x=0)
    assert (node.exit_status, node.exit_message) == FlakyErrors.TOO_BIG.value[:2]
    assert not outputs
    assert [child.process_label for child in node.called] == ['advance_early']


def test_capture_of_loop_return_exposes_only_error():
    outputs, node = run_get_node(capture_loop_return, x=0)
    assert node.is_finished_ok
    assert outputs['result'].value is True
    assert {child.process_label for child in node.called} == {'advance_early', 'mark_absent'}


@pytest.mark.parametrize('reject', [False, True])
def test_early_return_survives_template_and_checkpoint_round_trip(reject):
    template = GraphIR.from_dict(json.loads(json.dumps(compile_graph(guarded_join).to_dict())))
    value = Int(2).store()
    state = GraphRun(template, given={'x': value, 'reject': reject, 'enter': True})
    assert not state.step().starts
    restored = GraphRun.from_dict(template, state.given, deserialize_unsafe(serialize(state.to_dict())))
    assert not restored.step().starts
    if reject:
        assert restored.propagated_exit_code == FlakyErrors.ODD.value
        assert not restored.outputs()
    else:
        assert restored.propagated_exit_code is None
        assert restored.outputs()['result'].pk == value.pk


@graph
def invalid_early_member(x: int, reject: bool) -> Result[int, FlakyErrors]:
    if reject:
        return Err(results.DivisionErrors.ZERO_DENOMINATOR)
    return Ok(x)


def test_early_error_must_be_declared():
    with pytest.raises(GraphLanguageError, match='declared in Result'):
        invalid_early_member.build()


@graph
def propagate_formatted(x: float) -> float:
    """Forward the formatted exit message through the graph boundary."""
    return results.divide_reported(numerator=x, denominator=2.0)


@graph
def outer_formatted(x: float) -> float:
    return propagate_formatted(x=x)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_formatted_error_survives_nested_propagation():
    _, node = run_get_node(outer_formatted, x=-4.0)
    (child,) = node.called
    assert node.exit_status == child.exit_status == 411
    assert node.exit_message == child.exit_message == 'Negative numerator: -4.0'


@task
def also_410() -> Result[float, results.AliasErrors]:
    return Err(results.AliasErrors.ALSO_ZERO)


@graph
def choose_error(first: bool, x: float) -> float:
    if first:
        value = results.divide(numerator=x, denominator=0.0)
    else:
        value = also_410()
    return value


@graph
def capture_aliased_scope(first: bool, x: float) -> float:
    _, error = choose_error(first=first, x=x).alias('chosen').catch()
    if error is results.AliasErrors.ALSO_ZERO:
        selected = x
    else:
        selected = results.recover_zero(error=error)
    return selected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(('first', 'expected'), [(True, 0.0), (False, 3.0)])
def test_nested_capture_distinguishes_equal_statuses(first, expected):
    template = compile_graph(capture_aliased_scope)
    assert not template.declared_errors
    assert len(template.task('chosen').body.declared_errors) == 2
    outputs, node = run_get_node(capture_aliased_scope, first=first, x=3.0)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    assert all(not child.is_finished_ok or child.process_label == 'recover_zero' for child in node.called)


@graph
def capture_with_uncaught_sibling(x: int) -> bool:
    value, error = nested_flaky(x=x).alias('captured').catch()
    also = nested_flaky(x=x).alias('uncaught')
    if error is not None:
        selected = mark_present(value=also)
    else:
        selected = mark_present(value=value)
    return selected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_captured_invocation_does_not_handle_siblings():
    _, node = run_get_node(capture_with_uncaught_sibling, x=1)
    assert node.exit_status == FlakyErrors.ODD.value.status
    assert not node.is_excepted


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_capture_survives_checkpoint_before_and_after_failure():
    template = GraphIR.from_dict(json.loads(json.dumps(compile_graph(branch_on_nested_error).to_dict())))
    state = GraphRun(template, given={'x': Int(1)})
    (start,) = state.step().starts
    _, child = run_get_node(flaky_increment, x=1)
    state.started(start.instance, child.pk)
    pending = GraphRun.from_dict(template, state.given, state.to_dict())
    pending.completed(start.instance, child.pk)
    restored = GraphRun.from_dict(template, pending.given, pending.to_dict())
    assert restored.propagated_exit_code is None
    (recovery,) = restored.step().starts
    assert recovery.task.name == 'mark_absent'


@graph
def concurrent_failures(first: int, second: int) -> int:
    value = flaky_increment(x=first).alias('first_call')
    _other = flaky_increment(x=second).alias('second_call')
    return value


@pytest.mark.usefixtures('aiida_profile_clean')
def test_first_observed_failure_stays_latched_after_resume():
    template = compile_graph(concurrent_failures)
    state = GraphRun(template, given={'first': Int(1), 'second': Int(11)})
    first, second = state.step().starts
    assert (first.instance, second.instance) == ('first_call', 'second_call')
    _, first_child = run_get_node(flaky_increment, x=1)
    _, second_child = run_get_node(flaky_increment, x=11)
    state.started(first.instance, first_child.pk)
    state.started(second.instance, second_child.pk)
    state.completed(second.instance, second_child.pk)

    restored = GraphRun.from_dict(template, state.given, state.to_dict())
    restored.completed(first.instance, first_child.pk)
    assert not restored.step().starts
    assert restored.propagated_exit_code == FlakyErrors.TOO_BIG.value


@graph
def capture_value(x: int) -> int:
    value = flaky_increment(x=x)
    result, _ = value.catch()
    return result


@graph
def capture_expression(x: int) -> int:
    result, _ = (x + 1).catch()
    return result


@graph
def capture_infallible(x: int) -> bool:
    result, _ = mark_present(value=x).catch()
    return result


@graph
def capture_without_unpack(x: int) -> int:
    result = flaky_increment(x=x).catch()
    return result


@graph
def capture_with_argument(x: int) -> int:
    result, _ = flaky_increment(x=x).catch(x)
    return result


@graph
def capture_wrong_arity(x: int) -> int:
    result, _, _ = flaky_increment(x=x).catch()
    return result


@graph
def legacy_unpack(x: float) -> float:
    value, _ = results.divide_quotient(numerator=x, denominator=1.0)
    return value.ratio


@graph
def compare_undeclared_member(x: float) -> float:
    value, error = results.divide(numerator=x, denominator=0.0).catch()
    if error is results.AliasErrors.ALSO_ZERO:
        selected = x
    else:
        selected = value
    return selected


@pytest.mark.parametrize(
    ('declaration', 'message'),
    [
        (capture_value, 'a name cannot be both a wire and a declaration'),
        (capture_expression, 'use a task or graph declaration'),
        (capture_infallible, 'with declared failures'),
        (capture_without_unpack, 'tuple assignment'),
        (capture_with_argument, 'takes no arguments'),
        (capture_wrong_arity, 'must unpack into exactly two names'),
        (legacy_unpack, 'bare Result calls expose only success'),
        (compare_undeclared_member, 'enum is not declared'),
    ],
)
def test_invalid_capture_forms(declaration, message):
    with pytest.raises(GraphLanguageError, match=rf'test_results_integration.py:\d+:\d+:[^\n]+{message}'):
        declaration.build()


@graph
def bare_structured(x: float) -> float:
    value = results.divide_tuple(numerator=x, denominator=2.0)
    return value.ratio


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bare_structured_success_binds_its_fields():
    assert bare_structured.build() is None
    outputs, node = run_get_node(bare_structured, x=3.0)
    assert node.is_finished_ok
    assert outputs['result'].value == 1.5


@task
def maybe_value(x: int) -> Result[int | None, FlakyErrors]:
    if x < 0:
        return Err(FlakyErrors.ODD)
    return Ok(x or None)


@task
def describe_capture(value: int | None, error: FlakyErrors | None) -> str:
    if error is not None:
        assert value is None
        return error.name
    return str(value)


@graph
def capture_nullable(x: int) -> str:
    value, error = maybe_value(x=x).catch()
    return describe_capture(value=value, error=error)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(('x', 'expected'), [(-1, 'ODD'), (0, 'None'), (1, '1')])
def test_nullable_capture_uses_error_as_discriminator(x, expected):
    outputs, node = run_get_node(capture_nullable, x=x)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@graph
def loop_propagates(x: int) -> int:
    while x < 4:
        x = flaky_increment(x=x)
    return x


@pytest.mark.usefixtures('aiida_profile_clean')
def test_uncaught_failure_stops_loop_on_second_iteration():
    assert compile_graph(loop_propagates).declared_errors == compile_graph(nested_flaky).declared_errors
    _, node = run_get_node(loop_propagates, x=2)
    assert node.exit_status == FlakyErrors.ODD.value.status
    assert sorted(child.exit_status for child in node.called) == [0, FlakyErrors.ODD.value.status]


@graph
def recovery_can_fail(x: int) -> int:
    value, error = flaky_increment(x=x).catch()
    if error is not None:
        result = flaky_increment(x=11)
    else:
        result = value
    return result


@pytest.mark.usefixtures('aiida_profile_clean')
def test_uncaught_recovery_failure_propagates():
    assert compile_graph(recovery_can_fail).declared_errors == compile_graph(nested_flaky).declared_errors
    _, node = run_get_node(recovery_can_fail, x=1)
    assert node.exit_status == FlakyErrors.TOO_BIG.value.status


@task
def unexpected_failure(x: int) -> Result[int, FlakyErrors]:
    if x == 0:
        return Err(FlakyErrors.ODD)
    if x == 1:
        return Err(FlakyErrors.ODD.value._replace(status=777))
    if x == 2:
        raise RuntimeError('task exception')
    return Ok('not an int')  # type: ignore[arg-type]


@graph
def capture_unexpected(x: int) -> str:
    value, error = unexpected_failure(x=x).catch()
    return describe_capture(value=value, error=error)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('x', [1, 2, 3], ids=['undeclared', 'exception', 'invalid-output'])
def test_unexpected_failures_do_not_release_capture(x):
    outputs, node = run_get_node(capture_unexpected, x=x)
    expected = capture_unexpected.process_class.exit_codes.ERROR_TASK_FAILED.format(task='unexpected_failure')
    assert (node.exit_status, node.exit_message) == expected[:2]
    assert not outputs
    (child,) = node.called
    assert child.process_label == 'unexpected_failure'
    assert child.is_excepted


@pytest.mark.usefixtures('aiida_profile_clean')
def test_capture_does_not_handle_killed_child():
    state = GraphRun(compile_graph(capture_unexpected), given={'x': Int(0)})
    (start,) = state.step().starts
    child = CalcFunctionNode().store()
    child.set_process_state(ProcessState.KILLED)
    state.started(start.instance, child.pk)
    state.completed(start.instance, child.pk)
    assert not state.step().starts
    assert state.failed == [start.instance]
    assert state.propagated_exit_code is None


@task
def maybe_quotient(x: float) -> Result[results.Quotient | None, results.DivisionErrors]:
    if x < 0:
        return Err(results.DivisionErrors.ZERO_DENOMINATOR)
    return Ok(results.Quotient(ratio=x) if x else None)


@graph
def nested_nullable_structure(x: float) -> results.Quotient | None:
    return maybe_quotient(x=x)


@graph
def capture_nullable_structure(x: float) -> float:
    value, error = nested_nullable_structure(x=x).catch()
    if error is not None:
        selected = results.recover_zero(error=error)
    elif value is None:
        selected = x
    else:
        selected = value.ratio
    return selected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('x, expected', [(-1.0, 0.0), (0.0, 0.0), (2.0, 2.0)])
def test_nested_capture_preserves_optional_structured_success(x, expected):
    assert capture_nullable_structure.build() is None
    outputs, node = run_get_node(capture_nullable_structure, x=x)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
