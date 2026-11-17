###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Loops declarations shared by the graph behavior suites.

The inline authoring examples keep counters and retry predicates in the graph,
while tasks produce the returned data. See ``graph`` for the authoring contract.
The remaining declarations are task-based regression fixtures.
"""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.results import Err, Ok, Result
from tests.engine.processes.graphs.programs import tasks as task_module
from tests.engine.processes.graphs.programs.port_models import Settings
from tests.engine.processes.graphs.programs.ports import nullable_return
from tests.engine.processes.graphs.programs.tasks import add, arithmetic_pair, decrement, is_positive


class TryErrors(ExitCodeEnum):
    """Declared failures of the generic fallible step."""

    RETRYABLE = ExitCode(410, 'Simulated retryable failure.')


@task
def try_step(x: int, attempt: int) -> Result[int, TryErrors]:
    """Run one generic fallible step: declared failure on the first attempt, present after."""
    if attempt < 1:
        return Err(TryErrors.RETRYABLE)
    return Ok(x + 1)


@task
def check_present(value: int | None) -> None:
    """Validate the recovered value, leaving the returned node untouched."""
    if value is None:
        raise ValueError('the step never succeeded.')


@graph
def bounded_steps(start: int, limit: int, count: int = 0) -> int:
    """Step a value a bounded number of times, returning the last task output.

    The counter starts at its default input, advances inline, and gates the loop
    through an inline comparison; only the ``add`` placements create nodes.

    :param start: the value the first iteration steps from.
    :param limit: the number of steps; ``0`` returns the seeded value unchanged.
    :param count: the zero-based step the first iteration counts from.
    :return: ``start`` stepped ``limit`` times through ``add``.
    """
    value = add(x=start, y=0)
    while count < limit:
        count = count + 1
        value = add(x=value, y=1)
    return value


@graph
def retry_until_present(start: int, limit: int, attempt: int = 0) -> int | None:
    """Retry a generic fallible step until its value arm is present.

    The member check and budget combine with short-circuiting ``and``.
    The trailing guard validates without replacing the successful step's output.

    :param start: the value the steps build from.
    :param limit: the retry budget; retries continue while ``attempt < limit``.
    :param attempt: the zero-based attempt the first run steps from.
    :return: the first present step output; the guard fails if none succeeded.
    """
    value, error = try_step(x=start, attempt=attempt)
    retry = error is TryErrors.RETRYABLE and attempt < limit
    while retry:
        attempt = attempt + 1
        value, error = try_step(x=start, attempt=attempt)
        retry = error is TryErrors.RETRYABLE and attempt < limit
    checked = check_present(value=value)  # noqa: F841 - the guard validates without feeding the return
    return value


# --- Remaining graphs are intentionally task-based behavior regression fixtures ---
# They keep ``@task`` predicates (for example ``is_positive``) to lock in stored-provenance
# behavior, unlike the recommended inline authoring examples above. Left unchanged.


@graph
def namespaced_loop(value: int) -> int:
    """Call through a module namespace inside a loop body."""
    total = task_module.add(x=value, y=1)
    while task_module.is_positive(value=total):
        total = task_module.decrement(value=total)
    return total


@graph
def countdown(value: int, condition: bool) -> int:
    """Loop until a task-computed condition clears."""
    while condition:
        value = decrement(value=value)
        condition = is_positive(value=value)
    return value


@graph
def countdown_then_add(value: int, condition: bool) -> int:
    """Consume a loop output downstream, including when the loop never runs."""
    while condition:
        value = decrement(value=value)
        condition = is_positive(value=value)
    return add(x=value, y=1)


@graph
def countdown_call(value: int) -> int:
    """Loop on an inline predicate call, re-evaluated every iteration."""
    while is_positive(value=value):
        value = decrement(value=value)
    return value


@graph
def nested_branch_in_loop(value: int) -> int:
    """Branch inside a loop; arms rebind loop state like assignments do."""
    total = add(x=value, y=1)
    while is_positive(value=total):
        if is_positive.alias('is_positive_2')(value=total):
            total = decrement(value=total)
        total = decrement(value=total)
    return total


@graph
def nested_condition_update(value: int, running: bool) -> int:
    """Rebind the loop check only inside nested branches; every path updates it."""
    while running:
        if is_positive(value=value):
            if is_positive(value=value):
                running = is_positive(value=value)
            else:
                running = is_positive(value=value)
        elif is_positive(value=value):
            running = is_positive(value=value)
        else:
            running = is_positive(value=value)
        value = decrement(value=value)
    return value


# rejected at lowering: cannot loop over a list of unknown length.
@graph
def fanout(values: list[int]) -> int:
    """Loop over inputs of unknown length; the placement list cannot grow at runtime."""
    for value in values:
        result = add(x=value, y=1)
    return result


# rejected at lowering: write out one call per value instead.
@graph
def list_comprehension(values: list[int]) -> int:
    """Map over inputs inline; scatter is a runtime control, not syntax.

    Unroll the placements instead.
    """
    _ = [add(x=value, y=1) for value in values]
    return add(x=1, y=1)


@graph
def fresh_name_in_loop(value: int) -> int:
    """Bind a fresh name in a loop; each iteration declares it anew as iteration-local state."""
    total = add(x=value, y=1)
    while is_positive(value=total):
        fresh = decrement(value=total)
        total = add(x=fresh, y=0)
    return total


@graph
def iteration_local(value: int, flag: bool) -> int:
    """Rebind a carried total from an iteration-local step; no initial step is needed."""
    total = add(x=value, y=0)
    while flag:
        step = decrement(value=total)
        total = add(x=step, y=0)
        flag = is_positive(value=total)
    return total


@graph
def branch_local_join(value: int, flag: bool) -> int:
    """Bind an iteration-local step on both branch arms; the join stays iteration-local."""
    total = add(x=value, y=0)
    while flag:
        if is_positive(value=total):
            step = decrement(value=total)
        else:
            step = add(x=total, y=0)
        total = add(x=step, y=0)
        flag = is_positive.alias('is_positive_2')(value=total)
    return total


@graph
def nested_local_loop(value: int, flag: bool) -> int:
    """Carry an iteration-local step through a nested loop; each outer pass starts fresh."""
    total = add(x=value, y=0)
    while flag:
        step = decrement(value=total)
        while is_positive(value=step):
            step = decrement(value=step)
        total = add(x=step, y=0)
        flag = is_positive.alias('is_positive_2')(value=total)
    return total


# rejected at lowering: reads before any write need an initial value.
@graph
def local_use_before_def(value: int, flag: bool) -> int:
    """Read a loop-local before its first write; iteration state starts from enclosing names."""
    total = add(x=value, y=0)
    while flag:
        total = add(x=step, y=1)  # noqa: F821 - the undefined name is rejected
        step = add(x=total, y=1)  # noqa: F841 - the write after the rejected read never runs
        flag = is_positive(value=total)
    return total


# rejected at lowering: a conditionally assigned name may stay unbound.
@graph
def local_conditional_assign(value: int, flag: bool) -> int:
    """Read a name assigned on one branch arm only; the other path leaves it unbound."""
    total = add(x=value, y=0)
    while flag:
        if is_positive(value=total):
            step = add(x=total, y=1)
        total = add(x=step, y=0)
        flag = is_positive(value=total)
    return total


# rejected at lowering: iteration-locals never leave the loop.
@graph
def local_leaks_after_loop(value: int, flag: bool) -> int:
    """Return an iteration-local after the loop; locals are fresh each pass and unbound outside."""
    total = add(x=value, y=0)
    while flag:
        step = add(x=total, y=1)
        total = add.alias('add_2')(x=step, y=1)
        flag = is_positive(value=total)
    return step


# rejected at lowering: a branch or loop body only sees names defined around it.
@graph
def unknown_name_in_loop(value: int) -> int:
    """Read an unknown name in a loop body; only enclosing names are visible."""
    total = add(x=value, y=1)
    while is_positive(value=total):
        total = add(x=total, y=zz_missing_value)  # noqa: F821 - the undefined name is rejected
    return total


@graph
def nested_loops(value: int) -> int:
    """Loop inside a loop; inner state threads through the region."""
    total = add(x=value, y=1)
    rough = is_positive(value=total)
    step = decrement(value=total)
    while rough:
        while is_positive(value=step):
            step = decrement(value=step)
        total = decrement(value=step)
        step = decrement.alias('decrement_2')(value=total)
        rough = is_positive.alias('is_positive_2')(value=total)
    return total


@graph
def never_entered_optional(rounds: int, value: int | None = None) -> dict[str, int | None]:
    """Carry an optional input through a loop; an unset one stays absent when the loop never runs."""
    count = add(x=rounds, y=0)
    while is_positive(value=count):
        value = nullable_return(value=count)
        count = decrement(value=count)
    return {'direct': value, 'wired': nullable_return(value=value)}


@graph
def loop_pair_sum(value: int, rounds: int) -> int:
    """Rebind a namespace across loop iterations; each pass adds one."""
    pair = arithmetic_pair(x=value, y=0)
    count = add(x=rounds, y=0)
    while is_positive(value=count):
        pair = arithmetic_pair(x=pair.sum, y=1)
        count = decrement(value=count)
    return pair.sum


@graph
def loop_nullable_namespace(first: Settings, second: Settings, rounds: int) -> int:
    """Carry a namespace with a `None` leaf across loop iterations."""
    count = add(x=rounds, y=0)
    while is_positive(value=count):
        if is_positive.alias('is_positive_2')(value=count):
            first = second
        count = decrement(value=count)
    return first.count
