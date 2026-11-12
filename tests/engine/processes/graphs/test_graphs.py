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

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.exceptions import (
    GraphError,
    GraphLanguageError,
    GraphMaxIterationsError,
    GraphRuntimeError,
    GraphTypeCheckError,
    GraphValidationError,
    MissingRequiredInputsError,
)
from aiida.common.links import LinkType
from aiida.engine import Forward, task
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.run import GraphRun
from aiida.engine.processes.graphs.tasks import FunctionTaskHandle
from aiida.orm.nodes.data.bool import Bool
from aiida.orm.nodes.data.dict import Dict
from aiida.orm.nodes.data.float import Float
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.data.singlefile import SinglefileData
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.nodes.process.workflow.graph import GraphNode
from tests.engine.processes.graphs.programs import (
    assignments,
    branches,
    calcjobs,
    loops,
    parameters,
    ports,
    shelljobs,
    tasks,
    workchains,
)
from tests.engine.processes.graphs.programs import calls as call_programs

pytestmark = pytest.mark.presto


def _roundtrip(declaration: GraphHandle) -> GraphIR:
    """Rebuild one graph template the way a stored declaration node returns it.

    The daemon persists the template in a `graph` `Dict` node and rebuilds it with
    `from_dict` on restarts and loop continuations, so running from `build()` alone
    never exercises that path. The JSON step is the fidelity check: it rejects live
    objects a direct `from_dict(to_dict())` would silently accept but the database
    would mangle, such as tuples, sets, or non-string keys.
    """
    return GraphIR.from_dict(json.loads(json.dumps(declaration.build().to_dict())))


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, expected',
    [
        pytest.param(call_programs.multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 10}, id='multiply-add'),
        pytest.param(call_programs.nested_multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 11}, id='nested-graph'),
        pytest.param(call_programs.diamond, {'x': 2}, {'result': 7}, id='diamond'),
        pytest.param(call_programs.ordered, {'x': 2}, {'result': 3}, id='ordering-without-output'),
        pytest.param(call_programs.ordered_named, {'value': 2}, {'result': 3}, id='ordering-named'),
        pytest.param(call_programs.multiple_ordered, {'x': 2}, {'result': 3}, id='ordering-on-two'),
        pytest.param(call_programs.chain, {'x': 2, 'y': 3}, {'result': 8}, id='chain'),
        pytest.param(call_programs.spread_bundle, {'bundle': {'x': 2, 'y': 3}}, {'result': 5}, id='spread'),
        pytest.param(
            call_programs.spread_nested,
            {'bundle': {'config': {'settings': {'count': 2, 'nullable': None}}}},
            {'result': 2},
            id='spread-nested',
        ),
        pytest.param(call_programs.forwarded_add, {'bundle': {'x': 2, 'y': 3}}, {'result': 5}, id='forwarded'),
        pytest.param(
            call_programs.forwarded_nested,
            {'bundle': {'x': 2, 'y': 3, 'z': 4}},
            {'result': 11},
            id='forwarded-nested',
        ),
        pytest.param(call_programs.forwarded_exclude, {'bundle': {'x': 2}}, {'result': 4}, id='forwarded-exclude'),
        pytest.param(call_programs.forwarded_alias, {'bundle': {'x': 2, 'y': 3}}, {'result': 5}, id='forwarded-alias'),
        pytest.param(call_programs.generic_chain, {'x': 2, 'y': 3}, {'result': 4}, id='generic-chain'),
        pytest.param(call_programs.generic_mixed, {'x': 2, 'y': 2.5}, {'result': 4.5}, id='generic-mixed'),
        pytest.param(call_programs.namespaced_call, {'x': 1, 'y': 2}, {'result': 3}, id='namespaced'),
        pytest.param(call_programs.positional_task_arguments, {'value': 2}, {'result': 3}, id='positional-arguments'),
        pytest.param(ports.direct_result, {'value': 2}, {'result': 12}, id='direct-result'),
        pytest.param(ports.named, {'x': 2, 'y': 3}, {'total': 5, 'product': 6}, id='named-outputs'),
        pytest.param(
            ports.selected,
            {'config': {'settings': {'count': 2, 'nullable': None}}},
            {'result': 3},
            id='namespace-field',
        ),
        pytest.param(ports.selected_field, {'settings': {}}, {'result': 3}, id='namespace-field-default'),
        pytest.param(ports.flat_model, {'config': {'nullable': None}}, {'result': 6}, id='pydantic-flat-model'),
        pytest.param(ports.point_model, {'config': {'label': 'ab'}}, {'result': 4}, id='namedtuple-flat-model'),
        pytest.param(ports.flat_model_defaulted, {}, {'result': 13}, id='pydantic-instance-default'),
        pytest.param(
            ports.wired,
            {'config': {'settings': {'count': 5, 'nullable': None}, 'label': 'ab'}},
            {'result': 6},
            id='wired-namespace',
        ),
        pytest.param(
            ports.config_leaves,
            {'config': {'settings': {'count': 5, 'nullable': None}, 'label': 'ab'}},
            {'count': 6, 'label': 'ab'},
            id='namespace-leaves',
        ),
        pytest.param(ports.literal_dictionary, {}, {'result': 42}, id='dictionary-literal'),
        pytest.param(ports.dictionary_input, {'values': {'answer': 42}}, {'result': 42}, id='dictionary-leaf'),
        pytest.param(
            ports.summarize,
            {'values': [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]},
            {'mean': 5.0, 'stdev': 2.0},
            id='plain-python-body',
        ),
        pytest.param(ports.input_passthrough, {'value': 4}, {'result': 4}, id='input-passthrough'),
        pytest.param(ports.single_named_scalar, {'value': 2}, {'only': 2}, id='single-named-scalar'),
        pytest.param(ports.single_named_mapping, {'value': 2}, {'only': 2}, id='single-named-mapping'),
        pytest.param(branches.external_choice, {'value': 2, 'condition': True}, {'result': 3}, id='external-true'),
        pytest.param(branches.external_choice, {'value': 2, 'condition': False}, {'result': 4}, id='external-false'),
        pytest.param(branches.namespaced_choice, {'value': 2, 'condition': True}, {'result': 3}, id='namespaced-true'),
        pytest.param(
            branches.namespaced_choice, {'value': 2, 'condition': False}, {'result': 4}, id='namespaced-false'
        ),
        pytest.param(branches.computed_choice, {'value': 2}, {'result': 3}, id='computed-true'),
        pytest.param(branches.computed_choice, {'value': -2}, {'result': 0}, id='computed-false'),
        pytest.param(branches.inline_condition, {'value': 2}, {'result': 3}, id='inline-true'),
        pytest.param(branches.inline_condition, {'value': -2}, {'result': 0}, id='inline-false'),
        pytest.param(loops.countdown, {'value': 3, 'condition': True}, {'result': 0}, id='loop'),
        pytest.param(loops.countdown_call, {'value': 3}, {'result': 0}, id='loop-call'),
        pytest.param(loops.countdown_call, {'value': -2}, {'result': -2}, id='loop-call-zero'),
        pytest.param(loops.namespaced_loop, {'value': 3}, {'result': 0}, id='loop-namespaced'),
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
        pytest.param(parameters.positional_only_parameter, {'value': 2}, {'result': 3}, id='positional-only'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_supported_graph_syntax_executes(
    declaration: GraphHandle, inputs: dict[str, t.Any], expected: dict[str, int], serialized: bool
) -> None:
    """Supported declarations and their JSON representations return exact named values."""
    if serialized:
        spec = _roundtrip(declaration)
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
def test_load_waiting_checkpoint_rearms_child_callbacks(runner, monkeypatch: pytest.MonkeyPatch) -> None:
    """Restoring a checkpoint while tasks pend re-registers their finish callbacks."""
    from aiida.engine.processes.persistence import CheckpointPayload

    calls: list[int] = []
    monkeypatch.setattr(type(runner), 'call_on_process_finish', lambda self, pk, _cb: calls.append(pk))
    process = GraphProcess(inputs=call_programs.chain.get_launch_inputs(x=Int(2), y=3))
    name = call_programs.chain.build().task_names[0]
    process._run_state.started(name, 123)
    bundle = CheckpointPayload.from_object(process)
    process.close()
    calls.clear()
    restored = bundle.decode()
    assert calls == [123]
    assert restored._watched_pks == {123}
    restored.close()


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
    with pytest.raises(GraphRuntimeError, match='must be a `bool` or `Bool`'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_missing_else_keeps_prior_binding() -> None:
    """A missing `else` arm keeps the prior binding when skipped."""
    outputs, node = run_get_node(branches.overwrite_if, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 13
    outputs, node = run_get_node(branches.overwrite_if, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_missing_else_unbound_rejected() -> None:
    """A missing `else` arm without a prior binding fails naming the fix."""
    with pytest.raises(GraphLanguageError, match='assign it first or add an `else` arm'):
        branches.missing_else_unbound.build()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_in_branch_runs() -> None:
    """A loop in one arm rebinds loop state per iteration."""
    outputs, node = run_get_node(branches.loop_in_branch, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 0
    outputs, node = run_get_node(branches.loop_in_branch, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == -1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_in_missing_else_runs() -> None:
    """A loop in the only arm keeps the prior binding when skipped."""
    outputs, node = run_get_node(branches.loop_in_missing_else, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 0
    outputs, node = run_get_node(branches.loop_in_missing_else, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_overwrite_both_runs() -> None:
    """Both arms overwriting one name resolve to the taken side."""
    outputs, node = run_get_node(branches.overwrite_both, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 13
    outputs, node = run_get_node(branches.overwrite_both, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 103


@pytest.mark.usefixtures('aiida_profile_clean')
def test_alias_both_runs() -> None:
    """Both arms aliasing existing values resolve without tasks."""
    outputs, node = run_get_node(branches.alias_both, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    outputs, node = run_get_node(branches.alias_both, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_alias_call_runs() -> None:
    """A call arm and an alias arm merge on one port."""
    outputs, node = run_get_node(branches.alias_call, value=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 12
    outputs, node = run_get_node(branches.alias_call, value=2, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_alias_input_runs() -> None:
    """An alias to a graph input merges under the task port."""
    outputs, node = run_get_node(branches.alias_input, value=2, other=10, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    outputs, node = run_get_node(branches.alias_input, value=2, other=10, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 10


@pytest.mark.usefixtures('aiida_profile_clean')
def test_alias_inputs_runs() -> None:
    """Two same-type input aliases merge under the first port."""
    outputs, node = run_get_node(branches.alias_inputs, value=2, other=10, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 2
    outputs, node = run_get_node(branches.alias_inputs, value=2, other=10, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 10


def test_trailing_underscore_task_name_rejected() -> None:
    """A task class name must be a valid link label."""
    from aiida.engine.processes.calcjobs.calcjob import CalcJob

    class Trailing_(CalcJob):  # noqa: N801 - the test needs an invalid link label
        pass

    with pytest.raises(GraphTypeCheckError, match='invalid as a link label'):
        task(Trailing_)


def test_trailing_underscore_function_name_rejected() -> None:
    """A task function name must be a valid link label."""
    namespace: dict[str, t.Any] = {}
    exec('def trailing_(): ...', namespace)

    with pytest.raises(GraphLanguageError, match='invalid as a link label'):
        task(namespace['trailing_'])


def test_forward_string_exclusion_accepted() -> None:
    """A single string exclusion drops one port."""
    assert Forward(tasks.add, exclude='y').exclude == ('y',)


def test_forward_invalid_marker_rejected() -> None:
    """A forward exclusion must name input paths."""
    with pytest.raises(GraphLanguageError, match='must be strings'):
        Forward(tasks.add, exclude=(42,))


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_condition_rejects_non_bool() -> None:
    """A loop condition of any other type fails loudly instead of coercing."""
    state = GraphRun(loops.countdown.build(), given={'value': 3, 'condition': Int(1)})
    with pytest.raises(GraphRuntimeError, match='must be a `bool` or `Bool`'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_in_loop_runs() -> None:
    """A branch inside a loop body rebinds loop state per iteration."""
    outputs, node = run_get_node(loops.nested_branch_in_loop, value=2)
    assert node.is_finished_ok
    assert outputs['result'].value == -1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_loops_run() -> None:
    """A loop inside a loop body threads inner state through the region."""
    outputs, node = run_get_node(loops.nested_loops, value=2)
    assert node.is_finished_ok
    assert outputs['result'].value == -1


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
def test_zero_iteration_loop_returns_initial_state() -> None:
    """A never-entered loop returns its initial state like the equivalent Python loop."""
    outputs, node = run_get_node(loops.countdown, value=3, condition=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_downstream_task_consumes_zero_iteration_loop_output() -> None:
    """A task consuming a never-entered loop's output reads its passed-through state."""
    outputs, node = run_get_node(loops.countdown_then_add, value=3, condition=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_downstream_task_consumes_loop_output() -> None:
    """A task consuming a finished loop's output reads the last iteration's state."""
    outputs, node = run_get_node(loops.countdown_then_add, value=3, condition=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_iterations_share_one_body_node() -> None:
    """Loop iterations share one stored body declaration instead of one copy each."""
    outputs, node = run_get_node(loops.countdown, value=3, condition=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 0
    children: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert len(children) == 3
    pks = {
        child.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph').pk
        for child in children.values()
    }
    assert len(pks) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'cap, match',
    [
        pytest.param(0, 'allowing at least one iteration', id='zero-cap'),
        pytest.param(2.5, 'needs an integer', id='non-integer-cap'),
    ],
)
def test_loop_max_iterations_validated(cap: t.Any, match: str) -> None:
    """An unusable loop cap fails naming the violated rule."""
    import dataclasses

    from aiida.engine.processes.graphs.ir import LoopControl

    spec = loops.countdown.build()
    loop = spec.tasks[0]
    assert isinstance(loop, LoopControl)
    patched = [dataclasses.replace(loop, max_iterations=cap) if task is loop else task for task in spec.tasks]
    with pytest.raises(GraphTypeCheckError, match=match):
        dataclasses.replace(spec, tasks=tuple(patched))


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_raises_after_max_iterations(monkeypatch: pytest.MonkeyPatch) -> None:
    """A never-clearing loop dispatches exactly `max_iterations` iterations, then raises."""
    import dataclasses

    import aiida.engine.processes.graphs.run as run_module
    from aiida.engine.processes.graphs.ir import LoopControl

    spec = loops.countdown.build()
    loop = spec.tasks[0]
    assert isinstance(loop, LoopControl)
    capped = dataclasses.replace(spec, tasks=(dataclasses.replace(loop, max_iterations=2),))
    state = GraphRun(capped, given={'value': 3, 'condition': True})
    assert [start.instance for start in state.step().starts] == ['loop_1_iteration_0']

    class _Finished:
        is_finished_ok = True

    monkeypatch.setattr(run_module, 'load_node', lambda _pk: _Finished())
    monkeypatch.setattr(run_module, '_returned', lambda _node: {'condition': True, 'value': 3})
    state.completed('loop_1_iteration_0', 111)
    # One finished iteration below the cap still dispatches: the bound is `>=`, not an early trigger.
    assert [start.instance for start in state.step().starts] == ['loop_1_iteration_1']
    state.completed('loop_1_iteration_1', 112)
    # At the cap the scheduler raises instead of dispatching: with `>` this would start iteration 2.
    with pytest.raises(GraphMaxIterationsError, match='exceeded 2 iterations'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_failed_loop_iteration_dispatches_no_next_iteration(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed loop iteration surfaces the loop as failed without dispatching further."""
    import aiida.engine.processes.graphs.run as run_module

    state = GraphRun(loops.countdown.build(), given={'value': 3, 'condition': True})
    assert [start.instance for start in state.step().starts] == ['loop_1_iteration_0']

    class _Failed:
        is_finished_ok = False

    monkeypatch.setattr(run_module, 'load_node', lambda _pk: _Failed())
    state.completed('loop_1_iteration_0', 111)
    assert state.step().starts == []
    assert state.failed == ['loop_1']


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
def test_dynamic_leaf_stores_as_node() -> None:
    """A dynamic extra leaf arrives in provenance as a node."""
    _outputs, node = run_get_node(ports.input_passthrough, value=4)
    assert node.is_finished_ok
    linked = node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph_inputs__value')
    assert isinstance(linked, Int)


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
    from aiida.engine.processes.graphs.run import _STATE_VERSION

    state = GraphRun(call_programs.chain.build(), given={'x': Int(2), 'y': Int(3)})
    assert state.to_dict().get('version') == _STATE_VERSION
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
@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs, match',
    [
        pytest.param(tasks.scalar_for_named, {}, 'returned a single value', id='scalar-return'),
        pytest.param(tasks.extra_outputs, {'value': 2}, 'returned undeclared outputs', id='extra-outputs'),
        pytest.param(tasks.empty_outputs, {'value': 2}, 'omitted declared outputs', id='empty-mapping'),
    ],
)
def test_named_task_output_mismatches_fail(declaration: t.Any, inputs: dict[str, t.Any], match: str) -> None:
    """A task returning other than its declared outputs fails naming the mismatch."""
    with pytest.raises(GraphValidationError, match=match):
        run_get_node(declaration, **inputs)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, match',
    [
        pytest.param(tasks.partial_outputs, 'must be total', id='nontotal-typeddict'),
        pytest.param(tasks.pair_outputs, 'instead of a tuple', id='tuple-outputs'),
        pytest.param(tasks.bare_tuple_outputs, 'instead of a tuple', id='bare-tuple-outputs'),
    ],
)
def test_output_declarations_rejected(declaration: t.Any, match: str) -> None:
    """Output declarations outside total `TypedDict` names fail."""
    with pytest.raises(GraphTypeCheckError, match=match):
        task(declaration)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_typevar_inputs_expanded() -> None:
    """A constrained type variable declares the union of its constraints."""
    from aiida.engine.processes.graphs.shapes import shape_for_annotation

    shape = shape_for_annotation(t.TypeVar('T', int, float))
    assert getattr(shape, 'types', None) == (int, float)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_typevar_output_expanded() -> None:
    """A constrained type variable declares a union output port."""
    from aiida.engine.processes.graphs.tasks import _declare_output_ports
    from aiida.engine.processes.process_spec import ProcessSpec

    spec = ProcessSpec()
    _declare_output_ports(t.TypeVar('T', int, float), spec)
    assert spec.outputs['result'].valid_type == (Int, Float)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_typevar_rejected() -> None:
    """A type variable inside a generic annotation is rejected."""
    from aiida.engine.processes.graphs.shapes import shape_for_annotation

    with pytest.raises(GraphTypeCheckError, match='not nested generics'):
        shape_for_annotation(list[t.TypeVar('T')])


@pytest.mark.usefixtures('aiida_profile_clean')
def test_optional_task_output_value_arm_runs() -> None:
    """An optional task output returning a value executes normally."""
    outputs, node = run_get_node(call_programs.optional_result, x=2, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_optional_task_output_none_arm_rejected() -> None:
    """A task returning `None` for a declared output fails like any missing output."""
    outputs, node = run_get_node(call_programs.optional_result, x=2, flag=False)
    assert node.exit_status == 400
    assert outputs == {}
    assert node.called[0].exit_status == 11


@pytest.mark.usefixtures('aiida_profile_clean')
def test_omitted_defaulted_namespace_fills() -> None:
    """Omitting a required namespace whose children all default still launches."""
    launch = ports.selected_field.get_launch_inputs()
    assert launch['graph_inputs'] == {'settings': {'count': 2}}


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


@pytest.mark.usefixtures('aiida_profile_clean')
def test_calcjob_task_runs_straight_line_graph(aiida_code_installed) -> None:
    """A `CalcJob` task wires non-metadata inputs and returns the parsed sum."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    outputs, node = run_get_node(
        calcjobs.add_single,
        x=2,
        y=3,
        code=code,
        task_metadata={'add_calc': {'options': {'custom_scheduler_commands': '# sentinel'}}},
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    (child,) = node.called
    assert child.process_type == ArithmeticAddCalculation.build_process_type()
    assert child.outputs.sum.value == 5
    assert set(child.inputs) == {'x', 'y', 'code'}
    assert child.get_option('custom_scheduler_commands') == '# sentinel'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_calcjob_graph_forwards_task_metadata(aiida_code_installed) -> None:
    """Stashed placement metadata reaches `CalcJob` tasks in nested graphs."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    outputs, node = run_get_node(calcjobs.add_nested, x=2, y=3, code=code, task_metadata={'add_calc': {'options': {}}})
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_calcjob_task_chains_values(aiida_code_installed) -> None:
    """A downstream `CalcJob` placement consumes the parsed output of another."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    outputs, node = run_get_node(
        calcjobs.add_twice,
        x=2,
        y=3,
        code=code,
        task_metadata={'add_calc': {'options': {}}, 'add_calc_2': {'options': {}}},
    )
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert {link.link_label for link in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()} == {
        'add_calc_2',
        'add_calc',
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_calcjob_task_missing_metadata_fails_loudly(aiida_code_installed) -> None:
    """A `CalcJob` placement without launch metadata names the placement."""
    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    with pytest.raises(GraphValidationError, match='task `add_calc` is a `CalcJob` and needs launch metadata'):
        run_get_node(calcjobs.add_single, x=2, y=3, code=code)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_graph_level_metadata_reaches_process() -> None:
    """Standard `metadata` reaches the graph process instead of the stash."""
    outputs, node = run_get_node(call_programs.multiply_add, x=1, y=2, z=3, metadata={'label': 'given-label'})
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    assert node.label == 'given-label'
    assert 'task_metadata' not in node.base.links.get_incoming().all_link_labels()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_graph_metadata_forwards_to_launch_inputs() -> None:
    """Standard `metadata` forwards to the launch instead of vanishing into the stash."""
    launch_inputs = call_programs.multiply_add.get_launch_inputs(x=1, y=2, z=3, metadata={'store_provenance': False})
    assert launch_inputs['metadata'] == {'store_provenance': False}
    assert 'task_metadata' not in launch_inputs


@pytest.mark.usefixtures('aiida_profile_clean')
def test_graph_metadata_with_nested_mapping_rejects() -> None:
    """A mapping under `metadata` names `task_metadata` instead of passing silently."""
    with pytest.raises(GraphValidationError, match='under `task_metadata`'):
        run_get_node(call_programs.multiply_add, x=1, y=2, z=3, metadata={'add_calc': {'options': {}}})


@pytest.mark.usefixtures('aiida_profile_clean')
def test_standard_metadata_options_pass_through() -> None:
    """The standard `options` key under `metadata` is not mistaken for placement options."""
    launch_inputs = call_programs.chain.get_launch_inputs(x=1, y=2, metadata={'options': {'resources': {}}})
    assert launch_inputs['metadata'] == {'options': {'resources': {}}}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_calcjob_handle_registers_static_leaf_outputs() -> None:
    """`CalcJob` registration exposes non-metadata inputs only, with static leaf outputs."""
    spec = calcjobs.add_calc.spec()
    assert 'metadata' not in [name for name, _ in calcjobs.add_calc._task_spec.input_shape.fields]
    assert not spec.outputs.dynamic
    assert set(spec.outputs) == {'sum', 'remote_folder', 'remote_stash', 'retrieved'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_workchain_task_runs_straight_line_graph() -> None:
    """A `WorkChain` task wires non-metadata inputs and returns the child output."""
    outputs, node = run_get_node(workchains.add_single, x=Int(2), y=Int(3))
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    (child,) = node.called
    assert child.process_type == workchains.AddWorkChain.build_process_type()
    assert child.outputs.result.value == 5
    assert set(child.inputs) == {'x', 'y'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_workchain_task_chains_values() -> None:
    """A downstream `WorkChain` placement consumes the output of another."""
    outputs, node = run_get_node(workchains.add_twice, x=Int(2), y=Int(3))
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    assert {link.link_label for link in node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()} == {
        'add_chain',
        'add_chain_2',
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_workchain_handle_registers_static_leaf_outputs() -> None:
    """`WorkChain` registration exposes non-metadata inputs only, with static leaf outputs."""
    spec = workchains.add_chain.spec()
    assert 'metadata' not in {name for name, _ in workchains.add_chain._task_spec.input_shape.fields}
    assert not spec.outputs.dynamic
    assert set(spec.outputs) == {'result'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_workchain_handle_accepts_plain_values() -> None:
    """Process handles pass raw inputs through; the process prepares and validates them."""
    assert workchains.add_chain.get_launch_inputs(x=2, y=3) == {'x': 2, 'y': 3}
    outputs, node = run_get_node(workchains.add_chain, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_begin_loop_missing_condition_port_names_loop() -> None:
    """A loop dispatch without its condition port names the loop instead of raising `KeyError`."""
    from aiida.engine.processes.graphs.run import _Step

    spec = loops.countdown.build()
    state = GraphRun(spec, given={'value': 3, 'condition': True})
    with pytest.raises(GraphRuntimeError, match='loop `loop_1` is missing its condition port'):
        state._begin_loop(spec.tasks[0], {}, _Step())


@pytest.mark.usefixtures('aiida_profile_clean')
def test_continue_loop_missing_condition_port_names_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    """A loop iteration without its condition port names the loop instead of raising `KeyError`."""
    import aiida.engine.processes.graphs.run as run_module

    class _Finished:
        is_finished_ok = True

    monkeypatch.setattr(run_module, 'load_node', lambda _pk: _Finished())
    monkeypatch.setattr(run_module, '_returned', lambda _node: {})
    state = GraphRun(loops.countdown.build(), given={'value': 3, 'condition': True})
    assert [start.instance for start in state.step().starts] == ['loop_1_iteration_0']
    state.completed('loop_1_iteration_0', 111)
    with pytest.raises(GraphRuntimeError, match='loop `loop_1` is missing its condition port'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_is_finished_ok_caches_per_node(monkeypatch: pytest.MonkeyPatch) -> None:
    """Repeated finished checks load each node once."""
    import aiida.engine.processes.graphs.run as run_module

    calls: list[int] = []

    class _Finished:
        is_finished_ok = True

    def counting(pk: int):
        calls.append(pk)
        return _Finished()

    monkeypatch.setattr(run_module, 'load_node', counting)
    state = GraphRun(loops.countdown.build(), given={'value': 3, 'condition': True})
    assert state._is_finished_ok(111) is True
    assert state._is_finished_ok(111) is True
    assert calls == [111]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_merge_task_metadata_rejects_non_mapping() -> None:
    """A non-mapping stash entry fails naming the placement."""
    from aiida.engine.processes.graphs.tasks import _merge_task_metadata

    task = calcjobs.add_single.build().tasks[0]
    with pytest.raises(GraphValidationError, match='must be a mapping'):
        _merge_task_metadata(task, {'add_calc': ['options']}, {'x': 1})


@pytest.mark.requires_broker
def test_new_template_shapes_run_on_daemon(submit_and_await) -> None:
    """Solved generics with a loop arm survive template serialization."""
    spec = call_programs.daemon_proving.build()
    node = submit_and_await(GraphProcess, graph=Dict(dict=spec.to_dict()), graph_inputs={'x': 2, 'flag': True})
    assert node.is_finished_ok
    assert node.outputs.result.value == 0


@pytest.mark.requires_broker
def test_graph_with_unimportable_executors_runs_on_daemon(submit_and_await) -> None:
    """A graph whose task executors only resolve through payloads runs on the daemon."""
    import base64
    import dataclasses

    from aiida.common import _callables as callables
    from aiida.engine.processes.graphs.ir import ExecutorReference, ProcessTask, TaskIR

    def payload_task(task: ProcessTask) -> ProcessTask:
        payload = base64.b64encode(callables.dumps(task.spec.process_class)).decode('ascii')
        spec = TaskIR(
            identifier=task.spec.identifier,
            executor=ExecutorReference(module='__main__', name=task.spec.identifier, payload=payload),
        )
        return dataclasses.replace(task, spec=spec)

    spec = call_programs.chain.build()
    spec = dataclasses.replace(
        spec, tasks=tuple(payload_task(task) for task in spec.tasks if isinstance(task, ProcessTask))
    )
    node = submit_and_await(GraphProcess, graph=Dict(dict=spec.to_dict()), graph_inputs={'x': 2, 'y': 3}, timeout=120)
    assert node.is_finished_ok
    assert node.outputs.result.value == 8


def test_sibling_module_task_resolves_through_payload(tmp_path, monkeypatch) -> None:
    """A task from an uninstalled sibling module loads without importing it."""
    import importlib
    import sys

    monkeypatch.syspath_prepend(str(tmp_path))
    (tmp_path / 'sib_tasks.py').write_text(
        'from aiida.engine.processes.graphs.lowering import task\n'
        '\n'
        'OFFSET = 10\n'
        '\n'
        'def _helper(x: int) -> int:\n'
        '    return x + OFFSET\n'
        '\n'
        '@task\n'
        'def add(x: int, y: int) -> int:\n'
        '    return _helper(x) + y\n'
    )
    spec = importlib.import_module('sib_tasks').add._task_spec
    assert spec.executor.payload is not None
    monkeypatch.setitem(sys.modules, 'sib_tasks', None)
    assert sorted(spec.executor.load().spec().inputs) == ['metadata', 'x', 'y']


@pytest.fixture
def shell_code(aiida_code_installed):
    """Return a factory for a `core.shell` code running one system command."""
    import shutil

    def factory(command: str):
        return aiida_code_installed(
            label=command, default_calc_job_plugin='core.shell', filepath_executable=shutil.which(command)
        )

    return factory


@pytest.fixture
def text_file():
    """Return a stored-on-use text file with three words."""
    import io

    from aiida.orm import SinglefileData

    return SinglefileData(io.BytesIO(b'one two three\n'), filename='text.txt')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_shelljob_task_wires_declared_dynamic_ports(shell_code, text_file) -> None:
    """Declared `ShellJob` ports wire a dynamic output into a dynamic input namespace."""
    outputs, node = run_get_node(
        shelljobs.copy_and_count,
        text=text_file,
        cat_code=shell_code('cat'),
        wc_code=shell_code('wc'),
        cat_arguments=['{text}'],
        wc_arguments=['-w', '{text}'],
        task_metadata={'cat': {'options': {}}, 'count_words': {'options': {}}},
    )
    assert node.is_finished_ok
    assert outputs['result'].get_content().split()[0] == '3'
    copied = node.base.links.get_outgoing(link_label_filter='cat').one().node
    counted = node.base.links.get_outgoing(link_label_filter='count_words').one().node
    assert counted.inputs.nodes.text.uuid == copied.outputs.stdout.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_shelljob_task_missing_declared_output_fails_task(shell_code, text_file) -> None:
    """A finished task without a declared output fails the graph, naming the output."""
    _, node = run_get_node(
        shelljobs.expect_unproduced,
        text=text_file,
        code=shell_code('cat'),
        arguments=['{text}'],
        task_metadata={'unproduced': {'options': {}}},
    )
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    (child,) = node.called
    assert child.is_finished_ok
    reports = [log.message for log in orm.Log.collection.get_logs_for(node)]
    assert any(
        report.endswith("task `unproduced` finished without its declared outputs ['missing_txt']") for report in reports
    )


def test_shelljob_task_declarations_round_trip() -> None:
    """Declared ports survive serialization, and the shared class spec stays dynamic."""
    from aiida.calculations.shell import ShellJob

    rebuilt = _roundtrip(shelljobs.copy_and_count)
    task = rebuilt.task('cat')
    assert sorted(task.spec.outputs) == ['remote_folder', 'remote_stash', 'retrieved', 'stdout']
    assert list(task.spec.inputs['nodes']) == ['text']
    assert ShellJob.spec().outputs.dynamic
    assert ShellJob.spec().inputs['nodes'].dynamic
    assert list(ShellJob.spec().inputs['nodes']) == []


def test_shelljob_task_rejects_mistyped_declared_input() -> None:
    """Wiring a value into a declared port checks the declared node type."""
    with pytest.raises(GraphTypeCheckError):
        shelljobs.mistyped.build()


@pytest.mark.parametrize(
    'declarations, match',
    [
        pytest.param({}, 'declare the outputs of a dynamic namespace', id='undeclared-outputs'),
        pytest.param(
            {'inputs': {'arguments': SinglefileData}, 'outputs': {'stdout': SinglefileData}},
            '`arguments` is already a declared port',
            id='static-port',
        ),
        pytest.param(
            {'inputs': {'code': {'x': SinglefileData}}, 'outputs': {'stdout': SinglefileData}},
            '`code` is already a declared port',
            id='static-namespace',
        ),
        pytest.param(
            {'inputs': {'nodes': {'x': int}}, 'outputs': {'stdout': SinglefileData}},
            'takes `Data` subclasses',
            id='python-type',
        ),
        pytest.param(
            {'outputs': {'nested': {'a': SinglefileData}}},
            'task outputs are leaves',
            id='output-namespace',
        ),
    ],
)
def test_shelljob_task_rejects_invalid_declarations(declarations, match) -> None:
    """Declarations only fix names inside dynamic namespaces, with node types."""
    from aiida.calculations.shell import ShellJob

    with pytest.raises(GraphTypeCheckError, match=match):
        task(ShellJob, **declarations)


def test_function_task_rejects_port_declarations() -> None:
    """Task functions declare their ports through annotations alone."""
    with pytest.raises(GraphTypeCheckError, match='declare their ports through annotations'):
        task(shelljobs.double, outputs={'result': Int})


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, linked, launch',
    [
        pytest.param(shelljobs.run_remote_none_in_task_call, False, {}, id='unwired'),
        pytest.param(shelljobs.run_remote_from_previous_task, True, {}, id='wired'),
        pytest.param(shelljobs.run_remote_none_in_graph_signature, False, {'remote': None}, id='graph-input-none'),
        pytest.param(shelljobs.run_remote_none_in_graph_signature, False, {}, id='graph-input-omitted'),
    ],
)
def test_declared_optional_input_runs(
    shell_code, text_file, declaration: GraphHandle, linked: bool, launch: dict[str, t.Any]
) -> None:
    """An unwired optional input stays out of the launch; a wired one arrives."""
    metadata = {name: {'options': {}} for name in declaration.build().task_names}
    outputs, node = run_get_node(
        declaration,
        text=text_file,
        code=shell_code('cat'),
        arguments=['{text}'],
        task_metadata=metadata,
        **launch,
    )
    assert node.is_finished_ok
    assert outputs['result'].get_content() == 'one two three\n'
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    incoming = [link.link_label for link in calls['rerun'].base.links.get_incoming().all()]
    assert ('remote_folder' in incoming) == linked
    if linked:
        assert calls['rerun'].inputs.remote_folder.uuid == calls['cat'].outputs.remote_folder.uuid


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(tasks.generic_breaks, id='graph-output'),
        pytest.param(tasks.generic_breaks_downstream, id='downstream-task'),
    ],
)
def test_generic_task_breaking_narrowed_type_fails_task(declaration: GraphHandle) -> None:
    """A generic task breaking its narrowed output fails as a task, and its dependents never start."""
    _, node = run_get_node(declaration, a=2)
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    called = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all_link_labels()
    assert called == ['to_float']
    reports = [log.message for log in orm.Log.collection.get_logs_for(node)]
    assert any(
        report.endswith('task `to_float` returned `Float` for port `result`, expected `Int`') for report in reports
    )
