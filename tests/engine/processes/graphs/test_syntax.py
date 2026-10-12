###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""User-facing acceptance cases for supported and rejected graph syntax."""

import json

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.interface import GraphHandle
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.engine.processes.graphs.spec import GraphSpec
from aiida.manage.configuration.profile import Profile
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.process.workflow.graph import GraphNode
from tests.engine.processes.graphs import declarations

pytestmark = pytest.mark.presto


@pytest.mark.parametrize(
    ('declaration', 'inputs', 'expected'),
    [
        pytest.param(declarations.multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 10}, id='multiply-add'),
        pytest.param(declarations.nested_multiply_add, {'x': 2, 'y': 3, 'z': 4}, {'result': 11}, id='nested-graph'),
        pytest.param(declarations.diamond, {'x': 2}, {'result': 7}, id='diamond'),
        pytest.param(declarations.named, {'x': 2, 'y': 3}, {'total': 5, 'product': 6}, id='named-outputs'),
        pytest.param(declarations.selected_field, {'settings': {}}, {'sum': 3}, id='namespace-field-default'),
        pytest.param(declarations.literal_dictionary, {}, {'result': 42}, id='dictionary-literal'),
        pytest.param(declarations.dictionary_input, {'values': {'answer': 42}}, {'result': 42}, id='dictionary-leaf'),
        pytest.param(declarations.ordered_named, {'value': 2}, {'sum': 3}, id='ordering-without-output'),
        pytest.param(declarations.multiple_ordered, {'x': 2}, {'result': 3}, id='ordering-on-two'),
        pytest.param(declarations.positional_task_arguments, {'value': 2}, {'result': 3}, id='positional-arguments'),
        pytest.param(declarations.tuple_assignment, {'x': 2, 'y': 3}, {'result': 11}, id='tuple-unpacking'),
        pytest.param(declarations.chained_assignment, {'value': 2}, {'result': 6}, id='chained-assignment'),
        pytest.param(declarations.default_parameter, {}, {'result': 3}, id='parameter-default-filled'),
        pytest.param(declarations.default_parameter, {'value': 5}, {'result': 6}, id='parameter-default-overridden'),
        pytest.param(declarations.keyword_only_parameter, {'value': 2}, {'result': 3}, id='keyword-only'),
        pytest.param(declarations.positional_only_parameter, {'value': 2}, {'result': 3}, id='positional-only'),
    ],
)
@pytest.mark.parametrize('serialized', [pytest.param(False, id='declaration'), pytest.param(True, id='serialized')])
def test_supported_graph_syntax_executes(
    aiida_profile_clean: Profile,
    declaration: GraphHandle,
    inputs: dict[str, object],
    expected: dict[str, int],
    serialized: bool,
) -> None:
    """Supported declarations and their JSON representations return exact named values."""
    if serialized:
        specification: GraphSpec = declaration.build()
        restored: GraphSpec = GraphSpec.from_dict(json.loads(json.dumps(specification.to_dict())))
        outputs, node = run_get_node(GraphProcess, **GraphProcess.launch_inputs(body=restored, inputs=inputs))
    else:
        outputs, node = run_get_node(declaration, **inputs)
    assert node.is_finished_ok
    assert {name: value.value for name, value in outputs.items()} == expected


def test_multiply_add_preserves_original_input(aiida_profile_clean: Profile) -> None:
    """The arithmetic graph retains input identity and returns the addition output."""
    original: Int = Int(value=2)
    outputs, node = run_get_node(declarations.multiply_add, x=original, y=3, z=4)
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


def test_nested_graph_has_child_workflow_provenance(aiida_profile_clean: Profile) -> None:
    """A nested declaration executes as a child graph with its own task calls."""
    outputs, node = run_get_node(declarations.nested_multiply_add, x=2, y=3, z=4)
    assert node.is_finished_ok
    assert outputs['result'].value == 11
    calls = node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).nested()
    assert set(calls) == {'multiply_add'}
    child: GraphNode = calls['multiply_add']
    assert isinstance(child, GraphNode)
    assert child.is_finished_ok
    assert child.outputs.result.value == 10
    children = child.base.links.get_outgoing(link_type=LinkType.CALL_CALC).nested()
    assert set(children) == {'multiply', 'add'}


def test_ordering_dependency_consumes_no_value() -> None:
    """An `after` dependency orders placements without wiring an output value."""
    specification: GraphSpec = declarations.ordered_named.build()
    assert [(edge.source, edge.target, edge.source_port, edge.target_port) for edge in specification.dependencies] == [
        ('prepare', 'add_named', None, None)
    ]
