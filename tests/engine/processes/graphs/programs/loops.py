###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Loops declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs import tasks as task_module
from tests.engine.processes.graphs.programs.ports import nullable_return
from tests.engine.processes.graphs.programs.tasks import add, decrement, is_positive


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
        if is_positive(value=total):
            total = decrement(value=total)
        total = decrement(value=total)
    return total


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


# rejected at lowering: loop bodies only record task calls and branches.
@graph
def tuple_targets_in_loop(value: int) -> int:
    """Unpack in a loop; each line wires one placement to a plain name."""
    total = add(x=value, y=1)
    while is_positive(value=total):
        fresh_a, _ = add(x=total, y=1)
        total = add(x=fresh_a, y=1)
    return total


# rejected at lowering: a branch or loop body only sees names defined around it.
@graph
def unknown_after_unpack_in_loop(value: int) -> int:
    """Read an unknown name after unpacking in a loop."""
    total = add(x=value, y=1)
    while is_positive(value=total):
        total, _ = add(x=total, y=1)
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
        step = decrement(value=total)
        rough = is_positive(value=total)
    return total


@graph
def never_entered_optional(rounds: int, value: int | None = None) -> dict[str, int | None]:
    """Carry an optional input through a loop; an unset one stays absent when the loop never runs."""
    count = add(x=rounds, y=0)
    while is_positive(value=count):
        value = nullable_return(value=count)
        count = decrement(value=count)
    return {'direct': value, 'wired': nullable_return(value=value)}
