###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Nested, branching, and looping graph declarations shared by the behavior suites."""

from aiida.engine.processes.graphs.build_source import graph
from tests.engine.processes.graphs.declarations.graphs import chain, multiply_add
from tests.engine.processes.graphs.declarations.tasks import (
    add,
    decrement,
    is_positive,
    mismatched_alpha,
    mismatched_beta,
    statistics,
)

# Composition: nesting, branching, and looping.


@graph
def nested(x: int, y: int) -> int:
    """Nest one graph in another."""
    inner = chain(x=x, y=y)
    return add(x=inner, y=x)


@graph
def nested_multiply_add(x: int, y: int, z: int) -> int:
    """Nest the multiply-add graph once."""
    intermediate = multiply_add(x=x, y=y, z=z)
    return add(x=intermediate, y=1)


@graph
def external_choice(value: int, condition: bool) -> int:
    """Branch on an input flag."""
    if condition:
        selected_branch = add(x=value, y=1)
    else:
        selected_branch = add(x=value, y=2)
    return selected_branch


@graph
def computed_choice(value: int) -> int:
    """Branch on a task-computed condition."""
    condition = is_positive(value=value)
    if condition:
        selected_branch = add(x=value, y=1)
    else:
        selected_branch = add(x=value, y=2)
    return selected_branch


@graph
def inline_condition(value: int) -> int:
    """Branch on an inline predicate call, bound like the explicit form."""
    if is_positive(value=value):
        selected_branch = add(x=value, y=1)
    else:
        selected_branch = add(x=value, y=2)
    return selected_branch


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
def summarize(values: list[float]):
    """Expose summary statistics computed by plain Python."""
    stats = statistics(values=values)
    return {'mean': stats.mean, 'stdev': stats.stdev}


@graph
def mismatched_branches(value: int, condition: bool) -> int:
    """Return different outputs per side, rejected."""
    if condition:
        selected_branch = mismatched_alpha(value=value)
    else:
        selected_branch = mismatched_beta(value=value)
    return selected_branch


# NOTE: we could internally represent `for`-loops as `while`
# -> defer for follow-up
@graph
def fanout(values: list[int]) -> int:
    """Loop over inputs, rebinding each round; fan-out over runtime collections is not supported.

    Unroll the placements instead:

    >>> @graph
    >>> def unrolled_fanout(value: int) -> int:
    >>>     first = add(x=value, y=1)
    >>>     second = add(x=first, y=1)
    >>>     return add(x=second, y=1)
    """
    for value in values:
        result = add(x=value, y=1)
    return result  # rejected at lowering
