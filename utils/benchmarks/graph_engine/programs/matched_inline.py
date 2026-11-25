###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph equivalents of the engine benchmarks using inline operations.

Each workload in :mod:`tests.benchmark.test_engine` (``WORKCHAINS``) has one
``@graph`` counterpart below that matches the observable workload -- the same
number of loop iterations, child-graph equivalents, and
``ArithmeticAddCalculation`` placements with ``x=1`` and ``y=2`` -- but drives
control state with inline expressions (``iterations - 1``, ``iterations > 0``)
instead of ``decrement``/``is_positive`` tasks.

This module requires the inline-operations lowering: numeric arithmetic
``+ - * // %``, comparisons ``< <= > >= == !=``, unary ``+ - not``, and
``while n > 0: n = n - 1``. Explicit ``@task`` functions are never inlined;
the scientific placements (``add_calc`` and the ``par_map`` collector) stay
explicit tasks. Inline results are ephemeral orchestration state: checkpointed
with the scope but never stored as data nodes and never linked. The root graph
therefore never returns a newly computed scalar; basic and serial variants
declare no outputs explicitly with ``return {}``, while the map variant returns
its collector-built container and the threaded calcjob variant returns its
task outputs.

How to invoke each benchmark::

    from aiida.engine.launch import run_get_node
    from utils.benchmarks.graph_engine.programs.matched_inline import (
        GRAPH_BENCHMARKS_INLINE, prepare_benchmark_inputs_inline,
    )

    handle, iterations = GRAPH_BENCHMARKS_INLINE['serial-calcjob-loop']
    outputs, node = run_get_node(handle, **prepare_benchmark_inputs_inline('serial-calcjob-loop', code))

``prepare_benchmark_inputs_inline`` also accepts ``iterations`` to resize the
dynamic benchmarks. ``validate_benchmarks_inline`` pins the static placement
contracts: no control-state tasks, one step wrapper per serial iteration,
one map with its collector, and four direct ``ArithmeticAddCalculation``
placements for the threaded calcjob benchmark.

Like the originals, the calcjob benchmarks run the real
``ArithmeticAddCalculation`` with ``x=1`` and ``y=2``. Both sides use
``filepath_executable='/bin/bash'`` so each calculation parses ``sum == 3``
and finishes successfully. Calculations are placed directly through
``task(ArithmeticAddCalculation)``; per-placement ``options`` (``resources``
and ``withmpi``) ride under ``task_metadata`` keyed by placement name, which
:func:`prepare_benchmark_inputs_inline` supplies.
"""

from __future__ import annotations

import typing as t

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import graph, par_map, task
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.orm import Code, DataList, Int
from utils.benchmarks.graph_engine.programs.matched import _calc_task_metadata

__all__ = (
    'GRAPH_BENCHMARKS_INLINE',
    'add_calc',
    'calc_step_inline',
    'one_loop_inline',
    'prepare_benchmark_inputs_inline',
    'validate_benchmarks_inline',
    'wc_step_inline',
)

add_calc = task(ArithmeticAddCalculation)
"""Direct ``ArithmeticAddCalculation`` handle placed by the calcjob benchmarks."""


@graph
def one_loop_inline(value: int) -> int:
    """Single-iteration child equivalent: count down to zero with inline arithmetic."""
    while value > 0:
        value = value - 1
    return value


@graph
def basic_loop_inline(iterations: int) -> None:
    """Inline equivalent of ``WorkchainLoop``: ``n`` no-op steps with no tasks at all."""
    while iterations > 0:
        iterations = iterations - 1
    return {}


@graph
def wc_step_inline(value: int) -> int:
    """One serial workflow step: run the single-iteration child, then step the counter.

    Loop iterations dispatch sequentially, so the next iteration starts only
    after the nested scope completes; no ``after`` edge is needed.
    """
    done = one_loop_inline(value=1)  # noqa: F841 - placement runs for its scope, result unused
    return value - 1


@graph
def serial_wc_loop_inline(iterations: int) -> None:
    """Inline equivalent of ``WorkchainLoopWcSerial``: one nested scope per step."""
    while iterations > 0:
        iterations = wc_step_inline(value=iterations)
    return {}


@graph
def threaded_wc_loop_inline(values: DataList) -> DataList:
    """Inline equivalent of ``WorkchainLoopWcThreaded``: ``n`` nested scopes in one step.

    ``par_map`` dispatches one ``one_loop_inline`` scope per element in a single
    step, plus one collector calcfunction that creates the returned container.
    """
    return par_map(one_loop_inline, values)


@graph
def calc_step_inline(value: int, code: Code) -> int:
    """One serial calculation step: run the benchmark calculation, then step the counter.

    The counter update carries no dependency on the calculation output;
    sequential execution follows from the scope barrier (the iteration scope,
    calculation included, completes before the next iteration starts).
    """
    total = add_calc(x=1, y=2, code=code)  # noqa: F841 - placement runs the science, result unused
    return value - 1


@graph
def serial_calc_loop_inline(iterations: int, code: Code) -> None:
    """Inline equivalent of ``WorkchainLoopCalcSerial``: one calculation per step."""
    while iterations > 0:
        iterations = calc_step_inline(value=iterations, code=code)
    return {}


@graph
def threaded_calc_loop_inline(code: Code) -> dict[str, int]:
    """Inline-harness equivalent of ``WorkchainLoopCalcThreaded``: four calculations, one step.

    ``par_map`` only maps unary tasks and graphs while ``ArithmeticAddCalculation``
    needs ``x``, ``y``, and ``code``, so the fan-out is statically unrolled to four
    explicitly named direct placements with no ordering between them.
    """
    first = add_calc(x=1, y=2, code=code)
    second = add_calc(x=1, y=2, code=code)
    third = add_calc(x=1, y=2, code=code)
    fourth = add_calc(x=1, y=2, code=code)
    return {'first': first.sum, 'second': second.sum, 'third': third.sum, 'fourth': fourth.sum}


GRAPH_BENCHMARKS_INLINE: dict[str, tuple[GraphHandle[t.Any, t.Any], int]] = {
    'basic-loop': (basic_loop_inline, 4),
    'serial-wc-loop': (serial_wc_loop_inline, 4),
    'threaded-wc-loop': (threaded_wc_loop_inline, 4),
    'serial-calcjob-loop': (serial_calc_loop_inline, 4),
    'threaded-calcjob-loop': (threaded_calc_loop_inline, 4),
}
"""Inline graph handles keyed like ``WORKCHAINS``, each paired with its benchmark size."""


def prepare_benchmark_inputs_inline(
    name: str, code: Code | None = None, iterations: int | None = None
) -> dict[str, t.Any]:
    """Return the launch kwargs for one inline benchmark graph.

    :param name: a key of :data:`GRAPH_BENCHMARKS_INLINE`.
    :param code: the installed ``ArithmeticAddCalculation`` code; required for
        the ``serial-calcjob-loop`` and ``threaded-calcjob-loop`` benchmarks.
    :param iterations: override the benchmark size for the dynamic benchmarks
        (loop counters and the ``threaded-wc-loop`` collection length).
    :return: kwargs for :func:`~aiida.engine.launch.run_get_node`, including
        ``task_metadata`` with ``resources``/``withmpi`` options for the
        calcjob benchmarks, keyed by placement name.
    :raises KeyError: if ``name`` is not a benchmark.
    :raises ValueError: if ``code`` is missing for a calcjob benchmark, or if
        ``iterations`` is given for ``threaded-calcjob-loop`` with a value
        other than four.
    """
    handle, benchmark_iterations = GRAPH_BENCHMARKS_INLINE[name]
    count = benchmark_iterations if iterations is None else iterations
    if handle is threaded_wc_loop_inline:
        return {'values': DataList([Int(1) for _ in range(count)])}
    if handle is serial_calc_loop_inline:
        if code is None:
            msg = "'serial-calcjob-loop' needs the installed `code` for its `ArithmeticAddCalculation` placements."
            raise ValueError(msg)
        return {'iterations': count, 'code': code, 'task_metadata': _calc_task_metadata('add_calc')}
    if handle is threaded_calc_loop_inline:
        if code is None:
            msg = "'threaded-calcjob-loop' needs the installed `code` for its `ArithmeticAddCalculation` placements."
            raise ValueError(msg)
        if iterations is not None and iterations != benchmark_iterations:
            msg = (
                f"'threaded-calcjob-loop' is statically unrolled to {benchmark_iterations} placements, "
                f'not {iterations}; rerun without `iterations` instead.'
            )
            raise ValueError(msg)
        return {
            'code': code,
            'task_metadata': _calc_task_metadata('add_calc', 'add_calc_2', 'add_calc_3', 'add_calc_4'),
        }
    return {'iterations': count}


def validate_benchmarks_inline() -> dict[str, int]:
    """Assert the static structure each inline benchmark relies on.

    Checks that no benchmark carries control-state tasks (``decrement``/``is_positive``),
    that each serial loop body holds one step wrapper plus its inline condition update,
    that the fixed ``threaded-calcjob-loop`` places exactly four direct
    ``ArithmeticAddCalculation`` calls with no ordering between them, and that
    the ``threaded-wc-loop`` maps a unary single-output graph. Returns the
    placement count per benchmark for reporting.

    :raises AssertionError: if any structural expectation is violated.
    """
    from aiida.engine.processes.graphs.ir import InlineOperation, LoopControl, MapControl, ProcessTask, SubgraphTask

    counts: dict[str, int] = {}
    for name, (handle, _) in GRAPH_BENCHMARKS_INLINE.items():
        template = compile_graph(handle)
        control_tasks = [
            placement
            for placement in template.tasks
            if isinstance(placement, ProcessTask)
            and placement.name in ('decrement', 'is_positive', 'decrement_2', 'is_positive_2')
        ]
        assert not control_tasks, f'{name} must not carry control-state tasks, found {control_tasks}'
    fixed = compile_graph(threaded_calc_loop_inline)
    placements = [placement for placement in fixed.tasks if isinstance(placement, ProcessTask)]
    assert len(placements) == 4, f'threaded-calcjob-loop must place four calculations, not {len(placements)}'
    assert not fixed.dependencies, 'threaded-calcjob-loop placements must share no ordering edges'
    assert all(issubclass(placement.spec.process_class, ArithmeticAddCalculation) for placement in placements), (
        'threaded-calcjob-loop must place `ArithmeticAddCalculation` directly'
    )
    counts['threaded-calcjob-loop'] = len(placements)
    for name, step in (('serial-wc-loop', 'wc_step_inline'), ('serial-calcjob-loop', 'calc_step_inline')):
        handle, _ = GRAPH_BENCHMARKS_INLINE[name]
        (loop,) = [placement for placement in compile_graph(handle).tasks if isinstance(placement, LoopControl)]
        nested = [placement for placement in loop.body.tasks if isinstance(placement, SubgraphTask)]
        assert len(nested) == 1, f'{name} loop body must hold one nested placement, not {len(nested)}'
        assert nested[0].name == step, f'{name} loop body must call `{step}`, not `{nested[0].name}`'
        rest = [placement for placement in loop.body.tasks if placement not in nested]
        assert rest and all(isinstance(placement, InlineOperation) for placement in rest), (
            f'{name} loop body must hold only the step call plus its inline condition update'
        )
        counts[name] = 1
    wc_step = compile_graph(wc_step_inline)
    assert [placement.name for placement in wc_step.tasks if isinstance(placement, SubgraphTask)] == [
        'one_loop_inline'
    ], 'wc_step_inline must place one `one_loop_inline` scope'
    calc_step = compile_graph(calc_step_inline)
    step_calcs = [
        placement
        for placement in calc_step.tasks
        if isinstance(placement, ProcessTask) and issubclass(placement.spec.process_class, ArithmeticAddCalculation)
    ]
    assert [placement.name for placement in step_calcs] == ['add_calc'], (
        'calc_step_inline must place one `ArithmeticAddCalculation` directly'
    )
    (mapped,) = [
        placement for placement in compile_graph(threaded_wc_loop_inline).tasks if isinstance(placement, MapControl)
    ]
    assert mapped.body is not None and mapped.spec is None, 'threaded-wc-loop must map a graph, not a task'
    assert len(mapped.mapped_inputs.fields) == 1
    counts['threaded-wc-loop'] = 1
    (loop,) = [placement for placement in compile_graph(basic_loop_inline).tasks if isinstance(placement, LoopControl)]
    assert not [placement for placement in loop.body.tasks if isinstance(placement, ProcessTask)], (
        'basic-loop body must hold no task placements'
    )
    counts['basic-loop'] = 0
    one = compile_graph(one_loop_inline)
    assert not [placement for placement in one.tasks if isinstance(placement, ProcessTask)], (
        'one_loop_inline must count down with inline arithmetic only'
    )
    return counts
