###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Correctness and provenance checks for matched WorkChain and graph workloads.

Timing harnesses are kept separately in ``utils/benchmarks/graph_engine/test_graph_engine.py``.
"""

from __future__ import annotations

import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.orm import CalcJobNode, GraphNode, InstalledCode, Int, WorkChainNode
from aiida.orm.nodes.process.process import ProcessNode
from tests.benchmark.test_engine import WORKCHAINS
from utils.benchmarks.graph_engine.programs.matched import (
    GRAPH_BENCHMARKS,
    prepare_benchmark_inputs,
    validate_benchmarks,
)

pytestmark = pytest.mark.presto

#: Benchmark size shared by both implementations in every matched comparison.
BENCHMARK_SIZE = 4

_DYNAMIC_WORKLOADS = ('basic-loop', 'serial-wc-loop', 'threaded-wc-loop', 'serial-calcjob-loop')
_CALCJOB_WORKLOADS = ('serial-calcjob-loop', 'threaded-calcjob-loop')
_ALL_WORKLOADS = tuple(GRAPH_BENCHMARKS)

# Expected descendant counts at ``BENCHMARK_SIZE`` on the graph side. One
# ``GraphProcess`` runs everything, so there are no child graph nodes; every
# task and collector is a direct child with a hierarchical call label. Each loop
# benchmark spends one ``decrement`` plus one ``is_positive`` calcfunction per
# iteration plus one final ``is_positive`` check, so:
# basic-loop: 4 + 4 checks + 1 final = 9 calcfunctions.
# serial-wc-loop: per iteration 1 body check + one_loop (2 checks + 1
#   decrement) + 1 wc_step decrement = 5 calcfunctions (x4 = 20) + 1 final = 21.
# threaded-wc-loop: 4 x one_loop (2 checks + 1 decrement) = 12 + 1 par_map
#   collector = 13.
# serial-calcjob-loop: loop shape of basic-loop (9 tasks) + 4 direct
#   ArithmeticAddCalculation placements, one per calc_step.
# threaded-calcjob-loop: 4 direct placements in a single step, no tasks at all.
_EXPECTED_GRAPH: dict[str, dict[str, int]] = {
    'basic-loop': {'graphs': 0, 'calcfunctions': 9, 'calcjobs': 0},
    'serial-wc-loop': {'graphs': 0, 'calcfunctions': 21, 'calcjobs': 0},
    'threaded-wc-loop': {'graphs': 0, 'calcfunctions': 13, 'calcjobs': 0},
    'serial-calcjob-loop': {'graphs': 0, 'calcfunctions': 9, 'calcjobs': 4},
    'threaded-calcjob-loop': {'graphs': 0, 'calcfunctions': 0, 'calcjobs': 4},
}

# Expected descendant counts at ``BENCHMARK_SIZE`` on the WorkChain side, mirroring
# the ``outgoing`` contract of ``WORKCHAINS``: the wc loops submit four child
# WorkChains (serially or in one step), the calcjob loops submit four CalcJobs,
# and the basic loop submits nothing.
_EXPECTED_WORKFLOWS = {'basic-loop': 0, 'serial-wc-loop': 4, 'threaded-wc-loop': 4}
_EXPECTED_CALCJOBS = {'serial-calcjob-loop': 4, 'threaded-calcjob-loop': 4}


def _make_code(aiida_localhost) -> InstalledCode:
    """Return the ``/bin/bash`` arithmetic code both implementations execute successfully."""
    return InstalledCode(
        default_calc_job_plugin='core.arithmetic.add', computer=aiida_localhost, filepath_executable='/bin/bash'
    )


def _by_type(nodes: t.Iterable[ProcessNode]) -> dict[str, list[ProcessNode]]:
    """Bucket process nodes by class name for structural assertions."""
    bucketed: dict[str, list[ProcessNode]] = {}
    for node in nodes:
        bucketed.setdefault(type(node).__name__, []).append(node)
    return bucketed


def _assert_no_workflow_create(node: ProcessNode) -> None:
    """Assert no workflow node in the tree carries a CREATE link (workflows only RETURN)."""
    for child in (node, *node.called_descendants):
        if isinstance(child, (WorkChainNode, GraphNode)):
            assert child.base.links.get_outgoing(link_type=LinkType.CREATE).all() == []


def _assert_calcjobs_success(node: ProcessNode, count: int) -> None:
    """Assert exactly ``count`` CalcJob descendants, all finished with ``sum == 3`` (``x=1``, ``y=2``)."""
    calcjobs = [child for child in node.called_descendants if isinstance(child, CalcJobNode)]
    assert len(calcjobs) == count
    for calcjob in calcjobs:
        assert calcjob.is_finished_ok, (calcjob.exit_status, calcjob.exit_message)
        assert calcjob.outputs.sum.value == 3


@pytest.mark.parametrize('name', _ALL_WORKLOADS)
def test_graph_templates(name) -> None:
    """The serialized GraphIR each benchmark executes matches its lowered source template.

    ``validate_benchmarks`` pins the static placement contracts (four direct unrolled placements for
    ``threaded-calcjob-loop``, one call per serial loop body, the unary ``par_map`` shape), and the
    ``to_dict``/``from_dict`` round trip proves the stored declaration that ``GraphProcess`` executes is
    representative of ``compile_graph(handle)`` rather than a divergent copy.
    """
    from aiida.engine.processes.graphs.ir import GraphIR

    (handle, _iterations) = GRAPH_BENCHMARKS[name]
    counts = validate_benchmarks()
    assert set(counts) == set(GRAPH_BENCHMARKS)
    template = compile_graph(handle)
    assert GraphIR.from_dict(template.to_dict()).to_dict() == template.to_dict()
    if name == 'threaded-calcjob-loop':
        assert counts[name] == 4
    elif name in ('serial-wc-loop', 'serial-calcjob-loop'):
        assert counts[name] == 1


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('name', _ALL_WORKLOADS)
def test_correctness_matched(aiida_localhost, name) -> None:
    """Both implementations finish the workload at ``n=4`` with matching observable provenance.

    WorkChain side: finished ok, no outputs (the originals return nothing), the ``WORKCHAINS`` child counts
    (four child workflows or four calcjobs), and the exact ``sum == 3`` calcjob contract.
    Graph side: finished ok, the documented workload outputs, no child graph node anywhere (one
    ``GraphProcess`` runs every scope), the exact ``sum == 3`` calcjob contract, a stored declaration
    identical to the lowered template, and no CREATE link from any workflow node on either side.
    """
    from aiida.engine.processes.graphs.ir import GraphIR

    code = _make_code(aiida_localhost)

    workchain_class, iterations, _outgoing = WORKCHAINS[name]
    assert iterations == BENCHMARK_SIZE
    wc_outputs, wc_node = run_get_node(workchain_class, iterations=Int(iterations), code=code)
    assert wc_node.is_finished_ok, (wc_node.exit_status, wc_node.exit_message)
    assert isinstance(wc_node, WorkChainNode)
    assert dict(wc_outputs) == {}
    wc_called = _by_type(wc_node.called)
    wc_descendants = _by_type(wc_node.called_descendants)
    assert len(wc_descendants.get('WorkChainNode', [])) == _EXPECTED_WORKFLOWS.get(name, 0)
    assert len(wc_descendants.get('CalcJobNode', [])) == _EXPECTED_CALCJOBS.get(name, 0)
    if name in ('serial-wc-loop', 'threaded-wc-loop'):
        assert len(wc_called.get('WorkChainNode', [])) == 4
    if name in _CALCJOB_WORKLOADS:
        assert len(wc_called.get('CalcJobNode', [])) == 4
        _assert_calcjobs_success(wc_node, 4)
    _assert_no_workflow_create(wc_node)

    handle, graph_iterations = GRAPH_BENCHMARKS[name]
    assert graph_iterations == BENCHMARK_SIZE
    graph_outputs, graph_node = run_get_node(handle, **prepare_benchmark_inputs(name, code))
    assert graph_node.is_finished_ok, (graph_node.exit_status, graph_node.exit_message)
    assert isinstance(graph_node, GraphNode)
    stored = graph_node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph')
    assert GraphIR.from_dict(stored.get_dict()).to_dict() == compile_graph(handle).to_dict()
    if name in ('basic-loop', 'serial-wc-loop', 'serial-calcjob-loop'):
        assert graph_outputs['result'].value == 0
    elif name == 'threaded-wc-loop':
        assert [item.value for item in graph_outputs['result']] == [0] * BENCHMARK_SIZE
    elif name == 'threaded-calcjob-loop':
        assert {label: graph_outputs[label].value for label in ('first', 'second', 'third', 'fourth')} == {
            'first': 3,
            'second': 3,
            'third': 3,
            'fourth': 3,
        }
    expected = _EXPECTED_GRAPH[name]
    descendants = _by_type(graph_node.called_descendants)
    assert len(descendants.get('GraphNode', [])) == expected['graphs']
    assert len(descendants.get('CalcFunctionNode', [])) == expected['calcfunctions']
    assert len(descendants.get('CalcJobNode', [])) == expected['calcjobs']
    direct = _by_type(graph_node.called)
    # One process runs every scope, so every task and collector is a direct child.
    assert len(direct.get('GraphNode', [])) == 0
    if name == 'basic-loop':
        # The entry condition check plus four iterations of decrement and check.
        assert len(direct.get('CalcFunctionNode', [])) == 9
    elif name == 'serial-wc-loop':
        # The entry check plus four iterations of body check, one_loop, and counter step.
        assert len(direct.get('CalcFunctionNode', [])) == 21
    elif name == 'serial-calcjob-loop':
        # The entry check plus four iterations of calculation step and condition update.
        assert len(direct.get('CalcFunctionNode', [])) == 9
        assert len(direct.get('CalcJobNode', [])) == 4
    elif name == 'threaded-wc-loop':
        # One one_loop body per element plus the single result collector.
        assert len(direct.get('CalcFunctionNode', [])) == 13
    elif name == 'threaded-calcjob-loop':
        assert len(direct.get('CalcJobNode', [])) == 4
    if name in _CALCJOB_WORKLOADS:
        _assert_calcjobs_success(graph_node, 4)
    _assert_no_workflow_create(graph_node)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('name', _DYNAMIC_WORKLOADS)
@pytest.mark.parametrize('count', [0, 1])
def test_bounds_zero_one(aiida_localhost, name, count) -> None:
    """The resizable workloads accept the 0/1 bounds on both implementations.

    Zero iterations run no placements and return the identity result; one iteration runs exactly one
    placement (one child workflow, or one successful ``sum == 3`` calcjob for the serial calcjob loop).
    ``threaded-calcjob-loop`` is statically unrolled and covered by ``test_threaded_calcjob_static``.
    """
    code = _make_code(aiida_localhost)

    workchain_class, _iterations, _outgoing = WORKCHAINS[name]
    wc_outputs, wc_node = run_get_node(workchain_class, iterations=Int(count), code=code)
    assert wc_node.is_finished_ok, (wc_node.exit_status, wc_node.exit_message)
    assert dict(wc_outputs) == {}
    wc_descendants = _by_type(wc_node.called_descendants)
    if name in ('serial-wc-loop', 'threaded-wc-loop'):
        assert len(wc_descendants.get('WorkChainNode', [])) == count
    elif name == 'serial-calcjob-loop':
        assert len(wc_descendants.get('CalcJobNode', [])) == count
        _assert_calcjobs_success(wc_node, count)
    else:
        assert wc_node.called == []
    _assert_no_workflow_create(wc_node)

    handle, _graph_iterations = GRAPH_BENCHMARKS[name]
    graph_outputs, graph_node = run_get_node(handle, **prepare_benchmark_inputs(name, code, iterations=count))
    assert graph_node.is_finished_ok, (graph_node.exit_status, graph_node.exit_message)
    if name in ('basic-loop', 'serial-wc-loop', 'serial-calcjob-loop'):
        assert graph_outputs['result'].value == 0
    elif name == 'threaded-wc-loop':
        assert [item.value for item in graph_outputs['result']] == [0] * count
    graph_descendants = _by_type(graph_node.called_descendants)
    assert len(graph_descendants.get('CalcJobNode', [])) == (count if name == 'serial-calcjob-loop' else 0)
    if name == 'serial-calcjob-loop':
        _assert_calcjobs_success(graph_node, count)
    _assert_no_workflow_create(graph_node)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_threaded_calcjob_static(aiida_localhost) -> None:
    """The statically unrolled graph benchmark rejects any size but four and requires its code."""
    code = _make_code(aiida_localhost)
    for bad in (0, 1, 3, 5):
        with pytest.raises(ValueError, match='statically unrolled'):
            prepare_benchmark_inputs('threaded-calcjob-loop', code, iterations=bad)
    with pytest.raises(ValueError, match='needs the installed `code`'):
        prepare_benchmark_inputs('threaded-calcjob-loop')
    with pytest.raises(ValueError, match='needs the installed `code`'):
        prepare_benchmark_inputs('serial-calcjob-loop')
    with pytest.raises(KeyError):
        prepare_benchmark_inputs('not-a-benchmark', code)
