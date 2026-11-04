###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`WorkChain` tasks shared by the graph behavior suites."""

from aiida.engine import WorkChain, calcfunction, task
from aiida.engine.processes.graphs.lowering import graph
from aiida.orm import Int


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
