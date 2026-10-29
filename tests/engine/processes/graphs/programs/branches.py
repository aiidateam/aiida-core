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
from tests.engine.processes.graphs.programs.tasks import add, half, is_positive, mismatched_alpha, mismatched_beta


@graph
def mismatched_type_branches(value: int, flag: bool) -> float:
    """Return different types per side, rejected."""
    if flag:
        chosen = add(x=value, y=1)
    else:
        chosen = half(x=value)
    return chosen


@graph
def mismatched_branches(value: int, condition: bool) -> int:  # rejected at lowering
    """Return different outputs per side, rejected."""
    if condition:
        selected_branch = mismatched_alpha(value=value)
    else:
        selected_branch = mismatched_beta(value=value)
    return selected_branch


@graph
def boolean_condition(value: int, flag: bool) -> int:  # rejected at lowering
    """Combine conditions with operators; conditions are calls or names."""
    if flag and value:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def compare_condition(value: int) -> int:  # rejected at lowering
    """Compare inline; conditions are calls or names."""
    if value > 0:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def inline_conditional(value: int, flag: bool) -> int:  # rejected at lowering
    """Select inline; branch explicitly instead."""
    return add(x=value, y=1) if flag else add(x=value, y=2)


@graph
def walrus_condition(value: int, flag: bool) -> int:  # rejected at lowering
    """Bind inside a condition; bind before branching instead."""
    if picked := flag:  # noqa: F841 - the binding itself is rejected
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


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
def early_return(value: int, flag: bool) -> int:  # rejected at lowering
    """Return from a branch; graphs declare one output at the end."""
    if flag:
        return add(x=value, y=1)
    return add(x=value, y=2)


@graph
def match_statement(value: int) -> int:  # rejected at lowering
    """Match structurally; branch on conditions instead."""
    match value:
        case 0:
            return add(x=value, y=1)
        case _:
            return add(x=value, y=2)
