###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""WorkChain authoring-layer retry example: inline orchestration around real task outputs.

The runtime case checks WorkChain error mapping, nested inline predicates, and
returned-node identity. Generic retry-budget and guard failure cases live in
``test_loop_authoring_examples`` and ``test_restart``.
"""

import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import BranchControl, InlineOperation, LoopControl, ProcessTask, SubgraphTask
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.orm import GraphNode
from tests.engine.processes.graphs.programs import workchains
from tests.engine.processes.graphs.programs.workchains import ChainErrors

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
        elif isinstance(task, SubgraphTask):
            for nested in task.body.tasks:
                _visit(nested)

    for task in template.tasks:
        _visit(task)
    return found


def _branches(template: t.Any) -> list[BranchControl]:
    """Return every branch of a template, including nested bodies."""
    found: list[BranchControl] = []

    def _visit(task: t.Any) -> None:
        if isinstance(task, BranchControl):
            found.append(task)
            for nested in (*task.body.tasks, *task.otherwise.tasks):
                _visit(nested)
        elif isinstance(task, LoopControl):
            for nested in task.body.tasks:
                _visit(nested)
        elif isinstance(task, SubgraphTask):
            for nested in task.body.tasks:
                _visit(nested)

    for task in template.tasks:
        _visit(task)
    return found


def _loop(template: t.Any) -> LoopControl:
    """Return the single loop of the retry example."""
    (loop,) = [task for task in template.tasks if isinstance(task, LoopControl)]
    assert isinstance(loop, LoopControl)
    return loop


@pytest.mark.usefixtures('aiida_profile_clean')
def test_retry_recovers() -> None:
    """The first chain run fails mapped, the repaired retry succeeds, the guard validates."""
    outputs, node = run_get_node(workchains.retry_chain_until_repaired, max_retries=1)
    assert node.is_finished_ok
    assert outputs['result'].value == 1.0
    # Two chain runs plus the validation guard, and no control-state tasks: the
    # first chain keeps its declared failure while the retry and guard finish cleanly.
    children = [child for child in node.called if not isinstance(child, GraphNode)]
    assert len(children) == 3
    assert sorted(child.exit_status for child in children) == [0, 0, ChainErrors.UNSTABLE.status]
    assert node.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []
    # The returned node is the successful chain's own output, not a guard copy.
    owners = [
        child for child in children if 'result' in child.outputs and child.outputs.result.uuid == outputs['result'].uuid
    ]
    assert len(owners) == 1
    assert owners[0].process_label == 'FlakyChain'


def _subgraphs(template: t.Any) -> list[SubgraphTask]:
    """Return every graph-call expansion of a template, including nested bodies."""
    found: list[SubgraphTask] = []

    def _visit(task: t.Any) -> None:
        if isinstance(task, SubgraphTask):
            found.append(task)
            for nested in task.body.tasks:
                _visit(nested)
        elif isinstance(task, BranchControl):
            for nested in (*task.body.tasks, *task.otherwise.tasks):
                _visit(nested)
        elif isinstance(task, LoopControl):
            for nested in task.body.tasks:
                _visit(nested)

    for task in template.tasks:
        _visit(task)
    return found


def _process_tasks(template: t.Any) -> list[ProcessTask]:
    """Return every process task of a template, including nested bodies."""
    found: list[ProcessTask] = []

    def _visit(task: t.Any) -> None:
        if isinstance(task, ProcessTask):
            found.append(task)
        elif isinstance(task, BranchControl):
            for nested in (*task.body.tasks, *task.otherwise.tasks):
                _visit(nested)
        elif isinstance(task, LoopControl):
            for nested in task.body.tasks:
                _visit(nested)
        elif isinstance(task, SubgraphTask):
            for nested in task.body.tasks:
                _visit(nested)

    for task in template.tasks:
        _visit(task)
    return found


def test_retry_control_is_inline() -> None:
    """The attempt and the budget evaluate inline around one chain task per pass."""
    helper = compile_graph(workchains.retry_chain_allowed)
    assert all(isinstance(task, BranchControl) for task in helper.tasks)
    assert _process_tasks(helper) == []
    assert _subgraphs(helper) == []
    (member,) = _branches(helper)
    assert member.condition_test == 'is_member'
    assert member.condition_member is not None and member.condition_member[1] == 'UNSTABLE'
    template = compile_graph(workchains.retry_chain_until_repaired)
    loop = _loop(template)
    assert loop.condition_port == 'retry'
    stepped = [task for task in loop.body.tasks if isinstance(task, ProcessTask)]
    assert len(stepped) == 1
    assert stepped[0].spec.identifier == 'FlakyChain'
    # The reusable predicate expands as a subgraph, not a child process: the only
    # process tasks anywhere are the chain and the validation guard.
    assert {task.spec.identifier for task in _process_tasks(template)} == {'FlakyChain', 'check_chain_result'}
    predicates = _subgraphs(template)
    assert len(predicates) == 2
    assert all(task.body.identifier.endswith(':retry_chain_allowed') for task in predicates)
    branches = _branches(template)
    assert len(branches) == 2
    assert all(branch.condition_test == 'is_member' for branch in branches)
    assert all(branch.condition_member is not None and branch.condition_member[1] == 'UNSTABLE' for branch in branches)
    assert 'add' in _operations(template)
    assert 'lt' in _operations(template)
    assert {task.spec.identifier for task in loop.body.tasks if isinstance(task, ProcessTask)} == {'FlakyChain'}
