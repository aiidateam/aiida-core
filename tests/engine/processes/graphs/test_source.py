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
from aiida.engine.processes.graphs.ir import Dependency, GraphIR, TaskIR
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
        pytest.param(language.expanded_task_arguments, 'calls require named arguments', id='expanded'),
        pytest.param(language.arithmetic_expression, 'move the computation into a task', id='expression'),
        pytest.param(language.reassigned_name, 'assignment must bind a new name', id='rebound'),
        pytest.param(language.fanout, 'for loops are not supported', id='fanout'),
        pytest.param(language.variadic_parameters, 'variadic parameters are not supported', id='variadic'),
        pytest.param(language.literal_return, 'return must select a task output or graph input leaf', id='literal'),
        pytest.param(language.namespace_return, 'return must select a task output or graph input leaf', id='namespace'),
        pytest.param(language.nested_outputs, 'flat mappings of task outputs', id='nested-output'),
        pytest.param(language.missing_final_return, 'graph must end in a return', id='missing-return'),
        pytest.param(language.unbound, 'unbound name', id='unbound'),
        pytest.param(language.unregistered_call, 'unregistered call', id='unregistered'),
        pytest.param(language.subscript_assignment, 'only single-name assignments', id='subscript'),
        pytest.param(language.nested_definition, 'only single-name assignments', id='nested-def'),
        pytest.param(language.early_return, 'one assignment to the same name', id='early-return'),
        pytest.param(language.augmented_assignment, 'only single-name assignments', id='aug-assign'),
        pytest.param(language.annotated_assignment, 'only single-name assignments', id='ann-assign'),
        pytest.param(language.with_block, 'only single-name assignments', id='with'),
        pytest.param(language.try_block, 'only single-name assignments', id='try'),
        pytest.param(language.raise_statement, 'only single-name assignments', id='raise'),
        pytest.param(language.assert_statement, 'only single-name assignments', id='assert'),
        pytest.param(language.match_statement, 'graph must end in a return', id='match'),
        pytest.param(language.starred_call, 'unsupported unpacking', id='starred'),
        pytest.param(language.subscript_load, 'collections travel whole', id='subscript-load'),
        pytest.param(language.fstring_argument, 'format inside a task', id='fstring'),
        pytest.param(language.boolean_condition, 'compute the predicate', id='boolop'),
        pytest.param(language.compare_condition, 'compute the predicate', id='compare'),
        pytest.param(language.inline_conditional, 'branch explicitly', id='ifexp'),
        pytest.param(language.walrus_condition, 'bind before branching', id='walrus'),
        pytest.param(language.list_comprehension, 'must call a registered task or graph', id='listcomp'),
    ],
)
def test_rejected_source_syntax_fails_during_build(declaration: GraphHandle, message: str) -> None:
    """Rejected syntax raises `UnsupportedSyntax` before graph execution."""
    with pytest.raises(UnsupportedSyntax, match=message):
        declaration.lower()


def test_nested_graph_builds_subgraph_task() -> None:
    from aiida.engine.processes.graphs.ir import SubgraphTask

    spec = language.nested_multiply_add.lower()
    assert isinstance(spec.tasks[0], SubgraphTask)
    assert spec.tasks[0].body.identifier == 'multiply_add'


def test_branches_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.ir import BranchControl

    spec = language.external_choice.lower()
    assert isinstance(spec.tasks[0], BranchControl)
    assert set(spec.tasks[0].body.outputs) == {'result'}
    assert set(spec.tasks[0].otherwise.outputs) == {'result'}


def test_loops_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.ir import LoopControl

    spec = language.countdown.lower()
    assert isinstance(spec.tasks[0], LoopControl)
    assert set(spec.tasks[0].body.outputs) == {'value', 'condition'}
    called = language.countdown_call.lower()
    assert isinstance(called.tasks[1], LoopControl)
    assert set(called.tasks[1].body.outputs) == {'value', 'condition'}


def test_recursive_call_fails_during_build() -> None:
    with pytest.raises(UnsupportedSyntax, match='Recursive graph call'):
        language.recursive_call.lower()


def test_inline_condition_matches_bound_form() -> None:
    """An inline predicate call lowers like its explicit assignment form."""
    inline = language.inline_condition.lower().to_dict()
    bound = language.computed_choice.lower().to_dict()
    inline.pop('identifier')
    bound.pop('identifier')
    assert inline == bound


def test_mismatched_branch_outputs_fail_during_build() -> None:
    with pytest.raises(GraphTypeCheckError, match='same outputs'):
        language.mismatched_branches.lower()


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
    from aiida.engine.processes.graphs.build_source import task

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
