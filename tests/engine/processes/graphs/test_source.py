###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build-only contracts for straight-line source graphs."""

import json

import pytest

from aiida.common.exceptions import GraphError, GraphTypeCheckError, UnsupportedSyntax
from aiida.engine.processes.graphs.ir import Dependency, GraphIR, TaskIR
from aiida.engine.processes.graphs.lowering import GraphHandle, lower_from_source
from aiida.engine.processes.graphs.shapes import load_shape
from tests.engine.processes.graphs import language


def test_public_api_is_source_only() -> None:
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
    assert isinstance(language.chain, GraphHandle)
    with pytest.raises(GraphError, match='launch'):
        language.chain(x=1, y=2)


def test_build_does_not_invoke_graph_or_task_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError('must not invoke a task while lowering')

    monkeypatch.setattr(language.add.process_class, '_func', staticmethod(fail))
    spec = language.chain.lower()
    assert spec.task_names == ('add', 'add_2')
    assert spec.dependencies == (Dependency('add', 'add_2', 'result', 'x'),)
    assert spec.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_lower_from_source_matches_handle_build() -> None:
    assert lower_from_source(language.chain).to_dict() == language.chain.lower().to_dict()


def test_declared_spec_round_trips_through_json() -> None:
    spec = language.multiply_add.lower()
    restored = GraphIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored.to_dict() == spec.to_dict()
    assert restored.identifier == 'multiply_add'
    assert set(restored.outputs) == {'result'}


def test_custom_identifier_is_kept() -> None:
    assert language.labelled.lower().identifier == 'custom-label'


def test_task_alias_does_not_collide_with_generated_name() -> None:
    assert len(language.collision.lower().tasks) == 3


def test_missing_task_input_fails_during_build() -> None:
    with pytest.raises(UnsupportedSyntax, match='y'):
        language.missing_task_input.lower()


def test_parameter_defaults_fill_missing_inputs() -> None:
    """Literal parameter defaults apply without passing the input."""
    spec = language.default_parameter.lower()
    assert spec.prepare_inputs({}) == {'value': 2}
    assert spec.prepare_inputs({'value': 5}) == {'value': 5}


@pytest.mark.parametrize(
    'declaration, message',
    [
        pytest.param(language.expanded_task_arguments, 'name each argument', id='expanded'),
        pytest.param(language.arithmetic_expression, 'put this calculation in a task', id='expression'),
        pytest.param(language.reassigned_name, 'assign each result a new name', id='rebound'),
        pytest.param(language.fanout, 'for loops are not supported', id='fanout'),
        pytest.param(language.variadic_parameters, 'list each input separately', id='variadic'),
        pytest.param(language.literal_return, 'return a task output or graph input', id='literal'),
        pytest.param(language.namespace_return, 'return a task output or graph input', id='namespace'),
        pytest.param(language.nested_outputs, 'list each output by name', id='nested-output'),
        pytest.param(language.missing_final_return, 'end the graph with a return', id='missing-return'),
        pytest.param(language.unbound, 'is not known here', id='unbound'),
        pytest.param(language.unregistered_call, 'unregistered call', id='unregistered'),
        pytest.param(language.builtin_call, 'wrap it in a task', id='builtin'),
        pytest.param(language.unknown_call, 'check the spelling', id='unknown'),
        pytest.param(language.subscript_assignment, 'assign to a plain name', id='subscript'),
        pytest.param(language.nested_definition, 'move it into a task', id='nested-def'),
        pytest.param(language.augmented_assignment, 'move it into a task', id='aug-assign'),
        pytest.param(language.annotated_assignment, 'drop the annotation', id='ann-assign'),
        pytest.param(language.with_block, 'move it into a task', id='with'),
        pytest.param(language.try_block, 'move it into a task', id='try'),
        pytest.param(language.raise_statement, 'move it into a task', id='raise'),
        pytest.param(language.assert_statement, 'move it into a task', id='assert'),
        pytest.param(language.match_statement, 'end the graph with a return', id='match'),
        pytest.param(language.starred_call, 'list each input by name', id='starred'),
        pytest.param(language.subscript_load, 'pass the whole collection', id='subscript-load'),
        pytest.param(language.fstring_argument, 'build this text in a task', id='fstring'),
        pytest.param(language.inline_conditional, 'as if and else', id='ifexp'),
        pytest.param(language.list_comprehension, 'must call a task or graph', id='listcomp'),
    ],
)
def test_rejected_source_syntax_fails_during_build(declaration: GraphHandle, message: str) -> None:
    """Rejected syntax raises `UnsupportedSyntax` before graph execution."""
    with pytest.raises(UnsupportedSyntax, match=message):
        declaration.lower()


def test_ordering_dependency_carries_no_value() -> None:
    """An `after` dependency orders placements without wiring an output value."""
    specification = language.ordered_named.lower()
    assert [(edge.source, edge.target, edge.source_port, edge.target_port) for edge in specification.dependencies] == [
        ('prepare', 'add', None, None)
    ]


def test_incompatible_boundary_types_fail_during_build() -> None:
    with pytest.raises(GraphTypeCheckError, match='incompatible types'):
        language.wrong_type.lower()


def test_rejection_carries_source_location() -> None:
    with pytest.raises(UnsupportedSyntax) as caught:
        language.unbound.lower()
    assert 'language' in str(caught.value)
    assert 'unbound name' in str(caught.value)
    assert '^' in str(caught.value)


def test_spec_version_and_unknown_task_kind_rejection() -> None:
    data = language.chain.lower().to_dict()
    data['version'] = '99'
    with pytest.raises(GraphTypeCheckError, match='version'):
        GraphIR.from_dict(data)
    task_data = language.add.task_spec.to_dict()
    task_data['version'] = '99'
    with pytest.raises(GraphTypeCheckError, match='version'):
        TaskIR.from_dict(task_data)
    data = language.chain.lower().to_dict()
    data['tasks'][0]['kind'] = 'map'
    with pytest.raises(GraphTypeCheckError, match='unsupported graph task kind'):
        GraphIR.from_dict(data)
    with pytest.raises(GraphTypeCheckError, match='Unknown graph value shape'):
        load_shape({'kind': 'many', 'required': True})


def test_cyclic_and_invalid_ordering_dependencies() -> None:
    from dataclasses import replace

    spec = language.chain.lower()
    with pytest.raises(GraphTypeCheckError, match='cycle'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('add_2', 'add')))
    with pytest.raises(GraphTypeCheckError, match='both ports'):
        Dependency('add', 'add_2', source_port='result')


def test_task_registration_rejects_excluded_contracts() -> None:
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
    from aiida.engine.processes.graphs.lowering import task

    def local_function(x: int) -> int:
        return x

    with pytest.raises(GraphTypeCheckError, match='return annotation'):
        task(language.unannotated_function)
    with pytest.raises(GraphTypeCheckError, match='fixed inputs'):
        task(language.kwargs_function)
    with pytest.raises(GraphTypeCheckError, match='fixed inputs'):
        task(language.args_function)
    with pytest.raises(UnsupportedSyntax, match='module scope'):
        task(local_function)
    with pytest.raises(UnsupportedSyntax, match='not process classes'):
        task(ArithmeticAddCalculation)
