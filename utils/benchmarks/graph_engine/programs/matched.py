###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph equivalents of the ``tests/benchmark/test_engine.py`` workloads.

Each :class:`~aiida.engine.WorkChain` in ``WORKCHAINS`` has one ``@graph``
counterpart below that reimplements its behavior as Graph IR instead of
wrapping the original. The observable workload is preserved: the same number
of loop iterations, child-graph equivalents, and ``ArithmeticAddCalculation``
placements with ``x=1`` and ``y=2``.

How to invoke each benchmark::

    from aiida.engine.launch import run_get_node
    from utils.benchmarks.graph_engine.programs.matched import GRAPH_BENCHMARKS, prepare_benchmark_inputs

    handle, iterations = GRAPH_BENCHMARKS['serial-calcjob-loop']
    outputs, node = run_get_node(handle, **prepare_benchmark_inputs('serial-calcjob-loop', code))

``prepare_benchmark_inputs`` also accepts ``iterations`` to resize the dynamic
benchmarks. ``validate_benchmarks`` asserts the static placement counts of the
fixed benchmarks and the mapping contracts of the ``par_map`` ones.

Semantic differences from the ``WorkChain`` originals:

* Graphs always declare outputs, while the originals return nothing. Loop
  benchmarks return their final counter and the threaded benchmarks return
  their collected results.
* Graph loop state must be rewound through tasks, so every loop benchmark
  spends one ``decrement`` plus one ``is_positive`` calcfunction task per
  iteration (plus one final ``is_positive`` check that exits the loop). The
  originals keep ``counter``/``iter`` in memory and run zero tasks per no-op
  step.
* One ``GraphProcess`` runs every scope, so loop iterations and nested graphs run as scopes with
  hierarchical call labels, never as child graph nodes. Each ``par_map`` collection still dispatches
  one collector calcfunction that creates the result container, which has no original counterpart.
* ``threaded-calcjob-loop`` is statically unrolled to exactly four placements
  because ``par_map`` only maps unary tasks and graphs while the calculation
  needs ``x``, ``y``, and ``code``. The benchmark is fixed at four; requesting
  any other ``iterations`` value raises ``ValueError``.
* Like the originals, the calcjob benchmarks run the real
  ``ArithmeticAddCalculation`` with ``x=1`` and ``y=2``. Both sides use
  ``filepath_executable='/bin/bash'`` so each calculation parses ``sum == 3``
  and finishes successfully; no lenient wrapper is involved. Calculations are
  placed directly through ``task(ArithmeticAddCalculation)``, so each
  placement is a genuine ``CalcJob`` node and ``CalcJob`` tasks take no
  ``metadata`` input: per-placement ``options`` (``resources`` and
  ``withmpi``) ride under ``task_metadata`` keyed by placement name, which
  :func:`prepare_benchmark_inputs` supplies.
"""

from __future__ import annotations

import typing as t

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import graph, par_map, task
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph
from aiida.orm import Code, DataList, Int

__all__ = (
    'GRAPH_BENCHMARKS',
    'add_calc',
    'basic_loop',
    'calc_step',
    'decrement',
    'is_positive',
    'one_loop',
    'prepare_benchmark_inputs',
    'serial_calc_loop',
    'serial_wc_loop',
    'threaded_calc_loop',
    'threaded_wc_loop',
    'validate_benchmarks',
    'wc_step',
)


@task
def decrement(value: int) -> int:
    """Subtract one; loop benchmarks count down to zero through this task."""
    return value - 1


@task
def is_positive(value: int) -> bool:
    """Return whether the loop counter still has iterations left."""
    return value > 0


add_calc = task(ArithmeticAddCalculation)
"""Direct ``ArithmeticAddCalculation`` handle placed by the calcjob benchmarks."""


@graph
def one_loop(value: int) -> int:
    """Child-workflow equivalent: count down to zero; input ``1`` runs one iteration."""
    while is_positive(value=value):
        value = decrement(value=value)
    return value


@graph
def basic_loop(iterations: int) -> int:
    """Graph equivalent of ``WorkchainLoop``: ``n`` no-op state steps.

    Each of the ``n`` iterations runs one ``is_positive`` check and one
    ``decrement`` helper task where the original ran a bare ``pass``.
    """
    while is_positive(value=iterations):
        iterations = decrement(value=iterations)
    return iterations


@graph
def wc_step(value: int) -> int:
    """One serial workflow step: run the single-iteration child, then advance the counter.

    Loop bodies only rebind enclosing names, so the serial loop below rebinds
    just its counter through this wrapper instead of placing the child inline.
    """
    done = one_loop(value=1)
    return decrement(value=value, after=done)


@graph
def serial_wc_loop(iterations: int) -> int:
    """Graph equivalent of ``WorkchainLoopWcSerial``: one child loop per step.

    Loop iterations dispatch sequentially, so each iteration calls the
    ``wc_step`` wrapper exactly once, which runs one ``one_loop`` child
    (one loop iteration, mirroring ``WorkchainLoop(iterations=1)``) before
    advancing the counter.
    """
    while is_positive(value=iterations):
        iterations = wc_step(value=iterations)
    return iterations


@graph
def threaded_wc_loop(values: DataList) -> DataList:
    """Graph equivalent of ``WorkchainLoopWcThreaded``: ``n`` children in one step.

    ``par_map`` dispatches one ``one_loop`` child per element in a single
    scheduling step, plus one collector calcfunction that creates the returned
    container. ``prepare_benchmark_inputs`` packs ``n`` ones so each child runs
    one loop iteration, mirroring ``WorkchainLoop(iterations=1)`` children.
    """
    return par_map(one_loop, values)


@graph
def calc_step(value: int, code: Code) -> int:
    """One serial calculation step: run the benchmark calculation, then advance the counter.

    Loop bodies only rebind enclosing names, so the serial loop below rebinds
    just its counter through this wrapper instead of placing the calculation
    inline. The calculation runs first and the counter rewinds after its
    ``sum`` result, giving one direct ``ArithmeticAddCalculation`` placement
    plus the two loop-state tasks per iteration.
    """
    total = add_calc(x=1, y=2, code=code)
    return decrement(value=value, after=total.sum)


@graph
def serial_calc_loop(iterations: int, code: Code) -> int:
    """Graph equivalent of ``WorkchainLoopCalcSerial``: one calculation per step.

    Loop iterations dispatch sequentially, so each iteration calls the
    ``calc_step`` wrapper exactly once, which places one direct
    ``ArithmeticAddCalculation`` with ``x=1`` and ``y=2`` before advancing
    the counter.
    """
    while is_positive(value=iterations):
        iterations = calc_step(value=iterations, code=code)
    return iterations


@graph
def threaded_calc_loop(code: Code) -> dict[str, int]:
    """Graph equivalent of ``WorkchainLoopCalcThreaded``: four calculations, one step.

    The four placements share no dependencies, so the scheduler dispatches them
    in a single step. ``par_map`` cannot express this fan-out because it only
    maps unary tasks and graphs while ``ArithmeticAddCalculation`` needs ``x``,
    ``y``, and ``code``; the benchmark is therefore statically unrolled to
    exactly four explicitly named direct placements with no ordering between
    them.
    """
    first = add_calc(x=1, y=2, code=code)
    second = add_calc(x=1, y=2, code=code)
    third = add_calc(x=1, y=2, code=code)
    fourth = add_calc(x=1, y=2, code=code)
    return {'first': first.sum, 'second': second.sum, 'third': third.sum, 'fourth': fourth.sum}


GRAPH_BENCHMARKS: dict[str, tuple[GraphHandle[t.Any, t.Any], int]] = {
    'basic-loop': (basic_loop, 4),
    'serial-wc-loop': (serial_wc_loop, 4),
    'threaded-wc-loop': (threaded_wc_loop, 4),
    'serial-calcjob-loop': (serial_calc_loop, 4),
    'threaded-calcjob-loop': (threaded_calc_loop, 4),
}
"""Graph handles keyed like ``WORKCHAINS``, each paired with its benchmark size.

The loop benchmarks honor ``iterations`` dynamically; ``threaded-calcjob-loop``
is statically unrolled to four placements (see its docstring).
"""

_CALC_OPTIONS: dict[str, t.Any] = {
    'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1},
    'withmpi': False,
}
"""Per-placement ``metadata.options`` for the benchmark calculations."""


def _calc_task_metadata(*placements: str) -> dict[str, dict[str, t.Any]]:
    """Return ``task_metadata`` with fresh ``resources``/``withmpi`` options per placement."""
    return {placement: {'options': dict(_CALC_OPTIONS)} for placement in placements}


def prepare_benchmark_inputs(name: str, code: Code | None = None, iterations: int | None = None) -> dict[str, t.Any]:
    """Return the launch kwargs for one benchmark graph.

    :param name: a key of :data:`GRAPH_BENCHMARKS`.
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
    handle, benchmark_iterations = GRAPH_BENCHMARKS[name]
    count = benchmark_iterations if iterations is None else iterations
    if handle is threaded_wc_loop:
        return {'values': DataList([Int(1) for _ in range(count)])}
    if handle is serial_calc_loop:
        if code is None:
            msg = "'serial-calcjob-loop' needs the installed `code` for its `ArithmeticAddCalculation` placements."
            raise ValueError(msg)
        return {'iterations': count, 'code': code, 'task_metadata': _calc_task_metadata('add_calc')}
    if handle is threaded_calc_loop:
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


def validate_benchmarks() -> dict[str, int]:
    """Assert the static structure each benchmark relies on.

    Checks that the fixed ``threaded-calcjob-loop`` places exactly four direct
    ``ArithmeticAddCalculation`` calls with no ordering between them, that the
    serial loops place exactly one call per iteration body, and that the
    ``threaded-wc-loop`` maps a unary single-output graph. Returns the
    placement count per benchmark for reporting.

    :raises AssertionError: if any structural expectation is violated.
    """
    from aiida.engine.processes.graphs.ir import LoopControl, MapControl, ProcessTask

    counts: dict[str, int] = {}
    fixed = compile_graph(threaded_calc_loop)
    placements = [placement for placement in fixed.tasks if isinstance(placement, ProcessTask)]
    assert len(placements) == 4, f'threaded-calcjob-loop must place four calculations, not {len(placements)}'
    assert not fixed.dependencies, 'threaded-calcjob-loop placements must share no ordering edges'
    assert all(issubclass(placement.spec.process_class, ArithmeticAddCalculation) for placement in placements), (
        'threaded-calcjob-loop must place `ArithmeticAddCalculation` directly'
    )
    counts['threaded-calcjob-loop'] = len(placements)
    for name, child in (('serial-wc-loop', 'wc_step'), ('serial-calcjob-loop', 'calc_step')):
        handle, _ = GRAPH_BENCHMARKS[name]
        (loop,) = [placement for placement in compile_graph(handle).tasks if isinstance(placement, LoopControl)]
        assert child in loop.body.task_names, f'{name} loop body must call `{child}`'
        assert len(loop.body.tasks) == 2, f'{name} loop body must hold the step call and its condition update'
        counts[name] = 1
    step_calcs = [
        placement
        for placement in compile_graph(calc_step).tasks
        if isinstance(placement, ProcessTask) and issubclass(placement.spec.process_class, ArithmeticAddCalculation)
    ]
    assert len(step_calcs) == 1, 'calc_step must place one `ArithmeticAddCalculation` directly'
    assert [placement.name for placement in step_calcs] == ['add_calc']
    (mapped,) = [placement for placement in compile_graph(threaded_wc_loop).tasks if isinstance(placement, MapControl)]
    assert len(mapped.mapped_inputs.fields) == 1
    counts['threaded-wc-loop'] = 1
    (loop,) = [placement for placement in compile_graph(basic_loop).tasks if isinstance(placement, LoopControl)]
    counts['basic-loop'] = len(loop.body.tasks)
    one = compile_graph(one_loop)
    assert len(one.tasks) == 2, 'one_loop child must hold the check and the counter tasks'
    return counts
