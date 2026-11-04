###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Handler chain tasks shared by the graph behavior suites.

Each `@process_handler(priority, exit_codes)` becomes a task: codes outside
the set are declined by returning the inputs unchanged, priority is call
order, and fixed inputs stand in for the handler report. The error arm is
only ever read, never rebound, so nothing is lost on decline.
"""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.restart import RestartErrors
from aiida.engine.processes.graphs.results import Err, Ok, Result


class PwErrors(ExitCodeEnum):
    """Workflow failures, mirroring `PwBaseWorkChain` exit codes."""

    KNOWN_UNRECOVERABLE_FAILURE = ExitCode(310, 'The calculation failed with a known unrecoverable error.')


class PwCalculationErrors(ExitCodeEnum):
    """Parser failures the handlers match, mirroring `PwCalculation` exit codes."""

    OUT_OF_WALLTIME = ExitCode(400, 'The calculation stopped prematurely because it ran out of walltime.')
    COMPUTING_CHOLESKY = ExitCode(462, 'The code failed during the cholesky factorization.')
    DIAGONALIZATION_TOO_MANY_BANDS_NOT_CONVERGED = ExitCode(
        463, 'Too many bands failed to converge during the diagonalization.'
    )


CalculationFailure = PwErrors | PwCalculationErrors | RestartErrors
"""Every failure the chain knows, as one union."""


@task
def mock_pw(attempt: int) -> Result[float, PwCalculationErrors]:
    """Fail twice with handled codes, then succeed."""
    if attempt == 0:
        return Err(PwCalculationErrors.OUT_OF_WALLTIME)
    if attempt == 1:
        return Err(PwCalculationErrors.COMPUTING_CHOLESKY)
    return Ok(1.0)


@task
def handle_walltime(error: CalculationFailure | None, parameters: dict) -> dict:
    """Claim walltime failures, passing anything else through unchanged."""
    if error is not PwCalculationErrors.OUT_OF_WALLTIME:
        return parameters
    updated = dict(parameters)
    updated['restart_mode'] = 'restart'
    return updated


@task
def handle_diagonalization(error: CalculationFailure | None, parameters: dict) -> dict:
    """Claim diagonalization failures, passing anything else through unchanged."""
    if error not in (
        PwCalculationErrors.COMPUTING_CHOLESKY,
        PwCalculationErrors.DIAGONALIZATION_TOO_MANY_BANDS_NOT_CONVERGED,
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
def zero() -> int:
    """Seed the attempt counter."""
    return 0


@task
def step(attempt: int) -> int:
    """Count one further attempt."""
    return attempt + 1


@task
def should_retry(error: CalculationFailure | None, attempt: int, max_attempts: int) -> bool:
    """Retry while a declared failure remains and attempts do."""
    return error is not None and attempt < max_attempts


@task
def ensure(value: float | None, error: CalculationFailure | None) -> float:
    """Read the recovered value, failing loudly when none remains."""
    if error is not None or value is None:
        raise ValueError('the step never succeeded.')
    return value


@graph
def chained_retry(parameters: dict, max_attempts: int) -> float:
    """Retry with the handler chain until the step succeeds."""
    attempt = zero()
    value, error = mock_pw(attempt=attempt)
    fixed = fix_chain(error=error, parameters=parameters)
    retry = should_retry(error=error, attempt=attempt, max_attempts=max_attempts)
    while retry:
        attempt = step(attempt=attempt)
        value, error = mock_pw(attempt=attempt)
        fixed = fix_chain(error=error, parameters=fixed)
        retry = should_retry(error=error, attempt=attempt, max_attempts=max_attempts)
    return ensure(value=value, error=error)
