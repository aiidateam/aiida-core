###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Task declarations shared by the behavior suites."""

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
    'kwargs_function',
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
    'unannotated_function',
)

from tests.engine.processes.graphs.declarations.tasks.rejected import (
    kwargs_function,
    unannotated_function,
)
from tests.engine.processes.graphs.declarations.tasks.supported import (
    Alpha,
    ArithmeticPair,
    Beta,
    SummaryStats,
    add,
    arithmetic_pair,
    collision_add,
    decrement,
    fail_always,
    is_positive,
    mismatched_alpha,
    mismatched_beta,
    mistyped_dict,
    mistyped_list,
    mistyped_output,
    multiply,
    pass_int,
    prepare,
    read_answer,
    read_nested_count,
    read_orm_node,
    statistics,
)
