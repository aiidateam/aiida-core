###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Parameters declarations shared by the graph behavior suites."""

from dataclasses import field

from aiida.engine import PortModel
from aiida.engine.processes.graphs.lowering import graph, task
from tests.engine.processes.graphs.programs.tasks import add


@graph
def variadic_parameters(*values: int) -> int:  # rejected at lowering
    """Declare variadic parameters; dynamic arity is unrepresentable in fixed ports."""
    return add(*values)


@graph
def infinite_default(value: float = 1e999) -> int:  # rejected at lowering
    """Declare a non-finite default; defaults must be finite JSON values."""
    return add(x=1, y=1)


# Plain Python takes any count, `total(1, 2, 3)`. Declare fixed arity instead:

# @graph
# def fixed_parameters(x: int, y: int) -> int:
#     return add(x=x, y=y)


@graph
def default_parameter(value: int = 2) -> int:
    """Declare a parameter default, filled when absent."""
    return add(x=value, y=1)


@graph
def signed_literals() -> int:
    return add(x=-3, y=+1)


@task
def sum_optional(values: list[int] | None) -> int:
    return sum(values) if values is not None else 0


@graph
def optional_collection(values: list[int] | None) -> int:
    return sum_optional(values=values)


class FactorySettings(PortModel):
    values: list[int] = field(default_factory=list)


@task
def count_settings(settings: FactorySettings) -> int:
    return len(settings['values'])


@graph
def factory_defaults(settings: FactorySettings) -> int:
    return count_settings(settings=settings)


@graph
def keyword_only_parameter(*, value: int) -> int:
    """Declare a keyword-only parameter, treated as ordinary."""
    return add(x=value, y=1)


@graph
def keyword_only_after_default(count: int = 1, *, value: int) -> int:
    """Declare a default before a keyword-only parameter; launching binds by name."""
    return add(x=count, y=value)


@graph
def positional_only_parameter(value: int, /) -> int:
    """Declare a positional-only parameter, treated as ordinary."""
    return add(x=value, y=1)
