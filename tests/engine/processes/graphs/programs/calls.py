###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Calls declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add, collision_add, fail_always, multiply, prepare


@graph
def expanded_task_arguments(values: dict[str, int]) -> int:
    """Call with unpacked arguments; mappings cannot expand statically."""
    return add(**values)


# Declare the inputs explicitly instead:

# @graph
# def explicit_arguments(x: int, y: int) -> int:
#     return add(x=x, y=y)


@graph
def recursive_call(value: int) -> int:
    """Call itself; the spec would be infinite."""
    return recursive_call(value=value)


# Factor the step into a task instead:

# @task
# def single_step(value: int) -> int:
#     return value - 1


def plain_add(x: int, y: int) -> int:
    """Add without a task decorator; graphs only call registered tasks."""
    return x + y


@graph
def builtin_call(values: list[int]) -> int:
    """Call a built-in; built-ins cannot run here."""
    count = len(values)
    return add(x=count, y=1)


# Wrap the built-in in a task instead:
# @task
# def count_values(values: list[int]) -> int:
#     return len(values)


@graph
def unknown_call(value: int) -> int:
    """Call an undefined name; check the spelling."""
    return frobnicate(value)  # noqa: F821 - the undefined name is rejected


@graph
def unregistered_call(value: int) -> int:
    """Call an undecorated function; only registered tasks and graphs lower."""
    return plain_add(x=value, y=1)


# Decorate the callee instead:

# @task
# def plain_add(x: int, y: int) -> int:
#     return x + y


@graph
def starred_call(value: int) -> int:
    """Spread a sequence into a call; arity is static."""
    return add(*[value, 1])


# Pass each input by name instead:

# @graph
# def named_spread(value: int) -> int:
#     return add(x=value, y=1)


@graph
def chain(x: int, y: int) -> int:
    """Two whole-result placements."""
    first = add(x=x, y=y)
    return add(x=first, y=y)


@graph
def multiply_add(x: int, y: int, z: int) -> int:
    """Return the arithmetic result for the local multiply-add workflow example."""
    product = multiply(x=x, y=y)
    return add(x=product, y=z)


@graph
def diamond(x: int) -> int:
    """Fan two additions into one."""
    left = add(x=x, y=1)
    right = add(x=x, y=2)
    return add(x=left, y=right)


@graph
def ordered(x: int) -> int:
    """Order a placement with `after`."""
    first = prepare(value=x)
    return add(x=x, y=1, after=first)


@graph
def ordered_named(value: int) -> int:
    """Order on a task; the bare return takes the single output."""
    prepared = prepare(value=value)
    return add(x=value, y=1, after=prepared)


@graph
def multiple_ordered(x: int) -> int:
    """Order on two placements at once."""
    first = prepare(value=x)
    second = prepare(value=x)
    return add(x=x, y=1, after=(first, second))


@graph(identifier='custom-label')
def labelled(x: int) -> int:
    """Carry a custom identifier."""
    return add(x=x, y=1)


@graph
def failed(x: int) -> int:
    """Fail through a broken placement."""
    first = fail_always(x=x)
    return add(x=first, y=1)


@graph
def collision(x: int) -> int:
    """Place three tasks across two callees."""
    first = add(x=x, y=1)
    second = add(x=first, y=1)
    return collision_add(x=second, y=1)


@graph
def missing_task_input(x: int) -> int:
    """Omit a required task input."""
    return add(x=x)


@graph
def positional_task_arguments(value: int) -> int:
    """Call with positional arguments, bound through signature order."""
    return add(value, 1)


@graph
def nested(x: int, y: int) -> int:
    """Nest one graph in another."""
    inner = chain(x=x, y=y)
    return add(x=inner, y=x)


@graph
def nested_multiply_add(x: int, y: int, z: int) -> int:
    """Nest the multiply-add graph once."""
    intermediate = multiply_add(x=x, y=y, z=z)
    return add(x=intermediate, y=1)
