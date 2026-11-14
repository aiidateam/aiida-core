###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                   #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file       #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`par_map` inside branch arms and loop bodies stays composable.

The mapped callable (positional, `func=` keyword, or attribute-qualified) is a
declaration reference, not a wire read, so region collection must exclude it
while still routing the mapped collection. Covers `@task` as well as `@graph`
callables in branch arms (taken, otherwise, and missing-`else` rebind) and in
loop bodies.
"""

import pytest

from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.orm import DataList
from aiida.orm.nodes.data.int import Int
from tests.engine.processes.graphs.programs import map_regions

pytestmark = pytest.mark.presto


def _values() -> DataList:
    """Return the two-element list mapped throughout the suite."""
    return DataList([Int(1), Int(2)])


def _result_values(outputs: dict) -> list[int]:
    """Return the plain values of a mapped result container."""
    return [member.value for member in outputs['result']]


@pytest.mark.parametrize(
    'declaration',
    [
        map_regions.map_task_in_branch,
        map_regions.map_graph_in_branch,
        map_regions.map_keyword_in_branch,
        map_regions.map_namespaced_in_branch,
        map_regions.map_task_in_missing_else,
        map_regions.map_task_in_loop,
        map_regions.map_graph_in_loop,
        map_regions.map_keyword_namespaced_in_loop,
    ],
)
def test_region_maps_lower(declaration) -> None:
    """Every region map lowers without treating the callable as a wire read."""
    declaration.build()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, flag, expected',
    [
        (map_regions.map_task_in_branch, True, [2, 3]),
        (map_regions.map_task_in_branch, False, [2, 4]),
        (map_regions.map_graph_in_branch, True, [2, 3]),
        (map_regions.map_graph_in_branch, False, [2, 4]),
        (map_regions.map_keyword_in_branch, True, [2, 3]),
        (map_regions.map_keyword_in_branch, False, [2, 4]),
        (map_regions.map_namespaced_in_branch, True, [2, 3]),
        (map_regions.map_namespaced_in_branch, False, [2, 4]),
    ],
)
def test_branch_maps_execute(declaration, flag: bool, expected: list[int]) -> None:
    """Branch arms map the collection for either side."""
    outputs, node = run_get_node(declaration, values=_values(), flag=flag)
    assert node.is_finished_ok
    assert _result_values(outputs) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('flag, expected', [(True, [2, 4]), (False, [2, 3])])
def test_missing_else_map_executes(flag: bool, expected: list[int]) -> None:
    """A missing `else` arm keeps the prior mapped binding when skipped."""
    outputs, node = run_get_node(map_regions.map_task_in_missing_else, values=_values(), flag=flag)
    assert node.is_finished_ok
    assert _result_values(outputs) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, flag, expected',
    [
        (map_regions.map_task_in_loop, False, [2, 3]),
        (map_regions.map_task_in_loop, True, [2, 4]),
        (map_regions.map_graph_in_loop, False, [2, 3]),
        (map_regions.map_graph_in_loop, True, [2, 3]),
        (map_regions.map_keyword_namespaced_in_loop, False, [2, 3]),
        (map_regions.map_keyword_namespaced_in_loop, True, [2, 4]),
    ],
)
def test_loop_maps_execute(declaration, flag: bool, expected: list[int]) -> None:
    """Loop bodies rebind mapped results; a skipped loop keeps the entry binding."""
    outputs, node = run_get_node(declaration, values=_values(), flag=flag, value=1)
    assert node.is_finished_ok
    assert _result_values(outputs) == expected


@pytest.mark.parametrize(
    'declaration',
    [
        map_regions.map_task_in_branch,
        map_regions.map_graph_in_branch,
        map_regions.map_keyword_in_branch,
        map_regions.map_namespaced_in_branch,
    ],
)
def test_branch_regions_route_collection_not_callable(declaration) -> None:
    """Branch regions route the collection while the callable stays a declaration."""
    template = compile_graph(declaration)
    assert sorted(template.inputs) == ['flag', 'values']
    [branch] = list(template.tasks)
    for body in (branch.body, branch.otherwise):
        assert 'values' in body.inputs
        assert 'increment' not in body.inputs
        assert 'double' not in body.inputs
        assert 'add_one' not in body.inputs


def test_loop_regions_route_collection_not_callable() -> None:
    """Loop regions route the collection while the callable stays a declaration."""
    template = compile_graph(map_regions.map_keyword_namespaced_in_loop)
    assert sorted(template.inputs) == ['flag', 'value', 'values']
    loop = next(task for task in template.tasks if type(task).__name__ == 'LoopControl')
    assert 'values' in loop.body.inputs
    assert 'increment' not in loop.body.inputs
    assert 'double' not in loop.body.inputs
    assert 'par_maps' not in loop.body.inputs
