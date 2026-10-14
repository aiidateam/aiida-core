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
from aiida.engine.processes.graphs.build_source import GraphHandle, lower_from_source
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
    with pytest.raises(GraphError, match='launch'):
        declarations.chain(x=1, y=2)


def test_build_does_not_invoke_graph_or_task_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError('must not invoke a task while lowering')

    monkeypatch.setattr(declarations.add.process_class, '_func', staticmethod(fail))
    spec = declarations.chain.lower()
    assert spec.task_names == ('add', 'add_2')
    assert spec.dependencies == (Dependency('add', 'add_2', 'result', 'x'),)
    assert spec.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}
    assert GraphSpec.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_lower_from_source_matches_handle_build() -> None:
    assert lower_from_source(declarations.chain).to_dict() == declarations.chain.lower().to_dict()


def test_declared_spec_round_trips_through_json() -> None:
    spec = declarations.multiply_add.lower()
    restored = GraphSpec.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored.to_dict() == spec.to_dict()
    assert restored.identifier == 'multiply_add'
    assert set(restored.outputs) == {'result'}


def test_custom_identifier_is_kept() -> None:
    assert declarations.labelled.lower().identifier == 'custom-label'


def test_task_alias_does_not_collide_with_generated_name() -> None:
    assert len(declarations.collision.lower().tasks) == 3


def test_missing_task_input_fails_during_build() -> None:
    with pytest.raises(UnsupportedSyntax, match='y'):
        declarations.missing_task_input.lower()


def test_parameter_defaults_fill_missing_inputs() -> None:
    """Literal parameter defaults apply without passing the input."""
    spec = declarations.default_parameter.lower()
    assert spec.prepare_inputs({}) == {'value': 2}
    assert spec.prepare_inputs({'value': 5}) == {'value': 5}


@pytest.mark.parametrize(
    'declaration, message',
    [
        pytest.param(declarations.expanded_task_arguments, 'calls require named arguments', id='expanded'),
        pytest.param(declarations.arithmetic_expression, 'move the computation into a task', id='expression'),
        pytest.param(declarations.reassigned_name, 'assignment must bind a new name', id='rebound'),
        pytest.param(declarations.fanout, 'for loops are not supported', id='fanout'),
        pytest.param(declarations.variadic_parameters, 'variadic parameters are not supported', id='variadic'),
        pytest.param(declarations.literal_return, 'return must select a task output or graph input leaf', id='literal'),
        pytest.param(
            declarations.namespace_return, 'return must select a task output or graph input leaf', id='namespace'
        ),
        pytest.param(declarations.nested_outputs, 'flat mappings of task outputs', id='nested-output'),
        pytest.param(declarations.missing_final_return, 'graph must end in a return', id='missing-return'),
        pytest.param(declarations.unbound, 'unbound name', id='unbound'),
        pytest.param(declarations.unregistered_call, 'unregistered call', id='unregistered'),
        pytest.param(declarations.subscript_assignment, 'only single-name assignments', id='subscript'),
        pytest.param(declarations.nested_definition, 'only single-name assignments', id='nested-def'),
        pytest.param(declarations.early_return, 'one assignment to the same name', id='early-return'),
        pytest.param(declarations.augmented_assignment, 'only single-name assignments', id='aug-assign'),
        pytest.param(declarations.annotated_assignment, 'only single-name assignments', id='ann-assign'),
        pytest.param(declarations.with_block, 'only single-name assignments', id='with'),
        pytest.param(declarations.try_block, 'only single-name assignments', id='try'),
        pytest.param(declarations.raise_statement, 'only single-name assignments', id='raise'),
        pytest.param(declarations.assert_statement, 'only single-name assignments', id='assert'),
        pytest.param(declarations.match_statement, 'graph must end in a return', id='match'),
        pytest.param(declarations.starred_call, 'unsupported unpacking', id='starred'),
        pytest.param(declarations.subscript_load, 'collections travel whole', id='subscript-load'),
        pytest.param(declarations.fstring_argument, 'format inside a task', id='fstring'),
        pytest.param(declarations.boolean_condition, 'compute the predicate', id='boolop'),
        pytest.param(declarations.compare_condition, 'compute the predicate', id='compare'),
        pytest.param(declarations.inline_conditional, 'branch explicitly', id='ifexp'),
        pytest.param(declarations.walrus_condition, 'bind before branching', id='walrus'),
        pytest.param(declarations.list_comprehension, 'must call a registered task or graph', id='listcomp'),
    ],
)
def test_rejected_source_syntax_fails_during_build(declaration: GraphHandle, message: str) -> None:
    """Rejected syntax raises `UnsupportedSyntax` before graph execution."""
    with pytest.raises(UnsupportedSyntax, match=message):
        declaration.lower()


def test_nested_graph_builds_subgraph_task() -> None:
    from aiida.engine.processes.graphs.spec import SubgraphTask

    spec = declarations.nested_multiply_add.lower()
    assert isinstance(spec.tasks[0], SubgraphTask)
    assert spec.tasks[0].body.identifier == 'multiply_add'


def test_branches_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.spec import BranchControl

    spec = declarations.external_choice.lower()
    assert isinstance(spec.tasks[0], BranchControl)
    assert set(spec.tasks[0].body.outputs) == {'result'}
    assert set(spec.tasks[0].otherwise.outputs) == {'result'}


def test_loops_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.spec import LoopControl

    spec = declarations.countdown.lower()
    assert isinstance(spec.tasks[0], LoopControl)
    assert set(spec.tasks[0].body.outputs) == {'value', 'condition'}
    called = declarations.countdown_call.lower()
    assert isinstance(called.tasks[1], LoopControl)
    assert set(called.tasks[1].body.outputs) == {'value', 'condition'}


def test_recursive_call_fails_during_build() -> None:
    with pytest.raises(UnsupportedSyntax, match='Recursive graph call'):
        declarations.recursive_call.lower()


def test_inline_condition_matches_bound_form() -> None:
    """An inline predicate call lowers like its explicit assignment form."""
    inline = declarations.inline_condition.lower().to_dict()
    bound = declarations.computed_choice.lower().to_dict()
    inline.pop('identifier')
    bound.pop('identifier')
    assert inline == bound


def test_mismatched_branch_outputs_fail_during_build() -> None:
    with pytest.raises(GraphTypeCheckError, match='same outputs'):
        declarations.mismatched_branches.lower()


def test_incompatible_boundary_types_fail_during_build() -> None:
    with pytest.raises(GraphTypeCheckError, match='incompatible types'):
        declarations.wrong_type.lower()


def test_rejection_carries_source_location() -> None:
    with pytest.raises(UnsupportedSyntax) as caught:
        declarations.unbound.lower()
    assert 'declarations' in str(caught.value)
    assert 'unbound name' in str(caught.value)
    assert '^' in str(caught.value)


def test_spec_version_and_unknown_task_kind_rejection() -> None:
    data = declarations.chain.lower().to_dict()
    data['version'] = '99'
    with pytest.raises(GraphTypeCheckError, match='version'):
        GraphSpec.from_dict(data)
    task_data = declarations.add.task_spec.to_dict()
    task_data['version'] = '99'
    with pytest.raises(GraphTypeCheckError, match='version'):
        TaskSpec.from_dict(task_data)
    data = declarations.chain.lower().to_dict()
    data['tasks'][0]['kind'] = 'map'
    with pytest.raises(GraphTypeCheckError, match='unsupported graph task kind'):
        GraphSpec.from_dict(data)
    with pytest.raises(GraphTypeCheckError, match='Unknown graph value shape'):
        load_shape({'kind': 'many', 'required': True})


def test_cyclic_and_invalid_ordering_dependencies() -> None:
    from dataclasses import replace

    spec = declarations.chain.lower()
    with pytest.raises(GraphTypeCheckError, match='cycle'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('add_2', 'add')))
    with pytest.raises(GraphTypeCheckError, match='both ports'):
        Dependency('add', 'add_2', source_port='result')


def test_task_registration_rejects_excluded_contracts() -> None:
    from aiida.engine.processes.graphs.build_source import task

    def local_function(x: int) -> int:
        return x

    with pytest.raises(GraphTypeCheckError, match='return annotation'):
        task(declarations.unannotated_function)
    with pytest.raises(GraphTypeCheckError, match='fixed inputs'):
        task(declarations.kwargs_function)
    with pytest.raises(UnsupportedSyntax, match='module scope'):
        task(local_function)
