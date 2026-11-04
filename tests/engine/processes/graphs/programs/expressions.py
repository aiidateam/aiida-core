###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Expressions declarations shared by the graph behavior suites."""

from aiida.engine.processes.graphs.lowering import graph
from tests.engine.processes.graphs.programs.tasks import add


# rejected at lowering: every value needs a producing task.
@graph
def arithmetic_expression(value: int) -> int:
    """Compute an input inline; every value needs a producing task."""
    return add(x=value + 1, y=2)


# rejected at lowering: every value needs a producing task.
@graph
def fstring_argument(value: int) -> int:
    """Format a string inline; every value needs a producing task."""
    return add(x=value, y=f'{value}')


# rejected at lowering: literals must be finite JSON.
@graph
def nonfinite_literal(value: int) -> int:
    """Inline call literals must be finite; compute non-finite values in tasks instead."""
    return add(x=1e999, y=value)
