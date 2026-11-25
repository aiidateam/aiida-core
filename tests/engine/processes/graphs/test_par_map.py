###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution contracts for `par_map` fan-out maps over owned containers.

Covers list/dict mapping with order and key preservation, empty and computed
collections, nested graph callables, downstream chaining, serialized IR
execution, provenance (graphs never `CREATE` result containers), failure
propagation, scheduler fan-out, checkpoint restoration, and explicit
rejections of unsupported declarations.
"""

import json
import typing as t

import pytest

from aiida.common.exceptions import GraphLanguageError, GraphTypeCheckError, GraphValidationError
from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node, submit
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.run import GraphRun
from aiida.orm import DataDict, DataList, StructureData
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.process import ProcessNode
from tests.engine.processes.graphs.programs import par_maps

pytestmark = pytest.mark.presto


def _launch(
    declaration: GraphHandle, inputs: dict[str, t.Any], serialized: bool
) -> tuple[dict[str, t.Any], ProcessNode]:
    """Run a graph declaration directly or from its serialized IR."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        return run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    return run_get_node(declaration, **inputs)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_typed_structures_executes(serialized: bool) -> None:
    """Typed DataLists work through mapping, task ports, and serialized graph IR."""
    assert par_maps.map_typed_structures.build() is None
    original = DataList[StructureData](
        [StructureData(cell=[[side, 0, 0], [0, side, 0], [0, 0, side]]) for side in (2.0, 3.0)]
    )
    outputs, node = _launch(par_maps.map_typed_structures, {'structures': original}, serialized)
    assert node.is_finished_ok
    result = outputs['result']
    assert type(result) is DataList
    assert [member.get_cell_volume() for member in result] == pytest.approx([64.0, 216.0])
    assert [member.get_cell_volume() for member in original] == pytest.approx([8.0, 27.0])


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_list_executes(serialized: bool) -> None:
    """A task mapped over a list increments every element in order."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = _launch(par_maps.map_list, {'values': original}, serialized)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert [member.value for member in result] == [2, 3, 4]


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_mapping_executes(serialized: bool) -> None:
    """A task mapped over a mapping increments values while keeping keys and order."""
    original = DataDict({'zeta': Int(1), 'alpha': Int(2), 'mid': Int(3)})
    outputs, node = _launch(par_maps.map_mapping, {'values': original}, serialized)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataDict)
    assert list(result) == ['zeta', 'alpha', 'mid']
    assert {key: member.value for key, member in result.items()} == {'zeta': 2, 'alpha': 3, 'mid': 4}


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration',
    [pytest.param(par_maps.map_empty_list, id='list'), pytest.param(par_maps.map_empty_mapping, id='dict')],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_empty_collection_executes(declaration: GraphHandle, serialized: bool) -> None:
    """Maps over task-produced empty containers store empty containers with unset element type."""
    outputs, node = _launch(declaration, {}, serialized)
    assert node.is_finished_ok
    result = outputs['result']
    assert len(result) == 0
    assert result.element_type is None
    assert result.is_stored


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_empty_input_executes() -> None:
    """A map over an empty list graph input returns an empty stored list."""
    outputs, node = run_get_node(par_maps.map_empty_input, values=DataList())
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert len(result) == 0
    assert result.element_type is None


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_map_nested_graph_executes(serialized: bool) -> None:
    """A nested graph mapped over a list applies per element."""
    original = DataList([Int(1), Int(2)])
    outputs, node = _launch(par_maps.map_nested, {'values': original}, serialized)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [2, 3]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_computed_collection_executes() -> None:
    """A map over a task-produced list consumes that existing container."""
    outputs, node = run_get_node(par_maps.map_computed, a=1, b=2, c=3)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [2, 4, 6]


@pytest.mark.requires_broker
@pytest.mark.parametrize('container', [pytest.param('list', id='list'), pytest.param('dict', id='dict')])
def test_map_runs_on_daemon(submit_and_await, container: t.Literal['list', 'dict']) -> None:
    """A daemon worker dispatches the mapped tasks and collects their outputs."""
    values: DataList | DataDict
    if container == 'list':
        declaration = par_maps.map_list
        values = DataList([Int(1), Int(2)])
    else:
        declaration = par_maps.map_mapping
        values = DataDict({'zeta': Int(1), 'alpha': Int(2)})

    node = submit_and_await(submit(declaration, values=values))
    assert node.is_finished_ok
    result = node.outputs.result
    if container == 'list':
        assert isinstance(result, DataList)
        assert [member.value for member in result] == [2, 3]
    else:
        assert isinstance(result, DataDict)
        assert [(key, member.value) for key, member in result.items()] == [('zeta', 2), ('alpha', 3)]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_downstream_chaining_executes() -> None:
    """A mapped container feeds a downstream task unchanged."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(par_maps.map_chained, values=original)
    assert node.is_finished_ok
    assert outputs['result'].value == 9
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert 'total' in calls
    assert calls['total'].inputs.values.uuid == calls['map_increment_collect'].outputs.result.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_keyword_arguments() -> None:
    """Bind the callable and values by keyword."""
    original = DataList([Int(4)])
    outputs, node = run_get_node(par_maps.map_keyword, values=original)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [5]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_provenance() -> None:
    """The graph never creates the result container; the collector calculation does."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(par_maps.map_list, values=original)
    assert node.is_finished_ok
    result = outputs['result']
    assert isinstance(result, DataList)
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'map_increment_0', 'map_increment_1', 'map_increment_collect'}
    collected = calls['map_increment_collect'].outputs.result
    assert isinstance(collected, DataList)
    assert [member.value for member in collected] == [2, 3]
    assert result.uuid == collected.uuid
    assert calls['map_increment_0'].outputs.result.value == 2
    assert calls['map_increment_1'].outputs.result.value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_mapping_provenance() -> None:
    """The mapping collector creates the result mapping from per-key outputs."""
    original = DataDict({'b': Int(1), 'a': Int(2)})
    outputs, node = run_get_node(par_maps.map_mapping, values=original)
    assert node.is_finished_ok
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'map_increment_0', 'map_increment_1', 'map_increment_collect'}
    collector = calls['map_increment_collect']
    assert {key: member.value for key, member in collector.outputs.result.items()} == {'b': 2, 'a': 3}
    assert {key: member.value for key, member in outputs['result'].items()} == {'b': 2, 'a': 3}
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_nested_graph_provenance() -> None:
    """Mapped nested graphs run as scopes of the root graph under one collector."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(par_maps.map_nested, values=original)
    assert node.is_finished_ok
    items = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(items) == {'map_add_one_0', 'map_add_one_1'}
    collector = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).get_node_by_label('map_add_one_collect')
    for index, (name, item) in enumerate(sorted(items.items())):
        assert name == f'map_add_one_{index}'
        (increment,) = item.called
        assert collector.inputs[f'item_{index}'].uuid == item.outputs.result.uuid == increment.outputs.result.uuid
    assert [member.value for member in outputs['result']] == [2, 3]
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_failure_fails_parent() -> None:
    """A failing item fails the map and the graph without ever collecting."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(par_maps.map_fails, values=original)
    assert not node.is_finished_ok
    assert node.exit_status == 400
    assert outputs == {}
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'map_explode_on_two_0', 'map_explode_on_two_1', 'map_explode_on_two_2'}
    assert not calls['map_explode_on_two_1'].is_finished_ok


@pytest.mark.usefixtures('aiida_profile_clean')
def test_par_map_direct_call_fails() -> None:
    """Calling `par_map` outside a graph body names the authoring fix."""
    from aiida.common.exceptions import GraphLanguageError
    from aiida.engine import par_map

    with pytest.raises(GraphLanguageError, match='inside a `@graph` body'):
        par_map(par_maps.increment, DataList([Int(1)]))


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_wrong_collection_type_rejected() -> None:
    """An integer where a container is declared fails validation instead of iterating."""
    with pytest.raises(GraphValidationError):
        run_get_node(par_maps.map_list, values=Int(1))


@pytest.mark.parametrize(
    'declaration, match',
    [
        pytest.param(par_maps.map_obsolete_after, 'pass the callable and the collection', id='obsolete-after'),
        pytest.param(par_maps.map_two_inputs, 'exactly one input', id='non-unary'),
        pytest.param(par_maps.map_pair_outputs, 'exactly one value', id='multi-output'),
        pytest.param(par_maps.map_no_output, 'exactly one value', id='no-output'),
        pytest.param(par_maps.map_plain_function, 'registered declarations', id='unregistered'),
        pytest.param(par_maps.map_unknown, 'unknown name', id='unknown'),
        pytest.param(par_maps.map_bad_collection, 'annotate the collection', id='bad-collection'),
        pytest.param(par_maps.map_missing_collection, 'with both', id='missing-collection'),
    ],
)
def test_map_invalid_declarations_rejected(declaration: GraphHandle, match: str) -> None:
    """Unsupported maps fail at lowering with an actionable message."""
    with pytest.raises((GraphLanguageError, GraphTypeCheckError), match=match):
        declaration.build()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_scheduler_dispatches_all_items_before_waiting() -> None:
    """One scheduling step fans out to every item before any completion."""
    original = DataList([Int(1), Int(2), Int(3)])
    state = GraphRun(compile_graph(par_maps.map_list), given={'values': original})
    step = state.step()
    assert [start.instance for start in step.starts] == [
        'map_increment_0',
        'map_increment_1',
        'map_increment_2',
    ]
    assert state.instances['map_increment'] == ['map_increment_0', 'map_increment_1', 'map_increment_2']
    assert state.pending == {}
    # No collector runs before every item completes.
    assert 'map_increment_collect' not in state.instances['map_increment']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_avoids_placement_name_collisions() -> None:
    """Items and the collector avoid ordinary placements named like the default labels."""
    original = DataList([Int(1), Int(2)])
    outputs, node = run_get_node(par_maps.map_avoids_placement_names, values=original, x=10)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [2, 3]
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert calls['map_increment_0'].outputs.result.value == 110
    assert calls['map_increment_collect'].outputs.result.value == 1110
    assert set(calls) == {
        'map_increment_0',
        'map_increment_collect',
        'map_increment_0_map',
        'map_increment_1',
        'map_increment_collect_map',
    }
    assert [member.value for member in calls['map_increment_collect_map'].outputs.result] == [2, 3]
    state = GraphRun(compile_graph(par_maps.map_avoids_placement_names), given={'values': original, 'x': 10})
    assert state._collect_instance('map_increment') == 'map_increment_collect_map'
    assert state._item_instance('map_increment', 0) == 'map_increment_0_map'
    assert state._item_instance('map_increment', 1) == 'map_increment_1'
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert restored._collect_instance('map_increment') == 'map_increment_collect_map'
    assert restored._item_instance('map_increment', 0) == 'map_increment_0_map'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_missing_workchain_output_fails_without_collector() -> None:
    """An item omitting its declared `WorkChain` output fails the map without collecting."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(par_maps.map_missing_workchain_output, values=original)
    assert not node.is_finished_ok
    assert node.exit_status == 400
    assert outputs == {}
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(calls) == {
        'map_drop_second_chain_0',
        'map_drop_second_chain_1',
        'map_drop_second_chain_2',
    }
    assert calls['map_drop_second_chain_1'].is_finished_ok
    calc_calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert calc_calls == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_mistyped_workchain_output_fails_without_collector() -> None:
    """An item mistyping its declared `WorkChain` output fails the map without collecting."""
    original = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(par_maps.map_mistyped_workchain_output, values=original)
    assert not node.is_finished_ok
    assert node.exit_status == 400
    assert outputs == {}
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(calls) == {
        'map_mistype_second_chain_0',
        'map_mistype_second_chain_1',
        'map_mistype_second_chain_2',
    }
    calc_calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert calc_calls == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_scheduler_checkpoint_restores_expansion() -> None:
    """Checkpointing between fan-out and completion resumes without redispatching."""
    original = DataList([Int(1), Int(2)])
    state = GraphRun(compile_graph(par_maps.map_list), given={'values': original})
    state.step()
    _, first_node = par_maps.increment.run_get_node(x=1)
    _, second_node = par_maps.increment.run_get_node(x=2)
    state.started('map_increment_0', first_node.pk)
    state.started('map_increment_1', second_node.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert restored.step().starts == []
    restored.completed('map_increment_0', first_node.pk)
    restored.completed('map_increment_1', second_node.pk)
    step = restored.step()
    assert [start.instance for start in step.starts] == ['map_increment_collect']
    assert step.starts[0].inputs['item_0'].value == 2
    assert step.starts[0].inputs['item_1'].value == 3
