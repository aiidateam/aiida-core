###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Runtime execution of inline operations inside a single graph run.

Inline operations evaluate synchronously in :meth:`GraphRun.step` without
dispatching child processes. Their primitive results checkpoint per scope in a
dedicated ``values`` field, survive restores without reevaluation, and flow
through nested loops, branches, subgraphs, and maps. The root graph never
returns a newly computed primitive as scientific data.
"""

from __future__ import annotations

import typing as t
from copy import deepcopy

import pytest

from aiida.common.exceptions import GraphMaxIterationsError, GraphRuntimeError
from aiida.common.links import LinkType
from aiida.engine import run_get_node
from aiida.engine.processes.graphs import run as run_mod
from aiida.engine.processes.graphs.ir import (
    BranchControl,
    Dependency,
    Endpoint,
    GraphIR,
    GraphTask,
    InlineOperation,
    LoopControl,
    MapControl,
    ProcessTask,
    Route,
    SubgraphTask,
)
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape
from aiida.orm import Bool, DataList, Int
from tests.engine.processes.graphs.programs import tasks as program_tasks

pytestmark = pytest.mark.presto


def _inline(
    name: str,
    operation: str,
    fields: dict[str, tuple[type, ...]],
    *,
    out_types: tuple[type, ...] = (int,),
    literals: dict[str, t.Any] | None = None,
) -> InlineOperation:
    """Return an inline operation placement with the given operand contracts."""
    return InlineOperation(
        name=name,
        inputs=dict(literals or {}),
        operation=t.cast(t.Any, operation),
        input_shape=NamespaceShape(fields=tuple((key, LeafShape(types=value)) for key, value in fields.items())),
        result_shape=LeafShape(types=out_types),
    )


def _graph(
    tasks: list[GraphTask],
    input_fields: dict[str, tuple[type, ...] | t.Any],
    dependencies: list[Dependency],
    input_routes: dict[str, list[Route]],
    outputs: dict[str, Endpoint],
    identifier: str = 'inline-test',
) -> GraphIR:
    """Return a static graph template for the given placements."""
    shape_fields = []
    for key, value in input_fields.items():
        if isinstance(value, LeafShape | NamespaceShape):
            shape_fields.append((key, value))
        else:
            shape_fields.append((key, LeafShape(types=value if isinstance(value, tuple) else (value,))))
    return GraphIR(
        tasks=tuple(tasks),
        input_shape=NamespaceShape(fields=tuple(shape_fields)),
        dependencies=tuple(dependencies),
        inputs={key: tuple(input_routes.get(key, ())) for key, _ in shape_fields},
        outputs=outputs,
        identifier=identifier,
    )


def _process(name: str, handle: t.Any) -> ProcessTask:
    """Return a process placement from a task handle."""
    return ProcessTask(name=name, inputs={}, spec=handle._task_spec)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_inline_chain_settles_synchronously_without_dispatch() -> None:
    """Two chained inline operations settle inside one step with no child runs."""
    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    op_double = _inline('doubled', 'mul', {'left': (int,), 'right': (int,)})
    graph = _graph(
        [op_add, op_double],
        {'x': (int,), 'y': (int,), 'z': (int,)},
        [Dependency('total', 'doubled', source_port='result', target_port='left')],
        {
            'x': [Route('total', 'left')],
            'y': [Route('total', 'right')],
            'z': [Route('doubled', 'right')],
        },
        {'result': Endpoint(task='doubled', port='result')},
    )
    state = run_mod.GraphRun(graph, given={'x': 2, 'y': 3, 'z': 4})
    step = state.step()
    assert step.starts == []
    assert state.scopes['root']['values'] == {'total': 5, 'doubled': 20}
    assert state.outputs() == {'result': 20}
    assert state.pending == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_mixed_inline_and_real_tasks_count_dispatches() -> None:
    """Inline operations compute inline while real tasks still dispatch once each."""
    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    first = _process('first', program_tasks.add)
    second = _process('second', program_tasks.add)
    graph = _graph(
        [op_add, first, second],
        {'x': (int,), 'y': (int,), 'z': (int,)},
        [
            Dependency('total', 'first', source_port='result', target_port='x'),
            Dependency('first', 'second', source_port='result', target_port='x'),
        ],
        {
            'x': [Route('total', 'left')],
            'y': [Route('total', 'right')],
            'z': [Route('first', 'y'), Route('second', 'y')],
        },
        {'result': Endpoint(task='second', port='result')},
    )
    state = run_mod.GraphRun(graph, given={'x': 2, 'y': 3, 'z': 4})
    step = state.step()
    assert [start.instance for start in step.starts] == ['first']
    assert state.scopes['root']['values'] == {'total': 5}
    _, completed = program_tasks.add.run_get_node(x=5, y=4)
    assert completed.pk is not None
    state.started('first', completed.pk)
    state.completed('first', completed.pk)
    assert [start.instance for start in state.step().starts] == ['second']


@pytest.mark.usefixtures('aiida_profile_clean')
def test_graph_outputs_reject_computed_scalars_but_allow_existing_data() -> None:
    """The root cannot RETURN a newly computed primitive; passthrough stays allowed."""
    from aiida.engine.processes.graphs.process import GraphProcess

    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    computed = _graph(
        [op_add],
        {'x': (int,), 'y': (int,)},
        [],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')]},
        {'result': Endpoint(task='total', port='result')},
    )
    state = run_mod.GraphRun(computed, given={'x': 2, 'y': 3})
    state.step()
    assert state.outputs() == {'result': 5}
    _, failed_node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(computed, {'x': 2, 'y': 3}))
    assert failed_node.is_failed and not failed_node.is_excepted
    assert failed_node.exit_status == 401  # ERROR_GRAPH_RUNTIME per the graph runtime exit-code spec.
    assert '@task' in (failed_node.exit_message or '')

    passthrough = _graph(
        [],
        {'x': (int,)},
        [],
        {'x': []},
        {'result': Endpoint(task=None, port='x')},
    )
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(passthrough, {'x': 2}))
    assert node.is_finished_ok
    assert outputs['result'].value == 2

    task_only = _graph(
        [_process('first', program_tasks.add)],
        {'x': (int,), 'y': (int,)},
        [],
        {'x': [Route('first', 'x')], 'y': [Route('first', 'y')]},
        {'result': Endpoint(task='first', port='result')},
    )
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(task_only, {'x': 2, 'y': 3}))
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_computed_primitive_cannot_escape_through_nested_scopes() -> None:
    """A computed primitive stays a primitive through nested scopes, so the root rejects it.

    Regression for provenance laundering: nodeifying an inline result at an inner boundary
    would let the root `RETURN` a newly created standalone `Data` without a `CREATE` link.
    Both a nested passthrough and each branch arm must keep the primitive with provenance on,
    while explicit materialization through a real `@task` stays allowed. Step-level probes feed
    ORM `Int`/`Bool` scalars to prove the evaluator unwraps stored scalars inline.
    """
    from aiida.engine.processes.graphs.process import GraphProcess
    from aiida.orm import Node

    passthrough_body = _graph(
        [],
        {'value': (int,)},
        [],
        {'value': []},
        {'result': Endpoint(task=None, port='value')},
        identifier='inline-passthrough',
    )
    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    nested = SubgraphTask(name='nested', inputs={}, body=passthrough_body)
    laundered = _graph(
        [op_add, nested],
        {'x': (int,), 'y': (int,)},
        [Dependency('total', 'nested', source_port='result', target_port='value')],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')]},
        {'result': Endpoint(task='nested', port='result')},
    )
    probe = run_mod.GraphRun(laundered, given={'x': 2, 'y': 3})
    assert probe.step().starts == []
    assert probe.outputs() == {'result': 5}
    nested_given = probe.scopes['root/nested']['given']
    assert nested_given == {'value': 5}
    assert not isinstance(nested_given['value'], Node)
    orm_probe = run_mod.GraphRun(laundered, given={'x': Int(2), 'y': Int(3)})
    assert orm_probe.step().starts == []
    assert orm_probe.outputs() == {'result': 5}
    assert orm_probe.scopes['root/nested']['given'] == {'value': 5}
    assert not isinstance(orm_probe.scopes['root/nested']['given']['value'], Node)
    _, failed_node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(laundered, {'x': 2, 'y': 3}))
    assert failed_node.is_failed and not failed_node.is_excepted
    assert failed_node.exit_status == 401  # ERROR_GRAPH_RUNTIME per the graph runtime exit-code spec.
    assert '@task' in (failed_node.exit_message or '')

    taken_body = _graph(
        [],
        {'value': (int,)},
        [],
        {'value': []},
        {'value': Endpoint(task=None, port='value')},
        identifier='inline-branch-taken',
    )
    otherwise_body = _graph(
        [],
        {'value': (int,)},
        [],
        {'value': []},
        {'value': Endpoint(task=None, port='value')},
        identifier='inline-branch-otherwise',
    )
    branch = BranchControl(name='choose', inputs={}, body=taken_body, otherwise=otherwise_body)
    branched = _graph(
        [op_add, branch],
        {'x': (int,), 'y': (int,), 'condition': (bool,)},
        [
            Dependency('total', 'choose', source_port='result', target_port='value'),
        ],
        {
            'x': [Route('total', 'left')],
            'y': [Route('total', 'right')],
            'condition': [Route('choose', 'condition')],
        },
        {'result': Endpoint(task='choose', port='value')},
    )
    for condition in (True, False):
        probe = run_mod.GraphRun(branched, given={'x': 2, 'y': 3, 'condition': condition})
        assert probe.step().starts == []
        assert probe.outputs() == {'result': 5}
        child = probe.scopes['root']['frames']['choose'][0]
        assert probe.scopes[child]['given'] == {'value': 5}
        assert not isinstance(probe.scopes[child]['given']['value'], Node)
        orm_probe = run_mod.GraphRun(branched, given={'x': Int(2), 'y': Int(3), 'condition': Bool(condition)})
        assert orm_probe.step().starts == []
        assert orm_probe.outputs() == {'result': 5}
        orm_child = orm_probe.scopes['root']['frames']['choose'][0]
        assert orm_probe.scopes[orm_child]['given'] == {'value': 5}
        assert not isinstance(orm_probe.scopes[orm_child]['given']['value'], Node)
        launch = GraphProcess._launch_inputs(branched, {'x': 2, 'y': 3, 'condition': condition})
        _, failed_node = run_get_node(GraphProcess, **launch)
        assert failed_node.is_failed and not failed_node.is_excepted
        assert failed_node.exit_status == 401  # ERROR_GRAPH_RUNTIME per the graph runtime exit-code spec.
        assert '@task' in (failed_node.exit_message or '')

    materialized = _graph(
        [op_add, _process('first', program_tasks.add)],
        {'x': (int,), 'y': (int,), 'z': (int,)},
        [Dependency('total', 'first', source_port='result', target_port='x')],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')], 'z': [Route('first', 'y')]},
        {'result': Endpoint(task='first', port='result')},
    )
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(materialized, {'x': 2, 'y': 3, 'z': 4}))
    assert node.is_finished_ok
    assert outputs['result'].value == 9
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_no_task_loop_control_graph_has_root_only() -> None:
    """A loop settled without entering dispatches nothing and creates no data."""
    from aiida.engine.processes.graphs.process import GraphProcess

    body = _graph(
        [],
        {'value': (int,), 'condition': (bool,)},
        [],
        {},
        {'value': Endpoint(task=None, port='value'), 'condition': Endpoint(task=None, port='condition')},
        identifier='inline-test-body',
    )
    loop = LoopControl(name='iterate', inputs={}, body=body, condition_port='condition', max_iterations=5)
    graph = _graph(
        [loop],
        {'value': (int,), 'condition': (bool,)},
        [],
        {'value': [Route('iterate', 'value')], 'condition': [Route('iterate', 'condition')]},
        {'result': Endpoint(task='iterate', port='value')},
    )
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(graph, {'value': 3, 'condition': False}))
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    assert node.called == []
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_checkpoint_persister_keeps_op_values_with_pending_task() -> None:
    """The daemon checkpoint keeps inline values beside a pending real task without reevaluation."""
    from aiida.engine.persistence import AiidaCheckpointPersister
    from aiida.manage import get_manager

    calls: list[t.Any] = []
    real_evaluate = run_mod.evaluate_operation

    def counting(operation: t.Any, inputs: t.Any) -> t.Any:
        calls.append((operation, dict(inputs)))
        return real_evaluate(operation, inputs)

    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    first = _process('first', program_tasks.add)
    graph = _graph(
        [op_add, first],
        {'x': (int,), 'y': (int,), 'z': (int,)},
        [Dependency('total', 'first', source_port='result', target_port='x')],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')], 'z': [Route('first', 'y')]},
        {'result': Endpoint(task='first', port='result')},
    )
    runner = get_manager().create_runner(communicator=None)
    try:
        from aiida.engine.processes.graphs.process import GraphProcess

        process = GraphProcess(inputs=GraphProcess._launch_inputs(graph, {'x': 2, 'y': 3, 'z': 4}), runner=runner)
        restores = None
        run_mod.evaluate_operation = counting  # type: ignore[method-assign]
        try:
            assert [start.instance for start in process._run_state.step().starts] == ['first']
            assert len(calls) == 1
            assert process._run_state.scopes['root']['values'] == {'total': 5}
            _, completed = program_tasks.add.run_get_node(x=5, y=4)
            assert completed.pk is not None
            process._run_state.started('first', completed.pk)
            assert process._run_state.pending == {'first': completed.pk}
            persister = AiidaCheckpointPersister()
            persister.save_checkpoint(process)
            loaded = persister.load_checkpoint(process.node.pk)
            from aiida.common.loaders import get_object_loader
            from aiida.engine.processes.persistence import CheckpointContext

            restores = loaded.decode(CheckpointContext(loader=get_object_loader(), runner=runner, loop=runner.loop))
            assert restores._run_state.to_dict() == process._run_state.to_dict()
            assert restores._run_state.scopes['root']['values'] == {'total': 5}
            assert restores._run_state.pending == {'first': completed.pk}
            assert restores._run_state.step().starts == []
            assert len(calls) == 1
            restores._run_state.completed('first', completed.pk)
            assert restores._run_state.outputs()['result'].value == 9
        finally:
            run_mod.evaluate_operation = real_evaluate  # type: ignore[method-assign]
            process.close()
            if restores is not None:
                restores.close()
    finally:
        runner.close()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_old_checkpoint_without_values_loads_with_defaults() -> None:
    """Checkpoints saved before `values` existed restore with empty operation state."""
    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    graph = _graph(
        [op_add],
        {'x': (int,), 'y': (int,)},
        [],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')]},
        {'answer': Endpoint(task='total', port='result')},
    )
    state = run_mod.GraphRun(graph, given={'x': 1, 'y': 2})
    state.step()
    saved = state.to_dict()
    assert saved['scopes']['root']['values'] == {'total': 3}
    stripped = deepcopy(saved)
    for scope in stripped['scopes'].values():
        scope.pop('values', None)
    restored = run_mod.GraphRun.from_dict(graph, dict(state.given), stripped)
    assert restored.scopes['root']['values'] == {}
    restored.step()
    assert restored.scopes['root']['values'] == {'total': 3}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_branch_loop_and_subgraph_scopes_share_inline_values() -> None:
    """Inline values flow through subgraph, branch, and loop boundaries."""
    inner_op = _inline('doubled', 'mul', {'left': (int,), 'right': (int,)}, literals={'right': 2})
    inner = _graph(
        [inner_op],
        {'value': (int,)},
        [],
        {'value': [Route('doubled', 'left')]},
        {'result': Endpoint(task='doubled', port='result')},
        identifier='inline-inner',
    )
    sub = SubgraphTask(name='nested', inputs={}, body=inner)
    check = _inline('positive', 'gt', {'left': (int,), 'right': (int,)}, out_types=(Bool,), literals={'right': 0})
    taken_op = _inline('taken', 'add', {'left': (int,), 'right': (int,)}, literals={'right': 100})
    taken = _graph(
        [taken_op],
        {'value': (int,)},
        [],
        {'value': [Route('taken', 'left')]},
        {'value': Endpoint(task='taken', port='result')},
        identifier='inline-taken',
    )
    otherwise_op = _inline('otherwise', 'add', {'left': (int,), 'right': (int,)}, literals={'right': 1})
    otherwise = _graph(
        [otherwise_op],
        {'value': (int,)},
        [],
        {'value': [Route('otherwise', 'left')]},
        {'value': Endpoint(task='otherwise', port='result')},
        identifier='inline-otherwise',
    )
    branch = BranchControl(name='choose', inputs={}, body=taken, otherwise=otherwise)
    loop_body_op = _inline('step', 'add', {'left': (int,), 'right': (int,)}, literals={'right': 1})
    loop_done_op = _inline('done', 'ne', {'left': (int,), 'right': (int,)}, out_types=(Bool,), literals={'right': 105})
    loop_body = _graph(
        [loop_body_op, loop_done_op],
        {'value': (int,), 'condition': (bool,)},
        [Dependency('step', 'done', source_port='result', target_port='left')],
        {'value': [Route('step', 'left')]},
        {'value': Endpoint(task='step', port='result'), 'condition': Endpoint(task='done', port='result')},
        identifier='inline-loop-body',
    )
    loop = LoopControl(name='iterate', inputs={}, body=loop_body, condition_port='condition', max_iterations=3)
    graph = _graph(
        [sub, check, branch, loop],
        {'x': (int,), 'go': (bool,)},
        [
            Dependency('nested', 'positive', source_port='result', target_port='left'),
            Dependency('nested', 'choose', source_port='result', target_port='value'),
            Dependency('positive', 'choose', source_port='result', target_port='condition'),
            Dependency('choose', 'iterate', source_port='value', target_port='value'),
        ],
        {'x': [Route('nested', 'value')], 'go': [Route('iterate', 'condition')]},
        {'result': Endpoint(task='iterate', port='value')},
    )
    state = run_mod.GraphRun(graph, given={'x': 2, 'go': True})
    state.step()
    assert state.outputs() == {'result': 105}
    branch_scopes = state.scopes['root']['frames']['choose']
    assert len(branch_scopes) == 1
    assert state.scopes[branch_scopes[0]]['selector'] == 'taken'
    loop_scopes = state.scopes['root']['frames']['iterate']
    assert len(loop_scopes) == 1
    assert state.scopes[loop_scopes[0]]['values'] == {'step': 105, 'done': False}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_graph_mapped_map_collects_inline_results() -> None:
    """Graph-mapped items evaluate inline per element; the collector still creates data."""
    from aiida.engine.processes.graphs.process import GraphProcess

    item_op = _inline('doubled', 'mul', {'left': (int,), 'right': (int,)}, literals={'right': 10})
    body = _graph(
        [item_op],
        {'elem': (int,)},
        [],
        {'elem': [Route('doubled', 'left')]},
        {'result': Endpoint(task='doubled', port='result')},
        identifier='inline-map-body',
    )
    mapped = MapControl(name='over', inputs={}, spec=None, body=body, container='list')
    graph = _graph(
        [mapped],
        {'values': DataList},
        [],
        {'values': [Route('over', 'collection')]},
        {'result': Endpoint(task='over', port='result')},
    )
    collection = DataList([Int(1), Int(2), Int(3)])
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(graph, {'values': collection}))
    assert node.is_finished_ok
    assert sorted(member.value for member in outputs['result']) == [10, 20, 30]
    # The graph itself creates nothing: the `DataList` carries a `CREATE` link from its
    # collector calculation while the graph only returns that existing container.
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    collectors = [child for child in node.called if child.process_label == '_collect_list']
    assert len(collectors) == 1
    assert collectors[0].base.links.get_outgoing(link_type=LinkType.CREATE).all() != []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_max_iterations_counts_inline_only_progress() -> None:
    """An inline loop that never terminates raises after its iteration budget."""
    tick = _inline('tick', 'add', {'left': (int,), 'right': (int,)}, literals={'right': 1})
    body = _graph(
        [tick],
        {'value': (int,), 'condition': (bool,)},
        [],
        {'value': [Route('tick', 'left')]},
        {'value': Endpoint(task='tick', port='result'), 'condition': Endpoint(task=None, port='condition')},
        identifier='inline-loop-always',
    )
    loop = LoopControl(name='iterate', inputs={}, body=body, condition_port='condition', max_iterations=2)
    graph = _graph(
        [loop],
        {'value': (int,), 'condition': (bool,)},
        [],
        {'value': [Route('iterate', 'value')], 'condition': [Route('iterate', 'condition')]},
        {'result': Endpoint(task='iterate', port='value')},
    )
    state = run_mod.GraphRun(graph, given={'value': 0, 'condition': True})
    with pytest.raises(GraphMaxIterationsError, match='exceeded 2 iterations'):
        for _ in range(5):
            state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_loop_max_iterations_exhaustion_fails_graph() -> None:
    """An inline loop that never terminates fails the graph instead of excepting it."""
    from aiida.engine.processes.graphs.process import GraphProcess

    tick = _inline('tick', 'add', {'left': (int,), 'right': (int,)}, literals={'right': 1})
    body = _graph(
        [tick],
        {'value': (int,), 'condition': (bool,)},
        [],
        {'value': [Route('tick', 'left')]},
        {'value': Endpoint(task='tick', port='result'), 'condition': Endpoint(task=None, port='condition')},
        identifier='inline-loop-always',
    )
    loop = LoopControl(name='iterate', inputs={}, body=body, condition_port='condition', max_iterations=2)
    graph = _graph(
        [loop],
        {'value': (int,), 'condition': (bool,)},
        [],
        {'value': [Route('iterate', 'value')], 'condition': [Route('iterate', 'condition')]},
        {'result': Endpoint(task='iterate', port='value')},
    )
    _, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(graph, {'value': 0, 'condition': True}))
    assert node.is_failed and not node.is_excepted
    assert node.exit_status == 401  # ERROR_GRAPH_RUNTIME per the graph runtime exit-code spec.
    assert 'exceeded 2 iterations' in (node.exit_message or '')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_namespace_outputs_return_existing_nodes() -> None:
    """Nested namespaces regroup existing input and task nodes without creating data."""
    from aiida.engine.processes.graphs.process import GraphProcess

    first = _process('first', program_tasks.add)
    graph = _graph(
        [first],
        {'x': (int,), 'y': (int,)},
        [],
        {'x': [Route('first', 'x')], 'y': [Route('first', 'y')]},
        t.cast(
            t.Any,
            {
                'outer': {
                    'computed': Endpoint(task='first', port='result'),
                    'kept': Endpoint(task=None, port='x'),
                }
            },
        ),
    )
    outputs, node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(graph, {'x': 2, 'y': 3}))
    assert node.is_finished_ok
    assert outputs['outer']['computed'].value == 5
    assert outputs['outer']['kept'].value == 2
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_inline_primitive_leaf_rejected_with_nested_path() -> None:
    """A computed primitive nested inside a namespace fails naming its dotted path."""
    from aiida.engine.processes.graphs.process import GraphProcess
    from aiida.orm import Node

    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    first = _process('first', program_tasks.add)
    graph = _graph(
        [op_add, first],
        {'x': (int,), 'y': (int,), 'z': (int,)},
        [Dependency('total', 'first', source_port='result', target_port='x')],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')], 'z': [Route('first', 'y')]},
        t.cast(
            t.Any,
            {
                'outer': {
                    'good': Endpoint(task='first', port='result'),
                    'bad': Endpoint(task='total', port='result'),
                }
            },
        ),
    )
    probe = run_mod.GraphRun(graph, given={'x': 2, 'y': 3, 'z': 4})
    assert [start.instance for start in probe.step().starts] == ['first']
    _, completed = program_tasks.add.run_get_node(x=5, y=4)
    assert completed.pk is not None
    probe.started('first', completed.pk)
    probe.completed('first', completed.pk)
    resolved = probe.outputs()
    assert resolved['outer']['bad'] == 5
    assert isinstance(resolved['outer']['good'], Node)
    _, failed_node = run_get_node(GraphProcess, **GraphProcess._launch_inputs(graph, {'x': 2, 'y': 3, 'z': 4}))
    assert failed_node.is_failed and not failed_node.is_excepted
    assert failed_node.exit_status == 401  # ERROR_GRAPH_RUNTIME per the graph runtime exit-code spec.
    assert 'outer.bad' in (failed_node.exit_message or '')
    assert '@task' in (failed_node.exit_message or '')


@pytest.mark.usefixtures('aiida_profile_clean')
def test_failed_real_task_blocks_downstream_but_keeps_inline_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed task reports the placement while completed inline values persist."""
    op_add = _inline('total', 'add', {'left': (int,), 'right': (int,)})
    bad = _process('bad', program_tasks.add)
    graph = _graph(
        [op_add, bad],
        {'x': (int,), 'y': (int,), 'z': (int,)},
        [Dependency('total', 'bad', source_port='result', target_port='x')],
        {'x': [Route('total', 'left')], 'y': [Route('total', 'right')], 'z': [Route('bad', 'y')]},
        {'result': Endpoint(task='bad', port='result')},
        identifier='inline-failure',
    )
    state = run_mod.GraphRun(graph, given={'x': 2, 'y': 3, 'z': 4})
    assert [start.instance for start in state.step().starts] == ['bad']

    class _Failed:
        is_finished_ok = False

    monkeypatch.setattr(run_mod, 'load_node', lambda _pk: _Failed())
    state.started('bad', 111)
    state.completed('bad', 111)
    assert state.failed == ['bad']
    assert state.scopes['root']['values'] == {'total': 5}
    assert state.step().starts == []


def _const(name: str, value: t.Any, types: tuple[type, ...]) -> InlineOperation:
    """Return a constant placement binding one scalar literal."""
    leaf = LeafShape(types=types)
    return InlineOperation(
        name=name,
        inputs={'value': value},
        operation='const',
        input_shape=NamespaceShape(fields=(('value', leaf),)),
        result_shape=leaf,
    )


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bound_scalars_run_through_task() -> None:
    """Bound integers wire into tasks and return task outputs."""
    from tests.engine.processes.graphs.programs import constants

    outputs, node = run_get_node(constants.bound_scalars, value=5)
    assert node.is_finished_ok
    assert outputs['result'].value == 5
    outputs, node = run_get_node(constants.aliased_constant, value=0)
    assert node.is_finished_ok
    assert outputs['result'].value == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_const_fallback_selects_side() -> None:
    """The taken side, constant or task, feeds the downstream task."""
    from tests.engine.processes.graphs.programs import constants

    outputs, node = run_get_node(constants.const_fallback, value=5, flag=True)
    assert node.is_finished_ok
    assert outputs['result'].value == 11
    outputs, node = run_get_node(constants.const_fallback, value=5, flag=False)
    assert node.is_finished_ok
    assert outputs['result'].value == 5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_bound_mode_runs_both_branches() -> None:
    """A bound string wires through branch regions into task arguments."""
    from tests.engine.processes.graphs.programs import constants

    for flag in (True, False):
        outputs, node = run_get_node(constants.bound_mode, value=3, flag=flag)
        assert node.is_finished_ok
        assert outputs['result'].value == 6


@pytest.mark.usefixtures('aiida_profile_clean')
def test_looped_counter_runs_to_completion() -> None:
    """A bound counter carries across iterations and survives zero iterations."""
    from tests.engine.processes.graphs.programs import constants

    outputs, node = run_get_node(constants.looped_counter, value=1, rounds=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    outputs, node = run_get_node(constants.looped_counter, value=4, rounds=0)
    assert node.is_finished_ok
    assert outputs['result'].value == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_nested_const_threads_control_state() -> None:
    """A nested graph returns orchestration state the caller consumes in a task."""
    from tests.engine.processes.graphs.programs import constants

    outputs, node = run_get_node(constants.nested_const, value=5)
    assert node.is_finished_ok
    assert outputs['result'].value == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_none_condition_fails_loudly() -> None:
    """A bound `None` is a value, not a decision: branching on it fails instead of coercing."""
    from tests.engine.processes.graphs.programs import constants

    state = run_mod.GraphRun(compile_graph(constants.none_condition), given={'value': 2})
    with pytest.raises(GraphRuntimeError, match='must be a `bool` or `Bool`'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_const_creates_no_nodes_or_links() -> None:
    """Constants leave no provenance: only task runs create nodes under the graph."""
    from tests.engine.processes.graphs.programs import constants

    outputs, node = run_get_node(constants.looped_counter, value=1, rounds=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    labels = [entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()]
    assert labels
    assert all(not label.startswith('constant') for label in labels)
    roots = set()
    for label in labels:
        leaf = label.split('__')[-1]
        head, _, tail = leaf.rpartition('_')
        roots.add(head if tail.isdigit() else leaf)
    assert roots <= {'add', 'is_positive', 'decrement'}


def test_const_values_round_trip_through_run_state() -> None:
    """Checkpointed constant results restore without the bound literal revalidating."""
    const = _const('attempts', 0, (int,))
    first = _process('first', program_tasks.add)
    graph = _graph(
        [const, first],
        {'x': (int,)},
        [Dependency('attempts', 'first', source_port='result', target_port='y')],
        {'x': [Route('first', 'x')]},
        {'result': Endpoint(task='first', port='result')},
    )
    state = run_mod.GraphRun(graph, given={'x': 2})
    assert [start.instance for start in state.step().starts] == ['first']
    assert state.scopes['root']['values'] == {'attempts': 0}
    restored = run_mod.GraphRun.from_dict(graph, dict(state.given), deepcopy(state.to_dict()))
    assert restored.scopes['root']['values'] == {'attempts': 0}
    assert restored.step().starts == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_checkpoint_persister_keeps_const_values_without_reevaluation() -> None:
    """The daemon checkpoint keeps bound literals beside a pending task without reevaluating."""
    from aiida.engine.persistence import AiidaCheckpointPersister
    from aiida.manage import get_manager

    calls: list[t.Any] = []
    real_evaluate = run_mod.evaluate_operation

    def counting(operation: t.Any, inputs: t.Any) -> t.Any:
        calls.append((operation, dict(inputs)))
        return real_evaluate(operation, inputs)

    const = _const('attempts', 0, (int,))
    first = _process('first', program_tasks.add)
    graph = _graph(
        [const, first],
        {'x': (int,)},
        [Dependency('attempts', 'first', source_port='result', target_port='y')],
        {'x': [Route('first', 'x')]},
        {'result': Endpoint(task='first', port='result')},
    )
    runner = get_manager().create_runner(communicator=None)
    try:
        from aiida.engine.processes.graphs.process import GraphProcess

        process = GraphProcess(inputs=GraphProcess._launch_inputs(graph, {'x': 2}), runner=runner)
        restores = None
        run_mod.evaluate_operation = counting  # type: ignore[method-assign]
        try:
            assert [start.instance for start in process._run_state.step().starts] == ['first']
            assert calls == [('const', {'value': 0})]
            assert process._run_state.scopes['root']['values'] == {'attempts': 0}
            _, completed = program_tasks.add.run_get_node(x=2, y=0)
            assert completed.pk is not None
            process._run_state.started('first', completed.pk)
            persister = AiidaCheckpointPersister()
            persister.save_checkpoint(process)
            loaded = persister.load_checkpoint(process.node.pk)
            from aiida.common.loaders import get_object_loader
            from aiida.engine.processes.persistence import CheckpointContext

            restores = loaded.decode(CheckpointContext(loader=get_object_loader(), runner=runner, loop=runner.loop))
            assert restores._run_state.to_dict() == process._run_state.to_dict()
            assert restores._run_state.scopes['root']['values'] == {'attempts': 0}
            assert restores._run_state.step().starts == []
            assert calls == [('const', {'value': 0})]
            restores._run_state.completed('first', completed.pk)
            assert restores._run_state.outputs()['result'].value == 2
        finally:
            run_mod.evaluate_operation = real_evaluate  # type: ignore[method-assign]
            process.close()
            if restores is not None:
                restores.close()
    finally:
        runner.close()
