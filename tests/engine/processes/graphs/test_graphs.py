###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Execution contracts for source graphs."""

import json
import typing as t

import pytest

from aiida.common.exceptions import GraphError, GraphTypeCheckError, GraphValidationError, MissingRequiredInputsError
from aiida.common.links import LinkType
from aiida.engine import task
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.run import GraphRun
from aiida.engine.processes.graphs.tasks import FunctionTaskHandle
from aiida.orm.nodes.data.bool import Bool
from aiida.orm.nodes.data.dict import Dict
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.nodes.process.workflow.graph import GraphNode
from tests.engine.processes.graphs.programs import assignments, branches, parameters, ports, tasks
from tests.engine.processes.graphs.programs import calls as call_programs

pytestmark = pytest.mark.presto


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(call_programs.multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 10}, id='multiply-add'),
        pytest.param(call_programs.nested_multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 11}, id='nested-graph'),
        pytest.param(call_programs.diamond, {'x': 2}, {'result': 7}, id='diamond'),
        pytest.param(ports.direct_result, {'value': 2}, {'result': 12}, id='direct-result'),
        pytest.param(ports.named, {'x': 2, 'y': 3}, {'total': 5, 'product': 6}, id='named-outputs'),
        pytest.param(
            ports.selected,
            {'config': {'settings': {'count': 2, 'nullable': None}}},
            {'result': 3},
            id='namespace-field',
        ),
        pytest.param(ports.selected_field, {'settings': {}}, {'result': 3}, id='namespace-field-default'),
        pytest.param(ports.literal_dictionary, {}, {'result': 42}, id='dictionary-literal'),
        pytest.param(ports.dictionary_input, {'values': {'answer': 42}}, {'result': 42}, id='dictionary-leaf'),
        pytest.param(call_programs.ordered, {'x': 2}, {'result': 3}, id='ordering-without-output'),
        pytest.param(call_programs.ordered_named, {'value': 2}, {'result': 3}, id='ordering-named'),
        pytest.param(call_programs.multiple_ordered, {'x': 2}, {'result': 3}, id='ordering-on-two'),
        pytest.param(call_programs.chain, {'x': 2, 'y': 3}, {'result': 8}, id='chain'),
        pytest.param(branches.external_choice, {'value': 2, 'condition': True}, {'result': 3}, id='external-true'),
        pytest.param(branches.external_choice, {'value': 2, 'condition': False}, {'result': 4}, id='external-false'),
        pytest.param(branches.computed_choice, {'value': 2}, {'result': 3}, id='computed-true'),
        pytest.param(branches.computed_choice, {'value': -2}, {'result': 0}, id='computed-false'),
        pytest.param(branches.inline_condition, {'value': 2}, {'result': 3}, id='inline-true'),
        pytest.param(branches.inline_condition, {'value': -2}, {'result': 0}, id='inline-false'),
        pytest.param(call_programs.positional_task_arguments, {'value': 2}, {'result': 3}, id='positional-arguments'),
        pytest.param(assignments.tuple_assignment, {'x': 2, 'y': 3}, {'result': 1}, id='tuple-unpacking'),
        pytest.param(assignments.chained_assignment, {'value': 2}, {'result': 6}, id='chained-assignment'),
        pytest.param(parameters.signed_literals, {}, {'result': -2}, id='signed-literals'),
        pytest.param(parameters.optional_collection, {'values': [1, 2]}, {'result': 3}, id='optional-list'),
        pytest.param(parameters.optional_collection, {'values': None}, {'result': 0}, id='optional-none'),
        pytest.param(parameters.factory_defaults, {'settings': {}}, {'result': 0}, id='factory-defaults'),
        pytest.param(parameters.default_parameter, {}, {'result': 3}, id='parameter-default-filled'),
        pytest.param(parameters.default_parameter, {'value': 5}, {'result': 6}, id='parameter-default-overridden'),
        pytest.param(parameters.keyword_only_parameter, {'value': 2}, {'result': 3}, id='keyword-only'),
        pytest.param(
            parameters.keyword_only_after_default, {'value': 2}, {'result': 3}, id='keyword-only-default-filled'
        ),
        pytest.param(
            parameters.keyword_only_after_default,
            {'count': 5, 'value': 2},
            {'result': 7},
            id='keyword-only-default-overridden',
        ),
        pytest.param(
            ports.summarize,
            {'values': [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]},
            {'mean': 5.0, 'stdev': 2.0},
            id='plain-python-body',
        ),
        pytest.param(parameters.positional_only_parameter, {'value': 2}, {'result': 3}, id='positional-only'),
        pytest.param(ports.input_passthrough, {'value': 4}, {'value': 4}, id='input-passthrough'),
        pytest.param(ports.single_named_scalar, {'value': 2}, {'only': 2}, id='single-named-scalar'),
        pytest.param(ports.single_named_mapping, {'value': 2}, {'only': 2}, id='single-named-mapping'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_supported_graph_syntax_executes(
    declaration: GraphHandle, inputs: dict[str, t.Any], expected: dict[str, int], serialized: bool
) -> None:
    """Supported declarations and their JSON representations return exact named values."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(declaration.build().to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    else:
        outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert {name: value.value for name, value in outputs.items()} == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_orm_typed_inputs_arrive_as_nodes() -> None:
    outputs, node = run_get_node(ports.orm_passthrough, value=Int(4))
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_on_wait_registers_each_pending_task_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Repeated wake-ups register one finish callback per pending task."""
    process = GraphProcess(inputs=call_programs.chain.get_launch_inputs(x=Int(2), y=3))
    name = call_programs.chain.build().task_names[0]
    process._run_state.started(name, 123)
    calls: list[int] = []
    monkeypatch.setattr(process.runner, 'call_on_process_finish', lambda pk, _callback: calls.append(pk))
    process._watch_pending()
    process._watch_pending()
    assert calls == [123]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_condition_accepts_bool_nodes() -> None:
    """Branch conditions read `Bool` nodes by value like plain booleans."""
    outputs, node = run_get_node(branches.external_choice, value=2, condition=Bool(True))
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    outputs, node = run_get_node(branches.external_choice, value=2, condition=Bool(False))
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_condition_rejects_non_bool() -> None:
    """A branch condition of any other type fails loudly instead of coercing."""
    state = GraphRun(branches.external_choice.build(), given={'value': 2, 'condition': Int(1)})
    with pytest.raises(GraphTypeCheckError, match='must be a `bool` or `Bool`'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_can_run_without_retrievable_source(monkeypatch: pytest.MonkeyPatch) -> None:
    namespace = {'__name__': tasks.__name__}
    exec(compile('def generated(value: int) -> int:\n    return value + 1\n', '<generated-task>', 'exec'), namespace)
    declaration = task(namespace['generated'])
    monkeypatch.setattr(tasks, 'generated', declaration, raising=False)
    result, node = run_get_node(declaration, value=3)
    assert node.is_finished_ok
    assert result.value == 4


def test_task_after_kwarg_rejected_outside_graphs() -> None:
    """`after` orders graph placements; direct task calls reject it."""
    with pytest.raises(GraphError, match='orders placements'):
        tasks.add(x=1, y=1, after='x')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_graph_has_child_workflow_provenance() -> None:
    """A nested declaration executes as a child graph with its own task call_programs."""
    outputs, node = run_get_node(call_programs.nested_multiply_add, x=2, y=3, z=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 11
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(calls) == {'multiply_add'}
    child = calls['multiply_add']
    assert isinstance(child, GraphNode)
    assert child.is_finished_ok
    assert child.outputs.result.value == 10
    children: dict[str, ProcessNode] = child.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(children) == {'multiply', 'add'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_multiply_add_preserves_named_outputs_and_original_input() -> None:
    """The arithmetic graph retains input identity and returns the addition output."""
    original: Int = Int(2)
    outputs, node = run_get_node(call_programs.multiply_add, x=original, y=3, z=4)
    assert node.is_finished_ok
    assert set(outputs) == {'result'}
    assert outputs['result'].value == 10
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'multiply', 'add'}
    assert node.inputs.graph_inputs.x.uuid == original.uuid
    assert calls['multiply'].inputs.x.uuid == original.uuid
    assert calls['multiply'].outputs.result.value == 6
    assert calls['add'].inputs.x.uuid == calls['multiply'].outputs.result.uuid
    assert outputs['result'].uuid == calls['add'].outputs.result.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_chain_has_no_created_outputs() -> None:
    """Graphs return existing nodes instead of creating data."""
    outputs, node = run_get_node(call_programs.chain, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_dictionary_leaf_is_a_single_node() -> None:
    """Dictionary leaves store as one node shared by caller and task."""
    outputs, node = run_get_node(ports.dictionary_input, values={'answer': 42})
    assert outputs['result'].value == 42
    linked = node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph_inputs__values')
    assert isinstance(linked, Dict)
    child = node.called[0]
    assert child.inputs.values.uuid == linked.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_missing_inputs_are_aggregated() -> None:
    with pytest.raises(MissingRequiredInputsError) as caught:
        ports.whole.get_launch_inputs(config={'settings': {}})
    assert 'config.settings.nullable' in str(caught.value)
    with pytest.raises(MissingRequiredInputsError, match='missing required graph inputs'):
        call_programs.chain.get_launch_inputs()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_unexpected_inputs_are_rejected() -> None:
    with pytest.raises(TypeError, match='unexpected keyword argument'):
        call_programs.chain.get_launch_inputs(x=1, y=2, surprise=3)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_failure_does_not_dispatch_downstream() -> None:
    outputs, node = run_get_node(call_programs.failed, x=2)
    assert node.exit_status == 400
    assert outputs == {}
    assert len(node.called) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_ordering_is_a_scheduler_dependency() -> None:
    state = GraphRun(call_programs.ordered.build(), given={'x': Int(2)})
    assert [start.instance for start in state.step().starts] == ['prepare']
    _, completed = tasks.prepare.run_get_node(value=2)
    assert completed.pk is not None
    state.started('prepare', completed.pk)
    state.completed('prepare', completed.pk)
    assert [start.instance for start in state.step().starts] == ['add']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_raw_graph_launch_uses_fixed_boundary_contract() -> None:
    outputs, node = run_get_node(
        GraphProcess, graph=Dict(dict=call_programs.chain.build().to_dict()), graph_inputs={'x': 2, 'y': 3}
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert isinstance(node, GraphNode)
    with pytest.raises(MissingRequiredInputsError, match='missing required graph inputs'):
        GraphProcess(inputs={'graph': Dict(dict=call_programs.chain.build().to_dict()), 'graph_inputs': {'x': 2}})


@pytest.mark.usefixtures('aiida_profile_clean')
def test_checkpoint_preserves_boundary_node_and_runtime_values() -> None:
    from aiida.engine.processes.persistence import CheckpointPayload

    original = Int(2)
    process = GraphProcess(inputs=call_programs.chain.get_launch_inputs(x=original, y=3))
    restored = None
    try:
        assert process.inputs.graph_inputs.x == 2
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        restored = checkpoint.decode()
        assert isinstance(restored, GraphProcess)
        assert restored.inputs.graph_inputs.x == 2
        assert restored._run_state.given['x'].uuid == original.uuid
        assert restored._run_state.to_dict() == process._run_state.to_dict()
        restored.execute()
        assert restored.node.is_finished_ok
        assert restored.outputs['result'].value == 8
    finally:
        if restored is not None:
            restored.close()
        process.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_checkpointed_scheduler_does_not_repeat_completed_tasks() -> None:
    state = GraphRun(call_programs.chain.build(), given={'x': Int(2), 'y': Int(3)})
    assert [start.instance for start in state.step().starts] == ['add']
    _, completed = tasks.add.run_get_node(x=2, y=3)
    assert completed.pk is not None
    state.started('add', completed.pk)
    state.completed('add', completed.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert [start.instance for start in restored.step().starts] == ['add_2']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_run_state_versions_its_checkpoints() -> None:
    """Scheduler checkpoints carry a version; unknown ones fail loudly, old ones load."""
    from aiida.engine.processes.graphs.run import STATE_VERSION

    state = GraphRun(call_programs.chain.build(), given={'x': Int(2), 'y': Int(3)})
    assert state.to_dict().get('version') == STATE_VERSION
    saved = state.to_dict()
    GraphRun.from_dict(state.graph, state.given, {key: value for key, value in saved.items() if key != 'version'})
    with pytest.raises(GraphTypeCheckError, match='cannot read a graph run declaration'):
        GraphRun.from_dict(state.graph, state.given, {**saved, 'version': '0.0'})


@pytest.mark.usefixtures('aiida_profile_clean')
def test_tasks_are_cached() -> None:
    from aiida.manage.caching import enable_caching

    with enable_caching(identifier='*'):
        _, first = run_get_node(call_programs.chain, x=11, y=2)
        outputs, again = run_get_node(call_programs.chain, x=11, y=2)
    assert first.is_finished_ok and again.is_finished_ok
    assert outputs['result'].value == 15
    assert all(not child.base.caching.is_created_from_cache for child in first.called)
    assert all(child.base.caching.is_created_from_cache for child in again.called)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'function',
    [
        pytest.param(tasks.mistyped_list, id='list'),
        pytest.param(tasks.mistyped_dict, id='dict'),
    ],
)
def test_parameterized_output_annotation_rejects_other_container(function: FunctionTaskHandle[t.Any, t.Any]) -> None:
    with pytest.raises(ValueError, match='not of the right type'):
        run_get_node(function, x=3)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_invalid_output_is_rejected_at_runtime() -> None:
    with pytest.raises(ValueError, match='not of the right type'):
        run_get_node(tasks.mistyped_output, x=1)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_body_runs_plain_python() -> None:
    """Task bodies execute with imports, loops, and comprehensions; only graph bodies lower."""
    outputs, node = run_get_node(tasks.statistics, values=[2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert node.is_finished_ok
    assert outputs['mean'].value == 5.0
    assert outputs['stdev'].value == 2.0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_single_key_typeddict_task_unpacks_output() -> None:
    """A single-key `TypedDict` task stores its value under the named port, not the whole mapping."""
    outputs, node = run_get_node(tasks.mismatched_alpha, value=2)
    assert node.is_finished_ok
    assert isinstance(outputs['alpha'], Int)
    assert outputs['alpha'].value == 2


@pytest.mark.usefixtures('aiida_profile_clean')
def test_named_task_rejects_scalar_return() -> None:
    """A task declaring named outputs must return a mapping, not a scalar."""
    with pytest.raises(GraphValidationError, match='returned a single value'):
        tasks.scalar_for_named.run_get_node()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_named_task_rejects_extra_outputs() -> None:
    """A task returning undeclared outputs fails naming the extras."""
    with pytest.raises(GraphValidationError, match='returned undeclared outputs'):
        run_get_node(tasks.extra_outputs, value=2)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_named_task_rejects_empty_mapping() -> None:
    """A task omitting every declared output fails naming the missing ones."""
    with pytest.raises(GraphValidationError, match='omitted declared outputs'):
        run_get_node(tasks.empty_outputs, value=2)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nontotal_typeddict_outputs_rejected() -> None:
    """A non-total `TypedDict` cannot declare task outputs."""
    with pytest.raises(GraphTypeCheckError, match='must be total'):
        task(tasks.partial_outputs)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_tuple_outputs_rejected() -> None:
    """A tuple cannot declare multiple task outputs."""
    with pytest.raises(GraphTypeCheckError, match='instead of a tuple'):
        task(tasks.pair_outputs)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_task_process_checkpoint_round_trips() -> None:
    """A task process saves and restores its spec and inputs."""
    from aiida.engine.processes.persistence import CheckpointPayload
    from tests.engine.processes.graphs.programs import tasks

    process = tasks.add.process_class(inputs=tasks.add.get_launch_inputs(x=2, y=3))
    payload = CheckpointPayload.from_object(process)
    process.close()
    restored = payload.decode()
    assert type(restored) is type(process)
    assert sorted(restored.spec().outputs) == ['result']
    assert restored.inputs['x'] == 2
