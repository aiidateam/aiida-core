###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build-only contracts for straight-line source graphs."""

import importlib
import json

import pytest

from aiida.common.exceptions import GraphError, GraphLanguageError, GraphTypeCheckError
from aiida.engine.processes.graphs.ir import Dependency, Endpoint, GraphIR, Route, TaskIR
from aiida.engine.processes.graphs.lowering import GraphHandle
from aiida.engine.processes.graphs.shapes import load_shape
from tests.engine.processes.graphs.programs import (
    assignments,
    branches,
    calls,
    expressions,
    loops,
    parameters,
    ports,
    statements,
    tasks,
)


def test_graph_cannot_be_called_directly() -> None:
    with pytest.raises(GraphError, match='launch'):
        calls.chain(x=1, y=2)


def test_build_does_not_invoke_graph_or_task_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError('must not invoke a task while lowering')

    monkeypatch.setattr(tasks.add.process_class, '_func', staticmethod(fail))
    spec = calls.chain.build()
    assert spec.task_names == ('add', 'add_2')
    assert spec.dependencies == (Dependency('add', 'add_2', 'result', 'x'),)
    assert spec.inputs == {'x': (('add', 'x'),), 'y': (('add', 'y'), ('add_2', 'y'))}
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_signed_literals_keep_their_sign() -> None:
    assert parameters.signed_literals.build().tasks[0].inputs == {'x': -3, 'y': 1}


def test_optional_collection_keeps_both_types() -> None:
    spec = parameters.optional_collection.build()
    assert spec.input_spec()['values'].valid_type == (list, type(None))


def test_factory_defaults_are_independent_per_launch() -> None:
    spec = parameters.factory_defaults.build()
    first = spec.prepare_inputs({'settings': {}})
    second = spec.prepare_inputs({'settings': {}})
    assert first == second == {'settings': {'values': []}}
    first['settings']['values'].append(1)
    assert second == {'settings': {'values': []}}
    assert GraphIR.from_dict(spec.to_dict()).prepare_inputs({'settings': {}}) == second


def test_graph_declarations_can_be_reloaded() -> None:
    before = parameters.default_parameter.build().to_dict()
    importlib.reload(parameters)
    assert parameters.default_parameter.build().to_dict() == before


def test_declared_spec_round_trips_through_json() -> None:
    spec = calls.multiply_add.build()
    restored = GraphIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored.to_dict() == spec.to_dict()
    assert restored.identifier == f'{calls.__name__}:multiply_add'
    assert set(restored.outputs) == {'result'}


def test_identifier_includes_module() -> None:
    assert calls.labelled.identifier == f'{calls.__name__}:labelled'
    assert calls.labelled.build().identifier == f'{calls.__name__}:labelled'
    assert calls.chain.build().identifier == f'{calls.__name__}:chain'


def test_graph_rejects_identifier_argument() -> None:
    from aiida.engine import graph

    with pytest.raises(TypeError, match='identifier'):
        graph(identifier='custom-label')


def test_task_alias_does_not_collide_with_generated_name() -> None:
    assert len(calls.collision.build().tasks) == 3


def test_missing_task_input_fails_during_build() -> None:
    with pytest.raises(GraphLanguageError, match='y'):
        calls.missing_task_input.build()


def test_parameter_defaults_fill_missing_inputs() -> None:
    """Literal parameter defaults apply without passing the input."""
    spec = parameters.default_parameter.build()
    assert spec.prepare_inputs({}) == {'value': 2}
    assert spec.prepare_inputs({'value': 5}) == {'value': 5}


@pytest.mark.parametrize(
    'declaration, message',
    [
        pytest.param(calls.expanded_task_arguments, 'name each argument', id='expanded'),
        pytest.param(expressions.arithmetic_expression, 'put this calculation in a task', id='expression'),
        pytest.param(assignments.reassigned_name, 'assign each result a new name', id='rebound'),
        pytest.param(loops.fanout, 'for loops are not supported', id='fanout'),
        pytest.param(parameters.variadic_parameters, 'list each input separately', id='variadic'),
        pytest.param(ports.literal_return, 'return a task output or graph input', id='literal'),
        pytest.param(ports.namespace_return, 'return a task output or graph input', id='namespace'),
        pytest.param(ports.nested_outputs, 'list each output by name', id='nested-output'),
        pytest.param(ports.missing_final_return, 'end the graph with a return', id='missing-return'),
        pytest.param(assignments.unbound, 'is not known here', id='unbound'),
        pytest.param(calls.unregistered_call, 'unregistered call', id='unregistered'),
        pytest.param(calls.builtin_call, 'wrap it in a task', id='builtin'),
        pytest.param(calls.unknown_call, 'check the spelling', id='unknown'),
        pytest.param(assignments.subscript_assignment, 'assign to a plain name', id='subscript'),
        pytest.param(statements.nested_definition, 'move it into a task', id='nested-def'),
        pytest.param(branches.early_return, 'assign the same name on both sides', id='early-return'),
        pytest.param(assignments.augmented_assignment, 'move it into a task', id='aug-assign'),
        pytest.param(assignments.annotated_assignment, 'drop the annotation', id='ann-assign'),
        pytest.param(statements.with_block, 'move it into a task', id='with'),
        pytest.param(statements.try_block, 'move it into a task', id='try'),
        pytest.param(statements.raise_statement, 'move it into a task', id='raise'),
        pytest.param(statements.assert_statement, 'move it into a task', id='assert'),
        pytest.param(branches.match_statement, 'end the graph with a return', id='match'),
        pytest.param(calls.starred_call, 'list each input by name', id='starred'),
        pytest.param(ports.subscript_load, 'pass the whole collection', id='subscript-load'),
        pytest.param(expressions.fstring_argument, 'build this text in a task', id='fstring'),
        pytest.param(branches.boolean_condition, 'put this check in a task', id='boolop'),
        pytest.param(branches.compare_condition, 'put this check in a task', id='compare'),
        pytest.param(branches.inline_conditional, 'as if and else', id='ifexp'),
        pytest.param(branches.walrus_condition, 'on its own line', id='walrus'),
        pytest.param(loops.list_comprehension, 'must call a task or graph', id='listcomp'),
        pytest.param(parameters.infinite_default, 'finite JSON', id='infinite-default'),
    ],
)
def test_rejected_source_syntax_fails_during_build(declaration: GraphHandle, message: str) -> None:
    """Rejected syntax raises `GraphLanguageError` before graph execution."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()


def test_nested_graph_builds_subgraph_task() -> None:
    from aiida.engine.processes.graphs.ir import SubgraphTask

    spec = calls.nested_multiply_add.build()
    assert isinstance(spec.tasks[0], SubgraphTask)
    assert spec.tasks[0].body.identifier == f'{calls.__name__}:multiply_add'


def test_branches_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.ir import BranchControl

    spec = branches.external_choice.build()
    assert isinstance(spec.tasks[0], BranchControl)
    assert set(spec.tasks[0].body.outputs) == {'result'}
    assert set(spec.tasks[0].otherwise.outputs) == {'result'}


def test_loops_build_control_tasks() -> None:
    from aiida.engine.processes.graphs.ir import LoopControl

    spec = loops.countdown.build()
    assert isinstance(spec.tasks[0], LoopControl)
    assert set(spec.tasks[0].body.outputs) == {'value', 'condition'}
    called = loops.countdown_call.build()
    assert isinstance(called.tasks[1], LoopControl)
    assert set(called.tasks[1].body.outputs) == {'value', 'condition'}


def test_recursive_call_fails_during_build() -> None:
    with pytest.raises(GraphLanguageError, match='Recursive graph call'):
        calls.recursive_call.build()


def test_inline_condition_matches_bound_form() -> None:
    """An inline predicate call lowers like its explicit assignment form."""
    inline = branches.inline_condition.build().to_dict()
    bound = branches.computed_choice.build().to_dict()
    inline.pop('identifier')
    bound.pop('identifier')
    assert inline == bound


def test_mismatched_branch_outputs_fail_during_build() -> None:
    with pytest.raises(GraphTypeCheckError, match='same outputs'):
        branches.mismatched_branches.build()


def test_ordering_dependency_carries_no_value() -> None:
    """An `after` dependency orders placements without wiring an output value."""
    specification = calls.ordered_named.build()
    assert [(edge.source, edge.target, edge.source_port, edge.target_port) for edge in specification.dependencies] == [
        ('prepare', 'add', None, None)
    ]


def test_incompatible_boundary_types_fail_during_build() -> None:
    with pytest.raises(GraphTypeCheckError, match='incompatible types'):
        ports.wrong_type.build()


def test_rejection_carries_source_location() -> None:
    with pytest.raises(GraphLanguageError) as caught:
        assignments.unbound.build()
    assert 'programs/assignments.py' in str(caught.value)
    assert 'is not known here' in str(caught.value)
    assert '^' in str(caught.value)


def test_spec_version_and_unknown_task_kind_rejection() -> None:
    data = calls.chain.build().to_dict()
    data['version'] = '99'
    with pytest.raises(GraphTypeCheckError, match='version'):
        GraphIR.from_dict(data)
    task_data = tasks.add._task_spec.to_dict()
    task_data['version'] = '99'
    with pytest.raises(GraphTypeCheckError, match='version'):
        TaskIR.from_dict(task_data)
    data = calls.chain.build().to_dict()
    data['tasks'][0]['kind'] = 'map'
    with pytest.raises(GraphTypeCheckError, match='unsupported graph task kind'):
        GraphIR.from_dict(data)
    with pytest.raises(GraphTypeCheckError, match='Unknown graph value shape'):
        load_shape({'kind': 'many', 'required': True})


def test_cyclic_and_invalid_ordering_dependencies() -> None:
    from dataclasses import replace

    spec = calls.chain.build()
    with pytest.raises(GraphTypeCheckError, match='cycle'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('add_2', 'add')))
    with pytest.raises(GraphTypeCheckError, match='both ports'):
        Dependency('add', 'add_2', source_port='result')


def test_dangling_input_task_fails_validation() -> None:
    """A hand-built input route to a missing task raises a diagnostic, not `KeyError`."""
    from dataclasses import replace

    spec = calls.chain.build()
    dangling = {name: tuple(Route('missing', route.port) for route in routes) for name, routes in spec.inputs.items()}
    with pytest.raises(GraphTypeCheckError, match='unknown task'):
        replace(spec, inputs=dangling)


def test_dangling_dependency_task_fails_validation() -> None:
    """A hand-built dependency on a missing task raises a diagnostic, not `KeyError`."""
    from dataclasses import replace

    spec = calls.chain.build()
    with pytest.raises(GraphTypeCheckError, match='unknown task'):
        replace(spec, dependencies=(*spec.dependencies, Dependency('missing', spec.task_names[0])))


def test_dangling_output_task_fails_validation() -> None:
    """A hand-built output endpoint on a missing task raises a diagnostic, not `KeyError`."""
    from dataclasses import replace

    spec = calls.chain.build()
    with pytest.raises(GraphTypeCheckError, match='unknown task'):
        replace(spec, outputs={'result': Endpoint(port='result', task='missing')})


def test_unknown_output_port_fails_validation() -> None:
    """A hand-built output endpoint on a missing port raises a diagnostic instead of crashing."""
    from dataclasses import replace

    spec = calls.chain.build()
    with pytest.raises(GraphTypeCheckError, match='must reference a declared leaf'):
        replace(spec, outputs={'result': Endpoint(port='nope', task=None)})


def test_task_registration_rejects_excluded_contracts() -> None:
    from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
    from aiida.engine.processes.graphs.lowering import task

    def local_function(x: int) -> int:
        return x

    with pytest.raises(GraphTypeCheckError, match='return annotation'):
        task(tasks.unannotated_function)
    with pytest.raises(GraphTypeCheckError, match='fixed inputs'):
        task(tasks.kwargs_function)
    with pytest.raises(GraphTypeCheckError, match='fixed inputs'):
        task(tasks.args_function)
    with pytest.raises(GraphLanguageError, match='module scope'):
        task(local_function)
    with pytest.raises(GraphLanguageError, match='not process classes'):
        task(ArithmeticAddCalculation)
