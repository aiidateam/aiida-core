###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Matched restart workload: one fallible step retried by `BaseRestartWorkChain` and by a graph.

Both implementations drive the *same* real child process, :class:`FlakyStep`, a small
:class:`~aiida.engine.WorkChain` that fails deterministically and only later succeeds. The
:class:`~aiida.engine.BaseRestartWorkChain` side restarts it through genuine process handlers;
the graph side retries it through an explicit restart loop over the declared failure arms of
``task(FlakyStep, errors=...)``, mirroring ``tests/engine/processes/graphs/programs/restart.py``
from ``upstream/feature/graph-exit-codes`` (``zero``/``step`` attempt state, a ``should_restart``
gate, and a raising ``ensure``).

Scenarios, selected through the ``mode`` input of both implementations:

* ``recover``: the step fails transiently while ``attempt < 2`` and succeeds on the third run.
* ``always-fail``: the step always fails transiently, so a finite budget runs out.
* ``fatal``: the step always fails with a code no handler claims, so recovery is impossible.

Status mapping (both sides fail loudly; only the vocabulary differs):

* ``recover`` within budget: both exit ``0`` with ``value == 1.5`` after exactly three runs.
* ``fatal``: the work chain exits ``402`` (``ERROR_UNHANDLED_FAILURE``); the graph exits
  ``400`` (``ERROR_TASK_FAILED``) because ``ensure_recovered`` raises, exactly like the
  upstream ``restartable`` program when attempts run out.
* budget exhausted: the work chain exits ``401`` (``ERROR_MAXIMUM_ITERATIONS_EXCEEDED``)
  once a handler claimed the failure but the budget ran out; the graph exits ``400`` via
  ``ensure_recovered``.

Workload parity: the same child class, the same number of child runs per scenario, and the
same attempt progression (``0, 1, 2, ...``). The only deliberate asymmetry is the retry
vocabulary above, which the correctness tests pin per implementation.
"""

import typing as t

from aiida.engine import BaseRestartWorkChain, ProcessHandlerReport, process_handler, while_
from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import GraphHandle, compile_graph, graph, task
from aiida.engine.processes.workchains.workchain import WorkChain
from aiida.orm import Float, Int, Str

__all__ = (
    'RECOVER_RUNS',
    'RECOVER_VALUE',
    'RESTART_BENCHMARKS',
    'FlakyStep',
    'RestartBenchmarkWorkChain',
    'StepErrors',
    'advance',
    'ensure_recovered',
    'flaky_step',
    'prepare_restart_inputs',
    'prepare_restart_wc_inputs',
    'restartable',
    'should_restart',
    'validate_restart_benchmark',
    'zero',
)

#: Value the step stores on its successful run; both implementations must return it on ``recover``.
RECOVER_VALUE = 1.5

#: Runs the ``recover`` scenario needs: attempts ``0`` and ``1`` fail transiently, ``2`` succeeds.
RECOVER_RUNS = 3


class StepErrors(ExitCodeEnum):
    """Declared failures of the shared restart step."""

    TRANSIENT = ExitCode(410, 'Transient step failure, safe to retry.')
    FATAL = ExitCode(411, 'Fatal step failure, never retry.')


class FlakyStep(WorkChain):
    """Deterministic fallible step shared by the work-chain and graph implementations.

    The failure schedule is a pure function of the ``attempt`` and ``mode`` inputs so both
    sides observe identical behavior: ``recover`` fails transiently while ``attempt < 2`` and
    then returns the caller-provided ``result`` input unchanged; ``always-fail`` always fails
    transiently; ``fatal`` always fails with the unhandled code.

    Provenance: the success output is ``self.inputs.result``, an already-stored node the
    caller prepared outside the workflow, so no new ``Data`` is created inside and no
    workflow node carries a CREATE link.
    """

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        """Define the attempt/mode inputs and the optional success output."""
        super().define(spec)
        spec.input('attempt', valid_type=Int, help='Zero-based attempt number driving the failure schedule.')
        spec.input(
            'mode',
            valid_type=Str,
            default=lambda: Str('recover'),
            help="Failure schedule: 'recover', 'always-fail', or 'fatal'.",
        )
        spec.input(
            'result',
            valid_type=Float,
            default=lambda: Float(RECOVER_VALUE),
            help='Stored value returned unchanged on the successful run (prepared by the caller).',
        )
        spec.output('value', valid_type=Float, required=False, help='The ``result`` input, on success.')
        spec.exit_code(410, 'TRANSIENT', message='Transient step failure, safe to retry.')
        spec.exit_code(411, 'FATAL', message='Fatal step failure, never retry.')
        spec.outline(cls.run_step)

    def run_step(self) -> ExitCode | None:
        """Fail or succeed deterministically from the ``attempt`` and ``mode`` inputs."""
        mode = self.inputs.mode.value
        if mode == 'fatal':
            return self.exit_codes.FATAL
        if mode == 'always-fail' or self.inputs.attempt.value < 2:
            return self.exit_codes.TRANSIENT
        self.out('value', self.inputs.result)
        return None


flaky_step = task(FlakyStep, errors=StepErrors)
"""The shared child as a graph task; ``ran = flaky_step(...)`` exposes ``ran.value`` and ``ran.error``."""


@task
def zero() -> int:
    """Seed the attempt counter."""
    return 0


@task
def advance(attempt: int) -> int:
    """Count one further attempt."""
    return attempt + 1


@task
def should_restart(error: StepErrors | None, attempt: int, max_attempts: int) -> bool:
    """Retry only a handled transient failure while runs remain.

    ``attempt`` is zero-based, so ``attempt + 1`` runs have completed; a ``FATAL`` error is
    never retried, mirroring the work chain where no handler claims it.
    """
    return error is StepErrors.TRANSIENT and (attempt + 1) < max_attempts


@task
def ensure_recovered(value: float | None, error: StepErrors | None) -> float:
    """Return the recovered value, failing the graph when the step never succeeded."""
    if error is not None or value is None:
        raise ValueError('the step never recovered.')
    return value


@graph
def restartable(mode: str, max_attempts: int, result: Float) -> float:
    """Retry the shared step until it succeeds or the budget runs out.

    Mirrors the upstream ``restartable`` program: the ``Result`` arms are bound once as a
    typed tuple before the loop and rebound as a tuple inside it, so the loop carries
    only pre-declared state.

    :param mode: the :class:`FlakyStep` failure schedule (``recover``, ``always-fail``, ``fatal``).
    :param max_attempts: maximum number of step runs; ``recover`` needs three.
    :param result: stored value the step returns unchanged on success.
    """
    attempt = zero()
    value, error = flaky_step(attempt=attempt, mode=mode, result=result)
    retry = should_restart(error=error, attempt=attempt, max_attempts=max_attempts)
    while retry:
        attempt = advance(attempt=attempt)
        value, error = flaky_step(attempt=attempt, mode=mode, result=result)
        retry = should_restart(error=error, attempt=attempt, max_attempts=max_attempts)
    return ensure_recovered(value=value, error=error)


class RestartBenchmarkWorkChain(BaseRestartWorkChain):
    """Restart the shared step through genuine process handlers.

    The outline and inspection logic come entirely from :class:`BaseRestartWorkChain`; this
    subclass only wires the inputs, the attempt progression, and the transient handler.
    """

    _process_class = FlakyStep

    @classmethod
    def define(cls, spec) -> None:  # type: ignore[override]
        """Define the mode/result inputs, expose the step outputs, and set the restart outline."""
        super().define(spec)
        spec.input(
            'mode',
            valid_type=Str,
            default=lambda: Str('recover'),
            help="Failure schedule forwarded to the step: 'recover', 'always-fail', or 'fatal'.",
        )
        spec.input(
            'result',
            valid_type=Float,
            default=lambda: Float(RECOVER_VALUE),
            help='Stored value the step returns unchanged on success.',
        )
        spec.expose_outputs(FlakyStep)
        spec.outline(
            cls.setup,
            while_(cls.should_run_process)(
                cls.run_process,
                cls.inspect_process,
            ),
            cls.results,
        )

    def setup(self) -> None:
        """Initialize restart state and seed the first attempt inputs."""
        super().setup()
        self.ctx.inputs = {
            'attempt': Int(0),
            'mode': self.inputs.mode,
            'result': self.inputs.result,
        }

    @process_handler(priority=100, exit_codes=StepErrors.TRANSIENT.value)
    def handle_transient(self, node) -> ProcessHandlerReport:
        """Claim a transient step failure and schedule the next attempt number."""
        self.ctx.inputs['attempt'] = Int(node.inputs.attempt.value + 1)
        return ProcessHandlerReport(do_break=True)


RESTART_BENCHMARKS: dict[str, tuple[GraphHandle[t.Any, t.Any], type[RestartBenchmarkWorkChain]]] = {
    'restart-recover': (restartable, RestartBenchmarkWorkChain),
}
"""Matched implementations keyed by workload; the correctness tests fix the scenario per case."""


def prepare_restart_inputs(
    mode: str = 'recover', max_attempts: int = 5, result: Float | None = None
) -> dict[str, t.Any]:
    """Return the launch kwargs for the restart graph.

    :param mode: the :class:`FlakyStep` failure schedule.
    :param max_attempts: maximum number of step runs.
    :param result: stored value returned on success; created here (outside any timed
        region) when omitted so the workflow itself never creates data.
    :return: kwargs for :func:`~aiida.engine.launch.run_get_node` and
        :meth:`GraphHandle.get_launch_inputs`.
    """
    return {
        'mode': mode,
        'max_attempts': max_attempts,
        'result': result if result is not None else Float(RECOVER_VALUE),
    }


def prepare_restart_wc_inputs(
    mode: str = 'recover', max_iterations: int = 5, result: Float | None = None
) -> dict[str, t.Any]:
    """Return the launch kwargs for the restart work chain.

    :param mode: the :class:`FlakyStep` failure schedule.
    :param max_iterations: maximum number of step runs (``BaseRestartWorkChain`` budget).
    :param result: stored value returned on success; created here (outside any timed
        region) when omitted so the workflow itself never creates data.
    :return: kwargs with explicit nodes for :func:`~aiida.engine.launch.run_get_node`.
    """
    return {
        'mode': Str(mode),
        'max_iterations': Int(max_iterations),
        'result': result if result is not None else Float(RECOVER_VALUE),
    }


def validate_restart_benchmark() -> dict[str, int]:
    """Assert the static structure the restart benchmark relies on.

    Checks that the graph lowers to one loop whose body places the shared step exactly once,
    and that the placed step maps both declared failure statuses. Returns the per-loop
    placement count for reporting.

    :raises AssertionError: if any structural expectation is violated.
    """
    from aiida.engine.processes.graphs.ir import LoopControl, ProcessTask

    template = compile_graph(restartable)
    (loop,) = [entry for entry in template.tasks if isinstance(entry, LoopControl)]
    steps = [
        entry for entry in loop.body.tasks if isinstance(entry, ProcessTask) and entry.spec.process_class is FlakyStep
    ]
    assert len(steps) == 1, f'restart loop body must place the step once, not {len(steps)}'
    (placed,) = steps
    assert issubclass(placed.spec.process_class, FlakyStep), 'the loop must place the shared `FlakyStep`'
    assert {code.status for code in placed.spec.exit_codes.values()} >= {410, 411}, (
        'the placed step must map both declared failure statuses'
    )
    assert any(str(name).split(':')[-1] == 'StepErrors' for name in placed.spec.error_enums), (
        'the placed step must declare `StepErrors`'
    )
    return {'restartable-loop-placements': len(steps)}
