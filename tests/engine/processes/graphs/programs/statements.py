###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Statements declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add


# rejected at lowering: helpers belong in tasks.
@graph
def nested_definition(value: int) -> int:
    """Define a helper inside the body; helpers belong in tasks."""

    def helper(x: int) -> int:
        return add(x=x, y=1)

    return helper(x=value)


# rejected at lowering: templates hold no runtime resources.
@graph
def with_block(value: int) -> int:
    """Manage a resource in the body; templates hold no runtime resources.

    Move resource handling into a task instead.
    """
    with add(x=value, y=1):
        result = add(x=value, y=2)
    return result


# rejected at lowering: errors are values, not raises.
@graph
def try_block(value: int) -> int:
    """Catch errors in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    try:
        result = add(x=value, y=1)
    except ValueError:
        result = add(x=value, y=2)
    return result


# rejected at lowering: errors are values, not raises.
@graph
def raise_statement(value: int) -> int:
    """Raise in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    raise ValueError('graphs signal errors as values')
    return add(x=value, y=1)


# rejected at lowering: contracts validate at the boundary instead.
@graph
def assert_statement(value: int) -> int:
    """Assert in the body; contracts validate at the boundary instead.

    Declare the contract on the ports instead.
    """
    assert value > 0
    return add(x=value, y=1)
