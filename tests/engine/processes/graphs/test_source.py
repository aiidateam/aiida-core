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

from aiida.common.exceptions import UnsupportedSyntax
from aiida.engine.processes.graphs.build_source import build_from_source
from aiida.engine.processes.graphs.interface import GraphHandle
from aiida.engine.processes.graphs.shapes import load_shape
from aiida.engine.processes.graphs.spec import Dependency, GraphSpec, TaskSpec
from tests.engine.processes.graphs import declarations


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
    assert isinstance(declarations.chain, GraphHandle)
    with pytest.raises(TypeError, match='launch'):
        declarations.chain(x=1, y=2)


def test_build_does_not_invoke_graph_or_task_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError('must not invoke a task while lowering')

    monkeypatch.setattr(declarations.add.process_class, '_func', staticmethod(fail))
    spec = declarations.chain.build()
    assert spec.task_names == ('add', 'add_2')
    assert spec.dependencies == (Dependency('add', 'add_2', 'result', 'x'),)
    assert spec.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}
    assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_build_from_source_matches_handle_build() -> None:
    assert build_from_source(declarations.chain).to_dict() == declarations.chain.build().to_dict()


def test_declared_spec_round_trips_through_json() -> None:
    spec = declarations.multiply_add.build()
    restored = GraphSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored.to_dict() == spec.to_dict()
    assert restored.identifier == 'multiply_add'
    assert set(restored.outputs) == {'result'}


def test_custom_identifier_is_kept() -> None:
    assert declarations.labelled.build().identifier == 'custom-label'


def test_task_alias_does_not_collide_with_generated_name() -> None:
    assert len(declarations.collision.build().tasks) == 3


def test_missing_task_input_fails_during_build() -> None:
    with pytest.raises(ValueError, match='y'):
        declarations.missing_task_input.build()


def test_parameter_defaults_fill_missing_inputs() -> None:
    """Literal parameter defaults apply without passing the input."""
    spec = declarations.default_parameter.build()
    assert spec.prepare_inputs({}) == {'value': 2}
    assert spec.prepare_inputs({'value': 5}) == {'value': 5}


@pytest.mark.parametrize(
    'declaration, message',
    [
        pytest.param(declarations.expanded_task_arguments, 'calls require named arguments', id='expanded'),
        pytest.param(declarations.arithmetic_expression, 'unsupported expression', id='expression'),
        pytest.param(declarations.reassigned_name, 'assignment must bind a new name', id='rebound'),
        pytest.param(declarations.fanout, 'for loops are not supported', id='fanout'),
        pytest.param(declarations.variadic_parameters, 'variadic parameters are not supported', id='variadic'),
        pytest.param(declarations.literal_return, 'return must select a task output or graph input leaf', id='literal'),
        pytest.param(
            declarations.namespace_return, 'return must select a task output or graph input leaf', id='namespace'
        ),
        pytest.param(declarations.nested_outputs, 'unsupported expression', id='nested-output'),
        pytest.param(declarations.missing_final_return, 'graph must end in a return', id='missing-return'),
        pytest.param(declarations.unbound, 'unbound name', id='unbound'),
    ],
)
def test_rejected_source_syntax_fails_during_build(declaration: GraphHandle, message: str) -> None:
    """Rejected syntax raises `UnsupportedSyntax` before graph execution."""
    with pytest.raises(UnsupportedSyntax, match=message):
        declaration.build()


def test_nested_graph_builds_subgraph_task() -> None:
    from aiida.engine.processes.graphs.spec import SubgraphTask

    spec = declarations.nested_multiply_add.build()
    assert isinstance(spec.tasks[0], SubgraphTask)
    assert spec.tasks[0].body.identifier == 'multiply_add'


def test_branches_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.spec import BranchControl

    spec = declarations.external_choice.build()
    assert isinstance(spec.tasks[0], BranchControl)
    assert set(spec.tasks[0].body.outputs) == {'result'}
    assert set(spec.tasks[0].otherwise.outputs) == {'result'}


def test_loops_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.spec import LoopControl

    spec = declarations.countdown.build()
    assert isinstance(spec.tasks[0], LoopControl)
    assert set(spec.tasks[0].body.outputs) == {'value', 'condition'}
    called = declarations.countdown_call.build()
    assert isinstance(called.tasks[1], LoopControl)
    assert set(called.tasks[1].body.outputs) == {'value', 'condition'}


def test_recursive_call_fails_during_build() -> None:
    with pytest.raises(UnsupportedSyntax, match='Recursive graph call'):
        declarations.recursive_call.build()


def test_inline_condition_matches_bound_form() -> None:
    """An inline predicate call lowers like its explicit assignment form."""
    inline = declarations.inline_condition.build().to_dict()
    bound = declarations.computed_choice.build().to_dict()
    inline.pop('identifier')
    bound.pop('identifier')
    assert inline == bound


def test_mismatched_branch_outputs_fail_during_build() -> None:
    with pytest.raises(ValueError, match='same outputs'):
        declarations.mismatched_branches.build()


def test_incompatible_boundary_types_fail_during_build() -> None:
    with pytest.raises(ValueError, match='incompatible types'):
        declarations.wrong_type.build()


def test_rejection_carries_source_location() -> None:
    with pytest.raises(UnsupportedSyntax) as caught:
        declarations.unbound.build()
    assert 'declarations.py' in str(caught.value)
    assert 'unbound name' in str(caught.value)
    assert '^' in str(caught.value)


def test_spec_version_and_unknown_task_kind_rejection() -> None:
    data = declarations.chain.build().to_dict()
    data['version'] = '99'
    with pytest.raises(ValueError, match='version'):
        GraphSpec.from_dict(data)
    task_data = declarations.add.task_spec.to_dict()
    task_data['version'] = '99'
    with pytest.raises(ValueError, match='version'):
        TaskSpec.from_dict(task_data)
    data = declarations.chain.build().to_dict()
    data['tasks'][0]['kind'] = 'map'
    with pytest.raises(ValueError, match='unsupported graph task kind'):
        GraphSpec.from_dict(data)
    with pytest.raises(ValueError, match='Unknown graph value shape'):
        load_shape({'kind': 'many', 'required': True})


def test_cyclic_and_invalid_ordering_dependencies() -> None:
    from dataclasses import replace

    spec = declarations.chain.build()
    with pytest.raises(ValueError, match='cycle'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('add_2', 'add')))
    with pytest.raises(ValueError, match='both ports'):
        Dependency('add', 'add_2', source_port='result')


def test_task_registration_rejects_excluded_contracts() -> None:
    from aiida.engine.processes.graphs.build_source import task

    def local_function(x: int) -> int:
        return x

    with pytest.raises(TypeError, match='return annotation'):
        task(declarations.unannotated_function)
    with pytest.raises(TypeError, match='fixed inputs'):
        task(declarations.kwargs_function)
    with pytest.raises(UnsupportedSyntax, match='module scope'):
        task(local_function)
