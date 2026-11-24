###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution contracts for owned containers (`orm.DataList`/`orm.DataDict`) in graphs.

Covers node-typed graph/task inputs and outputs, task chaining, nested
graphs, serialized IR execution, empty containers, and member
identity/provenance. Container storage itself is covered by the ORM suites;
these tests pin the graph integration.
"""

import json
import typing as t

import pytest

from aiida.common.exceptions import GraphValidationError
from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.orm import DataDict, DataList
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.process import ProcessNode
from tests.engine.processes.graphs.programs import containers

pytestmark = pytest.mark.presto


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(containers.list_chain, {'x': 2, 'y': 3}, 5, id='list-chain'),
        pytest.param(containers.dict_chain, {'a': 2, 'b': 3}, 5, id='dict-chain'),
        pytest.param(containers.nested_chain, {'w': 1, 'x': 2, 'y': 3, 'z': 4}, 10, id='nested-chain'),
        pytest.param(containers.empty_length, {}, 0, id='empty-length'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_container_graphs_execute(
    declaration: GraphHandle, inputs: dict[str, t.Any], expected: int, serialized: bool
) -> None:
    """Container-producing chains return exact values, from declarations and serialized IR alike."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    else:
        outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_nested_graph_container_executes(serialized: bool) -> None:
    """An owned list flows through a nested graph boundary by value."""
    original = DataList([Int(1), Int(2)])
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(containers.outer_sum).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, {'values': original}))
    else:
        outputs, node = run_get_node(containers.outer_sum, values=original)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_empty_list_graph_executes(serialized: bool) -> None:
    """A task-produced empty list stores with unset element type."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(containers.empty_list_graph).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, {}))
    else:
        outputs, node = run_get_node(containers.empty_list_graph)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert len(result) == 0
    assert result.element_type is None
    assert result.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_empty_dict_graph_executes(serialized: bool) -> None:
    """A task-produced empty mapping stores with unset element type."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(containers.empty_dict_graph).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, {}))
    else:
        outputs, node = run_get_node(containers.empty_dict_graph)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataDict)
    assert len(result) == 0
    assert result.element_type is None
    assert result.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
def test_empty_list_input_passthrough() -> None:
    """An empty list graph input passes through without gaining an element type."""
    outputs, node = run_get_node(containers.list_passthrough, values=DataList())
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert len(result) == 0
    assert result.element_type is None


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_container_io() -> None:
    """Tasks take and return owned containers as nodes."""
    result, node = containers.pack_list.run_get_node(x=2, y=3)
    assert node.is_finished_ok
    assert isinstance(result, DataList)
    assert [member.value for member in result] == [2, 3]
    total, node = containers.list_sum.run_get_node(values=result)
    assert node.is_finished_ok
    assert total.value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_list_passthrough_preserves_identity() -> None:
    """A passed-through list keeps its identity from graph input to graph output."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(containers.list_passthrough, values=original)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert [member.value for member in result] == [1, 2]
    assert node.inputs['values'].uuid == original.uuid
    assert result.uuid == original.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dict_passthrough_preserves_identity() -> None:
    """A passed-through mapping keeps its identity from graph input to graph output."""
    original = DataDict({'a': Int(1), 'b': Int(2)})
    outputs, node = run_get_node(containers.dict_passthrough, values=original)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataDict)
    assert {key: member.value for key, member in result.items()} == {'a': 1, 'b': 2}
    assert node.inputs['values'].uuid == original.uuid
    assert result.uuid == original.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_passthrough_members_are_owned_copies() -> None:
    """Container members stay owned copies even as the container itself passes through."""
    source = Int(7)
    original = DataList([source])
    outputs, node = run_get_node(containers.list_passthrough, values=original)
    assert node.is_finished_ok
    result = outputs['result']
    assert result[0].uuid != source.uuid
    assert result[0].value == 7
    assert not source.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
def test_list_chain_provenance() -> None:
    """A chained list flows from the packing task into the consuming task unchanged."""
    outputs, node = run_get_node(containers.list_chain, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'pack_list', 'list_sum'}
    packed = calls['pack_list'].outputs.result
    assert isinstance(packed, DataList)
    assert [member.value for member in packed] == [2, 3]
    assert calls['list_sum'].inputs.values.uuid == packed.uuid
    assert outputs['result'].uuid == calls['list_sum'].outputs.result.uuid
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dict_chain_provenance() -> None:
    """A chained mapping flows from the packing task into the consuming task unchanged."""
    outputs, node = run_get_node(containers.dict_chain, a=2, b=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'pack_dict', 'dict_sum'}
    packed = calls['pack_dict'].outputs.result
    assert isinstance(packed, DataDict)
    assert {key: member.value for key, member in packed.items()} == {'a': 2, 'b': 3}
    assert calls['dict_sum'].inputs.values.uuid == packed.uuid
    assert outputs['result'].uuid == calls['dict_sum'].outputs.result.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_graph_container_provenance() -> None:
    """A nested container graph executes as a scope of the root graph returning the existing sum."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(containers.outer_sum, values=original)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    inner = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).get_node_by_label('inner_sum')
    assert inner.inputs.values.uuid == original.uuid
    summed = inner.base.links.get_outgoing(link_type=LinkType.CALL_CALC).get_node_by_label('list_sum')
    assert summed.is_finished_ok
    assert outputs['result'].uuid == summed.outputs.result.uuid
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_container_members() -> None:
    """A nested list stores homogeneous members with values intact."""
    outputs, node = run_get_node(containers.nested_chain, w=1, x=2, y=3, z=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 10
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    packed = calls['pack_nested'].outputs.result
    assert isinstance(packed, DataList)
    assert len(packed) == 2
    assert [[member.value for member in inner] for inner in packed] == [[1, 2], [3, 4]]
    assert calls['nested_sum'].inputs.values.uuid == packed.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_wrong_container_type_rejected() -> None:
    """A mapping where a list is declared fails validation instead of coercing."""
    with pytest.raises(GraphValidationError):
        run_get_node(containers.list_passthrough, values=DataDict({'a': Int(1)}))


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(containers.py_list_chain, {'x': 2, 'y': 3}, 5, id='py-list-chain'),
        pytest.param(containers.typing_list_chain, {'x': 2, 'y': 3}, 5, id='typing-list-chain'),
        pytest.param(containers.py_dict_chain, {'a': 2, 'b': 3}, 5, id='py-dict-chain'),
        pytest.param(containers.typing_dict_chain, {'a': 2, 'b': 3}, 5, id='typing-dict-chain'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_py_container_chains_execute(
    declaration: GraphHandle, inputs: dict[str, t.Any], expected: int, serialized: bool
) -> None:
    """Python ORM containers chain through placements, from declarations and serialized IR alike."""
    assert declaration.build() is None
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    else:
        outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, raw, stored_type, expected',
    [
        pytest.param(containers.py_list_consume, [1, 2], DataList, {'members': [1, 2], 'total': 3}, id='py-list-input'),
        pytest.param(
            containers.py_dict_consume,
            {'a': 1, 'b': 2},
            DataDict,
            {'members': {'a': 1, 'b': 2}, 'total': 3},
            id='py-dict-input',
        ),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_py_container_graph_inputs_execute(
    declaration: GraphHandle, raw: t.Any, stored_type: type, expected: dict[str, t.Any], serialized: bool
) -> None:
    """Python ORM container graph inputs store as owned containers with member values intact."""
    assert declaration.build() is None
    if isinstance(raw, list):
        values: t.Any = [Int(item) for item in raw]
    else:
        values = {key: Int(item) for key, item in raw.items()}
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, {'values': values}))
    else:
        outputs, node = run_get_node(declaration, values=values)
    assert node.is_finished_ok
    assert outputs['result'].value == expected['total']
    stored = node.inputs['values']
    assert isinstance(stored, stored_type)
    assert stored.is_stored
    if isinstance(stored, DataList):
        assert [member.value for member in stored] == expected['members']
        assert all(isinstance(member, Int) for member in stored)
    else:
        assert {key: member.value for key, member in stored.items()} == expected['members']
        assert all(isinstance(member, Int) for member in stored.values())


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, stored_type',
    [
        pytest.param(containers.empty_py_list_graph, DataList, id='empty-py-list'),
        pytest.param(containers.empty_py_dict_graph, DataDict, id='empty-py-dict'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_empty_py_container_graphs_execute(declaration: GraphHandle, stored_type: type, serialized: bool) -> None:
    """Empty Python ORM container outputs store as empty owned containers."""
    assert declaration.build() is None
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, {}))
    else:
        outputs, node = run_get_node(declaration)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, stored_type)
    assert len(result) == 0
    assert result.element_type is None
    assert result.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
def test_py_task_container_io() -> None:
    """Tasks produce and consume Python ORM containers as stored owned containers."""
    packed, node = containers.pack_py_list.run_get_node(x=2, y=3)
    assert node.is_finished_ok
    assert isinstance(packed, DataList)
    assert [member.value for member in packed] == [2, 3]
    assert all(isinstance(member, Int) for member in packed)
    total, node = containers.py_list_sum.run_get_node(values=[Int(2), Int(3)])
    assert node.is_finished_ok
    assert total.value == 5
    assert isinstance(node.inputs['values'], DataList)
    assert [member.value for member in node.inputs['values']] == [2, 3]
    mapping, node = containers.pack_py_dict.run_get_node(a=2, b=3)
    assert node.is_finished_ok
    assert isinstance(mapping, DataDict)
    assert {key: member.value for key, member in mapping.items()} == {'a': 2, 'b': 3}
    total, node = containers.py_dict_sum.run_get_node(values={'a': Int(2), 'b': Int(3)})
    assert node.is_finished_ok
    assert total.value == 5
    assert isinstance(node.inputs['values'], DataDict)
    assert {key: member.value for key, member in node.inputs['values'].items()} == {'a': 2, 'b': 3}
