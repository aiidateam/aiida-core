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
from tests.engine.processes.graphs.programs import tasks as task_module
from tests.engine.processes.graphs.programs.tasks import (
    add,
    arithmetic_pair,
    branch_2,
    decrement,
    half,
    is_positive,
    mismatched_alpha,
    mismatched_beta,
)


@graph
def external_choice(value: int, condition: bool) -> int:
    """Branch on an input flag."""
    if condition:
        selected_branch = add(x=value, y=1)
    else:
        selected_branch = add(x=value, y=2)
    return selected_branch


@graph
def namespaced_shadowed(value: int, condition: bool) -> int:
    """Call through a module name shadowed by a wire."""
    task_module = add(x=value, y=1)
    if condition:
        selected_branch = task_module.add(x=value, y=2)
    else:
        selected_branch = add(x=value, y=3)
    return selected_branch


@graph
def namespaced_choice(value: int, condition: bool) -> int:
    """Branch on an input flag, calling through a module namespace."""
    if condition:
        selected_branch = task_module.add(x=value, y=1)
    else:
        selected_branch = task_module.add(x=value, y=2)
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
def reserved_branch_name(value: int, flag: bool) -> int:
    """Call a task named like generated branch placements."""
    first = branch_2(value=value)
    if flag:
        chosen = add(x=first, y=1)
    else:
        chosen = add(x=first, y=2)
    return chosen


@graph
def overwrite_if(value: int, flag: bool) -> int:
    """Overwrite a prior binding only when taken; keep it otherwise."""
    total = add(x=value, y=1)
    if flag:
        total = add(x=total, y=10)
    return total


@graph
def loop_in_branch(value: int, flag: bool) -> int:
    """Run a loop in each arm; both arms rebind loop state."""
    total = add(x=value, y=1)
    if flag:
        while is_positive(value=total):
            total = decrement(value=total)
    else:
        while is_positive(value=total):
            total = add(x=total, y=-2)
    return total


@graph
def loop_in_missing_else(value: int, flag: bool) -> int:
    """Run a loop in the only arm; skip keeps the prior binding."""
    total = add(x=value, y=1)
    if flag:
        while is_positive(value=total):
            total = decrement(value=total)
    return total


@graph
def overwrite_both(value: int, flag: bool) -> int:
    """Overwrite one name on both arms; the taken side wins."""
    total = add(x=value, y=1)
    if flag:
        total = add(x=total, y=10)
    else:
        total = add(x=total, y=100)
    return total


@graph
def alias_both(value: int, flag: bool) -> int:
    """Select between two existing values; no task runs in the arms."""
    first = add(x=value, y=1)
    second = add(x=value, y=2)
    if flag:
        chosen = first
    else:
        chosen = second
    return chosen


@graph
def alias_call(value: int, flag: bool) -> int:
    """Select between a task output and an existing value."""
    first = add(x=value, y=1)
    if flag:
        chosen = add(x=value, y=10)
    else:
        chosen = first
    return chosen


@graph
def alias_input(value: int, other: int, flag: bool) -> int:
    """Select between a task output and a graph input of the same type."""
    if flag:
        chosen = add(x=value, y=1)
    else:
        chosen = other
    return chosen


@graph
def alias_inputs(value: int, other: int, flag: bool) -> int:
    """Alias two inputs of one type; same-type aliases merge."""
    if flag:
        chosen = value
    else:
        chosen = other
    return chosen


@graph
def field_select_arm(value: int, flag: bool) -> int:
    """Bind one field of a namespaced result directly in each arm."""
    pair = arithmetic_pair(x=value, y=3)
    if flag:
        selected = pair.sum
    else:
        selected = pair['product']
    return selected


# rejected at lowering: both sides must agree on types.
@graph
def mismatched_type_branches(value: int, flag: bool) -> float:
    """Return different types per side, rejected."""
    if flag:
        chosen = add(x=value, y=1)
    else:
        chosen = half(x=value)
    return chosen


# rejected at lowering: both sides must return the same output names.
@graph
def mismatched_branches(value: int, condition: bool) -> int:
    """Return different output keys per side, rejected."""
    if condition:
        selected_branch = mismatched_alpha(value=value)
    else:
        selected_branch = mismatched_beta(value=value)
    return selected_branch


# rejected at lowering: conditions are calls or names.
@graph
def boolean_condition(value: int, flag: bool) -> int:
    """Combine conditions with operators; conditions are calls or names."""
    if flag and value:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: conditions are calls or names.
@graph
def compare_condition(value: int) -> int:
    """Compare inline; conditions are calls or names."""
    if value > 0:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: branch explicitly instead.
@graph
def inline_conditional(value: int, flag: bool) -> int:
    """Select inline; branch explicitly instead."""
    return add(x=value, y=1) if flag else add(x=value, y=2)


# rejected at lowering: bind before branching instead.
@graph
def walrus_condition(value: int, flag: bool) -> int:
    """Bind inside a condition; bind before branching instead."""
    if _ := flag:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: graphs declare one output at the end.
@graph
def early_return(value: int, flag: bool) -> int:
    """Return from a branch; graphs declare one output at the end."""
    if flag:
        return add(x=value, y=1)
    return add(x=value, y=2)


# rejected at lowering: branch on conditions instead.
@graph
def match_statement(value: int) -> int:
    """Match structurally; branch on conditions instead."""
    match value:
        case 0:
            return add(x=value, y=1)
        case _:
            return add(x=value, y=2)


# rejected at lowering: a missing else arm needs a prior binding.
@graph
def missing_else_unbound(value: int, flag: bool) -> int:
    """Overwrite without a prior binding; the kept value would not exist."""
    if flag:
        total = add(x=value, y=1)
    return total


# rejected at lowering: a loop arm exposes one wire.
@graph
def loop_arm_two_names(value: int, flag: bool) -> int:
    """Loop arm rebinding two names; arms expose one wire."""
    total = add(x=value, y=1)
    step = decrement(value=total)
    if flag:
        while is_positive(value=total):
            total = decrement(value=total)
            step = decrement(value=step)
    else:
        total = add(x=total, y=0)
    return total


# rejected at lowering: branch outputs have incompatible types.
@graph
def alias_mismatched(value: int, label: str, flag: bool) -> int:
    """Alias values of different types; arms must agree on types."""
    if flag:
        chosen = value
    else:
        chosen = label
    return chosen
