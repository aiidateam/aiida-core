###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graphs binding scalar literals as ephemeral orchestration state.

Accepted programs bind finite numbers, strings, booleans, and `None` to names and thread them
through task arguments, branch arms, and loop state. Every bound literal lowers to a `const`
inline operation: the scheduler holds the plain value, checkpoints it with the scope, and wires
it into tasks, but never stores or links it. Rejected programs name the literal forms that stay
task concerns.
"""

from aiida.engine.processes.graphs.lowering import graph, task
from tests.engine.processes.graphs.programs.tasks import add, decrement, is_positive


@task
def apply_mode(value: int, mode: str) -> int:
    """Double the value in `square` mode, pass it through otherwise."""
    return value * 2 if mode == 'square' else value


@graph
def bound_scalars(value: int) -> int:
    """Bind an integer literal and wire it into a task."""
    attempts = 0
    return add(x=value, y=attempts)


@graph
def aliased_constant(value: int) -> int:
    """Alias a bound literal onto two names; both wire the same value."""
    first = second = 0
    return add(x=first, y=second)


@graph
def bound_flag(value: int) -> int:
    """Branch on a bound boolean literal, selecting the taken arm."""
    forced = True
    if forced:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def const_fallback(value: int, flag: bool) -> int:
    """Join a task arm with a constant arm; the selected side feeds a task."""
    if flag:
        chosen = add(x=value, y=1)
    else:
        chosen = 0
    return add(x=chosen, y=value)


@graph
def bound_mode(value: int, flag: bool) -> int:
    """Wire a bound string through both branch arms into task arguments."""
    mode = 'square'
    if flag:
        chosen = apply_mode(value=value, mode=mode)
    else:
        chosen = apply_mode(value=value, mode=mode)
    return chosen


@graph
def looped_counter(value: int, rounds: int) -> int:
    """Carry a bound counter across loop iterations, stepping it inline."""
    attempts = 0
    count = add(x=rounds, y=0)
    while is_positive(value=count):
        value = add(x=value, y=attempts)
        count = decrement(value=count)
        attempts = attempts + 1
    return add.alias('add_2')(x=value, y=attempts)


@graph
def none_condition(value: int) -> int:
    """Branch on a bound `None`; only booleans select a side, so the run fails loudly."""
    missing = None
    if missing:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def const_source() -> int:
    """Return a bound literal for the caller to consume as orchestration state."""
    step = 2
    return step


@graph
def nested_const(value: int) -> int:
    """Consume a nested graph's constant as orchestration state for a task."""
    step = const_source()
    return add(x=value, y=step)


# rejected at lowering: ephemeral constants never become root scientific outputs.
@graph
def root_constant(value: int) -> int:
    """Return a bound literal directly; constants carry no provenance."""
    result = 1
    return result


# rejected at lowering: inline numbers must be finite JSON.
@graph
def nonfinite_constant(value: int) -> int:
    """Bind a non-finite literal; compute non-finite values in tasks instead."""
    huge = 1e999
    return add(x=value, y=huge)


# rejected at lowering: collections travel whole through declared inputs.
@graph
def list_constant(value: int) -> int:
    """Bind a list literal; provide collections as graph inputs instead."""
    items = [1, 2]
    return add(x=value, y=items)


# rejected at lowering: string formatting is computation, not orchestration state.
@graph
def fstring_constant(value: int) -> str:
    """Bind a formatted string; build this text in a task instead."""
    text = f'{value}'
    return text


# rejected at lowering: both arms expose one wire of the same type.
@graph
def mismatched_const_arm(value: int, flag: bool) -> int:
    """Join a task arm with a constant arm of another type; convert in a task instead."""
    if flag:
        chosen = add(x=value, y=1)
    else:
        chosen = 'zero'
    return add(x=chosen, y=value)
