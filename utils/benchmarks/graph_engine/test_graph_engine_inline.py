###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Matched correctness and benchmark harness for the inline-operation graph workloads.

Each of the five workloads in :mod:`tests.benchmark.test_engine` (``WORKCHAINS``) has an
original-graph equivalent in :mod:`utils.benchmarks.graph_engine.programs.matched` (``GRAPH_BENCHMARKS``) and an
inline-operation equivalent in :mod:`utils.benchmarks.graph_engine.programs.matched_inline`
(``GRAPH_BENCHMARKS_INLINE``). All three preserve the observable workload: the same number of loop
iterations, child-graph equivalents, and ``ArithmeticAddCalculation`` placements with ``x=1`` and
``y=2``. The inline variants drive control state with expressions (``iterations - 1``,
``iterations > 0``) instead of ``decrement``/``is_positive`` tasks; the scientific placements
(``add_calc`` and the ``par_map`` collector) stay explicit tasks.

Correctness pins that correspondence at ``n=4`` across the three implementations. Supported graph
execution always stores its provenance, so every case runs with provenance on.

Benchmarks time ``run_get_node`` for each (workload, implementation) pair with the same runner
protocol as the existing suites: everything before ``benchmark.pedantic`` -- the ``InstalledCode``,
the prepared launch kwargs, and (graph sides) ``compile_graph(handle)`` -- stays outside the timed region,
so the timer covers warm execution only. Only ``run_get_node`` in the local runner is timed
(no daemon, no ``xdist``); run benchmarks serially.

Run correctness only (benchmarks skip by default via ``--benchmark-skip``)::

    uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_matched_inline.py

Run benchmarks only (never together with other ongoing work)::

    uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_graph_engine_inline.py \
        --benchmark-only \
        --benchmark-json=/tmp/graph-engine-inline-benchmark.json

``--benchmark-only`` also overrides the ``--benchmark-skip`` default from ``addopts`` and
deselects the correctness tests by itself, so no ``-k`` filter is needed.
"""

from __future__ import annotations

import pytest

from aiida.engine.launch import run_get_node
from utils.benchmarks.graph_engine.test_matched import (
    _by_type,
    _make_code,
)
from utils.benchmarks.graph_engine.test_matched_inline import (
    _ALL_WORKLOADS,
    _expected_outputs,
    _prepare_case,
)

pytestmark = pytest.mark.presto

ROUNDS = 10
WARMUP = 1


def _benchmark_cases() -> list:
    """Return the (workload, implementation) cases, grouped per workload for comparison."""
    return [
        pytest.param(name, implementation, marks=pytest.mark.benchmark(group=name), id=f'{implementation}-{name}')
        for name in _ALL_WORKLOADS
        for implementation in ('workchain', 'graph', 'inline')
    ]


@pytest.mark.timeout(1200)
@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize(('workload', 'implementation'), _benchmark_cases())
def test_benchmark_inline(benchmark, aiida_localhost, workload, implementation) -> None:
    """Time one (workload, implementation) pair (10 rounds, 1 warmup, 1 iteration).

    All setup -- the ``/bin/bash`` code, the prepared launch kwargs, and (graph sides) the warmed
    ``compile_graph(handle)`` lowering cache -- happens outside the timed region for all three
    implementations alike, so the timer covers warm execution only. Benchmarks run serially in the
    local runner; enable them explicitly (see module docstring) and never alongside other ongoing work.
    """
    code = _make_code(aiida_localhost)
    target, kwargs = _prepare_case(workload, implementation, code)

    def _run():
        return run_get_node(target, **kwargs)

    outputs, node = benchmark.pedantic(_run, iterations=1, rounds=ROUNDS, warmup_rounds=WARMUP)

    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    _expected_outputs(workload, implementation, outputs)
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
