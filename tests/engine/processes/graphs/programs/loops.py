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
from tests.engine.processes.graphs.programs.tasks import add, decrement, is_positive


# NOTE: we could internally represent `for`-loops as `while`
# -> defer for follow-up
@graph
def fanout(values: list[int]) -> int:
    """Loop over inputs, rebinding each round; fan-out over runtime collections is not supported."""
    for value in values:
        result = add(x=value, y=1)
    return result  # rejected at lowering


# Unroll the placements instead:

# @graph
# def unrolled_fanout(value: int) -> int:
#     first = add(x=value, y=1)
#     second = add(x=first, y=1)
#     return add(x=second, y=1)


@graph
def countdown(value: int, condition: bool) -> int:
    """Loop until a task-computed condition clears."""
    while condition:
        value = decrement(value=value)
        condition = is_positive(value=value)
    return value


@graph
def countdown_call(value: int) -> int:
    """Loop on an inline predicate call, re-evaluated every iteration."""
    while is_positive(value=value):
        value = decrement(value=value)
    return value


@graph
def list_comprehension(values: list[int]) -> int:
    """Map over inputs inline; scatter is a runtime control, not syntax.

    Unroll the placements instead.
    """
    doubled = [add(x=value, y=1) for value in values]  # noqa: F841 - the comprehension is rejected
    return add(x=values[0], y=1)


# Loop inside a task instead:
# @task
# def total(values: list[int]) -> int:
#     return sum(values)
#
# @graph
# def summed(values: list[int]) -> int:
#     return total(values=values)
