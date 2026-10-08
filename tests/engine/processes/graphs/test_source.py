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

from aiida.engine import GraphHandle, GraphSpec, UnsupportedSyntax, build_from_source
from aiida.engine.processes.graphs.shapes import load_shape
from aiida.engine.processes.graphs.spec import Dependency, TaskSpec
from tests.engine.processes.graphs import cases


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
    assert isinstance(cases.chain, GraphHandle)
    with pytest.raises(TypeError, match='launch'):
        cases.chain(x=1, y=2)


def test_build_does_not_invoke_graph_or_task_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError('must not invoke a task while lowering')

    monkeypatch.setattr(cases.add.process_class, '_func', staticmethod(fail))
    spec = cases.chain.build()
    assert spec.task_names == ('add', 'add_2')
    assert spec.dependencies == (Dependency('add', 'add_2', 'result', 'x'),)
    assert spec.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}
    assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_build_from_source_matches_handle_build() -> None:
    assert build_from_source(cases.chain).to_dict() == cases.chain.build().to_dict()


def test_declared_spec_round_trips_through_json() -> None:
    spec = cases.multiply_add.build()
    restored = GraphSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored.to_dict() == spec.to_dict()
    assert restored.identifier == 'multiply_add'
    assert set(restored.outputs) == {'result'}


def test_custom_identifier_is_kept() -> None:
    assert cases.labelled.build().identifier == 'custom-label'


def test_task_alias_does_not_collide_with_generated_name() -> None:
    assert len(cases.collision.build().tasks) == 3


def test_missing_task_input_fails_during_build() -> None:
    with pytest.raises(ValueError, match='y'):
        cases.missing_task_input.build()


@pytest.mark.parametrize(
    'declaration, message',
    [
        pytest.param(cases.positional_task_arguments, 'calls require named arguments', id='positional'),
        pytest.param(cases.expanded_task_arguments, 'calls require named arguments', id='expanded'),
        pytest.param(cases.arithmetic_expression, 'unsupported expression', id='expression'),
        pytest.param(cases.tuple_assignment, 'assignment must bind a new name', id='tuple'),
        pytest.param(cases.chained_assignment, 'only single-name assignments', id='chained'),
        pytest.param(cases.reassigned_name, 'assignment must bind a new name', id='rebound'),
        pytest.param(cases.fanout, 'only single-name assignments', id='fanout'),
        pytest.param(cases.default_parameter, 'parameter defaults are not supported', id='default'),
        pytest.param(cases.keyword_only_parameter, 'only ordinary positional parameters', id='keyword-only'),
        pytest.param(cases.positional_only_parameter, 'only ordinary positional parameters', id='positional-only'),
        pytest.param(cases.variadic_parameters, 'only ordinary positional parameters', id='variadic'),
        pytest.param(cases.literal_return, 'return must select a task output or graph input leaf', id='literal'),
        pytest.param(cases.namespace_return, 'return must select a task output or graph input leaf', id='namespace'),
        pytest.param(cases.nested_outputs, 'unsupported expression', id='nested-output'),
        pytest.param(cases.missing_final_return, 'graph must end in a return', id='missing-return'),
        pytest.param(cases.unbound, 'unbound name', id='unbound'),
    ],
)
def test_rejected_source_syntax_fails_during_build(declaration: GraphHandle, message: str) -> None:
    """Rejected syntax raises `UnsupportedSyntax` before graph execution."""
    with pytest.raises(UnsupportedSyntax, match=message):
        declaration.build()


@pytest.mark.parametrize(
    'declaration, message',
    [
        pytest.param(cases.nested, 'nested graphs are not supported', id='nested'),
        pytest.param(cases.recursive_call, 'nested graphs are not supported', id='recursive'),
        pytest.param(cases.external_choice, 'conditional branches are not supported', id='branch'),
        pytest.param(cases.countdown, 'loops are not supported', id='loop'),
    ],
)
def test_deferred_constructs_fail_during_build(declaration: GraphHandle, message: str) -> None:
    """Composition constructs fail explicitly until their owning commit lands."""
    with pytest.raises(UnsupportedSyntax, match=message):
        declaration.build()


def test_incompatible_boundary_types_fail_during_build() -> None:
    with pytest.raises(ValueError, match='incompatible types'):
        cases.wrong_type.build()


def test_rejection_carries_source_location() -> None:
    with pytest.raises(UnsupportedSyntax) as caught:
        cases.unbound.build()
    assert 'cases.py' in str(caught.value)
    assert 'unbound name' in str(caught.value)
    assert '^' in str(caught.value)


def test_spec_version_and_unknown_task_kind_rejection() -> None:
    data = cases.chain.build().to_dict()
    data['version'] = '99'
    with pytest.raises(ValueError, match='version'):
        GraphSpec.from_dict(data)
    task_data = cases.add.task_spec.to_dict()
    task_data['version'] = '99'
    with pytest.raises(ValueError, match='version'):
        TaskSpec.from_dict(task_data)
    data = cases.chain.build().to_dict()
    data['tasks'][0]['kind'] = 'map'
    with pytest.raises(ValueError, match='unsupported graph task kind'):
        GraphSpec.from_dict(data)
    with pytest.raises(ValueError, match='Unknown graph value shape'):
        load_shape({'kind': 'many', 'required': True})


def test_cyclic_and_invalid_ordering_dependencies() -> None:
    from dataclasses import replace

    spec = cases.chain.build()
    with pytest.raises(ValueError, match='cycle'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('add_2', 'add')))
    with pytest.raises(ValueError, match='both ports'):
        Dependency('add', 'add_2', source_port='result')


def test_task_registration_rejects_excluded_contracts() -> None:
    from aiida.engine import task

    def local_function(x: int) -> int:
        return x

    with pytest.raises(TypeError, match='return annotation'):
        task(cases.no_output_declaration)
    with pytest.raises(TypeError, match='fixed inputs'):
        task(cases.dynamic_inputs)
    with pytest.raises(UnsupportedSyntax, match='module scope'):
        task(local_function)
