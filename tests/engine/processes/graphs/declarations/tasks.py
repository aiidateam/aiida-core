###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Task declarations shared by the behavior suites."""

import typing as t

from aiida.engine.processes.graphs.build_source import task
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.declarations.port_models import Configuration

# Task definitions.


@task
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y


@task(outputs=('sum',))
def add_named(x: int, y: int) -> int:
    """Return the integer sum under a named output, for selection wiring."""
    return x + y


@task
def multiply(x: int, y: int) -> int:
    """Multiply two integers."""
    return x * y


@task(outputs=('sum', 'product'))
def arithmetic_pair(x: int, y: int) -> tuple[int, int]:
    """Return sum and product as named outputs."""
    return x + y, x * y


@task
def read_nested_count(config: Configuration) -> int:
    """Read the nested count from a model."""
    return config.settings.count


@task
def read_answer(values: dict[str, int]) -> int:
    """Read one answer from a mapping."""
    return values['answer']


@task
def pass_int(value: int) -> int:
    """Pass an integer through unchanged."""
    return value


@task
def read_orm_node(value: Int) -> int:
    """Unwrap an `Int` node to its value."""
    assert isinstance(value, Int)
    return value.value


@task
def is_positive(value: int) -> bool:
    """Decide whether a value is positive."""
    return value > 0


@task
def decrement(value: int) -> int:
    """Subtract one."""
    return value - 1


@task(outputs=('mean', 'stdev'))
def statistics(values: list[float]) -> tuple[float, float]:
    """Summarize samples; bodies run as plain Python and are never lowered."""
    import math

    total = 0.0
    for sample in values:
        total += sample
    mean = total / len(values)
    variance = sum((sample - mean) ** 2 for sample in values) / len(values)
    return mean, math.sqrt(variance)


@task(outputs=('alpha',))
def mismatched_alpha(value: int) -> int:
    """Return its input under the `alpha` output."""
    return value


@task(outputs=('beta',))
def mismatched_beta(value: int) -> int:
    """Return its input under the `beta` output."""
    return value


@task
def prepare(value: int) -> None:
    """Order downstream placements after this one."""
    return None


@task
def fail_always(x: int) -> int:
    """Raise unconditionally, for failure propagation."""
    raise ValueError('deliberately failed')


@task
def mistyped_output(x: int) -> int:
    """Return a mistyped value, rejected at runtime."""
    return 'wrong'  # rejected at runtime


@task
def mistyped_list(x: int) -> list[int]:
    """Return a mistyped collection, rejected at runtime."""
    return {'value': x}  # rejected at runtime


@task
def mistyped_dict(x: int) -> dict[str, int]:
    """Return a mistyped mapping, rejected at runtime."""
    return [x]  # rejected at runtime


@task
def collision_add(x: int, y: int) -> int:
    """Provide a second addition task for collision coverage."""
    return x + y


# Invalid task definitions.


def unannotated_function(x: int):
    """Reject functions without a return annotation at decoration.

    Static lowering wires placements against declared outputs, so annotate the
    function or wrap it in an annotated one instead of leaving it dynamic.
    """
    return x


def kwargs_function(**kwargs: t.Any) -> int:
    """Reject undecorated functions with kwargs at decoration."""
    return 1
