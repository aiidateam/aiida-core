###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Integration of pure inline collection expressions with graph execution.

Collections enter as graph inputs (``list[int]``, ``dict[str, int]``,
``list[Int]``, ``dict[str, Int]``) or as task-produced values whose element
hints flow into the expression; comprehensions and indexing evaluate inline in
one placement while every root output comes back through an ``@task`` consumer
with normal provenance. Collaborators: the ``expressions`` compiler and shape
contracts, ``lowering`` wiring ``InlineOperation(operation='expression')``
placements, the ``run`` scheduler evaluating them, and ``GraphIR`` JSON
round-tripping the templates.
"""

import json
import typing as t

import pytest

from aiida.common.exceptions import GraphLanguageError, GraphRuntimeError, GraphTypeCheckError, InvalidOperation
from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph, graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.run import GraphRun
from aiida.orm import Int
from aiida.orm.nodes.process.process import ProcessNode
from tests.engine.processes.graphs.programs import collection_expressions

pytestmark = pytest.mark.presto

_SERIALIZED = [
    pytest.param(False, id='declaration'),
    pytest.param(True, id='serialized'),
]

_ACCEPTED: list[GraphHandle] = [
    collection_expressions.scaled_filtered,
    collection_expressions.nested_pairs,
    collection_expressions.orm_bumped,
    collection_expressions.mapped_bumped,
    collection_expressions.plain_scaled_mapping,
    collection_expressions.head_plus_last,
    collection_expressions.keyed_forward,
    collection_expressions.first_member,
    collection_expressions.packed_scaled,
    collection_expressions.orm_packed_bumped,
    collection_expressions.mapping_packed_doubled,
    collection_expressions.shadowed_target,
    collection_expressions.counted_keys,
    collection_expressions.select_member,
]


def _inputs(raw: dict[str, t.Any], orm: tuple[str, ...] = ()) -> dict[str, t.Any]:
    """Return launch inputs, wrapping the named collections in owned ``Int`` members."""
    inputs = dict(raw)
    for key in orm:
        value = inputs[key]
        if isinstance(value, list):
            inputs[key] = [Int(item) for item in value]
        else:
            inputs[key] = {name: Int(item) for name, item in value.items()}
    return inputs


def _launch(
    declaration: GraphHandle, inputs: dict[str, t.Any], *, serialized: bool
) -> tuple[dict[str, t.Any], ProcessNode]:
    """Run a graph from its declaration or from its JSON round-tripped template."""
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(compile_graph(declaration).to_dict())))
        return run_get_node(GraphProcess, **GraphProcess._launch_inputs(spec, inputs))
    outputs, node = run_get_node(declaration, **inputs)
    assert isinstance(node, ProcessNode)
    return outputs, node


@pytest.mark.parametrize('declaration', _ACCEPTED)
def test_collection_graphs_build(declaration: GraphHandle) -> None:
    """Every collection graph lowers, and its template survives a JSON round trip."""
    assert declaration.build() is None
    spec = compile_graph(declaration)
    assert spec.version == '0.3'
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('declaration', 'raw', 'expected', 'orm'),
    [
        pytest.param(
            collection_expressions.scaled_filtered,
            {'values': [-1, 0, 2, 3], 'scale': 10},
            50,
            (),
            id='filtered-scale',
        ),
        pytest.param(
            collection_expressions.scaled_filtered, {'values': [], 'scale': 10}, 0, (), id='filtered-empty-input'
        ),
        pytest.param(
            collection_expressions.nested_pairs, {'xs': [1, 2], 'ys': [10, 20]}, 66, (), id='nested-generators'
        ),
        pytest.param(collection_expressions.nested_pairs, {'xs': [], 'ys': [1]}, 0, (), id='nested-empty-outer'),
        pytest.param(collection_expressions.orm_bumped, {'values': [1, 2]}, 5, ('values',), id='orm-member-values'),
        pytest.param(
            collection_expressions.mapped_bumped,
            {'values': {'a': 1, 'b': 2}},
            5,
            ('values',),
            id='orm-dictcomp-items',
        ),
        pytest.param(
            collection_expressions.plain_scaled_mapping,
            {'values': {'a': 1, 'b': 2}, 'factor': 3},
            9,
            (),
            id='plain-dictcomp-items',
        ),
        pytest.param(
            collection_expressions.plain_scaled_mapping,
            {'values': {}, 'factor': 3},
            0,
            (),
            id='plain-dictcomp-empty',
        ),
        pytest.param(collection_expressions.head_plus_last, {'values': [3, 4, 5]}, 8, (), id='index-first-and-last'),
        pytest.param(
            collection_expressions.keyed_forward,
            {'values': {'a': 1, 'b': 2}, 'key': 'b'},
            2,
            (),
            id='index-by-runtime-key',
        ),
        pytest.param(collection_expressions.first_member, {'values': [5, 6]}, 5, ('values',), id='index-member-value'),
        pytest.param(
            collection_expressions.packed_scaled, {'x': 2, 'y': 3, 'scale': 4}, 20, (), id='task-produced-list'
        ),
        pytest.param(collection_expressions.orm_packed_bumped, {'x': 2, 'y': 3}, 7, (), id='task-produced-orm-list'),
        pytest.param(
            collection_expressions.mapping_packed_doubled, {'a': 2, 'b': 3}, 10, (), id='task-produced-mapping'
        ),
        pytest.param(
            collection_expressions.shadowed_target,
            {'values': [1, 2], 'item': 100},
            106,
            (),
            id='shadowed-target',
        ),
        pytest.param(collection_expressions.counted_keys, {'values': {'a': 1, 'b': 2}}, 2, (), id='keys-iteration'),
    ],
)
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_collection_graphs_execute(
    declaration: GraphHandle, raw: dict[str, t.Any], expected: int, orm: tuple[str, ...], serialized: bool
) -> None:
    """Expressions evaluate inline while tasks produce the returned outputs."""
    assert declaration.build() is None
    outputs, node = _launch(declaration, _inputs(raw, orm), serialized=serialized)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_task_produced_hints_type_the_comprehension(serialized: bool) -> None:
    """Task result element contracts reach the expression without re-annotation."""
    hinted = collection_expressions.pack_pair._task_spec.result_shape
    assert hinted.element is not None and hinted.element.types == (int,)
    orm_hinted = collection_expressions.pack_orm_pair._task_spec.result_shape
    assert orm_hinted.element is not None and orm_hinted.element.types == (Int,)
    mapping_hinted = collection_expressions.pack_mapping._task_spec.result_shape
    assert mapping_hinted.element is not None and mapping_hinted.element.types == (int,)
    outputs, node = _launch(collection_expressions.packed_scaled, {'x': 2, 'y': 3, 'scale': 4}, serialized=serialized)
    assert node.is_finished_ok
    assert outputs['result'].value == 20


@pytest.mark.usefixtures('aiida_profile_clean')
def test_expression_placements_dispatch_no_child_processes() -> None:
    """Only the packing producer and the summing consumer call; the expression leaves no node."""
    outputs, node = run_get_node(collection_expressions.packed_scaled, x=2, y=3, scale=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 20
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'pack_pair', 'sum_values'}
    labels = [entry.link_label for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()]
    assert labels
    assert all(not label.startswith(('expression', 'operation')) for label in labels)
    packed = calls['pack_pair'].outputs.result
    assert list(packed) == [2, 3]
    consumer_input = calls['sum_values'].inputs.values
    assert consumer_input.uuid != packed.uuid
    assert consumer_input.creator is None
    assert list(consumer_input.get_list()) == [8, 12]
    assert list(packed) == [2, 3]
    assert outputs['result'].uuid == calls['sum_values'].outputs.result.uuid
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_orm_expression_provenance_flows_through_tasks() -> None:
    """An owned packing flows into the consumer unchanged while the expression stays inline."""
    outputs, node = run_get_node(collection_expressions.orm_packed_bumped, x=2, y=3)
    assert node.is_finished_ok
    assert outputs['result'].value == 7
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(calls) == {'pack_orm_pair', 'sum_values'}
    packed = calls['pack_orm_pair'].outputs.result
    assert [member.value for member in packed] == [2, 3]
    assert outputs['result'].uuid == calls['sum_values'].outputs.result.uuid
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_selected_owned_member_rejected_at_launch(serialized: bool) -> None:
    """Returning an owned container child fails launch under the existing workflow contract."""
    assert collection_expressions.select_member.build() is None
    with pytest.raises(InvalidOperation, match='owned container child'):
        _launch(collection_expressions.select_member, {'values': [Int(1), Int(7)]}, serialized=serialized)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_computed_scalar_cannot_launder_through_selection() -> None:
    """Selecting then shifting a member value is a computed scalar, so the root rejects it."""
    try:
        collection_expressions.laundered_scalar.build()
    except (GraphLanguageError, GraphTypeCheckError):
        return
    _, node = run_get_node(collection_expressions.laundered_scalar, values=[Int(1)])
    assert node.exit_status == 401
    assert node.exit_message is not None and 'task' in node.exit_message.lower()


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(collection_expressions.private_attr_comp, id='private-attr'),
        pytest.param(collection_expressions.method_call_comp, id='method-call'),
        pytest.param(collection_expressions.task_call_comp, id='task-call'),
        pytest.param(collection_expressions.untyped_comp, id='missing-element-annotation'),
        pytest.param(collection_expressions.wrong_index_type, id='wrong-index-type'),
        pytest.param(collection_expressions.sliced_index, id='slice'),
    ],
)
def test_rejected_collection_source_fails_during_build(declaration: GraphHandle) -> None:
    """Private reads, calls, unannotated elements, bad indices, and slices fail before running."""
    with pytest.raises((GraphLanguageError, GraphTypeCheckError)):
        declaration.build()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_runtime_missing_key_raises(serialized: bool) -> None:
    """A runtime key absent from the mapping fails as an expression runtime error."""
    assert collection_expressions.keyed_forward.build() is None
    spec = compile_graph(collection_expressions.keyed_forward)
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    state = GraphRun(spec, given={'values': {'a': 1}, 'key': 'missing'})
    with pytest.raises(GraphRuntimeError, match='missing key'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_runtime_out_of_range_raises(serialized: bool) -> None:
    """Indexing past an empty runtime list fails as an expression runtime error."""
    assert collection_expressions.head_plus_last.build() is None
    spec = compile_graph(collection_expressions.head_plus_last)
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    state = GraphRun(spec, given={'values': []})
    with pytest.raises(GraphRuntimeError, match='out of range'):
        state.step()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_expression_value_survives_checkpoint_without_reevaluate(
    serialized: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An evaluated expression checkpoints its value; restore reuses it without re-evaluating."""
    from copy import deepcopy

    from aiida.engine.processes.graphs import run as run_mod
    from aiida.engine.processes.graphs.ir import ProcessTask

    spec = compile_graph(collection_expressions.packed_scaled)
    if serialized:
        spec = GraphIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    state = GraphRun(spec, given={'x': 2, 'y': 3, 'scale': 4})
    first = state.step()
    assert [start.instance for start in first.starts] == ['pack_pair']
    for start in first.starts:
        assert isinstance(start.task, ProcessTask)
        _, completed = run_get_node(start.task.spec.process_class, **start.inputs)
        state.started(start.instance, completed.pk)
        state.completed(start.instance, completed.pk)
    second = state.step()
    assert [start.instance for start in second.starts] == ['sum_values']
    values = state.scopes['root']['values']
    assert len(values) == 1
    ((expression_name, expression_value),) = values.items()
    assert expression_value == [8, 12]
    saved = deepcopy(state.to_dict())
    assert json.loads(json.dumps(saved)) == saved
    restored = GraphRun.from_dict(spec, dict(state.given), saved)
    assert restored.to_dict() == saved
    assert restored.scopes['root']['values'] == {expression_name: [8, 12]}
    calls: list[t.Any] = []
    real_evaluate = run_mod.evaluate_expression

    def counting(expression: t.Any, inputs: t.Any) -> t.Any:
        calls.append((expression, dict(inputs)))
        return real_evaluate(expression, inputs)

    monkeypatch.setattr(run_mod, 'evaluate_expression', counting)
    assert restored.step().starts == []
    assert calls == []


@graph
def nested_producer(x: int, y: int) -> list[int]:
    """Produce a collection inside a nested graph."""
    return collection_expressions.pack_pair(x=x, y=y)


@graph
def nested_passthrough(values: list[int]) -> list[int]:
    """Pass a collection straight through a nested graph."""
    return values


@graph
def nested_produced_scaled(x: int, y: int, scale: int) -> int:
    """Scale a nested-produced collection inline."""
    packed = nested_producer(x=x, y=y)
    scaled = [item * scale for item in packed]
    return collection_expressions.sum_values(values=scaled)


@graph
def nested_passed_scaled(values: list[int], scale: int) -> int:
    """Scale a nested-passed collection inline."""
    passed = nested_passthrough(values=values)
    scaled = [item * scale for item in passed]
    return collection_expressions.sum_values(values=scaled)


def test_nested_collection_graphs_build_and_round_trip() -> None:
    """Nested producer and passthrough keep elements for comprehensions."""
    from aiida.engine.processes.graphs.shapes import LeafShape
    from aiida.orm import List

    for handle in (nested_producer, nested_passthrough, nested_produced_scaled, nested_passed_scaled):
        assert handle.build() is None
        spec = compile_graph(handle)
        assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()
    assert compile_graph(nested_producer).result_shape == LeafShape(types=(List,), element=LeafShape(types=(int,)))
    assert compile_graph(nested_passthrough).result_shape == LeafShape(types=(List,), element=LeafShape(types=(int,)))


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(nested_produced_scaled, id='nested-produced'),
        pytest.param(nested_passed_scaled, id='nested-passthrough'),
    ],
)
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_nested_collection_graphs_execute(declaration: GraphHandle, serialized: bool) -> None:
    """Comprehensions over nested collections evaluate while tasks return outputs."""
    assert declaration.build() is None
    given: dict[str, t.Any] = (
        {'x': 2, 'y': 3, 'scale': 4} if declaration is nested_produced_scaled else {'values': [2, 3], 'scale': 4}
    )
    outputs, node = _launch(declaration, given, serialized=serialized)
    assert node.is_finished_ok
    assert outputs['result'].value == 20
