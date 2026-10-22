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


@graph
def arithmetic_expression(value: int) -> int:  # rejected at lowering
    """Compute an input inline; every value needs a producing task."""
    return add(x=value + 1, y=2)


# Bind the intermediate explicitly:

# @graph
# def bound_expression(value: int) -> int:
#     incremented = add(x=value, y=1)
#     return add(x=incremented, y=2)


@graph
def fstring_argument(value: int) -> int:  # rejected at lowering
    """Format a string inline; every value needs a producing task.

    Format inside a task instead.
    """
    return add(x=value, y=f'{value}')


# Format inside a task instead:
# @task
# def greeting(value: int) -> str:
#     return f'result is {value}'
#
# @graph
# def formatted(value: int) -> str:
#     return greeting(value=value)
