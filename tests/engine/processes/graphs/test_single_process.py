###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Single-`GraphProcess` invariants: nested scopes never submit child graphs.

Every graph execution, including explicitly nested graphs and loop, branch,
and map bodies, runs as scopes of one root process. Only task runs and map
collectors become child processes, dispatched with hierarchical call labels.
These tests pin the invariant, the label hierarchy, failure propagation, and
checkpoint/restart behavior with pending and completed child work.
"""

import pytest

from aiida.common.exceptions import GraphMaxIterationsError
from aiida.common.links import LinkType
from aiida.engine import graph, par_map, task
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.run import GraphRun
from aiida.orm import DataList
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.nodes.process.workflow.graph import GraphNode
from tests.engine.processes.graphs.programs import branches, calls, loops, map_graphs, par_maps
from tests.engine.processes.graphs.programs import tasks as task_programs

pytestmark = pytest.mark.presto


@task
def fail_always(x: int) -> int:
    """Raise unconditionally, for nested failure propagation."""
    raise ValueError('deliberately failed')


@graph
def inner_failing(x: int) -> int:
    """Fail inside a nested graph."""
    return fail_always(x=x)


@graph
def outer_failing(x: int) -> int:
    """Consume a nested graph that fails, so the downstream task never dispatches."""
    intermediate = inner_failing(x=x)
    return task_programs.add(x=intermediate, y=1)


@graph
def passthrough_identity(x: int) -> int:
    """Pass one input through with no tasks; map elements settle synchronously."""
    return x


@graph
def map_passthrough_graph(values: DataList) -> DataList:
    """Map a task-free graph over a list; the collector must still dispatch."""
    return par_map(passthrough_identity, values)


@graph
def loop_sync_terminates(value: int, go: bool, flag: bool, other: bool) -> int:
    """Iterate a task-free branch body once, then settle without child processes."""
    while go:
        if flag:
            go = other
        else:
            go = flag
    return value


@graph
def loop_sync_persists(value: int, go: bool, flag: bool) -> int:
    """Rebind loop state to itself; synchronous iterations never clear."""
    while go:
        if flag:
            go = flag
        else:
            go = flag
    return value


@graph
def inner_with_default(x: int = 5) -> int:
    """Add one to an input that callers may omit."""
    return task_programs.add(x=x, y=1)


@graph
def outer_uses_default() -> int:
    """Call a nested graph without its defaulted input."""
    return inner_with_default()


@graph
def outer_overrides_default() -> int:
    """Call a nested graph overriding its defaulted input."""
    return inner_with_default(x=10)


def _local_runner():
    """Return a broker-free runner for checkpoint tests that must not require RabbitMQ."""
    from aiida.manage import get_manager

    return get_manager().create_runner(communicator=None)


def _decode_process(payload, runner):
    """Decode a checkpoint payload with an explicit broker-free runner."""
    from aiida.common.loaders import get_object_loader
    from aiida.engine.processes.persistence import CheckpointContext

    return payload.decode(CheckpointContext(loader=get_object_loader(), runner=runner, loop=runner.loop))


def _graph_nodes(node: ProcessNode) -> list[GraphNode]:
    """Return every graph node in the execution tree, root included."""
    return [node, *[child for child in node.called_descendants if isinstance(child, GraphNode)]]


def _call_labels(node: ProcessNode) -> set[str]:
    """Return the flat call link labels of the direct children of a process."""
    return set(node.base.links.get_outgoing(link_type=(LinkType.CALL_CALC, LinkType.CALL_WORK)).all_link_labels())


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, inputs',
    [
        pytest.param(calls.nested_multiply_add, {'x': 2, 'y': 3, 'z': 4}, id='nested-graph'),
        pytest.param(loops.countdown, {'value': 3, 'condition': True}, id='loop'),
        pytest.param(branches.external_choice, {'value': 2, 'condition': True}, id='branch-taken'),
        pytest.param(branches.external_choice, {'value': 2, 'condition': False}, id='branch-otherwise'),
        pytest.param(par_maps.map_list, {'values': [1, 2]}, id='map-task'),
        pytest.param(par_maps.map_nested, {'values': [1, 2]}, id='map-graph'),
        pytest.param(map_graphs.map_two_step, {'values': [1, 2]}, id='map-multistep-graph'),
        pytest.param(loops.nested_loops, {'value': 2}, id='nested-loops'),
        pytest.param(branches.loop_in_branch, {'value': 2, 'flag': True}, id='loop-in-branch'),
    ],
)
def test_single_graph_node_invariant(declaration, inputs: dict) -> None:
    """Nested graphs, loops, branches, and maps execute without child graph processes."""
    if 'values' in inputs:
        inputs = {**inputs, 'values': DataList([Int(value) for value in inputs['values']])}
    _, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert _graph_nodes(node) == [node]
    assert node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all() == []
    assert set(node.called) == set(node.called_descendants)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_hierarchical_labels_preserve_scope_identity() -> None:
    """Nested scopes dispatch with labels that name their scope and iteration."""
    outputs, node = run_get_node(loops.nested_branch_in_loop, value=2)
    assert node.is_finished_ok
    assert outputs['result'].value == -1
    labels = _call_labels(node)
    assert {'add', 'is_positive'} <= labels  # root tasks keep their plain placement labels
    scoped = {label for label in labels if '__' in label}
    assert scoped
    assert any('_iteration_' in label for label in scoped)
    assert any('__branch_' in label and label.count('__') == 2 for label in scoped)
    assert _graph_nodes(node) == [node]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_failure_propagates_without_dispatching_downstream() -> None:
    """A task failing inside a nested graph fails the root without dispatching dependents."""
    outputs, node = run_get_node(outer_failing, x=2)
    assert not node.is_finished_ok
    assert node.exit_status == GraphProcess.exit_codes.ERROR_TASK_FAILED.status
    assert outputs == {}
    assert _call_labels(node) == {'inner_failing__fail_always'}
    assert _graph_nodes(node) == [node]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_checkpoint_restores_scopes_and_rearms_callbacks(runner, monkeypatch) -> None:
    """Checkpointing with pending nested work restores scopes and re-registers callbacks."""
    from aiida.engine.processes.persistence import CheckpointPayload

    seen: list[int] = []
    monkeypatch.setattr(type(runner), 'call_on_process_finish', lambda self, pk, _callback: seen.append(pk))
    process = GraphProcess(inputs=calls.nested.get_launch_inputs(x=Int(2), y=3))
    try:
        restores = None
        assert [start.instance for start in process._run_state.step().starts] == ['chain__add']
        process._run_state.started('chain__add', 123)
        assert process._run_state.pending == {'chain__add': 123}
        checkpoint = CheckpointPayload.from_object(process)
        process.close()
        seen.clear()
        restores = checkpoint.decode()
        assert isinstance(restores, GraphProcess)
        assert restores._run_state.to_dict() == process._run_state.to_dict()
        assert restores._run_state.pending == {'chain__add': 123}
        assert restores._run_state.step().starts == []
        assert seen == [123]
        restores._run_state.completed('chain__add', 123)
    finally:
        process.close()
        if restores is not None:
            restores.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_completed_work_reused_across_restart() -> None:
    """Restoring a nested run reuses finished scope tasks instead of resubmitting them."""
    state = GraphRun(calls.nested.build(), given={'x': Int(2), 'y': Int(3)})
    assert [start.instance for start in state.step().starts] == ['chain__add']
    _, first = task_programs.add.run_get_node(x=2, y=3)
    state.started('chain__add', first.pk)
    state.completed('chain__add', first.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert [start.instance for start in restored.step().starts] == ['chain__add_2']
    _, second = task_programs.add.run_get_node(x=5, y=3)
    restored.started('chain__add_2', second.pk)
    restored.completed('chain__add_2', second.pk)
    again = GraphRun.from_dict(restored.graph, restored.given, restored.to_dict())
    starts = again.step().starts
    assert [start.instance for start in starts] == ['add']
    assert starts[0].inputs['x'].value == 8


@pytest.mark.usefixtures('aiida_profile_clean')
def test_branch_decision_survives_restart() -> None:
    """A restored branch keeps its taken side instead of re-entering the other arm."""
    state = GraphRun(branches.external_choice.build(), given={'value': 2, 'condition': True})
    assert [start.instance for start in state.step().starts] == ['branch_1__add']
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert restored.step().starts == []
    _, finished = task_programs.add.run_get_node(x=2, y=1)
    restored.started('branch_1__add', finished.pk)
    restored.completed('branch_1__add', finished.pk)
    assert restored.step().starts == []
    assert restored.outputs()['result'].value == 3


@pytest.mark.usefixtures('aiida_profile_clean')
def test_map_pending_items_reattach_without_resubmission() -> None:
    """A restored map with one finished item dispatches only its collector, never items twice."""
    original = DataList([Int(1), Int(2)])
    state = GraphRun(par_maps.map_list.build(), given={'values': original})
    assert [start.instance for start in state.step().starts] == ['map_increment_0', 'map_increment_1']
    _, first = par_maps.increment.run_get_node(x=1)
    _, second = par_maps.increment.run_get_node(x=2)
    state.started('map_increment_0', first.pk)
    state.started('map_increment_1', second.pk)
    state.completed('map_increment_0', first.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    # The pending item reattaches to the stored node instead of dispatching a duplicate.
    assert restored.pending == {'map_increment_1': second.pk}
    assert restored.step().starts == []
    restored.completed('map_increment_1', second.pk)
    starts = restored.step().starts
    assert [start.instance for start in starts] == ['map_increment_collect']
    assert starts[0].inputs['item_0'].value == 2


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_graph_map_collects_synchronously() -> None:
    """A map over a task-free graph dispatches its collector without child tasks."""
    values = DataList([Int(1), Int(2)])
    state = GraphRun(map_passthrough_graph.build(), given={'values': values})
    starts = state.step().starts
    assert [start.instance for start in starts] == ['map_passthrough_identity_collect']
    assert [starts[0].inputs['item_0'], starts[0].inputs['item_1']] == [1, 2]
    outputs, node = run_get_node(map_passthrough_graph, values=values)
    assert node.is_finished_ok
    assert [member.value for member in outputs['result']] == [1, 2]
    assert _graph_nodes(node) == [node]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_with_synchronous_body_settles_without_dispatch() -> None:
    """A loop whose body is task-free iterates and settles with no child processes."""
    state = GraphRun(loop_sync_terminates.build(), given={'value': 7, 'go': True, 'flag': True, 'other': False})
    assert state.step().starts == []
    assert state.outputs()['result'] == 7
    outputs, node = run_get_node(loop_sync_terminates, value=7, go=True, flag=True, other=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    assert _graph_nodes(node) == [node]


def test_loop_with_synchronous_body_raises_at_cap() -> None:
    """A never-clearing task-free loop reaches its cap inside one scheduling step."""
    import dataclasses

    from aiida.engine.processes.graphs.ir import LoopControl

    spec = loop_sync_persists.build()
    loop = spec.tasks[0]
    assert isinstance(loop, LoopControl)
    capped = dataclasses.replace(spec, tasks=(dataclasses.replace(loop, max_iterations=2),))
    state = GraphRun(capped, given={'value': 1, 'go': True, 'flag': True})
    with pytest.raises(GraphMaxIterationsError, match='exceeded 2 iterations'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_graph_default_fills_scope_inputs() -> None:
    """Entering a nested graph fills defaults the caller omits, like a child launch."""
    state = GraphRun(outer_uses_default.build(), given={})
    starts = state.step().starts
    assert [start.instance for start in starts] == ['inner_with_default__add']
    assert starts[0].inputs['x'] == 5
    assert state.scopes['root/inner_with_default']['given'] == {'x': 5}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_graph_default_end_to_end() -> None:
    """Nested defaults apply on execution, and explicit wires still override them."""
    filled, filled_node = run_get_node(outer_uses_default)
    assert filled_node.is_finished_ok
    assert filled['result'].value == 6
    overridden, overridden_node = run_get_node(outer_overrides_default)
    assert overridden_node.is_finished_ok
    assert overridden['result'].value == 11
    assert _graph_nodes(filled_node) == [filled_node]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_yaml_persister_roundtrip_pending_nested_work(monkeypatch) -> None:
    """Pending nested work survives the daemon YAML checkpoint round trip and re-arms callbacks."""
    from aiida.engine.persistence import AiidaCheckpointPersister
    from aiida.engine.runners import Runner

    seen: list[int] = []
    monkeypatch.setattr(Runner, 'call_on_process_finish', lambda self, pk, _callback: seen.append(pk))
    runner = _local_runner()
    try:
        process = GraphProcess(inputs=GraphProcess._launch_inputs(outer_uses_default.build(), {}), runner=runner)
        restores = None
        try:
            assert [start.instance for start in process._run_state.step().starts] == ['inner_with_default__add']
            process._run_state.started('inner_with_default__add', 123)
            assert process._run_state.pending == {'inner_with_default__add': 123}
            persister = AiidaCheckpointPersister()
            persister.save_checkpoint(process)
            loaded = persister.load_checkpoint(process.node.pk)
            restores = _decode_process(loaded, runner)
            assert isinstance(restores, GraphProcess)
            assert restores._run_state.to_dict() == process._run_state.to_dict()
            assert restores._run_state.pending == {'inner_with_default__add': 123}
            assert restores._run_state.step().starts == []
            assert seen == [123]
        finally:
            process.close()
            if restores is not None:
                restores.close()
    finally:
        runner.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_yaml_persister_stores_defaulted_scope_inputs_without_links() -> None:
    """Nested scope defaults checkpoint through YAML: stored standalone, never provenance-linked."""
    from aiida.engine.persistence import AiidaCheckpointPersister
    from aiida.orm import Node

    runner = _local_runner()
    try:
        process = GraphProcess(inputs=GraphProcess._launch_inputs(outer_uses_default.build(), {}), runner=runner)
        restores = None
        try:
            assert [start.instance for start in process._run_state.step().starts] == ['inner_with_default__add']
            default = process._run_state.scopes['root/inner_with_default']['given']['x']
            assert isinstance(default, Node) and not default.is_stored
            persister = AiidaCheckpointPersister()
            persister.save_checkpoint(process)
            # The default is stored so YAML can reference it, but the workflow links nothing to it:
            # workflows must not `CREATE` scientific outputs, and scope labels would collide with root inputs.
            assert default.is_stored
            assert default.base.links.get_incoming().all() == []
            assert process.node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
            loaded = persister.load_checkpoint(process.node.pk)
            restores = _decode_process(loaded, runner)
            assert isinstance(restores, GraphProcess)
            given = restores._run_state.scopes['root/inner_with_default']['given']
            assert given['x'].uuid == default.uuid
            assert given['x'].pk == default.pk
            assert given['x'].is_stored
            assert restores._run_state.to_dict() == process._run_state.to_dict()
        finally:
            process.close()
            if restores is not None:
                restores.close()
    finally:
        runner.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_yaml_persister_completed_nested_work_continues_identically() -> None:
    """Completed nested tasks survive the YAML restore and continue with identical inputs."""
    from aiida.engine.persistence import AiidaCheckpointPersister

    runner = _local_runner()
    try:
        process = GraphProcess(inputs=GraphProcess._launch_inputs(outer_uses_default.build(), {}), runner=runner)
        restores = None
        try:
            state = process._run_state
            assert [start.instance for start in state.step().starts] == ['inner_with_default__add']
            _, finished = task_programs.add.run_get_node(x=5, y=1)
            state.started('inner_with_default__add', finished.pk)
            state.completed('inner_with_default__add', finished.pk)
            assert state.step().starts == []
            assert state.outputs()['result'].value == 6
            persister = AiidaCheckpointPersister()
            persister.save_checkpoint(process)
            restores = _decode_process(persister.load_checkpoint(process.node.pk), runner)
            assert isinstance(restores, GraphProcess)
            assert restores._run_state.to_dict() == state.to_dict()
            assert restores._run_state.pending == {}
            assert restores._run_state.outputs()['result'].value == 6
            live = GraphRun.from_dict(state.graph, state.given, state.to_dict())
            again = GraphRun.from_dict(
                restores._run_state.graph, restores._run_state.given, restores._run_state.to_dict()
            )
            assert live.step().starts == again.step().starts == []
        finally:
            process.close()
            if restores is not None:
                restores.close()
    finally:
        runner.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_run_state_checkpoint_encodes_nodes_and_retains_identity() -> None:
    """Run state checkpoints as encoded references: pickle and dereference round trips keep node identity."""
    import pickle

    from aiida.engine.processes.persistence import CheckpointPayload

    runner = _local_runner()
    try:
        process = GraphProcess(inputs=GraphProcess._launch_inputs(outer_uses_default.build(), {}), runner=runner)
        try:
            assert [start.instance for start in process._run_state.step().starts] == ['inner_with_default__add']
            payload = CheckpointPayload.from_object(process)
            assert isinstance(payload['run'], str)
            original = process._run_state.scopes['root/inner_with_default']['given']['x']
            assert original.is_stored
            for round_tripped in (
                pickle.loads(pickle.dumps(payload)),
                CheckpointPayload.from_object(process, dereference=True),
            ):
                restores = _decode_process(round_tripped, runner)
                try:
                    assert isinstance(restores, GraphProcess)
                    given = restores._run_state.scopes['root/inner_with_default']['given']
                    assert given['x'].uuid == original.uuid
                    assert given['x'].pk == original.pk
                finally:
                    restores.close()
        finally:
            process.close()
    finally:
        runner.close()
