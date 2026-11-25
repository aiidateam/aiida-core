###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Conditional expressions selecting one value lazily at runtime.

Each `x if condition else y` lowers to a branch holding both arms, so only the taken arm ever
runs. Arms cover calls, scalar constants, references, and inline expressions; rejected programs
name the arm and condition forms that stay task or branch concerns.
"""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add, decrement, is_positive


@graph
def choose_value(value: int, flag: bool) -> int:
    """Select between two task calls; only the taken call runs."""
    chosen = add(x=value, y=1) if flag else add(x=value, y=2)
    return chosen


@graph
def const_arms(value: int, flag: bool) -> int:
    """Select between two scalar constants feeding one task."""
    chosen = 1 if flag else 2
    return add(x=value, y=chosen)


@graph
def ref_arms(value: int, other: int, flag: bool) -> int:
    """Select between two existing wires without running any task in the arms."""
    chosen = value if flag else other
    return add(x=chosen, y=1)


@graph
def expr_arms(value: int, flag: bool) -> int:
    """Select between two inline expressions computed in the taken arm."""
    chosen = (value + 1) if flag else (value - 1)
    return add(x=chosen, y=0)


@graph
def arg_conditional(value: int, flag: bool) -> int:
    """Select one task argument inline; the arm decision feeds the call."""
    return add(x=value if flag else 0, y=1)


@graph
def nested_conditional(value: int, flag: bool, flip: bool) -> int:
    """Nest one selection inside another; each level selects its own side."""
    chosen = (add(x=value, y=1) if flip else add(x=value, y=2)) if flag else add(x=value, y=3)
    return chosen


@graph
def boolop_conditional(value: int, flag: bool, other: bool) -> int:
    """Guard one selection with a joined boolean; both features compose."""
    chosen = add(x=value, y=1) if flag and other else add(x=value, y=2)
    return chosen


@graph
def loop_conditional(value: int, flag: bool) -> int:
    """Re-evaluate one task-checked selection before every iteration."""
    total = add(x=value, y=0)
    while is_positive(value=total) if flag else False:
        total = decrement(value=total)
    return total


# rejected at lowering: both arms expose one wire of the same type.
@graph
def mismatched_arms(value: int, flag: bool) -> int:
    """Select between an integer call and a float constant; convert in a task instead."""
    chosen = add(x=value, y=1) if flag else 0.5
    return add(x=chosen, y=value)


# rejected at lowering: every value needs a producing task or an enclosing binding.
@graph
def unbound_arm(value: int, flag: bool) -> int:
    """Select an unbound name in one arm; bind every name before selecting it."""
    chosen = missing if flag else add(x=value, y=2)  # noqa: F821 - the unbound name is rejected
    return chosen


# rejected at lowering: loop tests decide between two sides, so they must be true or false.
@graph
def loop_nonbool(value: int, flag: bool) -> int:
    """Select integers as a loop test; test booleans instead."""
    total = add(x=value, y=0)
    while add(x=value, y=1) if flag else 0:
        total = decrement(value=total)
    return total
