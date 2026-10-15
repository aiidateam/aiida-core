###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Supported task declarations shared by the behavior suites."""

import typing as t

from aiida.engine.processes.graphs.build_source import task
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.language.port_models import Configuration

__all__ = (
    'Alpha',
    'ArithmeticPair',
    'Beta',
    'SummaryStats',
    'add',
    'arithmetic_pair',
    'collision_add',
    'decrement',
    'fail_always',
    'is_positive',
    'mismatched_alpha',
    'mismatched_beta',
    'mistyped_dict',
    'mistyped_list',
    'mistyped_output',
    'multiply',
    'pass_int',
    'prepare',
    'read_answer',
    'read_nested_count',
    'read_orm_node',
    'statistics',
)


@task
def add(x: int, y: int) -> int:
    """Add two integers."""
    return x + y


@task
def multiply(x: int, y: int) -> int:
    """Multiply two integers."""
    return x * y


class ArithmeticPair(t.TypedDict):
    """Named outputs of the arithmetic pair task."""

    sum: int
    product: int


@task
def arithmetic_pair(x: int, y: int) -> ArithmeticPair:
    """Return sum and product as named outputs."""
    return {'sum': x + y, 'product': x * y}


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


class SummaryStats(t.TypedDict):
    """Named outputs of the statistics task."""

    mean: float
    stdev: float


@task
def statistics(values: list[float]) -> SummaryStats:
    """Summarize samples; bodies run as plain Python and are never lowered."""
    import math

    total = 0.0
    for sample in values:
        total += sample
    mean = total / len(values)
    variance = sum((sample - mean) ** 2 for sample in values) / len(values)
    return {'mean': mean, 'stdev': math.sqrt(variance)}


class Alpha(t.TypedDict):
    """Single named output, mismatched on purpose."""

    alpha: int


class Beta(t.TypedDict):
    """Single named output, mismatched on purpose."""

    beta: int


@task
def mismatched_alpha(value: int) -> Alpha:
    """Return its input under the `alpha` output."""
    return {'alpha': value}


@task
def mismatched_beta(value: int) -> Beta:
    """Return its input under the `beta` output."""
    return {'beta': value}


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
