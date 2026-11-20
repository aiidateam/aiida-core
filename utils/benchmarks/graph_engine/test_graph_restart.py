###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Matched restart correctness and benchmark harness for `graph_restart_programs`.

The work-chain implementation (:class:`RestartBenchmarkWorkChain`) and the graph
implementation (:data:`restartable`) drive the same real child (:class:`FlakyStep`): two
transient failures and then success on ``recover``, an unclaimable failure on ``fatal``,
and endless transient failures on ``always-fail``. The correctness tests pin that parity
at small budgets, including the deliberate vocabulary split (the work chain reports
``401``/``402`` while the graph reports ``400`` through its raising ``ensure``).

Timing modes, all on the ``recover`` scenario with budget five (three step runs):

* ``workchain``: local ``run_get_node`` of the restart work chain.
* ``graph``: local ``run_get_node`` of the authoring ``@graph`` handle.
* ``graph-direct-ir``: local ``run_get_node`` of ``GraphProcess`` with the stored IR
  launch inputs from ``handle.get_launch_inputs`` (same kwargs, lowering outside timing).
* ``workchain-submitted``: daemon ``submit_and_await`` of the restart work chain.
* ``graph-submitted``: daemon ``submit_and_await`` of ``GraphProcess`` with launch inputs
  resolved from the authoring handle per round.
* ``graph-submitted-direct-ir``: daemon ``submit_and_await`` of ``GraphProcess`` with a
  pre-serialized IR ``Dict`` and bare ``graph_inputs`` (the stored-declaration path).
* ``restart-ir``: local lowering-cache hit plus the ``to_dict``/``from_dict`` round trip
  (the IR assembly/serialization cost, kept separate from execution timing).

Setup -- the launch kwargs and, for the graph side, the warmed ``compile_graph(handle)`` lowering
cache -- stays outside the timed region, so the timer covers warm execution only. Local
modes reuse their kwargs across rounds (so the ``graph-direct-ir`` mode relinks the same
stored declaration ``Dict`` after warmup). Daemon modes differ deliberately: the
``graph-submitted`` mode resolves ``get_launch_inputs`` from the authoring handle per round
inside the timed region to keep the authoring path honest, while the ``direct-ir`` mode
keeps the serialized payload template outside timing but builds a fresh declaration ``Dict``
per round inside it.

Rounds: local execution modes run 10 rounds with 1 warmup; daemon modes run 5 rounds with
1 warmup because each round submits through the broker. Benchmarks run serially; never
alongside other ongoing work. Every mode uses supported launch paths only: no mocked
daemon, no global profile changes, and no skips. If a mode cannot launch, it must fail
loudly so the blocker is visible, never pass as a fake skip.

Run correctness only (benchmarks skip by default via ``--benchmark-skip``)::

    uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_matched_restart.py

Run benchmarks only (JSON report for all modes)::

    uv run python -m pytest -p tests.conftest -m presto utils/benchmarks/graph_engine/test_graph_restart.py \
        --benchmark-only \
        --benchmark-json=/tmp/graph-restart-benchmark.json
"""

from __future__ import annotations

import typing as t

import pytest

from aiida.engine.launch import run_get_node
from aiida.engine.processes.graphs.lowering import compile_graph
from aiida.engine.processes.graphs.process import GraphProcess
from aiida.orm import Dict
from utils.benchmarks.graph_engine.programs.matched_restart import (
    RECOVER_VALUE,
    RESTART_BENCHMARKS,
    prepare_restart_inputs,
    prepare_restart_wc_inputs,
)
from utils.benchmarks.graph_engine.test_matched_restart import (
    DAEMON_TIMEOUT,
    _by_type,
)

pytestmark = pytest.mark.presto

BENCHMARK_BUDGET = 5
LOCAL_ROUNDS = 10
LOCAL_WARMUP = 1
DAEMON_ROUNDS = 5
DAEMON_WARMUP = 1


def _local_cases() -> list:
    """Return the local execution benchmark cases."""
    return [
        pytest.param('workchain', marks=pytest.mark.benchmark(group='restart'), id='restart-workchain'),
        pytest.param('graph', marks=pytest.mark.benchmark(group='restart'), id='restart-graph'),
        pytest.param('graph-direct-ir', marks=pytest.mark.benchmark(group='restart'), id='restart-graph-direct-ir'),
    ]


@pytest.mark.timeout(1200)
@pytest.mark.parametrize('implementation', _local_cases())
def test_benchmark_restart_local(benchmark, implementation) -> None:
    """Time warm ``run_get_node`` for one restart implementation (10 rounds, 1 warmup).

    All setup -- the launch kwargs and, for the graph side, the warmed ``compile_graph(handle)``
    lowering cache -- happens outside the timed region for every implementation alike.
    The authoring ``graph`` mode and the ``graph-direct-ir`` mode therefore time the same
    warm execution shape; the direct mode additionally reuses its stored declaration
    ``Dict`` across rounds (relinked after warmup) rather than re-serializing per round.
    """
    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']
    if implementation == 'workchain':
        target = workchain
        kwargs: dict[str, t.Any] = prepare_restart_wc_inputs(mode='recover', max_iterations=BENCHMARK_BUDGET)
    elif implementation == 'graph':
        handle.build()
        target = handle
        kwargs = prepare_restart_inputs(mode='recover', max_attempts=BENCHMARK_BUDGET)
    else:
        handle.build()
        target = GraphProcess
        kwargs = handle.get_launch_inputs(**prepare_restart_inputs(mode='recover', max_attempts=BENCHMARK_BUDGET))

    def _run():
        return run_get_node(target, **kwargs)

    outputs, node = benchmark.pedantic(_run, iterations=1, rounds=LOCAL_ROUNDS, warmup_rounds=LOCAL_WARMUP)

    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    descendants = _by_type(node.called_descendants)
    benchmark.extra_info['provenance'] = {
        'workload': 'restart-recover',
        'implementation': implementation,
        'finished_ok': node.is_finished_ok,
        'graph_nodes': len(descendants.get('GraphNode', [])),
        'workchains': len(descendants.get('WorkChainNode', [])),
        'calcfunctions': len(descendants.get('CalcFunctionNode', [])),
        'calcjobs': len(descendants.get('CalcJobNode', [])),
    }
    if implementation == 'workchain':
        assert outputs['value'].value == RECOVER_VALUE
    else:
        assert outputs['result'].value == RECOVER_VALUE


@pytest.mark.timeout(600)
def test_benchmark_restart_ir(benchmark) -> None:
    """Time the IR assembly/serialization cost separately from execution.

    Each round hits the warmed ``compile_graph(handle)`` cache and runs the ``to_dict`` /
    ``from_dict`` round trip that the stored-declaration (``direct-ir``) launch paths pay.
    The equality check stays outside the timed region so the timer measures the round
    trip itself, not validation overhead (no second serialization inside ``_run``).
    """
    from aiida.engine.processes.graphs.ir import GraphIR

    (handle, _workchain) = RESTART_BENCHMARKS['restart-recover']
    handle.build()

    def _run():
        template = compile_graph(handle)
        payload = template.to_dict()
        restored = GraphIR.from_dict(payload)
        return restored, payload

    restored, payload = benchmark.pedantic(_run, iterations=1, rounds=LOCAL_ROUNDS, warmup_rounds=LOCAL_WARMUP)
    assert restored.to_dict() == payload


def _daemon_cases() -> list:
    """Return the daemon (submitted) benchmark cases."""
    return [
        pytest.param(
            'workchain-submitted', marks=pytest.mark.benchmark(group='restart-daemon'), id='restart-workchain-daemon'
        ),
        pytest.param('graph-submitted', marks=pytest.mark.benchmark(group='restart-daemon'), id='restart-graph-daemon'),
        pytest.param(
            'graph-submitted-direct-ir',
            marks=pytest.mark.benchmark(group='restart-daemon'),
            id='restart-graph-direct-ir-daemon',
        ),
    ]


@pytest.mark.timeout(1800)
@pytest.mark.usefixtures('started_daemon_client')
@pytest.mark.parametrize('implementation', _daemon_cases())
def test_benchmark_restart_daemon(benchmark, submit_and_await, implementation) -> None:
    """Time warm daemon submission for one restart implementation (5 rounds, 1 warmup).

    Uses the ``started_daemon_client`` / ``submit_and_await`` fixtures (ZeroMQ under presto);
    no global profile is modified and no unrelated daemon is touched. The ``graph-submitted``
    mode resolves ``get_launch_inputs`` from the authoring handle per round inside the timed
    region to keep the authoring path honest; the ``direct-ir`` mode keeps the serialized
    payload template outside timing but builds a fresh declaration ``Dict`` per round inside
    it, submitting bare ``graph_inputs`` instead.
    """
    (handle, workchain) = RESTART_BENCHMARKS['restart-recover']
    template = compile_graph(handle)
    wc_kwargs = prepare_restart_wc_inputs(mode='recover', max_iterations=BENCHMARK_BUDGET)
    graph_kwargs = prepare_restart_inputs(mode='recover', max_attempts=BENCHMARK_BUDGET)

    if implementation == 'workchain-submitted':

        def _run():
            return submit_and_await(workchain, timeout=DAEMON_TIMEOUT, **wc_kwargs)

    elif implementation == 'graph-submitted':

        def _run():
            return submit_and_await(GraphProcess, timeout=DAEMON_TIMEOUT, **handle.get_launch_inputs(**graph_kwargs))

    else:
        payload = template.to_dict()

        def _run():
            declaration = Dict(dict=payload)
            return submit_and_await(
                GraphProcess, graph=declaration, graph_inputs=dict(graph_kwargs), timeout=DAEMON_TIMEOUT
            )

    node = benchmark.pedantic(_run, iterations=1, rounds=DAEMON_ROUNDS, warmup_rounds=DAEMON_WARMUP)

    assert node.is_finished_ok, (node.exit_status, node.exit_message)
    descendants = _by_type(node.called_descendants)
    benchmark.extra_info['provenance'] = {
        'workload': 'restart-recover',
        'implementation': implementation,
        'finished_ok': node.is_finished_ok,
        'graph_nodes': len(descendants.get('GraphNode', [])),
        'workchains': len(descendants.get('WorkChainNode', [])),
        'calcfunctions': len(descendants.get('CalcFunctionNode', [])),
        'calcjobs': len(descendants.get('CalcJobNode', [])),
    }
    if implementation == 'workchain-submitted':
        assert node.outputs.value.value == RECOVER_VALUE
    else:
        assert node.outputs.result.value == RECOVER_VALUE
