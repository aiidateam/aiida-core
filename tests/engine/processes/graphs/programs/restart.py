###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Restart-loop programs: a fallible step retried until it succeeds."""

from aiida.engine.processes.exit_code import ExitCode, ExitCodeEnum
from aiida.engine.processes.graphs.lowering import graph, task
from aiida.engine.processes.graphs.restart import RestartErrors
from aiida.engine.processes.graphs.results import Err, Ok, Result
from aiida.orm import StructureData


class StepErrors(ExitCodeEnum):
    """Declared failures of the `run_step` task."""

    UNSTABLE = ExitCode(410, 'Unstable step.')


@task
def zero() -> int:
    """Seed the attempt counter."""
    return 0


@task
def step(attempt: int) -> int:
    """Count one further attempt."""
    return attempt + 1


@task
def should_restart(error: StepErrors | None, attempt: int, max_attempts: int) -> bool:
    """Decide whether another attempt remains after a declared failure."""
    return error is not None and attempt < max_attempts


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
def report_unhandled(value: float | None, error: StepErrors | None) -> Result[float, RestartErrors]:
    """Translate an unrecovered failure into the shared machinery vocabulary."""
    if error is not None or value is None:
        return Err(RestartErrors.UNHANDLED_FAILURE)
    return Ok(value)


@graph
def restartable(structure: StructureData, max_attempts: int) -> float:
    """Retry a fallible step until it succeeds or attempts run out."""
    attempt = zero()
    value, error = run_step(structure=structure, attempt=attempt)
    retry = should_restart(error=error, attempt=attempt, max_attempts=max_attempts)
    while retry:
        attempt = step(attempt=attempt)
        value, error = run_step(structure=structure, attempt=attempt)
        retry = should_restart(error=error, attempt=attempt, max_attempts=max_attempts)
    return ensure(value=value, error=error)
