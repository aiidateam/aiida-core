###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Branching graph declarations rejected at lowering shared by the behavior suites."""

from aiida.engine.processes.graphs.build_source import graph
from tests.engine.processes.graphs.language.tasks import add, mismatched_alpha, mismatched_beta

__all__ = (
    'boolean_condition',
    'compare_condition',
    'inline_conditional',
    'mismatched_branches',
    'walrus_condition',
)


@graph
def mismatched_branches(value: int, condition: bool) -> int:
    """Return different outputs per side, rejected."""
    if condition:
        selected_branch = mismatched_alpha(value=value)
    else:
        selected_branch = mismatched_beta(value=value)
    return selected_branch


@graph
def boolean_condition(value: int, flag: bool) -> int:
    """Combine conditions with operators; conditions are calls or names."""
    if flag and value:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# Compute the predicate in a task instead:

# @task
# def both(value: int, flag: bool) -> bool:
#     return flag and value > 0


@graph
def compare_condition(value: int) -> int:
    """Compare inline; conditions are calls or names."""
    if value > 0:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# Compute the predicate in a task instead:

# @task
# def positive(value: int) -> bool:
#     return value > 0


@graph
def inline_conditional(value: int, flag: bool) -> int:
    """Select inline; branch explicitly instead."""
    return add(x=value, y=1) if flag else add(x=value, y=2)


# @graph
# def explicit_choice(value: int, flag: bool) -> int:
#     if flag:
#         chosen = add(x=value, y=1)
#     else:
#         chosen = add(x=value, y=2)
#     return chosen


@graph
def walrus_condition(value: int, flag: bool) -> int:
    """Bind inside a condition; bind before branching instead."""
    if picked := flag:  # noqa: F841 - the binding itself is rejected
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# @graph
# def bound_before(value: int, flag: bool) -> int:
#     picked = flag
#     if picked:
#         chosen = add(x=value, y=1)
#     else:
#         chosen = add(x=value, y=2)
#     return chosen
