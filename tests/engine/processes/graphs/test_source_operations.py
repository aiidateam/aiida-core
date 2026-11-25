###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build-only contracts for inline scalar operations in source graphs."""

import json

import pytest

from aiida.common.exceptions import GraphLanguageError
from aiida.engine.processes.graphs.ir import Dependency, GraphIR, InlineOperation
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.orm import Bool
from tests.engine.processes.graphs.programs import operations


def _operation_tasks(spec: GraphIR) -> list[InlineOperation]:
    """Return the inline operation placements of a template, in order."""
    return [task for task in spec.tasks if isinstance(task, InlineOperation)]


def test_scaled_add_places_operation_before_task() -> None:
    """An operation feeding a task wires its result into the task input."""
    spec = compile_graph(operations.scaled_add)
    assert spec.task_names == ('operation_1', 'add')
    (placed,) = _operation_tasks(spec)
    assert placed.operation == 'mul'
    assert placed.input_shape.select('left') == spec.input_shape.select('value')
    assert placed.result_shape.types == (int,)
    assert spec.dependencies == (Dependency('operation_1', 'add', 'result', 'x'),)
    assert spec.inputs['value'] == (('operation_1', 'left'),)


def test_nested_operations_chain_with_dependency_wires() -> None:
    """Nested operations lower inner-first with a dependency wire between them."""
    spec = compile_graph(operations.nested_scale)
    inner, outer = _operation_tasks(spec)
    assert (inner.operation, outer.operation) == ('add', 'mul')
    assert spec.dependencies == (
        Dependency(inner.name, outer.name, 'result', 'left'),
        Dependency(outer.name, 'add', 'result', 'x'),
    )
    assert outer.input_shape.select('right').types == (int,)


def test_integer_arithmetic_stays_integer() -> None:
    """Floor division and remainders over integers infer integer results."""
    spec = compile_graph(operations.halved_remainder)
    assert [task.operation for task in _operation_tasks(spec)] == ['floordiv', 'mod']
    assert all(task.result_shape.types == (int,) for task in _operation_tasks(spec))


def test_unary_operations_place_single_operand() -> None:
    """Unary negation and affirmation each read the `operand` port."""
    spec = compile_graph(operations.unary_pair)
    negated, same = _operation_tasks(spec)
    assert (negated.operation, same.operation) == ('neg', 'pos')
    assert negated.result_shape.types == same.result_shape.types == (int,)


def test_branch_on_comparison_wires_condition() -> None:
    """A comparison in `if` binds a condition placement wired to the branch."""
    spec = compile_graph(operations.branch_on_compare)
    (placed,) = _operation_tasks(spec)
    assert placed.operation == 'gt'
    assert placed.result_shape.types == (Bool,)
    assert spec.dependencies == (Dependency(placed.name, 'branch_2', 'result', 'condition'),)


def test_branch_on_negation_binds_not() -> None:
    """`not` over a boolean input binds a unary operation as the branch condition."""
    spec = compile_graph(operations.branch_on_negation)
    (placed,) = _operation_tasks(spec)
    assert placed.operation == 'not'
    assert placed.result_shape.types == (Bool,)


def test_comparison_materializes_through_task() -> None:
    """Equality results feed a task, so the root return stays a task output."""
    spec = compile_graph(operations.compared_equality)
    assert [task.operation for task in _operation_tasks(spec)] == ['eq', 'ne']
    assert spec.task(spec.outputs['result'].task).kind == 'process'


def test_generic_task_reads_operation_shape_once() -> None:
    """Solving a generic call over an inline result leaves no stray placements."""
    spec = compile_graph(operations.generic_operation)
    assert [task.operation for task in _operation_tasks(spec)] == ['add']
    assert spec.task_names == ('operation_1', 'generic_add', 'add')


def test_field_operand_reads_namespaced_output() -> None:
    """An operation over one output field wires that field into the operand."""
    spec = compile_graph(operations.field_operand)
    (placed,) = _operation_tasks(spec)
    assert placed.operation == 'add'
    assert spec.dependencies == (
        Dependency('arithmetic_pair', 'operation_2', 'sum', 'left'),
        Dependency('operation_2', 'add', 'result', 'x'),
        Dependency('arithmetic_pair', 'add', 'product', 'y'),
    )


def test_nested_graph_scopes_operations() -> None:
    """Operations inside a nested graph lower in the nested scope."""
    spec = compile_graph(operations.nested_operations)
    (placed,) = _operation_tasks(spec)
    assert placed.operation == 'sub'
    [nested] = [task for task in spec.tasks if task.kind == 'graph']
    assert [task.operation for task in nested.body.tasks if isinstance(task, InlineOperation)] == ['mul']


def test_task_outputs_feed_operations() -> None:
    """Operations read task outputs without inlining the producing calls."""
    spec = compile_graph(operations.task_output_arithmetic)
    assert spec.tasks[0].kind == 'process'
    assert [task.operation for task in _operation_tasks(spec)] == ['sub', 'add']
    assert spec.dependencies == (
        Dependency('add', 'operation_2', 'result', 'left'),
        Dependency('operation_2', 'add_2', 'result', 'x'),
        Dependency('add', 'operation_3', 'result', 'left'),
        Dependency('operation_3', 'add_2', 'result', 'y'),
        Dependency('operation_2', 'operation_3'),
    )


def test_while_comparison_recomputes_each_iteration() -> None:
    """The loop body rebinds the counter and re-evaluates the comparison from loop state."""
    spec = compile_graph(operations.countdown_inline)
    initial, loop = spec.tasks[0], spec.tasks[1]
    assert isinstance(initial, InlineOperation) and initial.operation == 'gt'
    assert loop.kind == 'loop'
    assert [(task.operation) for task in loop.body.tasks if isinstance(task, InlineOperation)] == ['sub', 'gt']
    assert loop.body.tasks[1].operation == 'gt'
    assert loop.body.dependencies == (Dependency('operation_1', 'operation_2', 'result', 'left'),)
    assert set(loop.body.outputs) == {'counter', 'condition'}
    assert loop.condition_port == 'condition'
    assert spec.dependencies == (
        Dependency(initial.name, loop.name, 'result', 'condition'),
        Dependency(loop.name, 'add', 'counter', 'x'),
    )


def test_augmented_assignment_updates_loop_state() -> None:
    """`-= ` in a loop body desugars to a rebinding subtraction over loop state."""
    spec = compile_graph(operations.countdown_augmented)
    (loop,) = [task for task in spec.tasks if task.kind == 'loop']
    (placed,) = [task for task in loop.body.tasks if isinstance(task, InlineOperation)]
    assert placed.operation == 'sub'
    assert set(loop.body.outputs) == {'counter', 'active'}


def test_root_operation_builds_for_boundary_rejection() -> None:
    """Lowering accepts a primitive root return; the runtime launch boundary rejects it."""
    spec = compile_graph(operations.root_operation)
    (placed,) = _operation_tasks(spec)
    assert placed.operation == 'sub'
    assert spec.outputs['result'].task == placed.name


def test_operation_template_round_trips_through_json() -> None:
    """Operation placements and their operand contracts survive serialization."""
    spec = compile_graph(operations.scaled_add)
    restored = GraphIR.from_dict(json.loads(json.dumps(spec.to_dict())))
    assert restored == spec


@pytest.mark.parametrize(
    ('declaration', 'message'),
    [
        pytest.param(operations.unsupported_division, 'put this calculation in a task', id='truediv'),
        pytest.param(operations.unpacked_operation, 'only a multi-output call unpacks', id='unpack-operation'),
        pytest.param(operations.unsupported_power, 'put this calculation in a task', id='power'),
        pytest.param(operations.boolean_arithmetic, 'excluding `bool`', id='bool-arithmetic'),
        pytest.param(operations.chained_comparison, 'two values at a time', id='chained'),
        pytest.param(operations.nested_call_operand, 'put the inner call on its own line', id='nested-call'),
        pytest.param(operations.nonboolean_condition, 'must be true or false', id='nonbool-condition'),
        pytest.param(operations.negated_number, 'reads `bool`', id='not-number'),
        pytest.param(operations.string_concat, 'works on numbers', id='strings'),
        pytest.param(operations.untyped_operand, 'missing input annotations', id='untyped'),
        pytest.param(operations.mixed_equality, 'numbers with numbers', id='mixed-equality'),
        pytest.param(operations.divided_loop, 'put this calculation in a task', id='augmented-truediv'),
    ],
)
def test_rejected_operations_fail_during_build(declaration, message: str) -> None:
    """Unsupported inline forms raise `GraphLanguageError` before graph execution."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()
