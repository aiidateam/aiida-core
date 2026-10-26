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
from tests.engine.processes.graphs.programs.tasks import add


@graph
def reassigned_name(value: int) -> int:  # rejected at lowering
    """Rebind a name; single-assignment keeps the graph well-defined, not just readable."""
    result = add(x=value, y=1)
    result = add(x=result, y=2)
    return result


@graph
def unbound(value: int) -> int:  # rejected at lowering
    """Reference an unbound name; every name must bind first."""
    return add(x=value, y=missing)  # noqa: F821 - unbound names must fail at lowering


@graph
def subscript_assignment(value: int) -> int:  # rejected at lowering
    """Mutate a placement in place; placements bind new names instead."""
    chosen = add(x=value, y=1)
    chosen['count'] = add(x=chosen, y=2)
    return chosen


@graph
def augmented_assignment(value: int) -> int:  # rejected at lowering
    """Update a name in place; single-assignment keeps the graph well-defined."""
    total = add(x=value, y=1)
    total += 1
    return total


@graph
def annotated_assignment(value: int) -> int:  # rejected at lowering
    """Annotate a local; locals carry no contracts in templates."""
    total: int = add(x=value, y=1)
    return total


@graph
def chained_assignment(value: int) -> int:
    """Assign two names in one statement to one placement."""
    first = second = add(x=value, y=1)
    return add(x=first, y=second)
