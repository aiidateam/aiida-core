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
from aiida.engine import graph, par_map, task
from aiida.engine.launch import run_get_node
from aiida.engine.processes.exit_code import ExitCodeEnum
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.results import Err, Ok, Result
from aiida.orm import DataList

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
    """Wrap one fallible task in a nested scope, exposing absence on failure."""
    value, _ = flaky_increment(x=x)
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
    value = nested_flaky(x=x)
    if value is None:
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
    value, error = flaky_increment(x=x)
    retry = should_retry(error=error, attempt=x)
    while retry:
        x = x + 1
        value, error = flaky_increment(x=x)
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
    value, error = flaky_increment(x=x)
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
    """A nested declared failure completes and the outer branch sees `value is None`."""
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
