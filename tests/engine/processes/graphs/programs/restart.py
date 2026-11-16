###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Restart-loop programs: a fallible step retried until it succeeds.

Counters and short-circuiting retry predicates stay inline; only the scientific
steps, handlers, and guards run as child processes. See ``graph`` for the authoring contract.
"""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.results import Err, Ok, RestartErrors, Result
from aiida.orm import StructureData


class StepErrors(ExitCodeEnum):
    """Declared failures of the `run_step` task."""

    UNSTABLE = ExitCode(410, 'Unstable step.')


@task
def run_step(structure: StructureData, attempt: int) -> Result[float, StepErrors]:
    """Fail the first two attempts, then succeed."""
    if attempt < 2:
        return Err(StepErrors.UNSTABLE)
    return Ok(1.5)


@task
def ensure(value: float | None, error: StepErrors | None) -> float:
    """Read the recovered value, failing loudly when none remains."""
    if error is not None or value is None:
        raise ValueError('the step never succeeded.')
    return value


@task
def flip_step(attempt: int) -> Result[float, StepErrors]:
    """Succeed around one declared failure, so the loop rebinds both arms."""
    if attempt == 1:
        return Err(StepErrors.UNSTABLE)
    return Ok(float(attempt))


@task
def mark_absent() -> str:
    """Record that the previous iteration left no value arm."""
    return 'absent'


@task
def mark_present(value: float) -> str:
    """Record that the previous iteration left a value arm."""
    return f'present:{value}'


@task
def check_recovered(marker: str, value: float | None, error: StepErrors | None) -> str:
    """Return the marker, requiring the final iteration to have succeeded."""
    if error is not None or value is None:
        raise ValueError('the final iteration never succeeded.')
    return marker


@graph
def absent_arm_resets(attempt: int = 0) -> str:
    """Rebind a `Result` in a loop; an absent arm reads as `None`, not stale state."""
    marker = mark_absent()
    value, error = flip_step(attempt=attempt)
    while attempt < 2:
        attempt = attempt + 1
        if value is None:
            marker = mark_absent()
        else:
            marker = mark_present(value=value)
        value, error = flip_step(attempt=attempt)
    return check_recovered(marker=marker, value=value, error=error)


@task
def read_last(value: float | None) -> float:
    """Return the value arm of the final iteration."""
    if value is None:
        raise ValueError('the final iteration never succeeded.')
    return value


@graph
def discarded_arm(attempt: int = 0) -> float:
    """Discard the error arm with `_`; only the value arm carries across iterations."""
    value, _ = flip_step(attempt=attempt)
    while attempt < 2:
        attempt = attempt + 1
        value, _ = flip_step(attempt=attempt)
    return read_last(value=value)


@task
def report_unhandled(value: float | None, error: StepErrors | None) -> Result[float, RestartErrors]:
    """Translate an unrecovered failure into the shared machinery vocabulary."""
    if error is not None or value is None:
        return Err(RestartErrors.UNHANDLED_FAILURE)
    return Ok(value)


@graph
def restartable(structure: StructureData, max_attempts: int, attempt: int = 0) -> float:
    """Retry a fallible step until it succeeds or attempts run out.

    ``attempt`` stays zero-based and the budget keeps ``attempt < max_attempts``.

    :param structure: the structure the step reads.
    :param max_attempts: the budget; retries continue while ``attempt < max_attempts``.
    :param attempt: the zero-based attempt the first run steps from.
    """
    value, error = run_step(structure=structure, attempt=attempt)
    retry = error is not None and attempt < max_attempts
    while retry:
        attempt = attempt + 1
        value, error = run_step(structure=structure, attempt=attempt)
        retry = error is not None and attempt < max_attempts
    return ensure(value=value, error=error)


class MockWorkflowErrors(ExitCodeEnum):
    """Workflow failures of the mock calculation."""

    KNOWN_UNRECOVERABLE_FAILURE = ExitCode(310, 'The calculation failed with a known unrecoverable error.')


class MockScientificCodeErrors(ExitCodeEnum):
    """Calculation failures the handlers match."""

    OUT_OF_WALLTIME = ExitCode(400, 'The calculation stopped prematurely because it ran out of walltime.')
    COMPUTING_CHOLESKY = ExitCode(462, 'The code failed during the cholesky factorization.')
    DIAGONALIZATION_TOO_MANY_BANDS_NOT_CONVERGED = ExitCode(
        463, 'Too many bands failed to converge during the diagonalization.'
    )


CalculationFailure = MockWorkflowErrors | MockScientificCodeErrors | RestartErrors
"""Every failure the chain handles, as one union."""


@task
def mock_step(attempt: int) -> Result[float, MockScientificCodeErrors]:
    """Fail twice with handled codes, then succeed."""
    if attempt == 0:
        return Err(MockScientificCodeErrors.OUT_OF_WALLTIME)
    if attempt == 1:
        return Err(MockScientificCodeErrors.COMPUTING_CHOLESKY)
    return Ok(1.0)


@task
def handle_walltime(error: CalculationFailure | None, parameters: dict) -> dict:
    """Claim walltime failures, passing anything else through unchanged."""
    if error is not MockScientificCodeErrors.OUT_OF_WALLTIME:
        return parameters
    updated = dict(parameters)
    updated['restart_mode'] = 'restart'
    return updated


@task
def handle_diagonalization(error: CalculationFailure | None, parameters: dict) -> dict:
    """Claim diagonalization failures, passing anything else through unchanged."""
    if error not in (
        MockScientificCodeErrors.COMPUTING_CHOLESKY,
        MockScientificCodeErrors.DIAGONALIZATION_TOO_MANY_BANDS_NOT_CONVERGED,
    ):
        return parameters
    tried = parameters.get('tried', [])
    remaining = [value for value in ['david', 'cg'] if value not in tried]
    updated = dict(parameters)
    updated['diagonalization'] = remaining[-1]
    updated['tried'] = [*tried, remaining[-1]]
    return updated


@graph
def fix_chain(error: CalculationFailure | None, parameters: dict) -> dict:
    """Run the handler chain in priority order; unclaimed errors pass through."""
    wall_fixed = handle_walltime(error=error, parameters=parameters)
    return handle_diagonalization(error=error, parameters=wall_fixed)


@task
def ensure_chain(value: float | None, error: CalculationFailure | None) -> float:
    """Read the recovered value, failing loudly when none remains."""
    if error is not None or value is None:
        raise ValueError('the step never succeeded.')
    return value


@graph
def chained_retry(parameters: dict, max_attempts: int, attempt: int = 0) -> float:
    """Retry with the handler chain until the step succeeds.

    :param parameters: the settings the handler chain updates per attempt.
    :param max_attempts: the budget; retries continue while ``attempt < max_attempts``.
    :param attempt: the zero-based attempt the first run steps from.
    """
    value, error = mock_step(attempt=attempt)
    fixed = fix_chain(error=error, parameters=parameters)
    retry = error is not None and attempt < max_attempts
    while retry:
        attempt = attempt + 1
        value, error = mock_step(attempt=attempt)
        fixed = fix_chain(error=error, parameters=fixed)
        retry = error is not None and attempt < max_attempts
    return ensure_chain(value=value, error=error)
