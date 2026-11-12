###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Programs returning and wiring structured task outputs."""

from aiida.engine import PortModel
from aiida.engine.processes.graphs.lowering import graph, task
from tests.engine.processes.graphs.programs.tasks import add, arithmetic_pair


class Quotient(PortModel):
    """A structured value with one field."""

    ratio: float


@task
def read_quotient(value: Quotient) -> float:
    """Consume a structured value field by field."""
    return value.ratio


class Inner(PortModel):
    """A nested structured value, stored two levels deep."""

    ratio: float


class Outer(PortModel):
    """A structured value nesting another model."""

    inner: Inner


@task
def make_outer() -> Outer:
    """Build a nested structured value."""
    return Outer(inner=Inner(ratio=0.5))


@task
def read_inner(value: Inner) -> float:
    """Consume a nested namespace selected two levels deep."""
    return value.ratio


@graph
def nested_select() -> float:
    """Wire a two-level namespace select into a structured task input."""
    produced = make_outer()
    return read_inner(value=produced.inner)


@task
def make_quotient(numerator: float, denominator: float) -> Quotient:
    """Build a structured value."""
    return Quotient(ratio=numerator / denominator)


@graph
def quotient_double(numerator: float, denominator: float) -> float:
    """Wire a structured task output field by field into a structured task input."""
    produced = make_quotient(numerator=numerator, denominator=denominator)
    return read_quotient(value={'ratio': produced})


class PairTotal(PortModel):
    """A whole namespace input matching the arithmetic pair outputs."""

    sum: int
    product: int


@task
def combine_total(data: PairTotal) -> int:
    """Consume a whole namespace input."""
    return data.sum + data.product


@graph
def forward_plain(value: int) -> int:
    """Wire a whole task outputs namespace into a whole task input namespace."""
    produced = arithmetic_pair(x=value, y=3)
    return combine_total(data=produced)


@graph
def selected_plain(value: int) -> int:
    """Bind a whole multi-output call, then select fields from it."""
    pair = arithmetic_pair(x=value, y=3)
    return add(x=pair.sum, y=pair.product)
