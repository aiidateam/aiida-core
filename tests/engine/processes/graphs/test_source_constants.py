###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Build-only contracts for scalar literal bindings in source graphs.

A bound literal lowers to a `const` inline operation: ephemeral scheduler state that wires into
tasks, branches, and loops exactly like any other operation result, but is never stored or linked.
"""

import json

import pytest

from aiida.common.exceptions import GraphLanguageError, GraphTypeCheckError
from aiida.engine.processes.graphs.ir import Dependency, GraphIR, InlineOperation
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from tests.engine.processes.graphs.programs import constants


def _const_tasks(spec: GraphIR) -> list[InlineOperation]:
    """Return the constant placements of a template, in order."""
    return [task for task in spec.tasks if isinstance(task, InlineOperation) and task.operation == 'const']


def test_bound_literal_places_const_before_task() -> None:
    """A bound integer wires its constant result into the task input."""
    spec = compile_graph(constants.bound_scalars)
    assert spec.task_names == ('constant_1', 'add')
    (placed,) = _const_tasks(spec)
    assert placed.inputs == {'value': 0}
    assert placed.result_shape.types == (int,)
    assert spec.dependencies == (Dependency('constant_1', 'add', 'result', 'y'),)
    assert spec.inputs == {'value': (('add', 'x'),)}
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_aliased_constant_shares_one_placement() -> None:
    """Two names bound to one literal share its single constant placement."""
    spec = compile_graph(constants.aliased_constant)
    assert spec.task_names == ('constant_1', 'add')
    assert len(_const_tasks(spec)) == 1


def test_bound_flag_selects_taken_arm() -> None:
    """A bound boolean lowers like any other boolean condition wire."""
    spec = compile_graph(constants.bound_flag)
    (placed,) = _const_tasks(spec)
    assert placed.inputs == {'value': True}
    assert placed.result_shape.types == (bool,)
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_const_arm_joins_task_arm() -> None:
    """A constant arm exposes the same output contract as the task arm."""
    spec = compile_graph(constants.const_fallback)
    [branch] = [task for task in spec.tasks if task.kind == 'branch']
    assert set(branch.body.outputs) == {'result'}
    assert set(branch.otherwise.outputs) == {'result'}
    assert spec.dependencies == (Dependency(branch.name, 'add', 'result', 'x'),)
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_bound_string_wires_through_branch_regions() -> None:
    """A bound string routes into both branch arms as a region input."""
    spec = compile_graph(constants.bound_mode)
    (placed,) = _const_tasks(spec)
    assert placed.inputs == {'value': 'square'}
    assert placed.result_shape.types == (str,)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))) == spec


def test_bound_counter_is_carried_loop_state() -> None:
    """A bound counter lowered before the loop threads through iterations as state."""
    spec = compile_graph(constants.looped_counter)
    loop = next(task for task in spec.tasks if task.kind == 'loop')
    assert 'attempts' in loop.body.outputs
    assert 'attempts' in loop.body.inputs
    assert spec.inputs['rounds'] == spec.inputs['rounds']
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


def test_none_binds_untyped_leaf() -> None:
    """A bound `None` lowers; only booleans select a side, so the run fails loudly."""
    spec = compile_graph(constants.none_condition)
    (placed,) = _const_tasks(spec)
    assert placed.inputs == {'value': None}
    assert placed.result_shape.types == (type(None),)


def test_nested_graph_may_return_control_state() -> None:
    """A nested graph returning a constant threads it to the caller as orchestration state."""
    spec = compile_graph(constants.nested_const)
    [nested] = [task for task in spec.tasks if task.kind == 'graph']
    assert set(nested.body.outputs) == {'result'}
    assert GraphIR.from_dict(spec.to_dict()).to_dict() == spec.to_dict()


@pytest.mark.parametrize(
    'declaration',
    [
        pytest.param(constants.bound_scalars, id='int'),
        pytest.param(constants.bound_flag, id='bool'),
        pytest.param(constants.bound_mode, id='str'),
        pytest.param(constants.const_fallback, id='branch-join'),
        pytest.param(constants.looped_counter, id='loop-carried'),
        pytest.param(constants.nested_const, id='nested-control'),
    ],
)
def test_const_templates_round_trip_through_json(declaration: GraphHandle) -> None:
    """Constant placements and their bound values survive serialization."""
    spec = compile_graph(declaration)
    assert GraphIR.from_dict(json.loads(json.dumps(spec.to_dict()))) == spec


@pytest.mark.parametrize(
    ('declaration', 'message'),
    [
        pytest.param(constants.root_constant, 'scalar constant held as orchestration state', id='root-constant'),
        pytest.param(constants.const_source, 'scalar constant held as orchestration state', id='nested-source-root'),
        pytest.param(constants.nonfinite_constant, 'inline numbers must be finite', id='nonfinite'),
        pytest.param(constants.list_constant, 'provide collections as graph inputs', id='list'),
        pytest.param(constants.fstring_constant, 'build this text in a task', id='fstring'),
    ],
)
def test_rejected_constants_fail_during_build(declaration: GraphHandle, message: str) -> None:
    """Constants outside the finite-scalar contract, and constant root outputs, fail at build."""
    with pytest.raises(GraphLanguageError, match=message):
        declaration.build()


def test_mismatched_const_arm_fails_type_check() -> None:
    """A constant arm of another type than the task arm fails naming the context."""
    with pytest.raises(GraphTypeCheckError, match='incompatible types'):
        constants.mismatched_const_arm.build()
