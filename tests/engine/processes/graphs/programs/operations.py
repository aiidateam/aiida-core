###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph programs exercising inline scalar operations.

Accepted programs thread operation results through task arguments, branch conditions, and loop
state, always materializing root outputs through a real task: primitive inline results are
orchestration state, so only task outputs leave the graph. Rejected programs name the inline
form that must stay a task call instead.
"""

from aiida.engine.processes.graphs.lowering import graph, task
from tests.engine.processes.graphs.programs.tasks import add, arithmetic_pair, generic_add, is_positive


@task
def pick(flag: bool, when_true: int, when_false: int) -> int:
    """Select one of two integers, materializing an inline boolean for the root return."""
    return when_true if flag else when_false


@graph
def scaled_add(value: int) -> int:
    """Scale an input inline and pass it to a task."""
    doubled = value * 2
    return add(x=doubled, y=1)


@graph
def nested_scale(x: int, y: int) -> int:
    """Nest inline operations inside a task argument; each nests as its own placement."""
    return add(x=(x + 1) * 2, y=y)


@graph
def halved_remainder(value: int) -> int:
    """Divide and take the remainder inline, then combine both through a task."""
    halved = value // 2
    remainder = value % 2
    return add(x=halved, y=remainder)


@graph
def unary_pair(value: int) -> int:
    """Negate and reaffirm an input inline, then combine both through a task."""
    negated = -value
    same = +value
    return add(x=negated, y=same)


@graph
def branch_on_compare(value: int) -> int:
    """Branch on an inline comparison, recomputed nowhere: conditions bind once per branch."""
    if value > 0:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=-1)
    return chosen


@graph
def branch_on_negation(value: int, flag: bool) -> int:
    """Branch on an inline negation of a graph input."""
    if not flag:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def compared_equality(x: int, y: int) -> int:
    """Compare for equality inline and materialize the boolean through a task."""
    same = x == y
    different = x != y
    chosen = pick(flag=same, when_true=x, when_false=y)
    return pick(flag=different, when_true=chosen, when_false=x)


@graph
def materialized_flag(value: int, cutoff: int) -> int:
    """Materialize an ordering comparison through a task returning an integer."""
    passed = value >= cutoff
    return pick(flag=passed, when_true=value, when_false=cutoff)


@graph
def task_output_arithmetic(x: int, y: int) -> int:
    """Compute inline over task outputs; calls still lower to tasks, not into operations."""
    total = add(x=x, y=y)
    return add(x=total - 1, y=total + 1)


@graph
def generic_operation(a: int, b: int) -> int:
    """Pass an inline result into a generic task; solving reads the inferred shape once."""
    total = generic_add(a=a + 1, b=b)
    return add(x=total, y=0)


@graph
def field_operand(x: int, y: int) -> int:
    """Compute inline over one field of a namespaced task output."""
    pair = arithmetic_pair(x=x, y=y)
    return add(x=pair.sum + 1, y=pair.product)


@graph
def scaled_inner(value: int) -> int:
    """Scale an input inline for nesting inside another graph."""
    doubled = value * 2
    return add(x=doubled, y=1)


@graph
def nested_operations(value: int) -> int:
    """Compute inline over a nested graph output; operations lower per scope."""
    first = scaled_inner(value=value)
    return add(x=first - 1, y=0)


@graph
def countdown_inline(counter: int) -> int:
    """Count down with an inline comparison, recomputed every iteration."""
    while counter > 0:
        counter = counter - 1
    return add(x=counter, y=0)


@graph
def countdown_augmented(counter: int, active: bool) -> int:
    """Count down with an in-place update and a task-computed condition."""
    while active:
        counter -= 1
        active = is_positive(value=counter)
    return add(x=counter, y=0)


@graph
def root_operation(value: int) -> int:
    """Return an inline result directly; lowering accepts it, the launch boundary rejects it."""
    return value - 1


# rejected at lowering: unpacking needs a multi-output call.
@graph
def unpacked_operation(value: int) -> int:
    """Unpack an inline result; unpack a multi-output call instead."""
    first, second = value + 1
    return add(x=first, y=second)


# rejected at lowering: only the fixed scalar operators run inline.
@graph
def unsupported_division(value: int) -> int:
    """Divide with true division inline; only `//` runs inline."""
    halved = value / 2
    return add(x=halved, y=1)


# rejected at lowering: only the fixed scalar operators run inline.
@graph
def unsupported_power(value: int) -> int:
    """Raise a power inline; compute it in a task instead."""
    squared = value**2
    return add(x=squared, y=1)


# rejected at lowering: booleans are not numbers here.
@graph
def boolean_arithmetic(value: int, flag: bool) -> int:
    """Add a boolean inline; decide with a branch instead."""
    return add(x=value + flag, y=1)


# rejected at lowering: comparisons compare two values at a time.
@graph
def chained_comparison(value: int) -> int:
    """Chain comparisons inline; compare two values per line instead."""
    if 0 < value < 10:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: nested calls hide a placement.
@graph
def nested_call_operand(value: int) -> int:
    """Add a call result inline; put the inner call on its own line first."""
    return add(x=add(x=value, y=1) + 1, y=0)


# rejected at lowering: conditions must be true or false.
@graph
def nonboolean_condition(value: int) -> int:
    """Branch on arithmetic; compare values or call a task returning a boolean instead."""
    if value + 1:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: `not` reads a boolean.
@graph
def negated_number(value: int) -> int:
    """Negate a number logically; compare numbers or branch on a task result instead."""
    ready = not value
    return pick(flag=ready, when_true=value, when_false=0)


# rejected at lowering: inline operations work on numbers.
@graph
def string_concat(label: str, suffix: str) -> int:
    """Concatenate strings inline; build text in a task instead."""
    shouted = label + suffix  # noqa: F841 - lowering rejects the operation before use
    return add(x=1, y=1)


# rejected at lowering: inline operations need declared scalar types.
@graph
def untyped_operand(value) -> int:  # type: ignore[no-untyped-def]
    """Scale an unannotated input; annotate the input instead."""
    doubled = value * 2
    return add(x=doubled, y=1)


# rejected at lowering: equality keeps booleans apart from numbers.
@graph
def mixed_equality(value: int, flag: bool) -> int:
    """Compare a boolean with a number; compare numbers with numbers instead."""
    same = flag == value  # noqa: F841 - lowering rejects the operation before use
    return add(x=1, y=1)


# rejected at lowering: only `+`, `-`, `*`, `//`, `%` update in place.
@graph
def divided_loop(value: int, active: bool) -> int:
    """Halve loop state in place; `/=` has no inline counterpart."""
    total = add(x=value, y=0)
    while active:
        total /= 2
        active = is_positive(value=total)
    return total
