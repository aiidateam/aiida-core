###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`WorkChain` tasks shared by the graph behavior suites."""

import typing as t

from aiida.engine import Forward, WorkChain, calcfunction, task
from aiida.engine.processes.graphs.lowering import graph
from aiida.orm import Int
from tests.engine.processes.graphs.programs.tasks import combine_model


@calcfunction
def add(x: Int, y: Int) -> Int:
    """Add two integers; creating nodes belongs in a `calcfunction`, not the `WorkChain` body."""
    return Int(x.value + y.value)


class AddWorkChain(WorkChain):
    """Add two integers through a single outline step."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.output('result', valid_type=Int)
        spec.outline(cls.add_numbers)

    def add_numbers(self):
        """Store the sum of the two inputs."""
        self.out('result', add(self.inputs.x, self.inputs.y))


add_chain = task(AddWorkChain)


class OptionalInputWorkChain(WorkChain):
    """Return `x`; `y` is optional and has no default."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int, required=False)
        spec.output('result', valid_type=Int)
        spec.outline(cls.return_x)

    def return_x(self):
        """Return the required input unchanged."""
        self.out('result', self.inputs.x)


optional_input_chain = task(OptionalInputWorkChain)


@graph
def forward_optional_field(bundle: t.Annotated[t.Any, Forward(optional_input_chain)]) -> int | None:
    """Return an optional forwarded field without a default; an omitted one emits no output."""
    return bundle.y


@calcfunction
def pair_with_bonus(x: Int, y: Int) -> dict[str, Int]:
    """Return the sum and product, plus an extra `bonus` node."""
    return {'sum': Int(x.value + y.value), 'product': Int(x.value * y.value), 'bonus': Int(0)}


class BonusPairWorkChain(WorkChain):
    """Emit the pair outputs and an undeclared `bonus` on dynamic outputs."""

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.outputs.dynamic = True
        spec.outline(cls.emit)

    def emit(self):
        """Return every node of the calculation, declared or not."""
        for label, node in pair_with_bonus(self.inputs.x, self.inputs.y).items():
            self.out(label, node)


bonus_pair_chain = task(BonusPairWorkChain, outputs={'sum': Int, 'product': Int})


@graph
def select_declared(x: Int, y: Int, flag: bool) -> int:
    """Route a dynamic namespace into a branch; only its declared outputs enter the region."""
    pair = bonus_pair_chain(x=x, y=y)
    if flag:
        selected = pair.sum
    else:
        selected = pair.product
    return selected


@graph
def add_single(x: Int, y: Int) -> int:
    """Add two numbers through a single `WorkChain` placement."""
    total = add_chain(x=x, y=y)
    return total.result


@graph
def add_twice(x: Int, y: Int) -> int:
    """Add two numbers through two chained `WorkChain` placements."""
    first = add_chain(x=x, y=y)
    second = add_chain(x=first.result, y=y)
    return second.result


@graph
def forward_declared(x: Int, y: Int) -> int:
    """Wire a dynamic namespace whole; only its declared outputs reach the static input."""
    pair = bonus_pair_chain(x=x, y=y)
    return combine_model(pair=pair)


@graph
def forward_optional_namespace(bundle: t.Annotated[t.Any, Forward(optional_input_chain)]):
    """Return a forwarded namespace; an omitted optional field stays out of it."""
    return bundle
