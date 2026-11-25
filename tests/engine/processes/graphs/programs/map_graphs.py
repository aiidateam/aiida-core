###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tasks and graphs for independently verifying ``par_map`` over ``DataList``.

Graphs map multi-step and nested graph callables over owned lists, including
empty, task-produced (computed), serialized, and downstream-consumed inputs.
"""

from aiida.engine import graph, par_map, task
from aiida.orm import DataList
from aiida.orm.nodes.data.int import Int


@task
def increment(x: int) -> int:
    """Add one to the input."""
    return x + 1


@task
def double(x: int) -> int:
    """Double the input."""
    return 2 * x


@task
def pack_three(a: int, b: int, c: int) -> DataList:
    """Pack three integers as an owned list."""
    return DataList([Int(a), Int(b), Int(c)])


@task
def total(values: DataList) -> int:
    """Sum the owned integers."""
    assert isinstance(values, DataList)
    return sum(member.value for member in values)


@graph
def two_step(x: int) -> int:
    """Add one and then double, so mapping exercises a multi-step graph."""
    incremented = increment(x=x)
    return double(x=incremented)


@graph
def map_two_step(values: DataList) -> DataList:
    """Map a two-step graph over an owned list."""
    return par_map(two_step, values)


@graph
def map_single_task(values: DataList) -> DataList:
    """Map a single task over an owned list."""
    return par_map(increment, values)


@graph
def map_empty_input(values: DataList) -> DataList:
    """Map a task over an empty list graph input."""
    return par_map(increment, values)


@graph
def map_computed(a: int, b: int, c: int) -> DataList:
    """Map a task over a task-produced (computed) list."""
    packed = pack_three(a=a, b=b, c=c)
    return par_map(increment, packed)


@graph
def map_chained(values: DataList) -> int:
    """Map over a list and consume the mapped container in a downstream task."""
    mapped = par_map(increment, values)
    return total(values=mapped)


@graph
def inner_map(values: DataList) -> DataList:
    """Map a task over an owned list; itself the callable of an outer map."""
    return par_map(increment, values)


@graph
def map_nested(nested: DataList) -> DataList:
    """Map a graph that itself maps, over a list of lists."""
    return par_map(inner_map, nested)
