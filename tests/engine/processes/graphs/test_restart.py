###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Restart loops over declared failures, with inline orchestration state."""

import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.ir import BranchControl, InlineOperation, LoopControl, ProcessTask
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.results import RestartErrors
from aiida.orm import GraphNode, StructureData
from tests.engine.processes.graphs.programs import restart
from tests.engine.processes.graphs.programs.restart import CalculationFailure, StepErrors

pytestmark = pytest.mark.presto


@pytest.fixture
def structure() -> StructureData:
    """An empty structure to carry through the attempts."""
    return StructureData(cell=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])


def _leaf_labels(node: t.Any, leaf: str) -> list[str]:
    """Return the call labels whose leaf placement runs the named task, across loop scopes."""
    calc = node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()
    return [entry.link_label for entry in calc if entry.link_label.split('__')[-1] == leaf]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_restartable_recovers_within_attempts(structure: StructureData) -> None:
    """Two declared failures retry, the third attempt succeeds, the graph exits zero."""
    outputs, node = run_get_node(restart.restartable, structure=structure, max_attempts=2)
    assert node.is_finished_ok
    assert outputs['result'].value == 1.5
    # One root `GraphProcess` places every task call directly: loop iterations are hierarchical
    # `CALL_CALC` scopes, never child graphs, so no `CALL_WORK` links leave the root.
    assert list(node.base.links.get_outgoing(link_type=LinkType.CALL_WORK).all()) == []
    # Control state is inline: three step runs plus the guard, and no control-state tasks.
    assert len(node.called) == 4
    runs = _leaf_labels(node, 'run_step')
    assert len(runs) == 3
    calc = {entry.link_label: entry.node for entry in node.base.links.get_outgoing(link_type=LinkType.CALL_CALC).all()}
    ordered_runs = sorted((calc[label] for label in runs), key=lambda child: child.inputs.attempt.value)
    assert [child.inputs.attempt.value for child in ordered_runs] == [0, 1, 2]
    assert [child.exit_status for child in ordered_runs] == [410, 410, 0]
    assert [set(child.outputs) for child in ordered_runs] == [{'error'}, {'error'}, {'value'}]


def test_restart_control_state_is_inline() -> None:
    """The counter, the budget, and the retry gate evaluate inline around one step per pass."""
    template = compile_graph(restart.restartable)
    (loop,) = [task for task in template.tasks if isinstance(task, LoopControl)]
    assert loop.condition_port == 'retry'
    stepped = [task for task in loop.body.tasks if isinstance(task, ProcessTask)]
    assert len(stepped) == 1
    assert stepped[0].spec.identifier == 'run_step'
    operations = [task.operation for task in (*template.tasks, *loop.body.tasks) if isinstance(task, InlineOperation)]
    assert 'add' in operations
    processes = [task.spec.identifier for task in (*template.tasks, *loop.body.tasks) if isinstance(task, ProcessTask)]
    assert sorted(processes) == ['ensure', 'run_step', 'run_step']
    branches = [task for task in (*template.tasks, *loop.body.tasks) if isinstance(task, BranchControl)]
    assert len(branches) == 2
    assert all(branch.condition_test == 'is_not_none' for branch in branches)
    assert all(
        any(isinstance(task, InlineOperation) and task.operation == 'lt' for task in branch.body.tasks)
        for branch in branches
    )


@pytest.mark.usefixtures('aiida_profile_clean')
def test_restartable_fails_without_attempts(structure: StructureData) -> None:
    """No remaining attempt leaves the error unhandled, failing the graph."""
    outputs, node = run_get_node(restart.restartable, structure=structure, max_attempts=0)
    assert node.exit_status == 400
    assert outputs == {}
    assert len(node.called) == 2
    assert len(_leaf_labels(node, 'run_step')) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_restartable_exhausts_after_one_retry(structure: StructureData) -> None:
    """One retry exhausts the budget before the step can recover."""
    outputs, node = run_get_node(restart.restartable, structure=structure, max_attempts=1)
    assert len(_leaf_labels(node, 'run_step')) == 2
    assert node.exit_status == 400
    assert outputs == {}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_absent_arm_resets_between_iterations() -> None:
    """An iteration leaving no value arm reads as `None`, not the previous value."""
    outputs, node = run_get_node(restart.absent_arm_resets)
    assert node.is_finished_ok
    assert outputs['result'].value == 'absent'
    # Three step runs, three markers, and the final check.
    assert len(node.called) == 7


@pytest.mark.usefixtures('aiida_profile_clean')
def test_discarded_arm_stays_out_of_loop_state() -> None:
    """A `_` element discards its arm, so the loop carries only the named value arm."""
    spec = compile_graph(restart.discarded_arm)
    loop = next(entry for entry in spec.tasks if isinstance(entry, LoopControl))
    assert sorted(loop.body.outputs) == ['attempt', 'condition', 'value']
    outputs, node = run_get_node(restart.discarded_arm)
    assert node.is_finished_ok
    assert outputs['result'].value == 2.0
    assert len(node.called) == 4


@pytest.mark.usefixtures('aiida_profile_clean')
def test_report_unhandled_recovers_value() -> None:
    """A recovered value exits cleanly under the shared vocabulary."""
    outputs, node = run_get_node(restart.report_unhandled, value=1.5, error=None)
    assert node.is_finished_ok
    assert outputs['value'].value == 1.5


@pytest.mark.usefixtures('aiida_profile_clean')
def test_report_unhandled_exits_shared_status() -> None:
    """An unrecovered failure exits with the shared `UNHANDLED_FAILURE` status."""
    outputs, node = run_get_node(restart.report_unhandled, value=None, error=StepErrors.UNSTABLE)
    assert node.exit_status == 402
    assert outputs['error'].get_member() is RestartErrors.UNHANDLED_FAILURE


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(
    'declaration, error, key, expected',
    [
        pytest.param(
            restart.handle_walltime,
            restart.MockScientificCodeErrors.OUT_OF_WALLTIME,
            'restart_mode',
            'restart',
            id='claims-walltime',
        ),
        pytest.param(
            restart.handle_diagonalization,
            restart.MockScientificCodeErrors.COMPUTING_CHOLESKY,
            'diagonalization',
            'cg',
            id='claims-diagonalization',
        ),
        pytest.param(
            restart.handle_walltime,
            restart.MockWorkflowErrors.KNOWN_UNRECOVERABLE_FAILURE,
            'restart_mode',
            None,
            id='declines-unknown',
        ),
    ],
)
def test_handlers_claim_or_decline(
    declaration: t.Any, error: CalculationFailure, key: str, expected: str | None
) -> None:
    """A handler fixes its codes and passes anything else through unchanged."""
    outputs, node = run_get_node(declaration, error=error, parameters={})
    assert node.is_finished_ok
    assert outputs.get(key, None) == expected


@pytest.mark.usefixtures('aiida_profile_clean')
def test_chain_recovers_in_order() -> None:
    """Walltime then diagonalization each claim their code; the third attempt succeeds."""
    outputs, node = run_get_node(restart.chained_retry, parameters={}, max_attempts=5)
    assert node.is_finished_ok
    assert outputs['result'].value == 1.0
    # Three step runs, each followed by a graph that runs both handlers, plus the guard.
    assert len(node.called) == 7
    handlers = [child for child in node.called if isinstance(child, GraphNode)]
    assert len(handlers) == 3 and all(len(handler.called) == 2 for handler in handlers)
    assert sum(not isinstance(child, GraphNode) for child in node.called_descendants) == 10
    assert len(_leaf_labels(node, 'mock_step')) == 3
