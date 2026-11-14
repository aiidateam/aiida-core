###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graphs combining booleans with short-circuit `and` and `or`.

Accepted programs join boolean calls, comparisons, names, and constants; each pair lowers to a
branch that evaluates the right side only when the left side selects it. Rejected programs name
the operand forms that stay task concerns.
"""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.results import Err, Ok, Result
from tests.engine.processes.graphs.programs.operations import pick
from tests.engine.processes.graphs.programs.tasks import add, is_positive


class ParityErrors(ExitCodeEnum):
    """Declared failures of the parity check."""

    ODD = ExitCode(410, 'Odd value.')


@task
def check_even(value: int) -> Result[int, ParityErrors]:
    """Return the value when even, or the declared odd failure."""
    if value % 2:
        return Err(ParityErrors.ODD)
    return Ok(value)


@task
def step_down(value: int) -> int:
    """Count one step down."""
    return value - 1


@graph
def guarded_divisor(value: int, divisor: int) -> int:
    """Skip a zero divisor before dividing; the guarded side never runs when skipped."""
    if divisor != 0 and value % divisor == 0:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def lazy_rhs(value: int, flag: bool) -> int:
    """Evaluate the right-hand task only when the left-hand flag selects it."""
    if flag and is_positive(value=value):
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def lazy_or(value: int, flag: bool) -> int:
    """Skip the right-hand task when the left-hand flag already selects the side."""
    if flag or is_positive(value=value):
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def chained_guards(value: int, flag: bool, other: bool) -> int:
    """Fold three operands left to right, skipping every unselected task."""
    if flag and other and is_positive(value=value):
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def mixed_guards(value: int, flag: bool, other: bool) -> int:
    """Mix `and` inside `or`; each pair still skips its unselected side."""
    if (flag and other) or is_positive(value=value):
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def negated_guard(value: int, flag: bool) -> int:
    """Negate one combination; `not` reads the joined boolean like any other."""
    if not (flag and is_positive(value=value)):
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


@graph
def picked_guard(value: int, flag: bool) -> int:
    """Pass one combination as a task argument; the joined boolean wires like a name."""
    return pick(flag=flag and is_positive(value=value), when_true=value, when_false=0)


@graph
def bounded_count(value: int, target: int, max_steps: int) -> int:
    """Step toward a target until it matches or the attempt budget runs out."""
    attempts = 0
    while value != target and attempts < max_steps:
        value = value - 1
        attempts = attempts + 1
    return add(x=value, y=attempts)


@graph
def none_guarded(value: int | None, flag: bool) -> int:
    """Guard on presence before the flag; the presence test stays a branch test."""
    if value is not None and flag:
        chosen = add(x=1, y=1)
    else:
        chosen = add(x=1, y=2)
    return chosen


@graph
def guarded_task_loop(value: int, flag: bool) -> int:
    """Step with a task while the flag holds and the total stays positive."""
    total = add(x=value, y=0)
    while flag and is_positive(value=total):
        total = step_down(value=total)
        flag = is_positive(value=total)
    return total


@graph
def member_guarded(value: int, fallback: int) -> int:
    """Guard on a declared error member before the bound; the member test stays a branch test."""
    _, error = check_even(value=value)
    if error is ParityErrors.ODD and fallback > 0:
        chosen = add(x=fallback, y=1)
    else:
        chosen = add(x=fallback, y=0)
    return chosen


# rejected at lowering: boolean operators combine true/false values only.
@graph
def int_operands(value: int, flag: bool) -> int:
    """Combine an integer with a flag; operands must read as booleans."""
    if value and flag:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: Python operand tricks have no graph values.
@graph
def literal_operands(value: int) -> int:
    """Combine integer literals; `1 and 2` returns `2` in Python but means nothing here."""
    if 1 and 2:
        chosen = add(x=value, y=1)
    else:
        chosen = add(x=value, y=2)
    return chosen


# rejected at lowering: presence tests select a side instead of computing a value.
@graph
def presence_value(value: int) -> int:
    """Bind a presence test as a value; test presence in an `if` or `while` test instead."""
    flag = value is None  # noqa: F841 - the rejected binding never lowers
    return add(x=value, y=1)


# rejected at lowering: the right side of `and` must be a boolean value.
@graph
def presence_rhs(value: int | None, flag: bool) -> int:
    """Test presence on the right side; presence on the left stays a branch test instead."""
    if flag and value is None:
        chosen = add(x=1, y=1)
    else:
        chosen = add(x=1, y=2)
    return chosen
