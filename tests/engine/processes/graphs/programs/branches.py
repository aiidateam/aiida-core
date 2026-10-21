###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Branches declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add, is_positive, mismatched_alpha, mismatched_beta


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
def early_return(value: int, flag: bool) -> int:
    """Return from a branch; graphs declare one output at the end."""
    if flag:
        return add(x=value, y=1)
    return add(x=value, y=2)


# Bind the branch instead:

# @graph
# def branched(value: int, flag: bool) -> int:
#     if flag:
#         chosen = add(x=value, y=1)
#     else:
#         chosen = add(x=value, y=2)
#     return chosen


@graph
def match_statement(value: int) -> int:
    """Match structurally; branch on conditions instead."""
    match value:
        case 0:
            return add(x=value, y=1)
        case _:
            return add(x=value, y=2)


# @graph
# def matched(value: int) -> int:
#     if value:
#         chosen = add(x=value, y=1)
#     else:
#         chosen = add(x=value, y=2)
#     return chosen
