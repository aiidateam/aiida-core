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


@graph
def nested_definition(value: int) -> int:  # rejected at lowering
    """Define a helper inside the body; helpers belong in tasks."""

    def helper(x: int) -> int:
        return add(x=x, y=1)

    return helper(x=value)


# Move the helper into a task instead:

# @task
# def helper(x: int) -> int:
#     return add(x=x, y=1)


@graph
def with_block(value: int) -> int:  # rejected at lowering
    """Manage a resource in the body; templates hold no runtime resources.

    Move resource handling into a task instead.
    """
    with add(x=value, y=1):
        result = add(x=value, y=2)
    return result


# Move the block into a task instead:
# @task
# def resourced(value: int) -> int:
#     with acquire(value) as handle:
#         return use(handle)


@graph
def try_block(value: int) -> int:  # rejected at lowering
    """Catch errors in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    try:
        result = add(x=value, y=1)
    except ValueError:
        result = add(x=value, y=2)
    return result


# Declare fallible results instead:
# @task
# def fallible(value: int) -> Result[int, TaskErrors]: ...
#
# @graph
# def guarded(value: int) -> int:
#     outcome = fallible(value=value)
#     if outcome.error is None:
#         return outcome.result
#     return 0


@graph
def raise_statement(value: int) -> int:  # rejected at lowering
    """Raise in the body; errors are values, not raises.

    Declare fallible results instead.
    """
    raise ValueError('graphs signal errors as values')
    return add(x=value, y=1)


# Return declared errors instead of raising:
# @task
# def fallible(value: int) -> Result[int, TaskErrors]: ...
#
# @graph
# def guarded(value: int) -> int:
#     outcome = fallible(value=value)
#     if outcome.error is None:
#         return outcome.result
#     return 0


@graph
def assert_statement(value: int) -> int:  # rejected at lowering
    """Assert in the body; contracts validate at the boundary instead.

    Declare the contract on the ports instead.
    """
    assert value > 0
    return add(x=value, y=1)


# Check values where they execute, inside task bodies:
# @task
# def checked(value: int) -> int:
#     if value <= 0:
#         raise ValueError('expected a positive value')
#     return add(x=value, y=1)
