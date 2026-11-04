###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Assignments declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add, arithmetic_pair, subtract


@graph
def tuple_assignment(x: int, y: int) -> int:
    """Bind two names at once from multiple outputs, order-sensitively."""
    total, product = arithmetic_pair(x=x, y=y)
    return subtract(x=product, y=total)


@graph
def chained_assignment(value: int) -> int:
    """Assign two names in one statement to one placement."""
    first = second = add(x=value, y=1)
    return add(x=first, y=second)


# rejected at lowering: each name binds one placement.
@graph
def reassigned_name(value: int) -> int:
    """Rebind a name; single-assignment keeps the graph well-defined, not just readable."""
    result = add(x=value, y=1)
    result = add(x=result, y=2)
    return result


# rejected at lowering: every name must bind before use.
@graph
def unbound(value: int) -> int:
    """Reference an unbound name; every name must bind first."""
    return add(x=value, y=missing)  # noqa: F821 - unbound names must fail at lowering


# rejected at lowering: placements bind new names instead of mutating.
@graph
def attribute_assignment(value: int) -> int:
    """Mutate a placement in place; placements bind new names instead."""
    chosen = add(x=value, y=1)
    chosen.count = add(x=chosen, y=2)
    return chosen


# rejected at lowering: each name binds one placement.
@graph
def augmented_assignment(value: int) -> int:
    """Update a name in place; single-assignment keeps the graph well-defined."""
    total = add(x=value, y=1)
    total += 1
    return total


# rejected at lowering: locals carry no contracts.
@graph
def annotated_assignment(value: int) -> int:
    """Annotate a local; locals carry no contracts in templates."""
    total: int = add(x=value, y=1)
    return total


# rejected at lowering: graph inputs are recorded once at launch and cannot be reassigned.
@graph
def input_reassignment(value: int) -> int:
    """Rebind a graph input; inputs are fixed at launch."""
    value = add(x=value, y=1)
    return value
