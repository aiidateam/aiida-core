###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build and run source-only graphs, including their fixed namespace contracts."""

from dataclasses import replace

import pytest

from aiida.common.exceptions import MissingRequiredInputsError
from aiida.common.links import LinkType
from aiida.engine import (
    GraphHandle,
    GraphProcess,
    GraphSpec,
    PortModel,
    UnsupportedSyntax,
    graph,
    run_get_node,
    submit,
    task,
)
from aiida.engine.processes.graphs.run import GraphRun
from aiida.engine.processes.graphs.shapes import load_shape
from aiida.engine.processes.graphs.spec import (
    BranchControl,
    Dependency,
    LoopControl,
    SubgraphTask,
    TaskSpec,
)
from aiida.engine.processes.persistence import CheckpointPayload
from aiida.orm import Dict, GraphNode, Int

pytestmark = pytest.mark.requires_broker


@task
def add(x: int, y: int) -> int:
    return x + y


@task
def subtract(x: int) -> int:
    return x - 1


@task
def positive(x: int) -> bool:
    return x > 0


@task(outputs=('sum', 'product'))
def arithmetic(x: int, y: int) -> tuple[int, int]:
    return x + y, x * y


@task
def broken(x: int) -> int:
    raise ValueError('deliberately failed')


@task
def wrong_output(x: int) -> int:
    return 'wrong'


@task
def side_effect(x: int) -> None:
    assert x > 0


class Settings(PortModel):
    count: int = 2
    nullable: int | None


class Configuration(PortModel):
    settings: Settings
    label: str = 'test'


@task
def read_config(config: Configuration) -> int:
    return config.settings.count


@graph
def chain(x: int, y: int) -> int:
    first = add(x=x, y=y)
    return add(x=first, y=y)


@graph
def outer(x: int, y: int) -> int:
    inner = chain(x=x, y=y)
    return add(x=inner, y=x)


@graph
def ordered(x: int) -> int:
    first = side_effect(x=x)
    second = add(x=x, y=1, after=first)
    return second


@graph
def multiple_ordered(x: int) -> int:
    first = side_effect(x=x)
    second = side_effect(x=x)
    third = add(x=x, y=1, after=(first, second))
    return third


@graph
def named(x: int, y: int):
    pair = arithmetic(x=x, y=y)
    return {'total': pair.sum, 'product': pair.product}


@graph
def choose(x: int, flag: bool) -> int:
    if flag:
        chosen = add(x=x, y=1)
    else:
        chosen = add(x=x, y=2)
    return add(x=chosen, y=x)


@graph
def count(x: int, keep_going: bool) -> int:
    while keep_going:
        x = subtract(x=x)
        keep_going = positive(x=x)
    return x


@graph
def whole(config: Configuration) -> int:
    return read_config(config=config)


@graph
def selected(config: Configuration) -> int:
    return add(x=config.settings.count, y=1)


@graph
def wired(config: Configuration) -> int:
    chosen = add(x=config.settings.count, y=1)
    return read_config(config={'settings': {'count': chosen, 'nullable': config.settings.nullable}})


@graph
def namespace_branch(config: Configuration, flag: bool) -> int:
    if flag:
        chosen = read_config(config=config)
    else:
        chosen = add(x=config.settings.count, y=1)
    return chosen


@graph
def named_outer(x: int, y: int):
    pair = named(x=x, y=y)
    return {'sum': pair.total, 'product': pair.product}


@graph(identifier='custom-label')
def labelled(x: int) -> int:
    return add(x=x, y=1)


@graph
def namespace_loop(config: Configuration, x: int, keep_going: bool) -> int:
    while keep_going:
        x = read_config(config=config)
        x = add(x=x, y=3)
        keep_going = positive(x=0)
    return x


@graph
def namespace_output(config: Configuration) -> Configuration:
    return config


@graph
def failed(x: int) -> int:
    first = broken(x=x)
    return add(x=first, y=1)


@graph
def recursive(x: int) -> int:
    return recursive(x=x)


@graph
def arbitrary(x: int) -> int:
    print('a graph body must not run')
    return add(x=x, y=1)


@graph
def fanout(x: int) -> int:
    for item in x:
        value = subtract(x=item)
    return value


@graph
def unbound(x: int) -> int:
    return add(x=x, y=missing)  # noqa: F821 - unbound names must fail at lowering


@graph
def keyword_only(*, x: int) -> int:
    return add(x=x, y=1)


@graph
def wrong_type(x: str) -> int:
    return add(x=x, y=1)


@graph
def nested_outputs(x: int):
    value = add(x=x, y=1)
    return {'outer': {'inner': value}}


def test_public_api_is_source_only():
    from aiida import engine

    for excluded in (
        'graph_execution',
        'task_execution',
        'graph_source',
        'task_source',
        'Many',
        'each',
        'select',
        'monitor',
        'handler',
        'rerun_from',
        'task_from_builder',
        'task_from_workchain',
    ):
        assert not hasattr(engine, excluded)
    assert isinstance(chain, GraphHandle)
    with pytest.raises(TypeError, match='launch'):
        chain(x=1, y=2)


def test_build_does_not_invoke_graph_or_task_bodies(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError('must not invoke a task while lowering')

    monkeypatch.setattr(add.process_class, '_func', staticmethod(fail))
    spec = chain.build()
    assert spec.task_names == ('add', 'add_2')
    assert spec.dependencies == (Dependency('add', 'add_2', 'result', 'x'),)
    assert spec.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}
    assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


@pytest.mark.parametrize(
    'handle, reason',
    [
        (recursive, 'Recursive graph call'),
        (arbitrary, 'only single-name assignments'),
        (fanout, 'only single-name assignments'),
        (unbound, 'unbound name'),
        (keyword_only, 'only ordinary positional parameters'),
        (nested_outputs, 'unsupported expression'),
    ],
)
def test_rejects_unsupported_source_with_location(handle, reason):
    with pytest.raises(UnsupportedSyntax, match=reason):
        handle.build()


def test_rejects_incompatible_boundary_types():
    with pytest.raises(ValueError, match='incompatible types'):
        wrong_type.build()


def test_builds_control_flow():
    assert isinstance(outer.build().tasks[0], SubgraphTask)
    assert isinstance(choose.build().tasks[0], BranchControl)
    assert isinstance(count.build().tasks[0], LoopControl)
    assert set(count.build().tasks[0].body.outputs) == {'x', 'keep_going'}


@pytest.mark.parametrize(
    'handle, inputs, expected',
    [
        (chain, {'x': 2, 'y': 3}, {'result': 8}),
        (outer, {'x': 2, 'y': 3}, {'result': 10}),
        (named, {'x': 2, 'y': 3}, {'total': 5, 'product': 6}),
        (named_outer, {'x': 2, 'y': 3}, {'sum': 5, 'product': 6}),
        (labelled, {'x': 2}, {'result': 3}),
        (ordered, {'x': 2}, {'result': 3}),
        (multiple_ordered, {'x': 2}, {'result': 3}),
        (choose, {'x': 2, 'flag': True}, {'result': 5}),
        (choose, {'x': 2, 'flag': False}, {'result': 6}),
        (count, {'x': 3, 'keep_going': True}, {'x': 0}),
    ],
)
def test_runs_source_graph(handle, inputs, expected):
    outputs, node = run_get_node(handle, **inputs)
    assert node.is_finished_ok, node.exit_message
    assert isinstance(node, GraphNode)
    assert node.process_label == handle.identifier
    assert {name: value.value for name, value in outputs.items()} == expected


@pytest.mark.parametrize('handle, expected', [(whole, 2), (selected, 3), (wired, 3)])
def test_input_namespace_defaults_and_field_wiring(handle, expected):
    original = Int(2)
    outputs, node = run_get_node(handle, config={'settings': {'count': original, 'nullable': None}})
    assert node.is_finished_ok, node.exit_message
    assert next(iter(outputs.values())).value == expected
    assert node.inputs.graph_inputs.config.settings.count.uuid == original.uuid
    assert node.inputs.graph_inputs.config.label.value == 'test'


@pytest.mark.parametrize('flag, expected', [(True, 2), (False, 3)])
def test_branch_preserves_namespace_contract(flag, expected):
    outputs, node = run_get_node(namespace_branch, config=Configuration(settings=Settings(nullable=None)), flag=flag)
    assert node.is_finished_ok, node.exit_message
    assert outputs['result'].value == expected


def test_missing_inputs_are_aggregated():
    with pytest.raises(MissingRequiredInputsError) as caught:
        whole.get_launch_inputs(config={'settings': {}})
    assert 'config.settings.nullable' in str(caught.value)
    with pytest.raises(MissingRequiredInputsError):
        chain.get_launch_inputs()


def test_provenance_links_and_static_validation():
    original = Int(2)
    outputs, node = run_get_node(chain, x=original, y=3)
    children = {
        entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    }
    assert children['add'].inputs.x.uuid == original.uuid
    assert children['add_2'].inputs.x.uuid == children['add'].outputs.result.uuid
    assert outputs['result'].uuid == children['add_2'].outputs.result.uuid
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    with pytest.raises(TypeError, match='unexpected keyword argument'):
        chain.get_launch_inputs(x=1, y=2, surprise=3)


def test_ordering_is_a_scheduler_dependency():
    state = GraphRun(ordered.build(), given={'x': Int(2)})
    assert [start.instance for start in state.step().starts] == ['side_effect']
    _, completed = side_effect.run_get_node(x=2)
    state.started('side_effect', completed.pk)
    state.completed('side_effect', completed.pk)
    assert [start.instance for start in state.step().starts] == ['add']


def test_task_failure_does_not_dispatch_downstream():
    outputs, node = run_get_node(failed, x=2)
    assert node.exit_status == 400
    assert outputs == {}
    assert len(node.called) == 1


def test_spec_version_and_unknown_task_kind_rejection():
    data = chain.build().to_dict()
    data['version'] = '99'
    with pytest.raises(ValueError, match='version'):
        GraphSpec.from_dict(data)
    task_data = add.task_spec.to_dict()
    task_data['version'] = '99'
    with pytest.raises(ValueError, match='version'):
        TaskSpec.from_dict(task_data)
    data = chain.build().to_dict()
    data['tasks'][0]['kind'] = 'map'
    with pytest.raises(ValueError, match='unsupported graph task kind'):
        GraphSpec.from_dict(data)
    with pytest.raises(ValueError, match='Unknown graph value shape'):
        load_shape({'kind': 'many', 'required': True})


def test_cyclic_and_invalid_ordering_dependencies():
    spec = chain.build()
    with pytest.raises(ValueError, match='cycle'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('add_2', 'add')))
    with pytest.raises(ValueError, match='both ports'):
        Dependency('add', 'add_2', source_port='result')


def test_raw_graph_launch_uses_fixed_boundary_contract():
    outputs, node = run_get_node(GraphProcess, graph=Dict(dict=chain.build().to_dict()), graph_inputs={'x': 2, 'y': 3})
    assert node.is_finished_ok
    assert outputs['result'].value == 8
    with pytest.raises(MissingRequiredInputsError):
        GraphProcess(inputs={'graph': Dict(dict=chain.build().to_dict()), 'graph_inputs': {'x': 2}})


def test_checkpoint_preserves_boundary_node_and_runtime_values():
    original = Int(2)
    process = GraphProcess(inputs=chain.get_launch_inputs(x=original, y=3))
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


def test_checkpointed_scheduler_does_not_repeat_completed_tasks():
    state = GraphRun(chain.build(), given={'x': Int(2), 'y': Int(3)})
    assert [start.instance for start in state.step().starts] == ['add']
    _, completed = add.run_get_node(x=2, y=3)
    state.started('add', completed.pk)
    state.completed('add', completed.pk)
    restored = GraphRun.from_dict(state.graph, state.given, state.to_dict())
    assert [start.instance for start in restored.step().starts] == ['add_2']


def no_output_declaration(x: int):
    return x


def dynamic_inputs(**kwargs) -> int:
    return 1


def structured_output(x: int) -> Configuration:
    return Configuration(settings=Settings(nullable=x))


def unresolved_annotation(x: 'missing_type') -> int:  # noqa: F821 - deliberately unresolved
    return x


@pytest.mark.parametrize(
    'function, message',
    [
        (no_output_declaration, 'return annotation'),
        (dynamic_inputs, 'fixed inputs'),
        (structured_output, 'output namespaces'),
        (unresolved_annotation, 'Cannot resolve type hints'),
    ],
)
def test_task_registration_rejects_excluded_contracts(function, message):
    with pytest.raises(TypeError, match=message):
        task(function)


def test_task_rejects_local_definitions_and_process_classes():
    def local(x: int) -> int:
        return x

    with pytest.raises(UnsupportedSyntax, match='module scope'):
        task(local)
    with pytest.raises(UnsupportedSyntax, match='Python functions'):
        task(GraphProcess)
    with pytest.raises(UnsupportedSyntax, match='leaf'):
        namespace_output.build()


def test_invalid_output_is_rejected_at_runtime():
    with pytest.raises(ValueError, match='not of the right type'):
        run_get_node(wrong_output, x=1)


def test_loop_preserves_namespace_input():
    outputs, node = run_get_node(namespace_loop, config={'settings': {'nullable': None}}, x=3, keep_going=True)
    assert node.is_finished_ok, node.exit_message
    assert outputs['x'].value == 5


def test_tasks_are_cached_without_partial_rerun_support():
    from aiida.manage.caching import enable_caching

    with enable_caching(identifier='*'):
        _, first = run_get_node(chain, x=11, y=2)
        outputs, again = run_get_node(chain, x=11, y=2)
    assert first.is_finished_ok and again.is_finished_ok
    assert outputs['result'].value == 15
    assert all(not child.base.caching.is_created_from_cache for child in first.called)
    assert all(child.base.caching.is_created_from_cache for child in again.called)


@pytest.mark.parametrize(
    'handle, inputs, output, expected',
    [
        (outer, {'x': 2, 'y': 3}, 'result', 10),
        (choose, {'x': 2, 'flag': False}, 'result', 6),
        (count, {'x': 3, 'keep_going': True}, 'x', 0),
        (whole, {'config': {'settings': {'nullable': None}}}, 'result', 2),
    ],
)
def test_daemon_submission_uses_importable_tasks(submit_and_await, handle, inputs, output, expected):
    node = submit_and_await(submit(handle, **inputs), timeout=90)
    assert node.is_finished_ok, node.exit_message
    assert node.outputs[output].value == expected
    assert node.inputs.graph.get_dict() == handle.build().to_dict()
