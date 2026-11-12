###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Independent integration regressions for ``par_map`` mapping ``@graph`` callables over ``orm.DataList``.

Uses real collaborators (no mocks) and covers a multi-step graph mapped over
a list, an empty list, serialized IR execution, a computed (task-produced)
input list, downstream consumption of the mapped container, nested mapped
graphs, and provenance (graphs return the collector-created container instead
of creating result containers themselves).
"""

import json

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.orm import DataList
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.process import ProcessNode
from tests.engine.processes.graphs.programs import map_graphs

pytestmark = pytest.mark.presto


def _launch(declaration: GraphHandle, inputs: dict, serialized: bool) -> tuple[dict, ProcessNode]:
    """Run a graph declaration directly or from its serialized IR."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(declaration.build().to_dict())))
        return run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    return run_get_node(declaration, **inputs)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_multi_step_graph_over_list(serialized: bool) -> None:
    """A two-step graph mapped over a list applies both steps to every element in order."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = _launch(map_graphs.map_two_step, {'values': original}, serialized)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert [member.value for member in result] == [4, 6, 8]
    assert result.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_empty_list() -> None:
    """Mapping over an empty list returns an empty stored list with unset element type."""
    outputs, node = run_get_node(map_graphs.map_empty_input, values=DataList())
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert len(result) == 0
    assert result.element_type is None
    assert result.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_serialized_ir_matches_declaration(serialized: bool) -> None:
    """Serialized IR execution of a mapped graph returns the same values as the declaration."""
    original = DataList([Int(10), Int(20)])
    outputs, node = _launch(map_graphs.map_single_task, {'values': original}, serialized)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [11, 21]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_computed_input_list() -> None:
    """A map over a task-produced list consumes that existing container."""
    outputs, node = run_get_node(map_graphs.map_computed, a=1, b=2, c=3)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [2, 3, 4]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_downstream_consumption() -> None:
    """A downstream task consumes the mapped container with exact values."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(map_graphs.map_chained, values=original)
    assert node.is_finished_ok
    assert outputs['result'].value == 9


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_nested_mapped_graphs(serialized: bool) -> None:
    """A graph that itself maps can be the callable of an outer map over a list of lists."""
    nested = DataList([DataList([Int(1), Int(2)]), DataList([Int(3)])])
    outputs, node = _launch(map_graphs.map_nested, {'nested': nested}, serialized)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert [[member.value for member in inner] for inner in result] == [[2, 3], [4]]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_graph_never_creates_result_container() -> None:
    """The mapped graph returns the collector-created container instead of creating it."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(map_graphs.map_two_step, values=original)
    assert node.is_finished_ok
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert calls['map_two_step_collect'].outputs.result.uuid == outputs['result'].uuid
    work_calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(work_calls) == {'map_two_step_0', 'map_two_step_1'}
    assert all(child.is_finished_ok for child in work_calls.values())
