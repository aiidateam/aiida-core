###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution contracts for straight-line source graphs."""

import json

import pytest

from aiida.common.exceptions import MissingRequiredInputsError
from aiida.common.links import LinkType
from aiida.engine import GraphProcess, GraphSpec, run_get_node
from aiida.engine.processes.graphs.run import GraphRun
from aiida.orm import Dict, GraphNode, Int
from tests.engine.processes.graphs import cases

pytestmark = pytest.mark.presto


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(cases.multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 10}, id='multiply-add'),
        pytest.param(cases.diamond, {'x': 2}, {'result': 7}, id='diamond'),
        pytest.param(cases.named, {'x': 2, 'y': 3}, {'total': 5, 'product': 6}, id='named-outputs'),
        pytest.param(
            cases.selected,
            {'config': {'settings': {'count': 2, 'nullable': None}}},
            {'result': 3},
            id='namespace-field',
        ),
        pytest.param(cases.dictionary_input, {'values': {'answer': 42}}, {'result': 42}, id='dictionary-leaf'),
        pytest.param(cases.ordered, {'x': 2}, {'result': 3}, id='ordering-without-output'),
        pytest.param(cases.chain, {'x': 2, 'y': 3}, {'result': 8}, id='chain'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_supported_graph_syntax_executes(
    declaration, inputs: dict[str, object], expected: dict[str, int], serialized: bool
) -> None:
    """Supported declarations and their JSON representations return exact named values."""
    if serialized:
        spec = GraphSpec.from_dict(json.loads(json.dumps(declaration.build().to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(spec, inputs))
    else:
        outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert {name: value.value for name, value in outputs.items()} == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_orm_typed_inputs_arrive_as_nodes() -> None:
    outputs, node = run_get_node(cases.orm_passthrough, value=Int(4))
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_multiply_add_preserves_named_outputs_and_original_input() -> None:
    """The arithmetic graph retains input identity and returns the addition output."""
    original: Int = Int(2)
    outputs, node = run_get_node(cases.multiply_add, x=original, y=3, z=4)
    assert node.is_finished_ok
    assert set(outputs) == {'result'}
    assert outputs['result'].value == 10
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'multiply', 'add'}
    assert node.inputs.graph_inputs.x.uuid == original.uuid
    assert calls['multiply'].inputs.x.uuid == original.uuid
    assert calls['multiply'].outputs.result.value == 6
    assert calls['add'].inputs.x.uuid == calls['multiply'].outputs.result.uuid
    assert outputs['result'].uuid == calls['add'].outputs.result.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_chain_has_no_created_outputs() -> None:
    """Graphs return existing nodes instead of creating data."""
    outputs, node = run_get_node(cases.chain, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dictionary_leaf_is_a_single_node() -> None:
    """Dictionary leaves store as one node shared by caller and task."""
    outputs, node = run_get_node(cases.dictionary_input, values={'answer': 42})
    assert outputs['result'].value == 42
    linked = node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph_inputs__values')
    assert isinstance(linked, Dict)
    child = node.called[0]
    assert child.inputs.values.uuid == linked.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_missing_inputs_are_aggregated() -> None:
    with pytest.raises(MissingRequiredInputsError) as caught:
        cases.whole.get_launch_inputs(config={'settings': {}})
    assert 'config.settings.nullable' in str(caught.value)
    with pytest.raises(MissingRequiredInputsError):
        cases.chain.get_launch_inputs()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_unexpected_inputs_are_rejected() -> None:
    with pytest.raises(TypeError, match='unexpected keyword argument'):
        cases.chain.get_launch_inputs(x=1, y=2, surprise=3)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_failure_does_not_dispatch_downstream() -> None:
    outputs, node = run_get_node(cases.failed, x=2)
    assert node.exit_status == 400
    assert outputs == {}
    assert len(node.called) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_ordering_is_a_scheduler_dependency() -> None:
    state = GraphRun(cases.ordered.build(), given={'x': Int(2)})
    assert [start.instance for start in state.step().starts] == ['prepare']
    _, completed = cases.prepare.run_get_node(value=2)
    state.started('prepare', completed.pk)
    state.completed('prepare', completed.pk)
    assert [start.instance for start in state.step().starts] == ['add']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_raw_graph_launch_uses_fixed_boundary_contract() -> None:
    outputs, node = run_get_node(
        GraphProcess, graph=Dict(dict=cases.chain.build().to_dict()), graph_inputs={'x': 2, 'y': 3}
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert isinstance(node, GraphNode)
    with pytest.raises(MissingRequiredInputsError):
        GraphProcess(inputs={'graph': Dict(dict=cases.chain.build().to_dict()), 'graph_inputs': {'x': 2}})


@pytest.mark.usefixtures('aiida_profile_clean')
def test_checkpoint_preserves_boundary_node_and_runtime_values() -> None:
    from aiida.engine.processes.persistence import CheckpointPayload

    original = Int(2)
    process = GraphProcess(inputs=cases.chain.get_launch_inputs(x=original, y=3))
    restored = None
    try:
        assert process.inputs.graph_inputs.x == 2
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert restored.inputs.graph_inputs.x == 2
        assert restored.run_state.given['x'].uuid == original.uuid
        assert restored.run_state.to_dict() == process.run_state.to_dict()
        restored.execute()
        assert restored.node.is_finished_ok
        assert restored.outputs['result'].value == 8
    finally:
        if restored is not None:
            restored.close()
        process.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_checkpointed_scheduler_does_not_repeat_completed_tasks() -> None:
    state = GraphRun(cases.chain.build(), given={'x': Int(2), 'y': Int(3)})
    assert [start.instance for start in state.step().starts] == ['add']
    _, completed = cases.add.run_get_node(x=2, y=3)
    state.started('add', completed.pk)
    state.completed('add', completed.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert [start.instance for start in restored.step().starts] == ['add_2']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_run_state_versions_its_checkpoints() -> None:
    """Scheduler checkpoints carry a version; unknown ones fail loudly, old ones load."""
    from aiida.engine.processes.graphs.run import STATE_VERSION

    state = GraphRun(cases.chain.build(), given={'x': Int(2), 'y': Int(3)})
    assert state.to_dict()['version'] == STATE_VERSION
    saved = state.to_dict()
    GraphRun.from_dict(state.graph, state.given, {key: value for key, value in saved.items() if key != 'version'})
    with pytest.raises(ValueError, match='graph run'):
        GraphRun.from_dict(state.graph, state.given, {**saved, 'version': '0.0'})


@pytest.mark.usefixtures('aiida_profile_clean')
def test_tasks_are_cached() -> None:
    from aiida.manage.caching import enable_caching

    with enable_caching(identifier='*'):
        _, first = run_get_node(cases.chain, x=11, y=2)
        outputs, again = run_get_node(cases.chain, x=11, y=2)
    assert first.is_finished_ok and again.is_finished_ok
    assert outputs['result'].value == 15
    assert all(not child.base.caching.is_created_from_cache for child in first.called)
    assert all(child.base.caching.is_created_from_cache for child in again.called)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'function', [pytest.param(cases.wrong_list, id='list'), pytest.param(cases.wrong_dict, id='dict')]
)
def test_parameterized_output_annotation_rejects_other_container(function) -> None:
    with pytest.raises(ValueError, match='not of the right type'):
        run_get_node(function, x=3)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_invalid_output_is_rejected_at_runtime() -> None:
    with pytest.raises(ValueError, match='not of the right type'):
        run_get_node(cases.wrong_output, x=1)
