###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Looping graph declarations that lower shared by the behavior suites."""

from aiida.engine.processes.graphs.build_source import graph
from tests.engine.processes.graphs.language.tasks import decrement, is_positive

__all__ = (
    'countdown',
    'countdown_call',
    'countdown_compare',
)


@graph
def countdown(value: int, condition: bool) -> int:
    """Loop until a task-computed condition clears."""
    while condition:
        value = decrement(value=value)
        condition = is_positive(value=value)
    return value


@graph
def countdown_call(value: int) -> int:
    """Loop on an inline predicate call, re-evaluated every iteration."""
    while is_positive(value=value):
        value = decrement(value=value)
    return value


@graph
def countdown_compare(value: int) -> int:
    """Loop while the counter stays positive, compared inline."""
    while value > 0:
        value = decrement(value=value)
    return value
