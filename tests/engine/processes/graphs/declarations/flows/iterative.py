###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Looping graph declarations shared by the behavior suites."""

from aiida.engine.processes.graphs.build_source import graph
from tests.engine.processes.graphs.declarations.tasks import add, decrement, is_positive

__all__ = (
    'countdown',
    'countdown_call',
    'fanout',
)


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
