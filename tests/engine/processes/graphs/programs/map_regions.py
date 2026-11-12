###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                   #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`par_map` inside branch arms and loop bodies.

Covers positional and `func=` keyword binding, including attribute-qualified
mapped callables, over `@task` as well as `@graph` callables. Collections stay
wired reads: every region still routes the outer `values` input.
"""

from aiida.engine import graph, par_map
from aiida.orm import DataList
from tests.engine.processes.graphs.programs import par_maps
from tests.engine.processes.graphs.programs.par_maps import add_one, double, increment
from tests.engine.processes.graphs.programs.tasks import decrement, is_positive


@graph
def map_task_in_branch(values: DataList, flag: bool) -> DataList:
    """Map a task in each branch arm, positionally."""
    if flag:
        mapped = par_map(increment, values)
    else:
        mapped = par_map(double, values)
    return mapped


@graph
def map_graph_in_branch(values: DataList, flag: bool) -> DataList:
    """Map a nested graph in one arm and a task in the other."""
    if flag:
        mapped = par_map(add_one, values)
    else:
        mapped = par_map(double, values)
    return mapped


@graph
def map_keyword_in_branch(values: DataList, flag: bool) -> DataList:
    """Map with `func=` keyword binding in each branch arm."""
    if flag:
        mapped = par_map(func=increment, values=values)
    else:
        mapped = par_map(func=double, values=values)
    return mapped


@graph
def map_namespaced_in_branch(values: DataList, flag: bool) -> DataList:
    """Map attribute-qualified tasks in each branch arm."""
    if flag:
        mapped = par_map(par_maps.increment, values)
    else:
        mapped = par_map(par_maps.double, values)
    return mapped


@graph
def map_task_in_missing_else(values: DataList, flag: bool) -> DataList:
    """Rebind a mapped result with no `else` arm; skipping keeps the prior binding."""
    mapped = par_map(increment, values)
    if flag:
        mapped = par_map(double, values)
    return mapped


@graph
def map_task_in_loop(values: DataList, flag: bool, value: int) -> DataList:
    """Rebind a mapped task result inside a loop body."""
    mapped = par_map(increment, values)
    while flag:
        mapped = par_map(double, values)
        value = decrement(value=value)
        flag = is_positive(value=value)
    return mapped


@graph
def map_graph_in_loop(values: DataList, flag: bool, value: int) -> DataList:
    """Rebind a mapped nested graph result inside a loop body."""
    mapped = par_map(add_one, values)
    while flag:
        mapped = par_map(add_one, values)
        value = decrement(value=value)
        flag = is_positive(value=value)
    return mapped


@graph
def map_keyword_namespaced_in_loop(values: DataList, flag: bool, value: int) -> DataList:
    """Rebind attribute-qualified tasks with `func=` binding inside a loop body."""
    mapped = par_map(func=par_maps.increment, values=values)
    while flag:
        mapped = par_map(func=par_maps.double, values=values)
        value = decrement(value=value)
        flag = is_positive(value=value)
    return mapped
