###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Correctness and provenance checks for matched WorkChain and graph workloads.

Timing harnesses are kept separately in ``utils/benchmarks/graph_engine/test_graph_engine_inline.py``.
"""

from __future__ import annotations

import itertools
import typing as t

import pytest

from aiida.common.links import LinkType
from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.orm import CalcJobNode, GraphNode, Int, ProcessNode, WorkChainNode
from tests.benchmark.test_engine import WORKCHAINS
from utils.benchmarks.graph_engine.programs.matched import GRAPH_BENCHMARKS, prepare_benchmark_inputs
from utils.benchmarks.graph_engine.programs.matched_inline import (
    GRAPH_BENCHMARKS_INLINE,
    prepare_benchmark_inputs_inline,
    validate_benchmarks_inline,
)
from utils.benchmarks.graph_engine.test_matched import (
    _assert_calcjobs_success,
    _assert_no_workflow_create,
    _by_type,
    _make_code,
)

pytestmark = pytest.mark.presto

#: Benchmark size shared by all three implementations in every matched comparison.
BENCHMARK_SIZE = 4

_ALL_WORKLOADS = tuple(GRAPH_BENCHMARKS_INLINE)
assert set(_ALL_WORKLOADS) == set(GRAPH_BENCHMARKS) == set(WORKCHAINS)

_DYNAMIC_WORKLOADS = ('basic-loop', 'serial-wc-loop', 'threaded-wc-loop', 'serial-calcjob-loop')
_CALCJOB_WORKLOADS = ('serial-calcjob-loop', 'threaded-calcjob-loop')
_NO_RETURN_INLINE = ('basic-loop', 'serial-wc-loop', 'serial-calcjob-loop')

# Expected descendant counts at ``BENCHMARK_SIZE`` on the inline side. Control state is ephemeral
# orchestration state, never a child process: basic and serial control loops run root-only, the map
# keeps its single collector calcfunction, and the calcjob loops place four direct calculations.
# basic-loop: no tasks at all. serial-wc-loop: 4 x one_loop_inline scopes, inline only.
# threaded-wc-loop: 4 inline scopes + 1 collector. serial/threaded-calcjob-loop: 4 direct placements.
_EXPECTED_INLINE: dict[str, dict[str, int]] = {
    'basic-loop': {'graphs': 0, 'calcfunctions': 0, 'calcjobs': 0},
    'serial-wc-loop': {'graphs': 0, 'calcfunctions': 0, 'calcjobs': 0},
    'threaded-wc-loop': {'graphs': 0, 'calcfunctions': 1, 'calcjobs': 0},
    'serial-calcjob-loop': {'graphs': 0, 'calcfunctions': 0, 'calcjobs': 4},
    'threaded-calcjob-loop': {'graphs': 0, 'calcfunctions': 0, 'calcjobs': 4},
}

# Expected descendant counts on the original-graph side (see ``test_graph_engine``) and the
# ``WORKCHAINS`` child counts, repeated here so one test pins all three implementations together.
_EXPECTED_GRAPH: dict[str, dict[str, int]] = {
    'basic-loop': {'graphs': 0, 'calcfunctions': 9, 'calcjobs': 0},
    'serial-wc-loop': {'graphs': 0, 'calcfunctions': 21, 'calcjobs': 0},
    'threaded-wc-loop': {'graphs': 0, 'calcfunctions': 13, 'calcjobs': 0},
    'serial-calcjob-loop': {'graphs': 0, 'calcfunctions': 9, 'calcjobs': 4},
    'threaded-calcjob-loop': {'graphs': 0, 'calcfunctions': 0, 'calcjobs': 4},
}
_EXPECTED_WORKFLOWS = {'serial-wc-loop': 4, 'threaded-wc-loop': 4}
_EXPECTED_CALCJOBS = {'serial-calcjob-loop': 4, 'threaded-calcjob-loop': 4}


def _assert_calcjobs_sequential(node: ProcessNode, count: int) -> None:
    """Assert the ``count`` CalcJobs ran one after another, not in parallel.

    The serial calcjob loop places its calculation with no data dependency on the
    inline counter step, so only the loop iteration barrier keeps iterations
    sequential: the next iteration scope starts only after the previous scope --
    calculation included -- completes. Each later placement is therefore created
    no earlier than the previous placement finished, i.e. ``ctime`` is ordered
    and never precedes the previous ``mtime``.
    """
    calcjobs = [child for child in node.called_descendants if isinstance(child, CalcJobNode)]
    assert len(calcjobs) == count
    ordered = sorted(calcjobs, key=lambda calcjob: (calcjob.ctime, calcjob.pk))
    assert [calcjob.pk for calcjob in ordered] == sorted(calcjob.pk for calcjob in calcjobs)
    for previous, nxt in itertools.pairwise(ordered):
        assert nxt.ctime is not None and previous.mtime is not None
        assert nxt.ctime >= previous.mtime, (
            f'serial calcjobs must dispatch in iteration order: {previous.pk} mtime={previous.mtime} '
            f'precedes {nxt.pk} ctime={nxt.ctime}'
        )


def _expected_outputs(workload: str, implementation: str, outputs: dict[str, t.Any]) -> None:
    """Assert the observable outputs match the stored-provenance contract for one implementation."""
    if implementation == 'workchain':
        assert dict(outputs) == {}
    elif implementation == 'graph':
        if workload in ('basic-loop', 'serial-wc-loop', 'serial-calcjob-loop'):
            assert outputs['result'].value == 0
        elif workload == 'threaded-wc-loop':
            assert [item.value for item in outputs['result']] == [0] * BENCHMARK_SIZE
        elif workload == 'threaded-calcjob-loop':
            assert {label: outputs[label].value for label in ('first', 'second', 'third', 'fourth')} == {
                'first': 3,
                'second': 3,
                'third': 3,
                'fourth': 3,
            }
    elif workload in _NO_RETURN_INLINE:
        # Empty-output inline graphs behave like the original work chains: nothing to return.
        # The language still requires the declared ``return {}``.
        assert dict(outputs) == {}
    elif workload == 'threaded-wc-loop':
        assert [item.value for item in outputs['result']] == [0] * BENCHMARK_SIZE
    elif workload == 'threaded-calcjob-loop':
        assert {label: outputs[label].value for label in ('first', 'second', 'third', 'fourth')} == {
            'first': 3,
            'second': 3,
            'third': 3,
            'fourth': 3,
        }


def _prepare_case(workload: str, implementation: str, code) -> tuple[t.Any, dict[str, t.Any]]:
    """Return the launch target and kwargs; graph builds stay outside any timed region."""
    if implementation == 'workchain':
        workchain_class, iterations, _outgoing = WORKCHAINS[workload]
        assert iterations == BENCHMARK_SIZE
        return workchain_class, {'iterations': Int(iterations), 'code': code}
    if implementation == 'graph':
        handle, graph_iterations = GRAPH_BENCHMARKS[workload]
        assert graph_iterations == BENCHMARK_SIZE
        handle.build()
        return handle, prepare_benchmark_inputs(workload, code)
    assert implementation == 'inline'
    handle, inline_iterations = GRAPH_BENCHMARKS_INLINE[workload]
    assert inline_iterations == BENCHMARK_SIZE
    handle.build()
    return handle, prepare_benchmark_inputs_inline(workload, code)


@pytest.mark.parametrize('name', _ALL_WORKLOADS)
def test_inline_templates(name) -> None:
    """The serialized inline GraphIR each benchmark executes matches its lowered source template."""
    from aiida.engine.processes.graphs.ir import GraphIR

    (handle, _iterations) = GRAPH_BENCHMARKS_INLINE[name]
    counts = validate_benchmarks_inline()
    assert set(counts) == set(GRAPH_BENCHMARKS_INLINE)
    template = compile_graph(handle)
    assert GraphIR.from_dict(template.to_dict()).to_dict() == template.to_dict()
    if name == 'threaded-calcjob-loop':
        assert counts[name] == 4
    elif name in ('serial-wc-loop', 'serial-calcjob-loop'):
        assert counts[name] == 1


def _correctness_cases() -> list:
    """Return the (workload, implementation) cases."""
    return [
        pytest.param(name, implementation, id=f'{implementation}-{name}')
        for name in _ALL_WORKLOADS
        for implementation in ('workchain', 'graph', 'inline')
    ]


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(('workload', 'implementation'), _correctness_cases())
def test_correctness_inline_matched(aiida_localhost, workload, implementation) -> None:
    """All three implementations finish the workload with matching observable provenance.

    Each case runs with provenance on: finished ok, the documented outputs per implementation
    (work chains and empty-output inline graphs return nothing -- the latter via an explicit
    ``return {}``; original graphs return their counters/collections; the inline map
    returns its collector-built container and the inline threaded calcjobs return their sums), the
    ``WORKCHAINS`` child counts, the exact ``sum == 3`` calcjob contract, no child graph node anywhere
    (one ``GraphProcess`` runs every scope), a stored declaration identical to the lowered template,
    and no CREATE link from any workflow node.
    """
    from aiida.engine.processes.graphs.ir import GraphIR

    code = _make_code(aiida_localhost)
    target, kwargs = _prepare_case(workload, implementation, code)

    outputs, node = run_get_node(target, **kwargs)

    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    _expected_outputs(workload, implementation, outputs)
    if isinstance(node, GraphNode):
        stored = node.base.links.get_incoming(link_type=LinkType.INPUT_WORK).get_node_by_label('graph')
        if implementation == 'graph':
            (handle, _) = GRAPH_BENCHMARKS[workload]
        else:
            (handle, _) = GRAPH_BENCHMARKS_INLINE[workload]
        assert GraphIR.from_dict(stored.get_dict()).to_dict() == compile_graph(handle).to_dict()
    if implementation == 'workchain':
        assert isinstance(node, WorkChainNode)
        called = _by_type(node.called)
        descendants = _by_type(node.called_descendants)
        assert len(descendants.get('WorkChainNode', [])) == _EXPECTED_WORKFLOWS.get(workload, 0)
        assert len(descendants.get('CalcJobNode', [])) == _EXPECTED_CALCJOBS.get(workload, 0)
        if workload in ('serial-wc-loop', 'threaded-wc-loop'):
            assert len(called.get('WorkChainNode', [])) == 4
        if workload in _CALCJOB_WORKLOADS:
            assert len(called.get('CalcJobNode', [])) == 4
            _assert_calcjobs_success(node, 4)
    else:
        assert isinstance(node, GraphNode)
        expected = _EXPECTED_GRAPH[workload] if implementation == 'graph' else _EXPECTED_INLINE[workload]
        descendants = _by_type(node.called_descendants)
        assert len(descendants.get('GraphNode', [])) == expected['graphs']
        assert len(descendants.get('CalcFunctionNode', [])) == expected['calcfunctions']
        assert len(descendants.get('CalcJobNode', [])) == expected['calcjobs']
        direct = _by_type(node.called)
        # One process runs every scope, so every task and collector is a direct child.
        assert len(direct.get('GraphNode', [])) == 0
        if implementation == 'inline':
            if workload in ('basic-loop', 'serial-wc-loop'):
                # Root-only control loops: no child processes at all.
                assert node.called == []
            elif workload == 'threaded-wc-loop':
                # One inline scope per element plus the single result collector.
                assert len(direct.get('CalcFunctionNode', [])) == 1
            elif workload == 'serial-calcjob-loop':
                # Four sequential calculations, no control-state tasks; the loop barrier (not a
                # data dependency on the unused ``total``) keeps iterations sequential.
                assert len(direct.get('CalcFunctionNode', [])) == 0
                assert len(direct.get('CalcJobNode', [])) == 4
                _assert_calcjobs_sequential(node, 4)
            elif workload == 'threaded-calcjob-loop':
                assert len(direct.get('CalcJobNode', [])) == 4
        if workload in _CALCJOB_WORKLOADS:
            _assert_calcjobs_success(node, 4)
    _assert_no_workflow_create(node)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('name', _DYNAMIC_WORKLOADS)
@pytest.mark.parametrize('count', [0, 1])
def test_inline_bounds_zero_one(aiida_localhost, name, count) -> None:
    """The resizable inline workloads accept the 0/1 bounds with provenance on.

    Zero iterations run no placements and return the identity result (``{}`` for empty-output
    graphs, an empty container for the map); one iteration runs exactly one placement (one nested
    scope, or one successful ``sum == 3`` calcjob for the serial calcjob loop).
    ``threaded-calcjob-loop`` is statically unrolled and covered by ``test_inline_templates``.
    """
    code = _make_code(aiida_localhost)
    (handle, _) = GRAPH_BENCHMARKS_INLINE[name]
    outputs, node = run_get_node(handle, **prepare_benchmark_inputs_inline(name, code, iterations=count))
    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    if name in _NO_RETURN_INLINE:
        assert dict(outputs) == {}
    elif name == 'threaded-wc-loop':
        assert [item.value for item in outputs['result']] == [0] * count
    descendants = _by_type(node.called_descendants)
    assert len(descendants.get('CalcJobNode', [])) == (count if name == 'serial-calcjob-loop' else 0)
    if name == 'serial-calcjob-loop':
        _assert_calcjobs_success(node, count)
        if count:
            _assert_calcjobs_sequential(node, count)
    _assert_no_workflow_create(node)
