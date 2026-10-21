###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Parameters declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add


@graph
def variadic_parameters(*values: int) -> int:
    """Declare variadic parameters; dynamic arity is unrepresentable in fixed ports."""
    return add(*values)


# Plain Python takes any count, `total(1, 2, 3)`. Declare fixed arity instead:

# @graph
# def fixed_parameters(x: int, y: int) -> int:
#     return add(x=x, y=y)


@graph
def default_parameter(value: int = 2) -> int:
    """Declare a parameter default, filled when absent."""
    return add(x=value, y=1)


@graph
def keyword_only_parameter(*, value: int) -> int:
    """Declare a keyword-only parameter, treated as ordinary."""
    return add(x=value, y=1)


@graph
def positional_only_parameter(value: int, /) -> int:
    """Declare a positional-only parameter, treated as ordinary."""
    return add(x=value, y=1)
