###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Correctness and provenance checks for matched WorkChain and graph workloads.

Timing harnesses are kept separately in ``utils/benchmarks/graph_engine/test_graph_restart.py``.
"""

from __future__ import annotations

import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.orm import Dict, Float, GraphNode, WorkChainNode
from aiida.orm.nodes.process.process import ProcessNode
from utils.benchmarks.graph_engine.programs.matched_restart import (
    RECOVER_RUNS,
    RECOVER_VALUE,
    RESTART_BENCHMARKS,
    prepare_restart_inputs,
    prepare_restart_wc_inputs,
    restartable,
    validate_restart_benchmark,
)

pytestmark = pytest.mark.presto

#: Per-round broker wait budget for daemon modes (three sequential child work chains plus helpers).
DAEMON_TIMEOUT = 120

#: Expected task descendants on ``recover``: 3 step work chains, no child graphs, and exactly
#: seven calcfunctions (``zero`` + 3 ``should_restart`` + 2 ``advance`` + ``ensure_recovered``).
_EXPECTED_GRAPH: dict[str, int] = {'graphs': 0, 'calcfunctions': 7, 'workchains': 3}


def _by_type(nodes: t.Iterable[ProcessNode]) -> dict[str, list[ProcessNode]]:
    """Bucket process nodes by class name for structural assertions."""
    bucketed: dict[str, list[ProcessNode]] = {}
    for node in nodes:
        bucketed.setdefault(type(node).__name__, []).append(node)
    return bucketed


def _step_runs(node: ProcessNode) -> list[WorkChainNode]:
    """Return the shared-step descendants in run order (attempt ``0, 1, ...``)."""
    steps = [child for child in node.called_descendants if isinstance(child, WorkChainNode)]
    return sorted(steps, key=lambda step: step.inputs.attempt.value)


def _successful_step_values(node: ProcessNode) -> list[Float]:
    """Return the ``value`` outputs of the shared-step runs that succeeded."""
    return [step.outputs.value for step in _step_runs(node) if 'value' in step.outputs]


def _assert_no_workflow_create(node: ProcessNode) -> None:
    """Assert no workflow node in the tree carries a CREATE link (workflows only RETURN)."""
    for child in (node, *node.called_descendants):
        if isinstance(child, (WorkChainNode, GraphNode)):
            assert child.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


def _assert_attempt_schedule(node: ProcessNode, attempts: list[int]) -> None:
    """Assert the step runs used exactly the given zero-based attempt numbers in order."""
    assert [step.inputs.attempt.value for step in _step_runs(node)] == attempts


def test_graph_template() -> None:
    """The serialized GraphIR the restart graph executes matches its lowered source template."""
    from aiida.engine.processes.graphs.ir import GraphIR

    (handle, _workchain) = RESTART_BENCHMARKS['restart-recover']
    assert handle is restartable
    assert validate_restart_benchmark() == {'restartable-loop-placements': 1}
    template = compile_graph(handle)
    assert GraphIR.from_dict(template.to_dict()).to_dict() == template.to_dict()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_correctness_recover_matched() -> None:
    """Both implementations recover after two transient failures with identical provenance.

    Work-chain side: finished ok, ``value == 1.5``, three ``FlakyStep`` children with attempts
    ``0, 1, 2``. Graph side: finished ok, ``result == 1.5``, the same three step children with
    the same attempt schedule, a stored declaration identical to the lowered template, no child
    graph node anywhere, and no CREATE link from any workflow node on either side. Both sides
    forward the very ``result`` node they were given from the successful step run (provenance
    passthrough, no new data); the graph's final ``result`` is re-wrapped by its raising
    ``ensure`` calcfunction, exactly like the upstream ``restartable`` program.
    """
    from aiida.engine.processes.graphs.ir import GraphIR

    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']
    shared = Float(RECOVER_VALUE)

    wc_outputs, wc_node = run_get_node(
        workchain, **prepare_restart_wc_inputs(mode='recover', max_iterations=5, result=shared)
    )
    assert not wc_node.is_excepted, wc_node.exception
    assert wc_node.is_finished_ok, (wc_node.exit_status, wc_node.exit_message)
    assert isinstance(wc_node, WorkChainNode)
    assert wc_outputs['value'].value == RECOVER_VALUE
    assert wc_outputs['value'].uuid == shared.uuid
    assert len(_step_runs(wc_node)) == RECOVER_RUNS
    _assert_attempt_schedule(wc_node, [0, 1, 2])
    assert len(wc_node.called) == RECOVER_RUNS
    _assert_no_workflow_create(wc_node)

    graph_outputs, graph_node = run_get_node(
        handle, **prepare_restart_inputs(mode='recover', max_attempts=5, result=shared)
    )
    assert not graph_node.is_excepted, graph_node.exception
    assert graph_node.is_finished_ok, (graph_node.exit_status, graph_node.exit_message)
    assert isinstance(graph_node, GraphNode)
    assert graph_outputs['result'].value == RECOVER_VALUE
    assert [value.uuid for value in _successful_step_values(graph_node)] == [shared.uuid]
    assert [value.uuid for value in _successful_step_values(wc_node)] == [shared.uuid]
    assert len(_step_runs(graph_node)) == RECOVER_RUNS
    _assert_attempt_schedule(graph_node, [0, 1, 2])
    stored = graph_node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph')
    assert GraphIR.from_dict(stored.get_dict()).to_dict() == compile_graph(handle).to_dict()
    descendants = _by_type(graph_node.called_descendants)
    assert len(descendants.get('GraphNode', [])) == _EXPECTED_GRAPH['graphs']
    assert len(descendants.get('CalcFunctionNode', [])) == _EXPECTED_GRAPH['calcfunctions']
    assert len(descendants.get('WorkChainNode', [])) == _EXPECTED_GRAPH['workchains']
    direct = _by_type(graph_node.called)
    assert len(direct.get('GraphNode', [])) == 0
    assert len(direct.get('WorkChainNode', [])) == RECOVER_RUNS
    _assert_no_workflow_create(graph_node)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_correctness_recover_direct_ir() -> None:
    """The stored-IR launch of the graph recovers exactly like the authoring launch."""
    (handle, _workchain) = RESTART_BENCHMARKS['restart-recover']
    handle.build()
    shared = Float(RECOVER_VALUE)
    launch_inputs = handle.get_launch_inputs(**prepare_restart_inputs(mode='recover', max_attempts=5, result=shared))
    outputs, node = run_get_node(GraphProcess, **launch_inputs)
    assert not node.is_excepted, node.exception
    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    assert outputs['result'].value == RECOVER_VALUE
    assert [value.uuid for value in _successful_step_values(node)] == [shared.uuid]
    _assert_attempt_schedule(node, [0, 1, 2])


@pytest.mark.usefixtures('aiida_profile_clean')
def test_correctness_fatal_matched() -> None:
    """An unclaimable failure aborts both implementations after a single run.

    The work chain reports ``402`` (``ERROR_UNHANDLED_FAILURE``); the graph reports ``400``
    because ``ensure_recovered`` raises. Both run the step exactly once and store no value.
    A raising ``ensure`` is a controlled task failure (``is_failed``, never ``is_excepted``),
    exactly like the upstream ``restartable`` program when attempts run out.
    """
    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']

    _wc_outputs, wc_node = run_get_node(workchain, **prepare_restart_wc_inputs(mode='fatal', max_iterations=5))
    assert not wc_node.is_excepted, wc_node.exception
    assert wc_node.is_failed
    assert wc_node.exit_status == 402
    assert len(_step_runs(wc_node)) == 1

    graph_outputs, graph_node = run_get_node(handle, **prepare_restart_inputs(mode='fatal', max_attempts=5))
    assert not graph_node.is_excepted, graph_node.exception
    assert graph_node.is_failed
    assert graph_node.exit_status == 400
    assert dict(graph_outputs) == {}
    assert len(_step_runs(graph_node)) == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_correctness_exhausted_matched() -> None:
    """A transient failure with no budget left aborts both implementations after two runs.

    The work chain reports ``401`` (``ERROR_MAXIMUM_ITERATIONS_EXCEEDED``); the graph reports
    ``400`` through ``ensure_recovered``. Both run the step exactly twice, attempts ``0, 1``.
    Neither side is excepted: both are controlled failures.
    """
    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']

    _wc_outputs, wc_node = run_get_node(workchain, **prepare_restart_wc_inputs(mode='always-fail', max_iterations=2))
    assert not wc_node.is_excepted, wc_node.exception
    assert wc_node.is_failed
    assert wc_node.exit_status == 401
    _assert_attempt_schedule(wc_node, [0, 1])

    graph_outputs, graph_node = run_get_node(handle, **prepare_restart_inputs(mode='always-fail', max_attempts=2))
    assert not graph_node.is_excepted, graph_node.exception
    assert graph_node.is_failed
    assert graph_node.exit_status == 400
    assert dict(graph_outputs) == {}
    _assert_attempt_schedule(graph_node, [0, 1])


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('budget', [1, RECOVER_RUNS])
def test_bounds_minimal_budget(budget: int) -> None:
    """Boundary budgets behave identically on run count, differing only in vocabulary.

    Budget three recovers with exactly three runs and ``value == 1.5`` on both sides. Budget
    one runs the step once and fails: the work chain reports ``401`` (a handler claimed the
    failure but the budget is spent) while the graph reports ``400`` via ``ensure_recovered``.
    Neither failing side is excepted.
    """
    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']

    wc_outputs, wc_node = run_get_node(workchain, **prepare_restart_wc_inputs(mode='recover', max_iterations=budget))
    graph_outputs, graph_node = run_get_node(handle, **prepare_restart_inputs(mode='recover', max_attempts=budget))

    if budget == RECOVER_RUNS:
        assert not wc_node.is_excepted, wc_node.exception
        assert wc_node.is_finished_ok, (wc_node.exit_status, wc_node.exit_message)
        assert wc_outputs['value'].value == RECOVER_VALUE
        assert not graph_node.is_excepted, graph_node.exception
        assert graph_node.is_finished_ok, (graph_node.exit_status, graph_node.exit_message)
        assert graph_outputs['result'].value == RECOVER_VALUE
    else:
        assert not wc_node.is_excepted, wc_node.exception
        assert wc_node.is_failed
        assert wc_node.exit_status == 401
        assert not graph_node.is_excepted, graph_node.exception
        assert graph_node.is_failed
        assert graph_node.exit_status == 400
        assert dict(graph_outputs) == {}
    _assert_attempt_schedule(wc_node, list(range(budget)))
    _assert_attempt_schedule(graph_node, list(range(budget)))


@pytest.mark.timeout(600)
@pytest.mark.usefixtures('started_daemon_client')
@pytest.mark.parametrize('submission', ['workchain', 'graph', 'graph-direct-ir'])
def test_correctness_recover_submitted(submit_and_await, submission) -> None:
    """Daemon submission recovers without any timing harness, one submission mode per case.

    ``workchain`` submits the restart work chain; ``graph`` submits ``GraphProcess`` with
    launch inputs resolved from the authoring handle (``submit_and_await`` only accepts a
    process class, builder, or node, so the handle itself is not submittable -- the helper
    path is the supported authoring submission); ``graph-direct-ir`` submits the same
    process with a pre-serialized declaration ``Dict`` and bare ``graph_inputs``. Every
    mode asserts the same matched provenance as the local run: three step runs on attempts
    ``0, 1, 2``, ``value == 1.5`` passthrough of the shared ``result`` node, and no CREATE
    link from any workflow node.
    """
    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']
    template = compile_graph(handle)
    shared = Float(RECOVER_VALUE)

    if submission == 'workchain':
        node = submit_and_await(
            workchain,
            timeout=DAEMON_TIMEOUT,
            **prepare_restart_wc_inputs(mode='recover', max_iterations=5, result=shared),
        )
        assert not node.is_excepted, node.exception
        assert node.is_finished_ok, (node.exit_status, node.exit_message)
        assert node.outputs.value.value == RECOVER_VALUE
        assert node.outputs.value.uuid == shared.uuid
        _assert_attempt_schedule(node, [0, 1, 2])
        _assert_no_workflow_create(node)
        return

    if submission == 'graph':
        node = submit_and_await(
            GraphProcess,
            timeout=DAEMON_TIMEOUT,
            **handle.get_launch_inputs(**prepare_restart_inputs(mode='recover', max_attempts=5, result=shared)),
        )
    else:
        graph_kwargs = prepare_restart_inputs(mode='recover', max_attempts=5, result=shared)
        node = submit_and_await(
            GraphProcess,
            graph=Dict(dict=template.to_dict()),
            graph_inputs=dict(graph_kwargs),
            timeout=DAEMON_TIMEOUT,
        )
    assert not node.is_excepted, node.exception
    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    assert node.outputs.result.value == RECOVER_VALUE
    assert [value.uuid for value in _successful_step_values(node)] == [shared.uuid]
    _assert_attempt_schedule(node, [0, 1, 2])
    _assert_no_workflow_create(node)
