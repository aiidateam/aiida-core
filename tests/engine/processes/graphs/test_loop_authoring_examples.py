###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Authoring-layer loop examples: inline orchestration around real task outputs.

Compile-time checks cover both examples; runtime checks exercise bounded iteration
and the validation-only guard's success, exhaustion, and initially-present paths.
"""

import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.common.loaders import get_object_loader
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import BranchControl, InlineOperation, LoopControl, ProcessTask
from aiida.engine.processes.graphs.lowering import compile_graph
from tests.engine.processes.graphs.programs import loops
from tests.engine.processes.graphs.programs.loops import TryErrors

pytestmark = pytest.mark.presto


def _operations(template: t.Any) -> list[str]:
    """Return every inline operation of a template, including nested bodies."""
    found: list[str] = []

    def _visit(task: t.Any) -> None:
        if isinstance(task, InlineOperation):
            found.append(task.operation)
        elif isinstance(task, BranchControl):
            for nested in (*task.body.tasks, *task.otherwise.tasks):
                _visit(nested)
        elif isinstance(task, LoopControl):
            for nested in task.body.tasks:
                _visit(nested)

    for task in template.tasks:
        _visit(task)
    return found


def _loop(template: t.Any) -> LoopControl:
    """Return the single loop of an authoring example."""
    (loop,) = [task for task in template.tasks if isinstance(task, LoopControl)]
    assert isinstance(loop, LoopControl)
    return loop


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'limit, expected, calls',
    [
        pytest.param(3, 8, 4, id='three-steps'),
        pytest.param(0, 5, 1, id='empty-budget'),
    ],
)
def test_bounded_steps_runs(limit: int, expected: int, calls: int) -> None:
    """The counter steps the value once per pass, returning the last task output."""
    outputs, node = run_get_node(loops.bounded_steps, start=5, limit=limit)
    assert node.is_finished_ok
    assert outputs['result'].value == expected
    assert len(node.called) == calls
    assert all(child.is_finished_ok for child in node.called)
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


def test_bounded_steps_control_is_inline() -> None:
    """The counter and the budget evaluate inline around one addition per pass."""
    template = compile_graph(loops.bounded_steps)
    loop = _loop(template)
    stepped = [task for task in loop.body.tasks if isinstance(task, ProcessTask)]
    assert len(stepped) == 1
    assert stepped[0].spec.identifier == 'add'
    assert 'add' in _operations(template)
    assert 'lt' in _operations(template)
    assert {task.spec.identifier for task in loop.body.tasks if isinstance(task, ProcessTask)} == {'add'}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_retry_until_present_recovers() -> None:
    """The first attempt stays absent, the retry succeeds, the guard validates."""
    outputs, node = run_get_node(loops.retry_until_present, start=5, limit=2)
    assert node.is_finished_ok
    assert outputs['result'].value == 6
    # Two step runs plus the validation guard, and no control-state tasks: the first
    # step keeps its declared failure while the retry and the guard finish cleanly.
    assert len(node.called) == 3
    assert sorted(child.exit_status for child in node.called) == [0, 0, TryErrors.RETRYABLE.status]
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    # The returned node is the successful step's own output, not a guard copy.
    owners = [
        child
        for child in node.called
        if 'value' in child.outputs and child.outputs.value.uuid == outputs['result'].uuid
    ]
    assert len(owners) == 1
    assert owners[0].process_label == 'try_step'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_retry_until_present_exhausted_budget() -> None:
    """No retry budget leaves the first failure unrecovered, failing the guard."""
    outputs, node = run_get_node(loops.retry_until_present, start=5, limit=0)
    assert not node.is_finished_ok
    assert node.is_failed
    assert not node.is_excepted
    assert node.exit_status == 400
    assert outputs == {}
    # The loop never runs: the initial step keeps its declared failure and the
    # trailing guard excepts on the absent value.
    assert len(node.called) == 2
    by_label = {child.process_label: child for child in node.called}
    assert set(by_label) == {'try_step', 'check_present'}
    assert by_label['try_step'].exit_status == TryErrors.RETRYABLE.status
    assert by_label['try_step'].is_failed
    assert not by_label['try_step'].is_excepted
    assert by_label['check_present'].is_excepted
    assert not by_label['check_present'].is_failed
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


@pytest.mark.usefixtures('aiida_profile_clean')
def test_retry_until_present_first_attempt_succeeds() -> None:
    """A present first attempt skips the loop, returning the step's own node."""
    outputs, node = run_get_node(loops.retry_until_present, start=5, limit=0, attempt=1)
    assert node.is_finished_ok
    assert outputs['result'].value == 6
    assert len(node.called) == 2
    assert all(child.is_finished_ok for child in node.called)
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


def test_retry_presence_branch_is_inline() -> None:
    """Member branches arm the retry budget around one fallible step per pass."""
    template = compile_graph(loops.retry_until_present)
    loop = _loop(template)
    assert loop.condition_port == 'retry'
    stepped = [task for task in loop.body.tasks if isinstance(task, ProcessTask)]
    assert len(stepped) == 1
    assert stepped[0].spec.identifier == 'try_step'
    branches = [task for task in (*template.tasks, *loop.body.tasks) if isinstance(task, BranchControl)]
    assert len(branches) == 2
    assert all(branch.condition_test == 'is_member' for branch in branches)
    for branch in branches:
        assert branch.condition_member is not None
        identifier, name = branch.condition_member
        assert name == 'RETRYABLE'
        assert get_object_loader().load_object(identifier) is TryErrors
    assert 'add' in _operations(template)
    assert 'lt' in _operations(template)
