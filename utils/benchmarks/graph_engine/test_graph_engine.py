###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Matched correctness checks and benchmark harness for the engine benchmark workloads.

Each of the five workloads in :mod:`tests.benchmark.test_engine` (``WORKCHAINS``) has a graph equivalent in
:mod:`utils.benchmarks.graph_engine.programs.matched` (``GRAPH_BENCHMARKS``) that preserves the observable workload:
the same number of loop iterations, child-graph equivalents, and ``ArithmeticAddCalculation`` placements
with ``x=1`` and ``y=2``. Correctness tests in ``utils/benchmarks/graph_engine/test_matched.py`` pin that
correspondence at ``n=4`` for both implementations. The benchmark tests time ``run_get_node`` for the five
workloads times the two implementations (ten cases), grouped per workload so each
``workchain-*`` case compares directly against its ``graph-*`` counterpart.

Semantic overhead caveats (so benchmark deltas are read as workload-matched, not operation-identical):

* Graphs always declare outputs while the originals return nothing; loop benchmarks return their final counter and the
  threaded benchmarks return their collected results.
* Graph loop state rewinds through tasks, so every loop benchmark spends one ``decrement`` plus one ``is_positive``
  calcfunction task per iteration (plus one final ``is_positive`` check that exits the loop). The originals keep
  ``counter``/``iter`` in memory and run zero tasks per no-op step.
* One ``GraphProcess`` executes the whole graph: nested graphs, loop iterations, branch arms, and map elements run
  as scopes of that process with hierarchical call labels, never as child graph nodes. Each ``par_map`` collection
  still dispatches one collector calcfunction that creates the result container, which has no original counterpart.
* ``threaded-calcjob-loop`` is statically unrolled to exactly four placements (see ``graph_programs``); requesting any
  other iteration count raises ``ValueError`` on the graph side only.
* Calcjob placements on the graph side require per-placement ``metadata.options`` (``resources``/``withmpi``) under
  ``task_metadata``; the ``WorkChain`` originals submit without explicit options. Both sides run the real
  ``ArithmeticAddCalculation`` with ``filepath_executable='/bin/bash'`` so every calculation parses ``sum == 3``.

Benchmark timing notes:

* Everything before ``benchmark.pedantic`` -- the ``InstalledCode``, the prepared launch kwargs, and (graph side)
  ``handle.build()`` -- stays outside the timed region for both implementations alike. ``build()`` warms the lowering
  cache, so the timed region covers warm execution, matching the already-defined ``WorkChain`` classes.
* Only ``run_get_node`` in the local runner is timed (no daemon, no ``xdist``); run benchmarks serially.

Run correctness only (benchmarks skip by default via ``--benchmark-skip``)::

    uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_matched.py

Run benchmarks only (never together with other ongoing work)::

    uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_graph_engine.py \
        --benchmark-only \
        --benchmark-json=/tmp/graph-engine-benchmark.json

``--benchmark-only`` also overrides the ``--benchmark-skip`` default from ``addopts`` (``--benchmark-enable``
only overrides ``--benchmark-disable``) and deselects the correctness tests by itself, so no ``-k`` filter is
needed.
"""

from __future__ import annotations

import typing as t

import pytest

from aiida.engine.launch import run_get_node
from aiida.orm import Int
from tests.benchmark.test_engine import WORKCHAINS
from utils.benchmarks.graph_engine.programs.matched import (
    GRAPH_BENCHMARKS,
    prepare_benchmark_inputs,
)
from utils.benchmarks.graph_engine.test_matched import (
    _ALL_WORKLOADS,
    _by_type,
    _make_code,
)

pytestmark = pytest.mark.presto


def _benchmark_cases() -> list:
    """Return the ten (workload, implementation) cases, each grouped per workload for comparison."""
    cases = []
    for name in _ALL_WORKLOADS:
        cases.append(pytest.param(name, 'workchain', marks=pytest.mark.benchmark(group=name), id=f'workchain-{name}'))
        cases.append(pytest.param(name, 'graph', marks=pytest.mark.benchmark(group=name), id=f'graph-{name}'))
    return cases


@pytest.mark.timeout(1200)
@pytest.mark.parametrize(('workload', 'implementation'), _benchmark_cases())
def test_benchmark(benchmark, aiida_localhost, workload, implementation) -> None:
    """Time ``run_get_node`` for one workload/implementation pair (10 rounds, 1 warmup, 1 iteration).

    All setup -- the ``/bin/bash`` code, the prepared launch kwargs, and (graph side) the warmed
    ``compile_graph(handle)`` lowering cache -- happens outside the timed region for both implementations alike,
    so the timer covers warm execution only. Benchmarks run serially in the local runner; enable them
    explicitly (see module docstring) and never alongside other ongoing work.
    """
    code = _make_code(aiida_localhost)
    if implementation == 'workchain':
        workchain_class, iterations, _outgoing = WORKCHAINS[workload]
        target = workchain_class
        kwargs: dict[str, t.Any] = {'iterations': Int(iterations), 'code': code}
    else:
        handle, _iterations = GRAPH_BENCHMARKS[workload]
        handle.build()
        target = handle
        kwargs = prepare_benchmark_inputs(workload, code)

    def _run():
        return run_get_node(target, **kwargs)

    outputs, node = benchmark.pedantic(_run, iterations=1, rounds=10, warmup_rounds=1)

    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    if implementation == 'graph' and workload in ('basic-loop', 'serial-wc-loop', 'serial-calcjob-loop'):
        assert outputs['result'].value == 0
    descendants = _by_type(node.called_descendants)
    benchmark.extra_info['provenance'] = {
        'workload': workload,
        'implementation': implementation,
        'finished_ok': node.is_finished_ok,
        'graph_nodes': len(descendants.get('GraphNode', [])),
        'workchains': len(descendants.get('WorkChainNode', [])),
        'calcfunctions': len(descendants.get('CalcFunctionNode', [])),
        'calcjobs': len(descendants.get('CalcJobNode', [])),
    }
