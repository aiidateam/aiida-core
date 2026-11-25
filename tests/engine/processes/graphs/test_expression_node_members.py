###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Node-valued collection expressions keep owned contracts without cloning inline.

Inline comprehensions and literals return plain Python lists/dicts at runtime,
but when every member is one concrete ``DataNode`` their static contract declares
an owned ``DataList``/``DataDict`` so downstream ``list[Int]``/``dict[str, Int]``
task inputs validate. Collaborators: the ``expressions`` shape inference, the
``lowering`` wiring of ``InlineOperation(operation='expression')`` placements,
and the process machinery serializing plain node lists into owned containers.
"""

import ast
import json
import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.expressions import (
    compile_expression,
    evaluate_expression,
    infer_expression_shape,
)
from aiida.engine.processes.graphs.ir import GraphIR
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.shapes import LeafShape, shape_for_annotation
from aiida.orm import DataDict, DataList, Int
from aiida.orm.nodes.process.process import ProcessNode
from tests.engine.processes.graphs.programs import expression_node_members

pytestmark = pytest.mark.presto

_SERIALIZED = [
    pytest.param(False, id='declaration'),
    pytest.param(True, id='serialized'),
]


def _resolve(mapping: dict[str, tuple[str, LeafShape]]) -> t.Any:
    """Return a resolver reading free names from ``mapping``."""

    def resolve(node: ast.expr) -> tuple[str, LeafShape]:
        assert isinstance(node, ast.Name)
        return mapping[node.id]

    return resolve


def _compile(source: str, mapping: dict[str, tuple[str, LeafShape]]) -> tuple[dict, dict]:
    """Compile one source expression with the given name contracts."""
    return compile_expression(ast.parse(source, mode='eval').body, _resolve(mapping))


def test_identity_listcomp_declares_owned_container() -> None:
    """A direct member comprehension over ``list[Int]`` infers ``DataList``."""
    given = shape_for_annotation(list[Int])
    expression, _ = _compile('[item for item in values]', {'values': ('values', given)})
    inferred = infer_expression_shape(expression, {'values': given})
    assert isinstance(inferred, LeafShape)
    assert inferred.types == (DataList,)
    assert inferred.element is not None and inferred.element.types == (Int,)
    assert inferred == shape_for_annotation(list[Int])


def test_identity_dictcomp_declares_owned_container() -> None:
    """A direct pair comprehension over ``dict[str, Int]`` infers ``DataDict``."""
    given = shape_for_annotation(dict[str, Int])
    expression, _ = _compile('{key: value for key, value in values.items()}', {'values': ('values', given)})
    inferred = infer_expression_shape(expression, {'values': given})
    assert isinstance(inferred, LeafShape)
    assert inferred.types == (DataDict,)
    assert inferred.element is not None and inferred.element.types == (Int,)
    assert inferred == shape_for_annotation(dict[str, Int])


def test_filtered_node_comprehensions_stay_owned() -> None:
    """Filtering on ``.value`` keeps the owned contract for the surviving members."""
    given = shape_for_annotation(list[Int])
    expression, _ = _compile('[item for item in values if item.value > 0]', {'values': ('values', given)})
    assert infer_expression_shape(expression, {'values': given}).types == (DataList,)
    mapping = shape_for_annotation(dict[str, Int])
    dict_expression, _ = _compile(
        '{key: value for key, value in values.items() if value.value > 0}', {'values': ('values', mapping)}
    )
    assert infer_expression_shape(dict_expression, {'values': mapping}).types == (DataDict,)


def test_node_valued_literals_declare_owned_containers() -> None:
    """List/dict literals of one concrete node type infer owned containers uniformly."""
    member = LeafShape(types=(Int,))
    expression, _ = _compile('[a, b]', {'a': ('a', member), 'b': ('b', member)})
    assert infer_expression_shape(expression, {'a': member, 'b': member}).types == (DataList,)
    dict_expression, _ = _compile("{'x': a, 'y': b}", {'a': ('a', member), 'b': ('b', member)})
    assert infer_expression_shape(dict_expression, {'a': member, 'b': member}).types == (DataDict,)


def test_computed_members_stay_plain_python() -> None:
    """Unwrapped or computed members keep plain ``list``/``dict`` contracts."""
    given = shape_for_annotation(list[Int])
    expression, _ = _compile('[item.value + 1 for item in values]', {'values': ('values', given)})
    inferred = infer_expression_shape(expression, {'values': given})
    assert isinstance(inferred, LeafShape)
    assert inferred.types == (list,)
    assert inferred.element is not None and inferred.element.types == (int,)
    assert evaluate_expression(expression, {'values': [Int(1), Int(2)]}) == [2, 3]


def test_identity_comprehension_returns_plain_list_of_same_nodes() -> None:
    """Identity comprehensions build a new plain list around the same member nodes."""
    given = shape_for_annotation(list[Int])
    expression, _ = _compile('[item for item in values]', {'values': ('values', given)})
    members = [Int(1), Int(2)]
    result = evaluate_expression(expression, {'values': list(members)})
    assert type(result) is list
    assert result == members
    assert all(first is second for first, second in zip(result, members, strict=True))


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


def test_node_graphs_build_and_round_trip() -> None:
    """Every node-forwarding graph lowers, with its template surviving a JSON round trip."""
    for handle in (
        expression_node_members.forward_nodes,
        expression_node_members.filtered_nodes,
        expression_node_members.forward_mapping,
        expression_node_members.filtered_mapping,
    ):
        assert handle.build() is None
        spec = compile_graph(handle)
        assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))).to_dict() == spec.to_dict()


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    ('declaration', 'raw', 'expected'),
    [
        pytest.param(expression_node_members.forward_nodes, {'values': [1, 2, 3]}, 6, id='identity-list'),
        pytest.param(expression_node_members.filtered_nodes, {'values': [-1, 2, 3]}, 5, id='filtered-list'),
        pytest.param(expression_node_members.forward_mapping, {'values': {'a': 1, 'b': 2}}, 3, id='identity-dict'),
        pytest.param(expression_node_members.filtered_mapping, {'values': {'a': -1, 'b': 2}}, 2, id='filtered-dict'),
    ],
)
@pytest.mark.parametrize('serialized', _SERIALIZED)
def test_node_comprehensions_feed_owned_consumers(
    declaration: GraphHandle, raw: dict[str, t.Any], expected: int, serialized: bool
) -> None:
    """Filtered and identity node comprehensions validate into owned task inputs."""
    assert declaration.build() is None
    wrapped: dict[str, t.Any] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            wrapped[key] = [Int(item) for item in value]
        else:
            wrapped[key] = {name: Int(item) for name, item in value.items()}
    outputs, node = _launch(declaration, wrapped, serialized=serialized)
    assert node.is_finished_ok
    assert outputs['result'].value == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_forwarded_list_clones_container_keeping_members() -> None:
    """The consumer sees a new ``DataList`` clone; original members stay unchanged."""
    original = [Int(1), Int(2), Int(3)]
    before = [(member.uuid, member.value) for member in original]
    outputs, node = run_get_node(expression_node_members.forward_nodes, values=list(original))
    assert node.is_finished_ok
    assert outputs['result'].value == 6
    assert [(member.uuid, member.value) for member in original] == before
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    consumer_input = calls['consume_nodes'].inputs.values
    assert isinstance(consumer_input, DataList)
    assert [member.value for member in consumer_input] == [1, 2, 3]
    assert consumer_input.uuid not in {member.uuid for member in original}
    assert {member.uuid for member in consumer_input}.isdisjoint({member.uuid for member in original})
    assert [member.value for member in original] == [1, 2, 3]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_forwarded_dict_clones_container_keeping_members() -> None:
    """The consumer sees a new ``DataDict`` clone; original members stay unchanged."""
    original = {'a': Int(1), 'b': Int(2)}
    before = {key: (member.uuid, member.value) for key, member in original.items()}
    outputs, node = run_get_node(expression_node_members.forward_mapping, values=dict(original))
    assert node.is_finished_ok
    assert outputs['result'].value == 3
    assert {key: (member.uuid, member.value) for key, member in original.items()} == before
    calls: dict[str, ProcessNode] = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    consumer_input = calls['consume_mapping'].inputs.values
    assert isinstance(consumer_input, DataDict)
    assert {key: consumer_input[key].value for key in consumer_input} == {'a': 1, 'b': 2}
    assert {member.uuid for member in consumer_input.values()}.isdisjoint({member.uuid for member in original.values()})
    assert {key: member.value for key, member in original.items()} == {'a': 1, 'b': 2}
